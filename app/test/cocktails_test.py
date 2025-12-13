import pytest
from app.cocktails import (
    fetch_drinks_by_alcohol, fetch_drink_details, 
    drink_matches_mixers, parse_volume_to_ounces, 
    recommend_cocktails, estimate_bac_for_drink
)

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
