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


def test_generate_unique_magazyn_id_empty_name_has_timestamp():
    """Test that empty or invalid names get a timestamp suffix to prevent collisions."""
    # Generate IDs for empty names
    id1 = generate_unique_magazyn_id("", set())
    id2 = generate_unique_magazyn_id("   ", set())
    id3 = generate_unique_magazyn_id("!!!", set())
    
    # All should start with MAG_ and have a timestamp suffix
    assert id1.startswith("MAG_")
    assert id2.startswith("MAG_")
    assert id3.startswith("MAG_")
    
    # The suffix should be numeric (timestamp) and format should be MAG_<timestamp>
    assert len(id1.split("_")) == 2 and id1.split("_")[1].isdigit()
    assert len(id2.split("_")) == 2 and id2.split("_")[1].isdigit()
    assert len(id3.split("_")) == 2 and id3.split("_")[1].isdigit()
    
    # IDs should be unique (timestamps may differ if generated at different times)
    # But at minimum, they should not be just "MAG"
    assert id1 != "MAG"
    assert id2 != "MAG"
    assert id3 != "MAG"
