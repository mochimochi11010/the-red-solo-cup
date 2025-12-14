"""
Cocktail API module for The Red Solo Cup web application.

This module contains functions for interacting with The Cocktail DB API
to fetch cocktail recipes and perform ingredient matching.
"""

import requests
import os

BASE_URL = "https://www.thecocktaildb.com/api/json/v1/1"

def fetch_drinks_by_alcohol(alcohol):
    """
    Fetch a list of drinks from The Cocktail DB that contain the given alcohol type.

    Args:
        alcohol (str): The type of alcohol to search for (e.g., "vodka", "rum")

    Returns:
        list: List of drink dictionaries from the API, or empty list if error

    Note:
        This function makes an external API call and includes error handling.
    """
    try:
        response = requests.get(f"{BASE_URL}/filter.php", params={"i": alcohol})
        if response.status_code != 200:
            return []
        data = response.json()
        return data.get("drinks") or []
    except Exception as e:
        print(f"Error fetching drinks for {alcohol}: {e}")
        return []

def fetch_drink_details(drink_id):
    try:
        response = requests.get(f"{BASE_URL}/lookup.php", params={"i": drink_id})
        if response.status_code != 200:
            return None
        data = response.json()
        drinks = data.get("drinks")
        return drinks[0] if drinks else None
    except Exception as e:
        print(f"Error fetching details for drink_id {drink_id}: {e}")
        return None

def fetch_ingredient_list():
    """
    Fetch the list of all available ingredients from The Cocktail DB API.

    Returns:
        list: List of ingredient names as strings, or empty list if error
    """
    try:
        response = requests.get(f"{BASE_URL}/list.php", params={"i": "list"})
        if response.status_code != 200:
            return []
        data = response.json()
        ingredients_data = data.get("drinks") or []
        ingredients = []
        for ing_dict in ingredients_data:
            ing_name = ing_dict.get("strIngredient1")
            if ing_name:
                ingredients.append(ing_name.strip())
        return sorted(ingredients)
    except Exception as e:
        print(f"Error fetching ingredient list: {e}")
        return []

def drink_matches_mixers(drink, mixers):
    ingredients = []
    for n in range(1, 16):
        ing = drink.get(f"strIngredient{n}")
        if ing and ing.strip():
            ingredients.append(ing.strip().lower())
    if not mixers:
        return True

    # Common ingredient aliases for better matching
    aliases = {
        "cola": ["coca-cola", "coke", "cola", "coca cola"],
        "coca-cola": ["cola", "coke", "coca-cola", "coca cola"],
        "coke": ["cola", "coca-cola", "coke"],
        "orange juice": ["orange juice", "oj", "orange"],
        "lemon juice": ["lemon juice", "lemon"],
        "lime juice": ["lime juice", "lime"],
        "sugar": ["sugar", "sugar syrup", "syrup"],
        "soda": ["soda water", "club soda", "soda"],
        "tonic": ["tonic water", "tonic"],
    }

    # Enhanced matching: check exact match and fuzzy match (substring)
    for recipe_ing in ingredients:
        for user_mixer in mixers:
            um_lower = user_mixer.lower().strip()
            # Direct aliases
            if (um_lower in aliases.get(recipe_ing, []) or 
                recipe_ing in aliases.get(um_lower, [])):
                return True
            # Substring match
            if um_lower in recipe_ing or recipe_ing in um_lower:
                return True
            # Also check for word overlaps
            um_words = set(um_lower.split())
            ri_words = set(recipe_ing.split())
            if um_words.intersection(ri_words):
                return True

    return False

def parse_volume_to_ounces(measure_text):
    if not measure_text:
        return 0.0
    text = measure_text.lower()
    tokens = text.replace("(", " ").replace(")", " ").split()
    total = 0.0
    for tok in tokens:
        if "/" in tok:
            try:
                num, den = tok.split("/")
                total += float(num) / float(den)
                continue
            except:
                pass
        try:
            total += float(tok)
            continue
        except:
            pass
    if total == 0:
        return 0
    if "ml" in text:
        return total * 0.0338
    if "cl" in text:
        return total * 0.338
    return total

def recommend_cocktails(user_prefs, max_results=5):
    """
    Recommend cocktails based on user's available alcohols and mixers.

    Args:
        user_prefs (dict): Dictionary with "alcohol_types" list and "mixers" list
        max_results (int): Maximum number of recommendations to return (default: 5)

    Returns:
        list: List of recommended cocktail dictionaries with name, id, ingredients, etc.

    Note:
        This is the main function that orchestrates the recommendation process.
    """
    alcohols = user_prefs["alcohol_types"]
    mixers = user_prefs["mixers"]
    seen = set()
    results = []
    for alc in alcohols:
        for d in fetch_drinks_by_alcohol(alc):
            # Ensure d is a dict with idDrink
            if not isinstance(d, dict) or "idDrink" not in d:
                continue
            drink_id = d["idDrink"]
            if drink_id in seen:
                continue
            detail = fetch_drink_details(drink_id)
            if not detail:
                continue
            if not drink_matches_mixers(detail, mixers):
                continue
            ingredients = []
            for n in range(1, 16):
                ing = detail.get(f"strIngredient{n}")
                measure = detail.get(f"strMeasure{n}")
                if ing and ing.strip():
                    ingredients.append((measure or "").strip() + " " + ing.strip())
            results.append({
                "name": detail["strDrink"],
                "id": drink_id,
                "ingredients": ingredients,
                "instructions": detail.get("strInstructions", "").strip(),
                "thumb": detail.get("strDrinkThumb"),
                "detail": detail
            })
            seen.add(drink_id)
            if len(results) >= max_results:
                return results
    return results

def estimate_bac_for_drink(detail, avg_weight_lbs, alcohol_keywords):
    total_alcohol_oz = 0.0
    for n in range(1, 16):
        ing = detail.get(f"strIngredient{n}")
        measure = detail.get(f"strMeasure{n}")
        if ing and ing.strip() and any(kw.lower() in ing.lower() for kw in alcohol_keywords):
            total_alcohol_oz += parse_volume_to_ounces(measure or "")
    if total_alcohol_oz == 0:
        return None
    ethanol_oz = total_alcohol_oz * 0.4
    standard_drinks = ethanol_oz / 0.6
    r = 0.7  # for simplicity, assume male; could be 0.73 for male, 0.66 for female
    bac = standard_drinks * 5.14 / (avg_weight_lbs * r)
    return bac

def search_youtube_tutorial(cocktail_name):
    """
    Search for a YouTube tutorial video for the given cocktail.

    Args:
        cocktail_name (str): The name of the cocktail to search for

    Returns:
        dict: Dictionary with video_id for embedding, or None if API key not configured

    Note:
        Requires YOUTUBE_API_KEY environment variable to be set.
        Returns a specific video ID that can be embedded directly on the page.
    """
    search_query = f"how to make {cocktail_name} cocktail recipe"
    api_key = os.environ.get("YOUTUBE_API_KEY")
    
    if not api_key:
        print(f"Warning: No YOUTUBE_API_KEY found. Cannot fetch videos for {cocktail_name}")
        return {
            "video_id": None,
            "video_title": None,
            "search_query": search_query,
            "api_key_missing": True
        }
    
    try:
        # Search for videos using YouTube Data API
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "maxResults": 3,  # Get top 3 results
            "videoDuration": "short",  # Prefer shorter tutorials
            "relevanceLanguage": "en",
            "key": api_key
        }
        
        response = requests.get(search_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            if items:
                # Use the first video
                video = items[0]
                video_id = video["id"]["videoId"]
                video_title = video["snippet"]["title"]
                video_description = video["snippet"]["description"]
                
                return {
                    "video_id": video_id,
                    "video_title": video_title,
                    "video_description": video_description,
                    "search_query": search_query,
                    "api_key_missing": False
                }
        else:
            print(f"YouTube API returned status {response.status_code} for {cocktail_name}")
            
    except Exception as e:
        print(f"Error searching YouTube for {cocktail_name}: {e}")
    
    # Return None if we couldn't get a video
    return {
        "video_id": None,
        "video_title": None,
        "search_query": search_query,
        "api_key_missing": False
    }
