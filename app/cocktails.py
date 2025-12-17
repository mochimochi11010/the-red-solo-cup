import requests
import os

BASE_URL = "https://www.thecocktaildb.com/api/json/v1/1"

def fetch_drinks_by_alcohol(alcohol):
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

def generate_unique_color(ingredient_name):
    """
    Generate a unique, highly distinct color for an ingredient based on its name.
    Uses a predefined palette of 15 maximally contrasting colors for optimal visual distinction.

    Args:
        ingredient_name (str): The name of the ingredient

    Returns:
        str: Hex color code from a highly distinct palette
    """
    # Predefined palette of 15 maximally contrasting colors
    # These colors were chosen for maximum visual distinction across the color spectrum
    distinct_colors = [
        "#FF0000",  # Bright Red
        "#00FF00",  # Bright Green
        "#0000FF",  # Bright Blue
        "#FFFF00",  # Bright Yellow
        "#FF00FF",  # Magenta
        "#00FFFF",  # Cyan
        "#FF8000",  # Orange
        "#8000FF",  # Purple
        "#FF0080",  # Pink
        "#80FF00",  # Lime Green
        "#0080FF",  # Sky Blue
        "#FF8080",  # Light Red
        "#80FF80",  # Light Green
        "#8080FF",  # Light Blue
        "#FFFF80",  # Light Yellow
    ]

    # Create a hash from the ingredient name for consistency
    hash_value = hash(ingredient_name.lower().strip())

    # Use the hash to select from our distinct color palette
    color_index = hash_value % len(distinct_colors)

    return distinct_colors[color_index]

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

def standardize_ingredients_to_cup(detail, cup_size_oz=16.0):
    """
    Standardize cocktail ingredients to fit a red solo cup of specified size.

    Args:
        detail (dict): Cocktail detail from API
        cup_size_oz (float): Size of the red solo cup in ounces (default 16.0)

    Returns:
        list: List of tuples (ingredient_name, standardized_ounces, percentage)
    """
    ingredients_volumes = []
    total_volume = 0.0

    # Parse all ingredients and their volumes
    for n in range(1, 16):
        ing = detail.get(f"strIngredient{n}")
        measure = detail.get(f"strMeasure{n}")
        if ing and ing.strip():
            volume_oz = parse_volume_to_ounces(measure or "")
            if volume_oz > 0:
                ingredients_volumes.append((ing.strip(), volume_oz))
                total_volume += volume_oz

    # If no volumes found, return empty list
    if total_volume == 0:
        return []

    # Scale to fit the cup size
    scale_factor = cup_size_oz / total_volume

    standardized = []
    cumulative_pct = 0.0
    for ing, vol_oz in ingredients_volumes:
        standardized_vol = vol_oz * scale_factor
        percentage = (standardized_vol / cup_size_oz) * 100
        standardized.append((ing, standardized_vol, percentage))
        cumulative_pct += percentage

    # Adjust last ingredient to ensure total is exactly 100%
    if standardized:
        standardized[-1] = (standardized[-1][0], standardized[-1][1], 100.0 - (cumulative_pct - percentage))

    return standardized

def display_red_solo_cup_visualization(standardized_ingredients, cup_size_oz=16.0):
    """
    Display a simple ASCII visualization of the red solo cup with ingredient bars.

    Args:
        standardized_ingredients (list): List from standardize_ingredients_to_cup
        cup_size_oz (float): Size of the red solo cup in ounces
    """
    print("\nRed Solo Cup Visualization (16 oz):")
    print("   _________ ")
    print("  /         \\")
    print(" /           \\")

    # Cup has 10 lines of content
    cup_lines = 10
    current_level = 0.0
    ingredient_bars = []

    for i, (ing, vol_oz, pct) in enumerate(standardized_ingredients):
        # Calculate how many lines this ingredient takes
        lines_for_ing = int((pct / 100.0) * cup_lines)
        if lines_for_ing < 1 and pct > 0:
            lines_for_ing = 1  # At least one line for any ingredient

        for line in range(lines_for_ing):
            if current_level < cup_lines:
                print(" |###########|")
                current_level += 1

        # Collect the ingredient bar
        bar_length = int(pct / 10)  # Scale to 10 characters
        bar = "#" * bar_length + " " * (10 - bar_length)
        ingredient_bars.append(f"     [{bar}] {ing} ({vol_oz:.1f} oz, {pct:.1f}%)")

    # Fill remaining cup with empty space
    while current_level < cup_lines:
        print(" |           |")
        current_level += 1

    print(" \\___________/")
    print(f"Total volume: {cup_size_oz:.1f} oz")

    # Print all ingredient bars
    print("\nIngredient Breakdown:")
    for bar in ingredient_bars:
        print(bar)
