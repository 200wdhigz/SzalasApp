from src.id_utils import generate_unique_magazyn_id, slugify_id


def test_slugify_id_is_alnum_only_and_max_8():
    assert slugify_id("Magazyn Warszawa") == "magazynw"


def test_slugify_id_drops_non_alnum_and_limits_length():
    # Polskie znaki mogą zostać utracone w ASCII, wynik ma być alnum i max 8.
    out = slugify_id("Magazyn Łąka Żółw")
    assert out.isalnum()
    assert len(out) <= 8


def test_generate_unique_magazyn_id_base():
    assert generate_unique_magazyn_id("Magazyn Warszawa", set()) == "MAG_MAGAZYNW"


def test_generate_unique_magazyn_id_suffix_increment():
    existing = {"MAG_MAGAZYNW", "MAG_MAGAZYNW_2"}
    assert generate_unique_magazyn_id("Magazyn Warszawa", existing) == "MAG_MAGAZYNW_3"
