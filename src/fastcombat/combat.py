"""Damage, healing, going down and getting up, stuns, and cards counting down.

Every hit and every heal in the game goes through this file, so the tally of
who did what is always right.
"""

from fastcombat.casting import drop_cast
from fastcombat.targeting import apply_loud
from fastcombat.units import Enemy, FightState, Hero, Stack

# Cards that heal their value at the top of each party turn.
HEAL_STACKS = ("rejuvenation", "wild_growth")
# Cards that end the moment the enemy takes any damage.
BROKEN_BY_DAMAGE = ("sap", "sheep")


def add_stack(
    unit: Hero | Enemy, name: str, cards: int, value: int = 0, source: str | None = None
) -> None:
    """Give `unit` a stack of cards, in place of any stack it had with that name.

    `source` is the id of the hero who put it on, if it matters who did
    (heal cards: their healing goes in that hero's tally).
    """
    unit.stacks[name] = Stack(cards, value, source)


def control(state: FightState, enemy: Enemy, name: str, cards: int) -> None:
    """Stun, sap or sheep `enemy` for `cards` cards. `name` says which one.

    While it has those cards, the enemy does nothing on its turn. A new one
    never shortens one already there: if the enemy has more cards of that
    name than `cards`, it keeps the ones it has. A boss never gets them: it
    cannot be stunned, sapped or sheeped. But a stun breaks the cast an
    enemy has announced, and that goes for a boss too. Every ability that
    stuns, saps or sheeps comes through here.
    """
    if name == "stun":
        enemy.announced = None
    if enemy.spec.tier == "boss":
        return
    old = enemy.stacks.get(name)
    if old is None or old.cards < cards:
        add_stack(enemy, name, cards)


def tick_stacks(unit: Hero | Enemy) -> None:
    """One card comes off every stack. An empty stack is gone."""
    for name in list(unit.stacks):
        _take_a_card(unit, name)


def damage_enemy(
    state: FightState,
    hero_id: str,
    enemy: Enemy,
    amount: int,
    *,
    auto: bool = False,
    loud: bool = False,
) -> int:
    """`hero_id` hits `enemy` for `amount`. Gives back the HP really taken off.

    `auto` means it was an auto-attack, for the tally. `loud` means it was a
    Loud hit: if the enemy is still alive afterwards, it loses a Taunt card
    or is pulled toward the hero (see `targeting.apply_loud`). That happens
    even when a shield turned the whole hit aside.
    """
    if enemy.dead:
        return 0
    if amount < enemy.spec.shielded:
        done = 0  # the shield turns the whole hit aside
    elif enemy.spec.tier == "fodder" and amount >= 1:
        done = enemy.hp  # any hit kills fodder
    else:
        done = min(amount, enemy.hp)
    enemy.hp -= done
    if enemy.hp <= 0:
        enemy.dead = True
    if done > 0:
        for name in BROKEN_BY_DAMAGE:
            enemy.stacks.pop(name, None)
    state.tally.damage[hero_id] += done
    if auto:
        state.tally.auto_damage[hero_id] += done
    if loud and not enemy.dead:
        apply_loud(state, hero_id, enemy)
    return done


def damage_hero(
    state: FightState,
    hero: Hero,
    amount: int,
    *,
    attacker: Enemy | None,
    blast: bool = False,
) -> int:
    """`hero` takes `amount` damage. Gives back the HP really lost.

    `attacker` is the enemy whose attack it is, or None for damage no enemy
    is attacking with right now, like poison. Guarded cards take their value
    off any hit, and Bulwark takes its value off a blast. With an Unbroken
    card the hero stops at 1 HP. Damage never breaks a cast.
    """
    if not hero.up:
        return 0  # nobody hits a downed hero, and a hit must not restart the bleeding
    taken = amount
    if "guarded" in hero.stacks:
        taken -= hero.stacks["guarded"].value
    if blast and "bulwark" in hero.stacks:
        taken -= hero.stacks["bulwark"].value
    lowest = 1 if "unbroken" in hero.stacks else 0
    taken = max(0, min(taken, hero.hp - lowest))
    hero.hp -= taken

    if attacker is not None and not blast and hero.cls == "warden":
        pool = state.numbers.heroes[hero.cls].pool
        grit = state.numbers.rules["grit_per_attack"]
        hero.resource = min(pool, hero.resource + grit)

    lowest_hp = state.tally.lowest_hp
    lowest_hp[hero.id] = min(lowest_hp[hero.id], hero.hp / hero.max_hp)
    if hero.hp == 0:
        go_down(state, hero)
    return taken


def go_down(state: FightState, hero: Hero) -> None:
    """`hero` is down: they lose their cast and all their cards, and start bleeding.

    Each wound makes the Bleeding stack one card shorter. With no cards
    left to give, the hero is out at once.
    """
    hero.down = True
    drop_cast(state, hero)  # a blast they were casting will not land
    hero.hidden = False
    hero.stacks.clear()
    state.tally.times_down[hero.id] += 1
    cards = state.numbers.rules["bleeding_cards"] - hero.wounds
    if cards > 0:
        add_stack(hero, "bleeding", cards)
    else:
        _bleed_out(hero)


def get_up(state: FightState, hero: Hero, hp: int) -> None:
    """A downed `hero` gets up on `hp` HP (at most their max) and keeps a wound.

    A hero who is not down (up, or out) is left as they are.
    """
    if not hero.down:
        return
    hero.down = False
    hero.stacks.pop("bleeding", None)
    hero.wounds += 1
    hero.hp = min(hp, hero.max_hp)


def heal_hero(state: FightState, healer_id: str, target: Hero, amount: int) -> int:
    """`healer_id` heals `target` by `amount`. Gives back the HP really healed.

    Any heal gets a downed hero up, on `amount` HP. Nobody can heal a hero
    who is out. Healing past max HP is not counted.
    """
    if target.out or amount <= 0:
        return 0
    if target.down:
        get_up(state, target, amount)
        healed = target.hp
    else:
        healed = min(amount, target.max_hp - target.hp)
        target.hp += healed
    state.tally.healing[healer_id] += healed
    return healed


def top_of_party_turn_cards(state: FightState) -> None:
    """Every hero who is not out turns in one card from each stack they hold.

    Heal cards heal (the hero who put them on gets the credit, or the hero
    holding them if nobody did) and poison hurts. Then each stack the hero
    held when this began loses one card. A stack that went away in between,
    because the hero went down or got up, does not. Bleeding cards are the
    one exception: they come off at the end of the party turn instead, in
    `end_of_party_turn_cards`.
    """
    for hero in state.heroes.values():
        if hero.out:
            continue
        held = dict(hero.stacks)
        for name in HEAL_STACKS:
            if name in hero.stacks:
                stack = hero.stacks[name]
                heal_hero(state, stack.source or hero.id, hero, stack.value)
        if "poison" in hero.stacks:
            damage_hero(state, hero, hero.stacks["poison"].value, attacker=None)
        for name, stack in held.items():
            if name == "bleeding" or hero.stacks.get(name) is not stack:
                continue
            _take_a_card(hero, name)


def end_of_party_turn_cards(state: FightState) -> None:
    """Every hero who is down loses one Bleeding card, after everyone has acted.

    This comes at the end of the party turn so that even a hero with one
    card left gets a whole party turn in which someone can save them. When
    the last card comes off, the hero is out. A hero who got up this turn
    has no Bleeding cards and is left alone.
    """
    for hero in state.heroes.values():
        if not hero.down:
            continue
        _take_a_card(hero, "bleeding")
        if "bleeding" not in hero.stacks:
            _bleed_out(hero)


def _take_a_card(unit: Hero | Enemy, name: str) -> None:
    stack = unit.stacks[name]
    stack.cards -= 1
    if stack.cards <= 0:
        del unit.stacks[name]


def _bleed_out(hero: Hero) -> None:
    """The hero is out for the rest of the fight. Out is not the same as down."""
    hero.down = False
    hero.out = True
