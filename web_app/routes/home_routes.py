# this is the "web_app/routes/home_routes.py" file...

from flask import Blueprint, request, render_template, redirect, url_for, flash
import sys
import os

# Add the parent directory to the Python path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.cocktails import recommend_cocktails, fetch_drink_details, fetch_ingredient_list, fetch_drinks_by_alcohol, search_youtube_tutorial, standardize_ingredients_to_cup, generate_unique_color

def is_solid_ingredient(ingredient_name):
    """Determine if an ingredient is typically solid/powder vs liquid."""
    solid_keywords = [
        'sugar', 'salt', 'brown sugar', 'powdered sugar', 'caster sugar',
        'granulated sugar', 'icing sugar', 'confectioners sugar',
        'superfine sugar', 'demerara sugar', 'muscovado sugar',
        'syrup', 'honey', 'extract', 'bitters', 'cream', 'milk',
        'mint', 'fruit', 'lemon', 'lime', 'cherry',
        'olive', 'onion', 'celery', 'cucumber', 'ginger', 'pepper',
        'powder'
    ]

    ingredient_lower = ingredient_name.lower().strip()

    # Check if ingredient contains solid keywords
    for keyword in solid_keywords:
        if keyword in ingredient_lower:
            return True

    return False

def format_measurement(ingredient_name, vol_oz, original_measure=None, context="visualization"):
    """Format measurements based on context.

    Args:
        context: "visualization" for cup lines, "breakdown" for ingredient list
    """
    if context == "breakdown":
        # For breakdown: solids show original units, liquids show ounces
        if is_solid_ingredient(ingredient_name):
            if original_measure and original_measure.strip():
                return original_measure.strip()
            else:
                # Fallback to ounces if no original measure
                return f"{vol_oz:.1f} oz"
        else:
            # Liquid ingredients show ounces in breakdown
            return f"{vol_oz:.1f} oz"
    else:
        # For visualization lines: liquids show cup fractions, solids show original
        if is_solid_ingredient(ingredient_name):
            if original_measure and original_measure.strip():
                return original_measure.strip()
            else:
                # Fallback to ounces if no original measure
                return f"{vol_oz:.1f} oz"
        else:
            # For liquid ingredients, convert to cup fraction format
            fraction = vol_oz / 16.0
            if abs(fraction - 1/2) < 0.01:
                return "1/2 of a cup"
            elif abs(fraction - 1/3) < 0.01:
                return "1/3 of a cup"
            elif abs(fraction - 1/4) < 0.01:
                return "1/4 of a cup"
            elif abs(fraction - 1/5) < 0.01:
                return "1/5 of a cup"
            elif abs(fraction - 1/6) < 0.01:
                return "1/6 of a cup"
            elif abs(fraction - 1/8) < 0.01:
                return "1/8 of a cup"
            elif abs(fraction - 1/10) < 0.01:
                return "1/10 of a cup"
            elif abs(fraction - 1/12) < 0.01:
                return "1/12 of a cup"
            elif abs(fraction - 1/16) < 0.01:
                return "1/16 of a cup"
            else:
                return f"{fraction:.2f} of a cup"

def get_percentage_display(ingredient_name, pct):
    """Get percentage display for ingredient breakdown.

    Args:
        ingredient_name: Name of the ingredient
        pct: Percentage value

    Returns:
        "0%" for solid ingredients, formatted percentage for liquids
    """
    if is_solid_ingredient(ingredient_name):
        return "0%"
    else:
        return f"{pct:.1f}%"

home_routes = Blueprint("home_routes", __name__)

@home_routes.route("/")
@home_routes.route("/home")
def index():
    ingredients = fetch_ingredient_list()
    # Separate common alcohols and mixers for prioritized display
    common_alcohols = ['Vodka', 'Gin', 'Rum', 'Whiskey', 'Tequila', 'Bourbon', 'Scotch', 'Wine', 'Beer', 'Champagne', 'Cognac', 'Brandy', 'Vermouth']
    common_mixers = ['Orange Juice', 'Lemon Juice', 'Lime Juice', 'Cola', 'Soda Water', 'Tonic Water', 'Sugar', 'Salt', 'Mint', 'Ice', 'Coca-Cola', 'Sprite', 'Cranberry Juice', 'Pineapple Juice']
    return render_template("home.html", ingredients=ingredients, common_alcohols=common_alcohols, common_mixers=common_mixers)

@home_routes.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    from flask import session

    if request.method == "GET":
        # Check if we have stored cocktail IDs to show the exact same results
        if 'last_cocktail_ids' in session:
            cocktail_ids = session['last_cocktail_ids']
            recs = []

            # Reconstruct the cocktail list from stored IDs
            for cocktail_id in cocktail_ids:
                detail = fetch_drink_details(cocktail_id)
                if detail:
                    cocktail = {
                        "id": cocktail_id,
                        "name": detail["strDrink"],
                        "thumb": detail.get("strDrinkThumb")
                    }
                    recs.append(cocktail)

            if recs:
                return render_template("recommendations.html", cocktails=recs)

        return redirect(url_for("home_routes.index"))

    alcohols = request.form.get("alcohols", "").strip()
    mixers = request.form.get("mixers", "").strip()

    if not alcohols:
        flash("Please enter at least one alcohol type.", "danger")
        return redirect(url_for("home_routes.index"))

    alcohol_types = [x.strip().lower() for x in alcohols.split(",") if x.strip()]
    mixers_list = [x.strip().lower() for x in mixers.split(",") if x.strip()]

    user_prefs = {
        "alcohol_types": alcohol_types,
        "mixers": mixers_list
    }

    recs = recommend_cocktails(user_prefs, max_results=10)

    if not recs:
        flash("No cocktails found for those ingredients. Try different combinations.", "warning")
        return redirect(url_for("home_routes.index"))

    # Store only the cocktail IDs in session for reliable back navigation
    cocktail_ids = [cocktail['id'] for cocktail in recs]
    session['last_cocktail_ids'] = cocktail_ids
    session['last_search_alcohols'] = alcohol_types
    session['last_search_mixers'] = mixers_list

    return render_template("recommendations.html", cocktails=recs)

@home_routes.route("/cocktail/<drink_id>")
def cocktail_detail(drink_id):
    detail = fetch_drink_details(drink_id)
    if not detail:
        flash("Cocktail not found.", "danger")
        return redirect(url_for("home_routes.index"))

    ingredients = []
    for n in range(1, 16):
        ing = detail.get(f"strIngredient{n}")
        measure = detail.get(f"strMeasure{n}")
        if ing and ing.strip():
            ingredients.append((measure or "").strip() + " " + ing.strip())

    cocktail = {
        "name": detail["strDrink"],
        "ingredients": ingredients,
        "instructions": detail.get("strInstructions", "").strip(),
        "thumb": detail.get("strDrinkThumb"),
        "detail": detail
    }

    # Fetch YouTube tutorial video
    youtube_video = search_youtube_tutorial(detail["strDrink"])

    # Standardize ingredients for 16 oz red solo cup
    standardized_ingredients = standardize_ingredients_to_cup(detail, cup_size_oz=16.0)

    # Generate unique colors for each ingredient
    ingredient_colors = {}
    for ing, _, _ in standardized_ingredients:
        ingredient_colors[ing] = generate_unique_color(ing)

    # Create ingredient_measures mapping
    ingredient_measures = {}
    for ing, _, _ in standardized_ingredients:
        # Find the original measurement for this ingredient
        for n in range(1, 16):
            orig_ing = detail.get(f"strIngredient{n}")
            orig_measure = detail.get(f"strMeasure{n}")
            if orig_ing and orig_ing.strip() == ing:
                ingredient_measures[ing] = orig_measure or ""
                break

    return render_template("cocktail_detail.html", cocktail=cocktail, youtube_video=youtube_video, standardized_ingredients=standardized_ingredients, ingredient_colors=ingredient_colors, ingredient_measures=ingredient_measures, format_measurement=format_measurement, get_percentage_display=get_percentage_display)

@home_routes.route("/compatible_mixers")
def compatible_mixers():
    alcohols_param = request.args.get('alcohols', '').strip()
    if not alcohols_param:
        return {'mixers': []}

    from flask import jsonify
    alcohols = [a.strip().lower() for a in alcohols_param.split(',') if a.strip()]

    # Find all mixers that appear in recipes with these alcohols
    compatible_mixers = set()
    seen_cocktails = set()

    for alcohol in alcohols:
        drinks = fetch_drinks_by_alcohol(alcohol)
        for drink in drinks:
            if isinstance(drink, dict) and 'idDrink' in drink:
                drink_id = drink['idDrink']
                if drink_id not in seen_cocktails:
                    seen_cocktails.add(drink_id)
                    detail = fetch_drink_details(drink_id)
                    if detail:
                        for i in range(1, 16):
                            ing = detail.get(f'strIngredient{i}')
                            if ing and ing.strip():
                                ing_lower = ing.lower().strip()
                                # Add as mixer if not in alcohols list
                                if ing_lower not in alcohols:
                                    compatible_mixers.add(ing.lower().strip())

    sorted_mixers = sorted(compatible_mixers)
    return jsonify({'mixers': sorted_mixers})

@home_routes.route("/about")
def about():
    print("ABOUT...")
    #return "About Me"
    return render_template("about.html")

@home_routes.route("/hello")
def hello_world():
    print("HELLO...")

    # if the request contains url params, for example a request to "/hello?name=Harper"
    # the request object's args property will hold the values in a dictionary-like structure
    url_params = dict(request.args)
    print("URL PARAMS:", url_params) #> can be empty like {} or full of params like {"name":"Harper"}

    # get a specific key called "name" if available, otherwise use some specified default value
    # see also: https://www.w3schools.com/python/ref_dictionary_get.asp
    name = url_params.get("name") or "World"

    message = f"Hello, {name}!"
    #return message
    return render_template("hello.html", message=message, x=5, y=20)
