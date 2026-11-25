"""The tuned numbers meet every target in the design.

This plays 600 fights with the whole party, and 600 more without each hero,
so it is slow. Run it with `uv run pytest -m slow`.
"""

import pytest
from fastcombat.cli import main


@pytest.mark.slow
def test_the_numbers_meet_the_targets():
    assert main(["check", "--n", "600", "--seed", "500000"]) == 0
