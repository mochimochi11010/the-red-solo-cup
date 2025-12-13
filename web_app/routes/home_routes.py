# this is the "web_app/routes/home_routes.py" file...

from flask import Blueprint, request, render_template, redirect, url_for, flash
import sys
import os

# Add the parent directory to the Python path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.cocktails import recommend_cocktails, fetch_drink_details, fetch_ingredient_list, fetch_drinks_by_alcohol

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

    return render_template("cocktail_detail.html", cocktail=cocktail)

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
