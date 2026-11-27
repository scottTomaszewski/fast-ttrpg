import json
from dataclasses import replace

from tests.helpers import GAME, REAL_GAME
from fastcombat.numbers import load_numbers, load_fight, load_usage
from fastcombat.fight import run_fight
from fastcombat.report import Summary, summarize, check_targets, format_summary, format_checks
from fastcombat.cli import main
from fastcombat.policies import AutoOnly, POLICIES

N = load_numbers(GAME / "numbers.toml"); F = load_fight(GAME / "fights" / "ogre_warlord.toml")
PARTY = ["guardian", "rogue", "druid", "mage"]
# The command line reads the real game files unless told otherwise. These
# tests point it at the tests' frozen copy, so tuning cannot break them.
FILES = ["--numbers", str(GAME / "numbers.toml"), "--fight", str(GAME / "fights" / "ogre_warlord.toml")]

def test_summary_adds_up():
    s = summarize([run_fight(N, F, PARTY, seed=i) for i in range(20)])
    assert s.fights == 20 and 0 <= s.win_rate <= 1 and s.rounds_p10 <= s.rounds_median <= s.rounds_p90
    assert abs(sum(s.damage_share.values()) - 1) < 1e-9 and 0 <= s.auto_share <= 1
    assert set(s.starved) == set(PARTY)

def test_checks_are_the_agreed_list():
    full = summarize([run_fight(N, F, PARTY, seed=i) for i in range(10)])
    without = {h: summarize([run_fight(N, F, [p for p in PARTY if p != h], seed=i) for i in range(10)]) for h in PARTY}
    on_auto = {h: summarize([run_fight(N, F, PARTY, policies={h: AutoOnly()}, seed=i) for i in range(10)]) for h in PARTY}
    no_boss_taunt = summarize([run_fight(N, F, PARTY, policies={"guardian": POLICIES["guardian_no_boss_taunt"]()},
                                         seed=i) for i in range(10)])
    names = [c.name for c in check_targets(full, without, on_auto, no_boss_taunt)]
    assert names == ["length", "win_rate", "no_timeouts", "danger", "auto_share",
                     "resource:guardian", "resource:rogue", "resource:druid", "resource:mage",
                     "needed:guardian", "needed:rogue", "needed:druid", "needed:mage",
                     "kit:guardian", "kit:rogue", "kit:druid", "kit:mage", "taunt:boss"]
    assert "taunt:boss" not in [c.name for c in check_targets(full, without, on_auto)]

def test_run_prints_a_summary_and_takes_a_changed_number(capsys):
    assert main(["run", "--n", "5", *FILES, "--set", "abilities.meteor.cost=12"]) == 0
    assert "win" in capsys.readouterr().out.lower()

def test_a_bad_setting_is_a_clean_error(capsys):
    assert main(["run", "--n", "1", *FILES, "--set", "abilities.meteor.cots=1"]) == 2
    assert "abilities.meteor.cots" in capsys.readouterr().err

def test_an_unknown_class_in_the_party_is_a_clean_error(capsys):
    assert main(["run", "--n", "1", *FILES, "--party", "guardian,bard"]) == 2
    assert "bard" in capsys.readouterr().err


# --- What the summary counts -------------------------------------------------

def test_the_summary_counts_from_the_tallies():
    a = run_fight(N, F, PARTY, seed=1); b = run_fight(N, F, PARTY, seed=2)
    s = summarize([a, b])
    damage = sum(sum(r.tally.damage.values()) for r in (a, b))
    autos = sum(sum(r.tally.auto_damage.values()) for r in (a, b))
    assert s.auto_share == autos / damage
    assert s.damage_share["mage"] == (a.tally.damage["mage"] + b.tally.damage["mage"]) / damage
    assert s.rounds_median == (a.rounds + b.rounds) / 2
    starved = [r.tally.starved_rounds["druid"] / r.tally.up_rounds["druid"] for r in (a, b)]
    assert s.starved["druid"] == sum(starved) / 2
    assert s.lowest_hp["mage"] == (a.tally.lowest_hp["mage"] + b.tally.lowest_hp["mage"]) / 2
    # the curve is as long as the longest fight
    assert len(s.resource_curve["mage"]) == max(a.rounds, b.rounds)

def test_danger_and_down_and_ended_full():
    r = run_fight(N, F, PARTY, seed=1)
    calm = replace(r, tally=replace(r.tally, lowest_hp={h: 0.9 for h in PARTY}, times_down={h: 0 for h in PARTY}),
                   end_resource={h: 0 for h in PARTY}, heroes_up=list(PARTY))
    low = replace(calm, tally=replace(calm.tally, lowest_hp={**calm.tally.lowest_hp, "mage": 0.25}))
    down = replace(calm, tally=replace(calm.tally, times_down={**calm.tally.times_down, "rogue": 2}),
                   end_resource={**calm.end_resource, "guardian": r.pool["guardian"]})
    s = summarize([calm, low, down, calm])
    assert s.danger_rate == 0.5
    assert s.down_rate == {"guardian": 0, "rogue": 0.25, "druid": 0, "mage": 0}
    assert s.ended_full == {"guardian": 0.25, "rogue": 0, "druid": 0, "mage": 0}

def test_a_hero_who_is_not_up_at_the_end_did_not_end_full():
    r = run_fight(N, F, PARTY, seed=1)
    full = {h: r.pool[h] for h in PARTY}
    up = replace(r, end_resource=full, heroes_up=list(PARTY))
    fallen = replace(up, heroes_up=["guardian", "rogue"])            # the druid is down, the mage is out
    s = summarize([up, fallen])
    assert s.ended_full == {"guardian": 1, "rogue": 1, "druid": 0.5, "mage": 0.5}

def test_a_fight_knows_who_is_up_at_the_end():
    r = run_fight(N, F, PARTY, seed=1)
    assert not r.won and r.heroes_up == []                          # the party lost: nobody is up
    one_wolf = replace(F, spawns=[s for s in F.spawns if s.type == "wolf"][:1], boss_script=[])
    won = run_fight(N, one_wolf, PARTY, seed=0)
    assert won.won and won.heroes_up == PARTY                       # an easy win: everyone is still up

def test_the_printed_summary_says_ended_full_means_up_and_full():
    text = format_summary(summarize([run_fight(N, F, PARTY, seed=1)]))
    assert "up and full" in text

def test_starved_counts_only_the_rounds_a_hero_was_up():
    r = run_fight(N, F, PARTY, seed=1)
    tally = replace(r.tally, starved_rounds={**r.tally.starved_rounds, "mage": 3},
                    up_rounds={**r.tally.up_rounds, "mage": 4})      # down or out for the rest
    assert summarize([replace(r, rounds=20, tally=tally)]).starved["mage"] == 0.75
    never_up = replace(tally, starved_rounds={**tally.starved_rounds, "mage": 0},
                       up_rounds={**tally.up_rounds, "mage": 0})
    assert summarize([replace(r, tally=never_up)]).starved["mage"] == 0

def test_the_printed_summary_shows_each_heros_lowest_hp():
    r = run_fight(N, F, PARTY, seed=1)
    low = replace(r, tally=replace(r.tally, lowest_hp={"guardian": 0.5, "rogue": 0.25, "druid": 1.0, "mage": 0.0}))
    text = format_summary(summarize([low]))
    assert "lowest HP" in text
    lines = text.splitlines()
    table = lines.index(next(line for line in lines if "lowest HP" in line))
    rows = {line.split()[0]: line.split() for line in lines[table + 1:table + 5]}
    assert rows["guardian"][-1] == "50%" and rows["rogue"][-1] == "25%" and rows["mage"][-1] == "0%"

def test_the_summary_counts_the_mean_uses_of_every_button_per_fight():
    a = run_fight(N, F, PARTY, seed=1); b = run_fight(N, F, PARTY, seed=2)
    s = summarize([a, b])
    assert list(s.uses) == list(a.kit) and s.kit == a.kit
    assert s.uses["taunt"] == (a.tally.uses["guardian"].get("taunt", 0)
                               + b.tally.uses["guardian"].get("taunt", 0)) / 2
    # a shared button adds up every hero's uses
    disrupts = sum(r.tally.uses[h].get("disrupt", 0) for r in (a, b) for h in PARTY)
    assert s.uses["disrupt"] == disrupts / 2

def test_a_button_never_pressed_is_still_in_the_summary_at_zero():
    r = run_fight(N, F, PARTY, seed=1)
    none = replace(r, tally=replace(r.tally, uses={h: {} for h in PARTY}))
    s = summarize([none])
    assert s.uses["meteor"] == 0 and s.uses["haul_up"] == 0 and len(s.uses) == len(r.kit)

def test_only_the_buttons_of_the_classes_in_the_party_are_counted():
    r = run_fight(N, F, ["mage", "mage"], seed=1)
    uses = {"mage": {"firebolt": 2}, "mage2": {"firebolt": 3}}
    s = summarize([replace(r, tally=replace(r.tally, uses=uses))])
    assert "meteor" in s.uses and "disrupt" in s.uses and "taunt" not in s.uses
    assert s.uses["firebolt"] == 5                              # both mages count together

def test_the_printed_summary_lists_the_uses_by_hero():
    r = run_fight(N, F, PARTY, seed=1)
    uses = {h: {} for h in PARTY} | {"guardian": {"taunt": 4}, "mage": {"meteor": 1}, "rogue": {"disrupt": 2}}
    text = format_summary(summarize([replace(r, tally=replace(r.tally, uses=uses))]))
    lines = [line.split() for line in text.splitlines()]
    assert ["taunt", "4.0"] in lines and ["meteor", "1.0"] in lines and ["disrupt", "2.0"] in lines
    assert ["vanish", "0.0"] in lines and ["haul_up", "0.0"] in lines
    # each hero's buttons come under the hero's name; shared ones come last
    names = [line[0] for line in lines if line]
    assert names.index("guardian", names.index("Uses")) < names.index("taunt") < names.index("rogue", names.index("taunt"))
    assert names.index("anyone") < names.index("disrupt") and names.index("mage", names.index("taunt")) < names.index("meteor")

def test_a_fight_knows_each_heros_full_pool():
    r = run_fight(N, F, ["mage", "rogue", "rogue"], seed=0)
    assert r.pool == {"mage": N.heroes["mage"].pool, "rogue": N.heroes["rogue"].pool,
                      "rogue2": N.heroes["rogue"].pool}


# --- The checks -----------------------------------------------------------

USAGE = load_usage(REAL_GAME / "usage_targets.toml", N)

def test_a_use_check_for_each_button_when_usage_targets_are_given():
    full = good(uses={"taunt": 3.0, "backstab": 99.0, "haul_up": 0.0},
                kit={"taunt": "guardian", "backstab": "rogue", "haul_up": "shared"})
    checks = check_targets(full, {}, {}, None, USAGE)
    assert [c.name for c in checks][-3:] == ["use:taunt", "use:backstab", "use:haul_up"]
    assert all(c.passed for c in checks)
    assert not any(c.name.startswith("use:") for c in check_targets(full, {}, {}, None))

def test_a_use_check_passes_only_inside_its_band():
    kit = {"taunt": "guardian", "backstab": "rogue"}
    def ok(**uses):
        return passed_use(good(uses=uses, kit={a: kit[a] for a in uses}))
    assert ok(taunt=3.0)["use:taunt"] and ok(taunt=10.0)["use:taunt"]
    assert not ok(taunt=2.9)["use:taunt"] and not ok(taunt=10.1)["use:taunt"]
    assert ok(backstab=1000.0)["use:backstab"] and not ok(backstab=3.9)["use:backstab"]

def passed_use(full):
    return {c.name: c.passed for c in check_targets(full, {}, {}, None, USAGE)}

def test_a_use_check_says_how_often_and_what_was_wanted():
    full = good(uses={"taunt": 2.25, "backstab": 5.0}, kit={"taunt": "guardian", "backstab": "rogue"})
    checks = {c.name: c for c in check_targets(full, {}, {}, None, USAGE)}
    assert "2.2" in checks["use:taunt"].value and "3 to 10" in checks["use:taunt"].wanted
    assert "at least 4" in checks["use:backstab"].wanted

def test_a_hero_starved_a_fifth_of_their_rounds_fails_the_resource_check():
    assert passed(good(starved={"guardian": 0.19, "mage": 0.0}))["resource:guardian"]
    assert not passed(good(starved={"guardian": 0.2, "mage": 0.0}))["resource:guardian"]

def good(**changes) -> Summary:
    """A summary that meets every target, with some numbers changed."""
    heroes = ["guardian", "mage"]
    s = Summary(fights=100, win_rate=0.8, timeout_rate=0.0, rounds_median=20, rounds_p10=18,
                rounds_p90=22, in_band=0.6, danger_rate=0.5, down_rate={h: 0.1 for h in heroes},
                auto_share=0.3, damage_share={h: 0.5 for h in heroes},
                healing_share={h: 0.5 for h in heroes}, starved={h: 0.1 for h in heroes},
                ended_full={h: 0.2 for h in heroes}, lowest_hp={h: 0.5 for h in heroes},
                resource_curve={h: [] for h in heroes}, uses={}, kit={})
    return replace(s, **changes)

def passed(full, without=None, on_auto=None, no_boss_taunt=None):
    return {c.name: c.passed for c in check_targets(full, without or {}, on_auto or {}, no_boss_taunt)}

def test_a_summary_at_the_edges_of_every_target_passes():
    assert all(passed(good(), {"mage": good(win_rate=0.6)}).values())
    # 0.7 - 0.5 is a hair under 0.2 to a computer; it still counts as 0.2
    assert all(passed(good(win_rate=0.7), {"mage": good(win_rate=0.5)}).values())
    assert all(passed(good(win_rate=0.9, auto_share=0.5)).values())
    assert all(passed(good(win_rate=0.7, auto_share=0.2)).values())
    # the kit check: 0.7 - 0.6 is a hair under 0.1 to a computer; it still counts as 0.1
    assert all(passed(good(win_rate=0.7), on_auto={"mage": good(win_rate=0.6)}).values())
    # the boss-taunt check: the same hair under 0.1 still counts as 0.1
    assert all(passed(good(win_rate=0.7), no_boss_taunt=good(win_rate=0.6)).values())

def test_each_target_can_fail():
    assert not passed(good(in_band=0.59))["length"]
    assert not passed(good(win_rate=0.91))["win_rate"]
    assert not passed(good(win_rate=0.69))["win_rate"]
    assert not passed(good(timeout_rate=0.01))["no_timeouts"]
    assert not passed(good(danger_rate=0.49))["danger"]
    assert not passed(good(auto_share=0.51))["auto_share"]
    assert not passed(good(auto_share=0.19))["auto_share"]
    assert not passed(good(starved={"guardian": 0.2, "mage": 0.1}))["resource:guardian"]
    assert not passed(good(ended_full={"guardian": 0.2, "mage": 0.5}))["resource:mage"]
    assert not passed(good(), {"mage": good(win_rate=0.61)})["needed:mage"]
    assert not passed(good(), on_auto={"mage": good(win_rate=0.71)})["kit:mage"]
    assert not passed(good(), on_auto={"mage": good(win_rate=0.9)})["kit:mage"]   # a kit that hurts
    assert not passed(good(), no_boss_taunt=good(win_rate=0.71))["taunt:boss"]
    assert not passed(good(), no_boss_taunt=good(win_rate=0.9))["taunt:boss"]    # taunting the boss hurts

def test_the_printed_checks_say_pass_or_fail():
    text = format_checks(check_targets(good(win_rate=0.95), {}))
    assert "FAIL" in text and "PASS" in text and "win_rate" in text
    assert len(text.splitlines()) == 7          # five checks and one per hero

def test_the_printed_summary_names_every_hero():
    text = format_summary(summarize([run_fight(N, F, ["mage", "mage"], seed=i) for i in range(3)]))
    assert "mage" in text and "mage2" in text and "win" in text.lower()


# --- The command line --------------------------------------------------------

def test_run_writes_the_summary_as_json(tmp_path, capsys):
    out = tmp_path / "s.json"
    assert main(["run", "--n", "3", "--seed", "7", *FILES, "--json", str(out)]) == 0
    data = json.loads(out.read_text())
    expected = summarize([run_fight(N, F, PARTY, seed=i) for i in range(7, 10)])
    assert data["fights"] == 3 and data["damage_share"] == expected.damage_share

def test_a_changed_number_changes_the_fights(tmp_path):
    plain, changed = tmp_path / "a.json", tmp_path / "b.json"
    main(["run", "--n", "3", *FILES, "--json", str(plain)])
    main(["run", "--n", "3", *FILES, "--set", "heroes.mage.hp=1", "--json", str(changed)])
    assert json.loads(plain.read_text()) != json.loads(changed.read_text())

def test_a_set_value_is_read_as_toml(capsys):
    # a word in quotes, a list, true: each goes in as itself, so a wrong kind is a clean error
    assert main(["run", "--n", "1", *FILES, "--set", 'heroes.mage.pool="lots"']) == 2
    assert "heroes.mage.pool" in capsys.readouterr().err
    assert main(["run", "--n", "1", *FILES, "--set", "abilities.meteor.dice=[3, 6]"]) == 0

def test_a_set_without_an_equals_sign_is_a_clean_error(capsys):
    assert main(["run", "--n", "1", *FILES, "--set", "abilities.meteor.cost"]) == 2
    assert "abilities.meteor.cost" in capsys.readouterr().err

def test_a_policy_can_be_picked_per_hero(tmp_path):
    plain, auto = tmp_path / "a.json", tmp_path / "b.json"
    main(["run", "--n", "3", *FILES, "--json", str(plain)])
    main(["run", "--n", "3", *FILES, "--policy", "mage=auto", "--json", str(auto)])
    assert json.loads(plain.read_text()) != json.loads(auto.read_text())

def test_an_unknown_hero_or_policy_is_a_clean_error(capsys):
    assert main(["run", "--n", "1", *FILES, "--policy", "rogue2=auto"]) == 2
    assert "rogue2" in capsys.readouterr().err
    assert main(["run", "--n", "1", *FILES, "--policy", "mage=sleepy"]) == 2
    assert "sleepy" in capsys.readouterr().err

def test_an_unknown_fight_is_a_clean_error(capsys):
    assert main(["run", "--n", "1", "--numbers", str(GAME / "numbers.toml"), "--fight", "dragon"]) == 2
    assert "dragon" in capsys.readouterr().err

def test_check_removes_each_hero_in_turn_and_fails_on_a_missed_target(capsys):
    # The frozen numbers are not tuned: the party loses, so some checks fail.
    code = main(["check", "--n", "2", *FILES, "--party", "guardian,rogue,rogue"])
    out = capsys.readouterr().out
    assert code == 1 and "FAIL" in out
    for name in ("needed:guardian", "needed:rogue", "needed:rogue2", "resource:rogue2",
                 "kit:guardian", "kit:rogue", "kit:rogue2"):
        assert name in out

def test_check_plays_each_hero_on_auto_and_writes_it_down(tmp_path, capsys):
    out = tmp_path / "c.json"
    main(["check", "--n", "2", *FILES, "--party", "guardian,mage", "--json", str(out)])
    data = json.loads(out.read_text())
    assert set(data["on_auto"]) == {"guardian", "mage"}
    expected = summarize([run_fight(N, F, ["guardian", "mage"], policies={"mage": AutoOnly()}, seed=i)
                          for i in range(2)])
    assert data["on_auto"]["mage"]["damage_share"] == expected.damage_share
    names = [c["name"] for c in data["checks"]]
    assert names[-3:] == ["kit:guardian", "kit:mage", "taunt:boss"]

def test_check_plays_the_guardian_without_boss_taunts_and_writes_it_down(tmp_path, capsys):
    out = tmp_path / "c.json"
    main(["check", "--n", "2", *FILES, "--party", "mage,guardian", "--json", str(out)])
    data = json.loads(out.read_text())
    no_taunt = {"guardian": POLICIES["guardian_no_boss_taunt"]()}
    expected = summarize([run_fight(N, F, ["mage", "guardian"], policies=no_taunt, seed=i) for i in range(2)])
    assert data["no_boss_taunt"]["damage_share"] == expected.damage_share
    assert "taunt:boss" in capsys.readouterr().out

def test_check_has_no_boss_taunt_check_without_a_guardian(tmp_path, capsys):
    out = tmp_path / "c.json"
    main(["check", "--n", "2", *FILES, "--party", "rogue,mage", "--json", str(out)])
    data = json.loads(out.read_text())
    assert data["no_boss_taunt"] is None
    assert "taunt:boss" not in [c["name"] for c in data["checks"]]
    assert "taunt:boss" not in capsys.readouterr().out

def test_check_has_no_boss_taunt_check_when_the_guardian_is_made_to_auto_attack(tmp_path, capsys):
    # A Guardian on `auto` never Taunts anyone, so there is nothing to switch off.
    out = tmp_path / "c.json"
    main(["check", "--n", "2", *FILES, "--party", "guardian,mage", "--policy", "guardian=auto",
          "--json", str(out)])
    data = json.loads(out.read_text())
    assert data["no_boss_taunt"] is None
    assert "taunt:boss" not in [c["name"] for c in data["checks"]]
    assert "taunt:boss" not in capsys.readouterr().out

def test_check_has_use_checks_only_for_a_party_of_one_of_each_class(tmp_path, capsys):
    out = tmp_path / "c.json"
    main(["check", "--n", "2", *FILES, "--party", "mage,druid,guardian,rogue", "--json", str(out)])
    names = [c["name"] for c in json.loads(out.read_text())["checks"]]
    assert [n for n in names if n.startswith("use:")] == [f"use:{a}" for a in N.abilities] + ["use:haul_up"]
    assert "use:meteor" in capsys.readouterr().out
    main(["check", "--n", "2", *FILES, "--party", "guardian,rogue,druid,mage,mage", "--json", str(out)])
    assert not any(c["name"].startswith("use:") for c in json.loads(out.read_text())["checks"])

def test_check_reads_the_usage_targets_given(tmp_path, capsys):
    usage = tmp_path / "u.toml"
    usage.write_text((REAL_GAME / "usage_targets.toml").read_text() + "\n[fireball]\nmin = 1\n")
    assert main(["check", "--n", "1", *FILES, "--usage", str(usage)]) == 2
    assert "fireball" in capsys.readouterr().err
