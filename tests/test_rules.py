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


@pytest.mark.parametrize(
    ("location", "is_pink"),
    [
        ("Г-332", False),
        ("Г333", False),
        ("Г-334", True),
        ("Г382", True),
        ("Г-383", False),
        ("Г-456", False),
        ("Г457", True),
        ("Г-4108", True),
        ("Г4109", False),
        ("Г-558", False),
        ("Г559", True),
        ("Г-5104", True),
        ("Г5105", False),
    ],
)
def test_g_building_pink_room_ranges(location, is_pink):
    info = enrich_location(location)

    if is_pink:
        assert info.display_location == f"{location} (розовый корпус)"
        assert info.description_lines == ("Аудитория расположена в «розовом» корпусе Г.",)
    else:
        assert info.display_location == location
        assert not info.description_lines


def test_regular_g_building_room_is_unchanged():
    assert enrich_location("Г-412").display_location == "Г-412"


@pytest.mark.parametrize("location", ["Б-3", "Б-210", "Б-434"])
def test_g_building_rules_do_not_change_b_building_locations(location):
    assert enrich_location(location).display_location.startswith(location)


def test_empty_other_and_unknown_locations_are_safe():
    assert enrich_location(None).display_location is None
    assert enrich_location("А-509").display_location == "А-509"
    assert enrich_location("Б-неизвестно").display_location == "Б-неизвестно"
