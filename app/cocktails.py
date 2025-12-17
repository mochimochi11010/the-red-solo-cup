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
        response = requests.get(f"{BASE_URL}/lookup.php", params={"i": drink_id}, timeout=10)
        if response.status_code == 429:
            print(f"Rate limited (429) for drink_id {drink_id}")
            return None
        if response.status_code != 200:
            print(f"API returned status {response.status_code} for drink_id {drink_id}")
            return None
        data = response.json()
        drinks = data.get("drinks")
        if not drinks:
            print(f"No drink details found for drink_id {drink_id}")
            return None
        return drinks[0]
    except requests.exceptions.Timeout:
        print(f"Timeout fetching details for drink_id {drink_id}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching details for drink_id {drink_id}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching details for drink_id {drink_id}: {e}")
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
    # Get all ingredients from the drink recipe
    ingredients = []
    for n in range(1, 16):
        ing = drink.get(f"strIngredient{n}")
        if ing and ing.strip():
            ingredients.append(ing.strip().lower())

    # If no mixers specified, any drink matches
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

    # Check if any user mixer matches any recipe ingredient
    for recipe_ing in ingredients:
        for user_mixer in mixers:
            user_mixer_clean = user_mixer.lower().strip()

            # Check aliases first
            if (user_mixer_clean in aliases.get(recipe_ing, []) or
                recipe_ing in aliases.get(user_mixer_clean, [])):
                return True

            # Check if one contains the other
            if user_mixer_clean in recipe_ing or recipe_ing in user_mixer_clean:
                return True

            # Check for word overlaps (like "orange" in "orange juice")
            user_words = set(user_mixer_clean.split())
            recipe_words = set(recipe_ing.split())
            if user_words.intersection(recipe_words):
                return True

    return False

def parse_volume_to_ounces(measure_text):
    # If there's no measurement text, return 0
    if not measure_text:
        return 0.0

    # Convert to lowercase and split into words
    text = measure_text.lower()

    # If it's marked as garnish or common garnish terms, it's not a measurable amount
    garnish_terms = ["garnish", "wedge", "slice", "twist", "wheel", "peel", "sprig", "leaf", "leaves"]
    if any(term in text for term in garnish_terms):
        return 0.0

    tokens = text.replace("(", " ").replace(")", " ").split()

    total = 0.0

    # Go through each word/token
    for tok in tokens:
        # Handle fractions like "1/2"
        if "/" in tok:
            try:
                num, den = tok.split("/")
                total += float(num) / float(den)
                continue
            except:
                pass

        # Try to convert to a number
        try:
            total += float(tok)
            continue
        except:
            # Handle concatenated units like "12oz", "50ml"
            # Extract number from start of string
            num_str = ""
            unit_str = ""
            for i, char in enumerate(tok):
                if char.isdigit() or char == '.':
                    num_str += char
                else:
                    unit_str = tok[i:]
                    break

            if num_str:
                try:
                    total += float(num_str)
                    # Check for units in the remaining part
                    if "ml" in unit_str:
                        total *= 0.0338
                    elif "cl" in unit_str:
                        total *= 0.338
                    # oz is already in ounces, no conversion needed
                    continue
                except:
                    pass

    # Special handling for ice
    if "ice" in text or "cube" in text:
        if total == 0:
            total = 4.0  # Default ice amount
        if "cube" in text:
            if total < 2:
                total = 3 * 1.5  # Assume 3 cubes if no number given
            else:
                total = total * 1.5  # Convert cube count to ounces

    # If we still have 0, return 0
    if total == 0:
        return 0

    # Convert different units to ounces (for space-separated cases)
    if "cup" in text or "cups" in text:
        return total * 8.0  # 1 cup = 8 fluid ounces
    if "ml" in text and not any("ml" in tok for tok in tokens if tok != tokens[0]):  # Avoid double conversion
        return total * 0.0338
    if "cl" in text and not any("cl" in tok for tok in tokens if tok != tokens[0]):  # Avoid double conversion
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



def generate_unique_color(ingredient_name):
    distinct_colors = [
        "#DC143C",
        "#FF4500",
        "#32CD32",
        "#00CED1",
        "#1E90FF",
        "#9370DB",
        "#FF69B4",
        "#8B4513",
        "#20B2AA",
        "#FF6347",
        "#4682B4",
        "#CD5C5C",
        "#40E0D0",
        "#800080",
        "#008000",
        "#FFA500",
        "#FF0000",
        "#0000FF",
        "#FFD700",
        "#228B22",
        "#FF00FF",
        "#00FFFF",
        "#800000",
        "#808000",
        "#008080",
        "#000080",
        "#696969",
        "#8B0000",
        "#8A2BE2",
        "#FF1493",
    ]

    hash_value = hash(ingredient_name.lower().strip())
    color_index = hash_value % len(distinct_colors)
    return distinct_colors[color_index]

def search_youtube_tutorial(cocktail_name):
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
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": search_query,
            "type": "video",
            "maxResults": 3,
            "videoDuration": "short",
            "relevanceLanguage": "en",
            "key": api_key
        }

        response = requests.get(search_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            if items:
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

    return {
        "video_id": None,
        "video_title": None,
        "search_query": search_query,
        "api_key_missing": False
    }

def is_solid_ingredient(ingredient_name):
    solid_keywords = [
        'sugar', 'salt', 'brown sugar', 'powdered sugar', 'caster sugar',
        'granulated sugar', 'icing sugar', 'confectioners sugar',
        'superfine sugar', 'demerara sugar', 'muscovado sugar',
        'syrup', 'honey', 'extract', 'bitters', 'cream', 'milk',
        'mint', 'fruit', 'cherry',
        'olive', 'onion', 'celery', 'cucumber', 'ginger', 'pepper',
        'powder'
    ]

    ingredient_lower = ingredient_name.lower().strip()

    # Liquids that might contain solid keywords
    liquid_indicators = ['juice', 'ade', 'soda', 'cola', 'beer', 'wine', 'whiskey', 'vodka', 'rum', 'gin', 'tequila']
    for indicator in liquid_indicators:
        if indicator in ingredient_lower:
            return False

    # Check if ingredient contains solid keywords
    for keyword in solid_keywords:
        if keyword in ingredient_lower:
            return True

    return False

def parse_ice_proportion_from_instructions(instructions):
    if not instructions:
        return None

    text = instructions.lower()

    # Common patterns for ice proportions
    if "half" in text and "ice" in text:
        return 0.5
    if "fill" in text and "ice" in text:
        # Look for "fill with ice" or similar
        if "half" in text or "1/2" in text:
            return 0.5
        # Assume fill means most of the cup
        return 0.75
    if "top" in text and "ice" in text:
        return 0.25
    if "quarter" in text and "ice" in text:
        return 0.25

    return None

def infer_missing_amounts(ingredients_data, cocktail_name=""):
    name_lower = cocktail_name.lower()

    # Collect specified and missing ingredients
    specified = []
    missing = []

    for ing, measure in ingredients_data:
        volume = parse_volume_to_ounces(measure or "")
        if volume > 0 and not is_solid_ingredient(ing):
            specified.append((ing, volume))
        elif not is_solid_ingredient(ing):
            missing.append(ing)

    if not missing:
        return specified + [(ing, 0) for ing in missing]  # Keep missing as 0

    total_specified = sum(vol for _, vol in specified)

    # Cocktail-specific conventions
    if "mimosa" in name_lower:
        # Mimosas are typically 50/50 orange juice and champagne
        if len(missing) == 1 and len(specified) == 1:
            remaining = 16.0 - total_specified
            if remaining > 0:
                return specified + [(missing[0], remaining)]

    elif "bloody mary" in name_lower:
        # Bloody Mary typically has tomato juice as base, vodka, then smaller amounts
        pass  # Use default even distribution

    # Default: distribute remaining volume evenly among missing ingredients
    remaining_volume = 16.0 - total_specified
    if remaining_volume > 0 and missing:
        per_missing = remaining_volume / len(missing)
        return specified + [(ing, per_missing) for ing in missing]

    return specified + [(ing, 0) for ing in missing]

def standardize_ingredients_to_cup(detail, cup_size_oz=16.0):
    ingredients_volumes = []
    total_volume = 0.0

    cocktail_name = detail.get("strDrink", "").lower()

    # Collect all liquid ingredients with their measures
    all_ingredients = []
    for n in range(1, 16):
        ing = detail.get(f"strIngredient{n}")
        measure = detail.get(f"strMeasure{n}")
        if ing and ing.strip():
            ing_clean = ing.strip()
            measure_clean = (measure or "").strip()

            # Special handling for known garnish ingredients in specific cocktails
            is_garnish = False
            if "3-mile long island iced tea" in cocktail_name and "lemon" in ing_clean.lower():
                is_garnish = True
            elif any(term in measure_clean.lower() for term in ["garnish", "wedge", "slice", "twist", "wheel", "peel", "sprig", "leaf", "leaves"]):
                is_garnish = True
            # Additional check: if measure is just a small number and ingredient is a common garnish
            elif measure_clean and measure_clean.replace(".", "").isdigit() and float(measure_clean) <= 2.0 and ing_clean.lower() in ["lemon", "lime", "orange"]:
                is_garnish = True

            if not is_garnish and not is_solid_ingredient(ing_clean):
                all_ingredients.append((ing_clean, measure_clean))

    # Infer missing amounts based on cocktail conventions
    cocktail_name = detail.get("strDrink", "")
    ingredients_volumes = infer_missing_amounts(all_ingredients, cocktail_name)

    # Calculate total volume
    total_volume = sum(vol for _, vol in ingredients_volumes)

    # Check for ice proportion in instructions
    ice_proportion = parse_ice_proportion_from_instructions(detail.get("strInstructions", ""))
    ice_adjusted = False
    ice_volume = 0

    if ice_proportion is not None:
        # Find ice in ingredients
        for i, (ing, vol_oz) in enumerate(ingredients_volumes):
            if ing.lower() == "ice":
                # Adjust ice volume based on instructions
                ice_volume = ice_proportion * cup_size_oz
                ingredients_volumes[i] = (ing, ice_volume)
                total_volume = total_volume - (vol_oz or 0) + ice_volume
                ice_adjusted = True
                break

    # If no volumes found, return empty list
    if total_volume == 0:
        return []

    # Handle scaling based on whether ice was adjusted
    if ice_adjusted:
        # Scale non-ice ingredients to fit remaining space
        remaining_space = cup_size_oz - ice_volume
        non_ice_volumes = [(ing, vol_oz) for ing, vol_oz in ingredients_volumes if ing.lower() != "ice"]
        if non_ice_volumes:
            non_ice_total = sum(vol_oz for _, vol_oz in non_ice_volumes)
            if non_ice_total > 0:
                scale_factor = remaining_space / non_ice_total
                ingredients_volumes = [(ing, vol_oz * scale_factor) if ing.lower() != "ice" else (ing, vol_oz) for ing, vol_oz in ingredients_volumes]
    else:
        # Normal scaling to fit entire cup
        if total_volume > 0:
            scale_factor = cup_size_oz / total_volume
            ingredients_volumes = [(ing, vol_oz * scale_factor) for ing, vol_oz in ingredients_volumes]

    standardized = []
    cumulative_pct = 0.0
    for ing, vol_oz in ingredients_volumes:
        percentage = (vol_oz / cup_size_oz) * 100
        standardized.append((ing, vol_oz, percentage))
        cumulative_pct += percentage

    # Ensure total is exactly 100%
    if standardized:
        standardized[-1] = (standardized[-1][0], standardized[-1][1], 100.0 - (cumulative_pct - percentage))

    return standardized
