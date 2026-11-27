"""Tests for making the player rules from their templates."""

from pathlib import Path

import pytest

from fastcombat import cli
from fastcombat.rules_doc import RulesError, load_game, render, render_all
from tests.helpers import GAME, REAL_GAME

RULES = Path(__file__).parent.parent / "rules"


@pytest.fixture
def game():
    """The tests' frozen copy of the game files."""
    return load_game(GAME)


def test_a_number_is_filled_in(game):
    text = "Meteor costs {abilities.meteor.cost} mana. The Warden has {heroes.warden.hp} HP."
    assert render(text, game, "core.md") == "Meteor costs 10 mana. The Warden has 60 HP."


def test_rules_enemies_and_boss_moves_are_filled_in(game):
    text = "{rules.bleeding_cards} {enemy.wolf.hp} {boss.ground_slam.radius} {fight.width}"
    assert render(text, game, "core.md") == "3 16 2 16"


def test_dice_are_written_like_8d6(game):
    assert render("{abilities.meteor.dice}", game, "core.md") == "8d6"
    assert render("{boss.ground_slam.dice}", game, "core.md") == "3d6"


def test_dice_with_a_bonus_are_written_like_2d6_plus_2(game):
    assert render("{enemy.ogre.dice}", game, "core.md") == "2d6+2"
    assert render("{abilities.regrowth.dice}", game, "core.md") == "3d6+4"


def test_something_that_rolls_no_dice_has_no_dice_placeholder(game):
    with pytest.raises(RulesError, match=r"abilities\.taunt\.dice"):
        render("{abilities.taunt.dice}", game, "core.md")


def test_true_and_false_are_written_yes_and_no(game):
    text = "{abilities.eviscerate.loud} {abilities.backstab.loud}"
    assert render(text, game, "core.md") == "yes no"


def test_a_loud_ability_is_marked_loud(game):
    text = "Eviscerate{abilities.eviscerate.loud_tag}. Backstab{abilities.backstab.loud_tag}."
    assert render(text, game, "core.md") == "Eviscerate · **Loud**. Backstab."


def test_how_long_an_ability_takes_is_written_out(game):
    text = "{abilities.taunt.timing}|{abilities.firebolt.timing}|{abilities.meteor.timing}|{abilities.arcane_volley.timing}"
    assert render(text, game, "core.md") == "Instant|Cast, 1 round|Cast, 2 rounds|Channel, 3 hits"


def test_numbers_can_be_added_and_taken_away(game):
    text = "{heroes.mage.hp - enemy.wolf.damage} {rules.bleeding_cards + 1} {10 - abilities.backstab.cost}"
    assert render(text, game, "core.md") == "24 4 6"


def test_a_sum_that_comes_out_below_zero_is_an_error(game):
    with pytest.raises(RulesError, match="below 0"):
        render("{1 - abilities.meteor.cost}", game, "core.md")


def test_a_sum_of_something_that_is_not_a_number_is_an_error(game):
    with pytest.raises(RulesError, match="not a number"):
        render("{abilities.meteor.dice + 1}", game, "core.md")


def test_the_rounds_a_boss_move_comes_up_are_listed(game):
    # The frozen Ground Slam: first in round 3, then every 4 rounds.
    assert render("{boss.ground_slam.rounds}", game, "core.md") == "3, 7, 11, 15, 19 and so on"


def test_how_many_enemies_of_a_kind_come_and_when(game):
    assert render("{spawns.wolf.count} {spawns.wolf.round}", game, "core.md") == "2 0"


def test_enemies_of_a_kind_that_come_in_different_rounds_have_no_one_round(game):
    # The frozen goblins come in two waves.
    with pytest.raises(RulesError, match="different rounds"):
        render("{spawns.goblin.round}", game, "core.md")


def test_a_note_is_left_out(game):
    text = "{# A note for whoever edits this. #}\n\nFirst.\n\n{# Another,\nover two lines. #}\n\nSecond."
    assert render(text, game, "core.md") == "First.\n\nSecond."


def test_an_unknown_placeholder_names_the_file_and_the_placeholder(game):
    with pytest.raises(RulesError) as caught:
        render("Fine: {heroes.mage.hp}. Wrong: {heroes.wizard.hp}.", game, "classes/mage.md")
    assert "classes/mage.md" in str(caught.value)
    assert "{heroes.wizard.hp}" in str(caught.value)


@pytest.mark.parametrize(
    "placeholder",
    ["{abilities.meteor.costt}", "{rules.nope}", "{enemy.dragon.hp}", "{boss.stomp.dice}", "{}", "{cost}"],
)
def test_every_kind_of_unknown_placeholder_is_an_error(game, placeholder):
    with pytest.raises(RulesError, match="unknown placeholder"):
        render(placeholder, game, "core.md")


@pytest.mark.parametrize(
    "text",
    ["HP {heroes.mage.hp", "HP heroes.mage.hp}", "{# a note that never ends\n\nHP {heroes.mage.hp}."],
)
def test_a_brace_left_over_is_an_error_naming_the_file(game, text):
    # An unclosed placeholder or note would end up in the rules as it is.
    with pytest.raises(RulesError, match=r"classes/mage\.md.*left over"):
        render(text, game, "classes/mage.md")


def test_how_many_enemies_a_fight_has_in_all(game):
    # The frozen fight: an ogre, a brute, two shamans, two wolves and twelve
    # goblins.
    assert render("{fight.enemies}", game, "core.md") == "18"


def test_the_biggest_roll_is_written_like_dice(game):
    # The frozen Meteor is 8d6, the most dice rolled at once.
    assert render("{dice.biggest} {dice.most}", game, "core.md") == "8d6 8"


def test_a_fight_can_be_named(game):
    assert render("{fights.ogre_warlord.enemy.brute.shielded}", game, "core.md") == "5"


def test_the_map_shows_where_everyone_starts(game):
    lines = render("{fight.map}", game, "core.md").splitlines()
    rows = [line.split(" ") for line in lines[:12]]
    assert len(rows) == 12 and all(len(row) == 16 for row in rows)
    assert rows[6][3] == "W" and rows[5][2] == "R" and rows[7][1] == "D" and rows[5][1] == "M"
    assert rows[6][11] == "o" and rows[7][10] == "b" and rows[3][10] == "w"
    assert rows[7][2] == "+"  # a start square for a fifth hero
    legend = "\n".join(lines[12:])
    assert "W Warden" in legend and "o ogre" in legend
    assert "g goblin" in legend and "round 6" in legend


def test_render_all_makes_one_file_for_each_template(tmp_path, game):
    templates = tmp_path / "templates"
    (templates / "classes").mkdir(parents=True)
    (templates / "core.md").write_text("Bleeding: {rules.bleeding_cards}\n")
    (templates / "classes" / "mage.md").write_text("HP {heroes.mage.hp}\n")
    made = render_all(tmp_path, game)
    assert set(made) == {Path("core.md"), Path("classes/mage.md")}
    assert made[Path("core.md")].endswith("Bleeding: 3\n")
    assert "templates/core.md" in made[Path("core.md")].splitlines()[0]


def test_no_templates_folder_is_an_error(tmp_path, game):
    with pytest.raises(RulesError, match="no templates"):
        render_all(tmp_path, game)


def test_a_template_under_fights_uses_its_own_fight(tmp_path):
    # Two fights, so only the fight sheet's own name says which one it means.
    game_dir = tmp_path / "game"
    (game_dir / "fights").mkdir(parents=True)
    (game_dir / "numbers.toml").write_text((GAME / "numbers.toml").read_text())
    fight = (GAME / "fights" / "ogre_warlord.toml").read_text()
    (game_dir / "fights" / "ogre_warlord.toml").write_text(fight)
    (game_dir / "fights" / "other.toml").write_text(fight.replace("hp = 16", "hp = 99"))
    rules = tmp_path / "rules"
    (rules / "templates" / "fights").mkdir(parents=True)
    (rules / "templates" / "fights" / "other.md").write_text("{enemy.wolf.hp}\n")
    two = load_game(game_dir)
    assert render_all(rules, two)[Path("fights/other.md")].endswith("99\n")
    (rules / "templates" / "core.md").write_text("{enemy.wolf.hp}\n")
    with pytest.raises(RulesError, match="core.md.*which fight"):
        render_all(rules, two)


def test_the_rules_command_writes_the_files(tmp_path, monkeypatch, capsys):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "core.md").write_text("Move {rules.hero_move}.\n")
    monkeypatch.setattr(cli, "RULES", tmp_path)
    assert cli.main(["rules"]) == 0
    assert (tmp_path / "core.md").read_text().endswith("Move 6.\n")
    assert "core.md" in capsys.readouterr().out


def test_the_rules_command_stops_on_an_unknown_placeholder(tmp_path, monkeypatch, capsys):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "core.md").write_text("Move {rules.hero_moves}.\n")
    monkeypatch.setattr(cli, "RULES", tmp_path)
    assert cli.main(["rules"]) == 2
    assert "{rules.hero_moves}" in capsys.readouterr().err
    assert not (tmp_path / "core.md").exists()


def test_the_rules_in_the_repo_are_up_to_date():
    """The rules in `rules/` must be what the templates make from the real game files.

    If this fails, a number or a template changed and nobody ran the command.
    """
    made = render_all(RULES, load_game(REAL_GAME))
    assert Path("core.md") in made and Path("classes/warden.md") in made
    for path, text in made.items():
        written = RULES / path
        assert written.exists(), f"rules/{path} is missing: run `uv run fastcombat rules`"
        assert written.read_text() == text, (
            f"rules/{path} is out of date: run `uv run fastcombat rules`"
        )
    for written in RULES.rglob("*.md"):
        path = written.relative_to(RULES)
        if path.parts[0] != "templates":
            assert path in made, f"rules/{path} has no template in rules/templates/"
