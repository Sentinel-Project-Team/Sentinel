import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from system_prompt import build_system_prompt, load_canaries  # noqa: E402


def test_at_least_three_canaries():
    canaries = load_canaries()
    assert len(canaries) >= 3


def test_canary_values_are_unique_and_not_empty():
    values = [c["value"] for c in load_canaries()]
    assert all(v.strip() for v in values)
    assert len(values) == len(set(values))



def test_every_canary_appears_in_system_prompt():
    canaries = load_canaries()
    prompt = build_system_prompt(canaries)
    for c in canaries:
        assert c["value"] in prompt, f"{c['id']} missing from system prompt"