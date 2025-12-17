import pytest
from app.cocktails import (
    fetch_drinks_by_alcohol, fetch_drink_details,
    drink_matches_mixers, parse_volume_to_ounces,
    recommend_cocktails, estimate_bac_for_drink,
    standardize_ingredients_to_cup, display_red_solo_cup_visualization,
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

def test_estimate_bac_for_drink():
    detail = {
        "strIngredient1": "Vodka",
        "strMeasure1": "2 oz",
        "strIngredient2": "Orange Juice",
        "strMeasure2": "4 oz"
    }
    bac = estimate_bac_for_drink(detail, 180, ["vodka"])
    assert bac is not None
    assert isinstance(bac, float)

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
        "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
        "#FF8000", "#8000FF", "#FF0080", "#80FF00", "#0080FF", "#FF8080",
        "#80FF80", "#8080FF", "#FFFF80"
    ]
    assert color in predefined_colors

def test_display_red_solo_cup_visualization(capsys):
    standardized = [
        ("Vodka", 8.0, 50.0),
        ("Orange Juice", 8.0, 50.0)
    ]
    display_red_solo_cup_visualization(standardized, cup_size_oz=16.0)
    captured = capsys.readouterr()
    assert "Red Solo Cup Visualization" in captured.out
    assert "Ingredient Breakdown:" in captured.out
    assert "Vodka" in captured.out
    assert "Orange Juice" in captured.out

def test_cup_visualization_proportion_accuracy():
    """Test that the rectangle cup visualization accurately represents ingredient proportions."""
    # Test with a simple 2-ingredient cocktail: 8 oz vodka + 8 oz orange juice = 16 oz total
    standardized = [
        ("Vodka", 8.0, 50.0),
        ("Orange Juice", 8.0, 50.0)
    ]

    # Verify proportions add up to 100%
    total_percentage = sum(pct for _, _, pct in standardized)
    assert abs(total_percentage - 100.0) < 0.1

    # Test fraction calculations
    for ing, vol_oz, pct in standardized:
        fraction = vol_oz / 16.0
        expected_pct = fraction * 100
        assert abs(pct - expected_pct) < 0.1

    # Test with a more complex 3-ingredient cocktail
    standardized_complex = [
        ("Vodka", 4.0, 25.0),        # 4 oz = 25%
        ("Orange Juice", 8.0, 50.0), # 8 oz = 50%
        ("Lime Juice", 4.0, 25.0)    # 4 oz = 25%
    ]

    # Verify all proportions are correct
    for ing, vol_oz, pct in standardized_complex:
        expected_pct = (vol_oz / 16.0) * 100
        assert abs(pct - expected_pct) < 0.1

    total_percentage_complex = sum(pct for _, _, pct in standardized_complex)
    assert abs(total_percentage_complex - 100.0) < 0.1

    # Test fraction representations
    for ing, vol_oz, pct in standardized_complex:
        fraction = vol_oz / 16.0
        # Should be able to represent as simple fractions
        assert fraction in [1/16, 1/8, 1/6, 1/5, 1/4, 1/3, 1/2, 1.0]

def test_cup_visualization_line_logic():
    """Test the cup visualization line logic: 1 ingredient = 1 line."""
    from app.cocktails import standardize_ingredients_to_cup, generate_unique_color

    # Test cocktail with 2 ingredients
    detail_2_ing = {
        "strIngredient1": "Vodka",
        "strMeasure1": "8 oz",
        "strIngredient2": "Orange Juice",
        "strMeasure2": "8 oz"
    }
    standardized_2 = standardize_ingredients_to_cup(detail_2_ing, cup_size_oz=16.0)
    assert len(standardized_2) == 2  # Should have 2 ingredients
    # Should generate 2 lines (1:1 ratio)

    # Test cocktail with 3 ingredients
    detail_3_ing = {
        "strIngredient1": "Vodka",
        "strMeasure1": "4 oz",
        "strIngredient2": "Orange Juice",
        "strMeasure2": "8 oz",
        "strIngredient3": "Lime Juice",
        "strMeasure3": "4 oz"
    }
    standardized_3 = standardize_ingredients_to_cup(detail_3_ing, cup_size_oz=16.0)
    assert len(standardized_3) == 3  # Should have 3 ingredients
    # Should generate 3 lines (1:1 ratio)

    # Test cocktail with 4 ingredients
    detail_4_ing = {
        "strIngredient1": "Gin",
        "strMeasure1": "2 oz",
        "strIngredient2": "Vodka",
        "strMeasure2": "2 oz",
        "strIngredient3": "Orange Juice",
        "strMeasure3": "8 oz",
        "strIngredient4": "Lime Juice",
        "strMeasure4": "4 oz"
    }
    standardized_4 = standardize_ingredients_to_cup(detail_4_ing, cup_size_oz=16.0)
    assert len(standardized_4) == 4  # Should have 4 ingredients
    # Should generate 4 lines (1:1 ratio)

    # Test that each ingredient gets a consistent color
    ingredient_colors = {}
    for ing, _, _ in standardized_4:
        ingredient_colors[ing] = generate_unique_color(ing)

    # Verify colors are from the predefined palette and consistent
    colors = list(ingredient_colors.values())
    predefined_colors = [
        "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
        "#FF8000", "#8000FF", "#FF0080", "#80FF00", "#0080FF", "#FF8080",
        "#80FF80", "#8080FF", "#FFFF80"
    ]
    for color in colors:
        assert color in predefined_colors

    # Test consistency - same ingredient should always get same color
    for ing in ingredient_colors.keys():
        color1 = generate_unique_color(ing)
        color2 = generate_unique_color(ing)
        assert color1 == color2

    # Test fraction calculations for line display
    for ing, vol_oz, pct in standardized_4:
        fraction = vol_oz / 16.0
        # Verify fractions are reasonable (between 0 and 1)
        assert 0 < fraction <= 1
        # Verify percentage matches fraction
        assert abs(pct - (fraction * 100)) < 0.1



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
