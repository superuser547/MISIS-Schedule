import pytest

from misis_schedule.rules import enrich_location


@pytest.mark.parametrize("room", ["Б-3", "Б-4"])
def test_b_building_ground_floor(room):
    info = enrich_location(room)
    assert info.display_location.endswith("(1-й этаж)")
    assert "лифты" not in " ".join(info.description_lines)


@pytest.mark.parametrize("room", ["Б-210", "Б-901", "Б-1001"])
def test_b_building_any_elevators(room):
    assert "Любые лифты" in enrich_location(room).display_location


@pytest.mark.parametrize("room", ["Б-434", "Б-1135"])
def test_b_building_left_elevators(room):
    assert "Только левые лифты" in enrich_location(room).display_location


def test_empty_other_and_unknown_locations_are_safe():
    assert enrich_location(None).display_location is None
    assert enrich_location("А-509").display_location == "А-509"
    assert enrich_location("Б-неизвестно").display_location == "Б-неизвестно"
