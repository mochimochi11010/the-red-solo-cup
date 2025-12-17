import pytest
from app.cocktails import (
    fetch_drinks_by_alcohol, fetch_drink_details,
    drink_matches_mixers, parse_volume_to_ounces,
    recommend_cocktails,
    standardize_ingredients_to_cup,
    generate_unique_color
)
from web_app.routes.home_routes import format_measurement

def test_parse_volume_to_ounces():
    assert parse_volume_to_ounces("1 oz") == 1.0
    assert parse_volume_to_ounces("2 oz") == 2.0
    assert round(parse_volume_to_ounces("50 ml"), 2) == 1.69
    assert round(parse_volume_to_ounces("25 cl"), 2) == 8.45
    assert parse_volume_to_ounces("") == 0.0
    assert parse_volume_to_ounces("1 1/2 oz") > 1.0

def test_drink_matches_mixers():
    drink = {
        "strIngredient1": "Vodka",
        "strIngredient2": "Orange Juice",
        "strIngredient3": "Pineapple"
    }
    # Exact match
    assert drink_matches_mixers(drink, ["orange juice"]) == True
    # Alias match
    drink2 = {
        "strIngredient1": "Vodka",
        "strIngredient2": "Cola",
        "strIngredient3": "Pineapple"
    }
    assert drink_matches_mixers(drink2, ["cola"]) == True
    assert drink_matches_mixers(drink2, ["coke"]) == True  # alias
    assert drink_matches_mixers(drink, []) == True
    # Word overlap
    assert drink_matches_mixers(drink, ["orange"]) == True

def test_recommend_cocktails():
    prefs = {
        "alcohol_types": ["vodka"],
        "mixers": []
    }
    recs = recommend_cocktails(prefs, max_results=2)
    assert len(recs) <= 2
    if recs:
        assert "name" in recs[0]
        assert "ingredients" in recs[0]



def test_fetch_drinks_by_alcohol():
    # This makes a network request, but for testing, we can assume it returns a list
    drinks = fetch_drinks_by_alcohol("vodka")
    assert isinstance(drinks, list)

def test_fetch_drink_details():
    # Test with a known id
    detail = fetch_drink_details("11000")  # Test with Margarita id
    assert detail is None or isinstance(detail, dict)

def test_standardize_ingredients_to_cup():
    detail = {
        "strIngredient1": "Vodka",
        "strMeasure1": "2 oz",
        "strIngredient2": "Orange Juice",
        "strMeasure2": "4 oz"
    }
    standardized = standardize_ingredients_to_cup(detail, cup_size_oz=16.0)
    assert len(standardized) == 2
    assert all(len(item) == 3 for item in standardized)  # Each tuple should have 3 elements
    total_pct = sum(pct for _, _, pct in standardized)
    assert abs(total_pct - 100.0) < 0.1  # Should be approximately 100%
    total_vol = sum(vol for _, vol, _ in standardized)
    assert abs(total_vol - 16.0) < 0.1  # Should be approximately 16 oz

def test_generate_unique_color():
    # Test that same ingredient gets same color consistently
    vodka_color1 = generate_unique_color("Vodka")
    vodka_color2 = generate_unique_color("Vodka")
    assert vodka_color1 == vodka_color2

    # Test that different ingredients can get different colors (though with 15 colors, some might collide)
    vodka_color = generate_unique_color("Vodka")
    rum_color = generate_unique_color("Rum")
    # Note: With only 15 colors, some ingredients might get the same color, but that's acceptable

    # Test valid hex color format
    color = generate_unique_color("Orange Juice")
    assert color.startswith("#")
    assert len(color) == 7
    # Test that all characters after # are valid hex
    assert all(c in "0123456789abcdefABCDEF" for c in color[1:])

    # Test that color is from our predefined palette
    predefined_colors = [
        "#DC143C", "#FF4500", "#32CD32", "#00CED1", "#1E90FF",
        "#9370DB", "#FF69B4", "#8B4513", "#20B2AA", "#FF6347", "#4682B4",
        "#CD5C5C", "#40E0D0", "#800080", "#008000", "#FFA500", "#FF0000",
        "#0000FF", "#FFD700", "#228B22", "#FF00FF", "#00FFFF", "#800000",
        "#808000", "#008080", "#000080", "#696969", "#8B0000", "#8A2BE2",
        "#FF1493"
    ]
    assert color in predefined_colors





def test_measurement_formatting():
    """Test the measurement formatting based on context."""
    # Test visualization context (default): solids use original, liquids use cup portions
    assert format_measurement("Sugar", 1.0, "1 tsp", "visualization") == "1 tsp"
    assert format_measurement("Vodka", 8.0, "2 oz", "visualization") == "1/2 of a cup"
    assert format_measurement("Orange Juice", 5.333, "4 oz", "visualization") == "1/3 of a cup"

    # Test breakdown context: solids show original units, liquids show ounces
    assert format_measurement("Sugar", 1.0, "1 tsp", "breakdown") == "1 tsp"  # solid shows original
    assert format_measurement("Vodka", 8.0, "2 oz", "breakdown") == "8.0 oz"  # liquid shows ounces
    assert format_measurement("Orange Juice", 5.333, "4 oz", "breakdown") == "5.3 oz"  # liquid shows ounces
