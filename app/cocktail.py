import requests
import webbrowser
from IPython.display import Image, display

BASE_URL = "https://www.thecocktaildb.com/api/json/v1/1"

#USER INPUT SECTION
def get_list_from_user(prompt):
    raw = input(prompt).strip()
    items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    while not items:
        print("Please enter at least one item, separated by commas.")
        raw = input(prompt).strip()
        items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    return items

def get_alcohol_strength():
    valid_strengths = {"light", "medium", "strong"}
    print("Choose target alcohol strength:")
    print("Options: light, medium, strong")
    choice = input("Enter strength: ").strip().lower()
    while choice not in valid_strengths:
        print("Invalid choice. Please enter light, medium, or strong.")
        choice = input("Enter strength: ").strip().lower()
    return choice

def get_number_of_people():
    raw = input("How many people are you serving? ").strip()
    while True:
        try:
            n = int(raw)
            if n > 0:
                return n
            print("Please enter an integer greater than 0.")
        except ValueError:
            print("Please enter a valid integer.")
        raw = input("How many people are you serving? ").strip()

def get_average_weight():
    raw = input("What is the average weight in pounds of the people drinking? ").strip()
    while True:
        try:
            w = float(raw)
            if w > 0:
                return w
            print("Please enter a number greater than 0.")
        except ValueError:
            print("Please enter a valid number.")
        raw = input("What is the average weight in pounds of the people drinking? ").strip()

def get_user_preferences():
    print("Welcome to the Red Solo Cup, your personal bartender and party helper")
    print("Tell us what you have and what you want.")
    alcohol_types = get_list_from_user("Enter the types of alcohol you have (for example vodka, rum, tequila): ")
    mixers = get_list_from_user("Enter the mixers you have (for example coke, sprite, orange juice): ")
    strength = get_alcohol_strength()
    num_people = get_number_of_people()
    avg_weight_lbs = get_average_weight()
    prefs = {"alcohol_types": alcohol_types, "mixers": mixers, "strength": strength, "num_people": num_people, "avg_weight_lbs": avg_weight_lbs}
    print("\nSummary of your inputs:")
    print(f"Alcohol types: {', '.join(alcohol_types)}")
    print(f"Mixers: {', '.join(mixers)}")
    print(f"Target strength: {strength}")
    print(f"Number of people: {num_people}")
    print(f"Average weight: {avg_weight_lbs:.1f} pounds\n")
    return prefs

#API SECTION
def fetch_drinks_by_alcohol(alcohol):
    response = requests.get(f"{BASE_URL}/filter.php", params={"i": alcohol})
    data = response.json()
    return data.get("drinks") or []

def fetch_drink_details(drink_id):
    response = requests.get(f"{BASE_URL}/lookup.php", params={"i": drink_id})
    data = response.json()
    drinks = data.get("drinks")
    return drinks[0] if drinks else None

def drink_matches_mixers(drink, mixers):
    ingredients = []
    for n in range(1, 16):
        ing = drink.get(f"strIngredient{n}")
        if ing and ing.strip():
            ingredients.append(ing.strip().lower())
    if not mixers:
        return True
    return any(m.lower() in ingredients for m in mixers)

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

#BAC CALCULATION SECTION
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
    r = 0.7
    bac = standard_drinks * 5.14 / (avg_weight_lbs * r)
    return bac

#RECOMMENDATION SECTION
def recommend_cocktails(user_prefs, max_results=5):
    alcohols = user_prefs["alcohol_types"]
    mixers = user_prefs["mixers"]
    seen = set()
    results = []
    for alc in alcohols:
        for d in fetch_drinks_by_alcohol(alc):
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
            results.append({"name": detail["strDrink"], "id": drink_id, "ingredients": ingredients, "instructions": detail.get("strInstructions", "").strip(), "thumb": detail.get("strDrinkThumb"), "detail": detail})
            seen.add(drink_id)
            if len(results) >= max_results:
                return results
    return results

#VISUALIZATION SECTION
def display_tipsiness_bar(bac, drink_label):
    if bac is None:
        print(f"Tipsiness estimate for {drink_label}:")
        print("Could not estimate BAC for this recipe.\n")
        return
    max_bac = 0.15
    pct = min(bac / max_bac, 1.0)
    filled = int(20 * pct)
    bar = "[" + "#" * filled + " " * (20 - filled) + "]"
    if bac < 0.02:
        label = "Very light effect"
    elif bac < 0.05:
        label = "Light buzz"
    elif bac < 0.08:
        label = "Tipsy"
    else:
        label = "Unsafe to drive"
    print(f"Estimated BAC from one serving of {drink_label}: {bac:.3f}")
    print(bar, label)
    print("Educational estimate only. Never drink and drive.\n")

def display_red_solo_cup(ingredients):
    total = 0.0
    for ing in ingredients:
        for w in ing.split():
            try:
                total += float(w)
                break
            except:
                if "/" in w:
                    try:
                        num, den = w.split("/")
                        total += float(num) / float(den)
                        break
                    except:
                        pass
    pct = min(total / 16, 1.0)
    filled = int(pct * 10)
    empty = 10 - filled
    print("\nYour Red Solo Cup fill level:")
    print("   _________ ")
    print("  /         \\")
    print(" /           \\")
    for _ in range(empty):
        print(" |           |")
    for _ in range(filled):
        print(" |###########|")
    print(" \\___________/")
    print(f"\nEstimated liquid: {total:.1f} oz ({pct*100:.0f}% of a solo cup)\n")

#MAIN APPLICATION SECTION
user_prefs = get_user_preferences()
recs = recommend_cocktails(user_prefs, max_results=5)
while not recs:
    print("No cocktails found for those ingredients. Try again.")
    user_prefs = get_user_preferences()
    recs = recommend_cocktails(user_prefs, max_results=5)

print("Cocktail recommendations for you:\n")
for i, rec in enumerate(recs, start=1):
    print(f"{i}. {rec['name']}")
    if rec["thumb"]:
        display(Image(requests.get(rec["thumb"]).content, width=200))
    print("Ingredients:")
    for ing in rec["ingredients"]:
        print(" ", ing)
    print("Instructions:", rec["instructions"])
    bac = estimate_bac_for_drink(rec["detail"], user_prefs["avg_weight_lbs"], user_prefs["alcohol_types"])
    display_tipsiness_bar(bac, rec["name"])

if len(recs) == 1:
    selected = recs[0]
    print("Only one result. Automatically selecting it.")
else:
    choice = input("Choose a drink number (1 to 5): ").strip()
    while not choice.isdigit() or not (1 <= int(choice) <= len(recs)):
        choice = input("Enter a valid number: ").strip()
    selected = recs[int(choice) - 1]

print("\nYou selected:", selected["name"])
youtube_url = f"https://www.youtube.com/results?search_query={selected['name'].replace(' ', '+')}+cocktail+recipe"
print("YouTube tutorial:", youtube_url)
webbrowser.open(youtube_url)

if selected["thumb"]:
    display(Image(requests.get(selected["thumb"]).content))

display_red_solo_cup(selected["ingredients"])
bac_final = estimate_bac_for_drink(selected["detail"], user_prefs["avg_weight_lbs"], user_prefs["alcohol_types"])
display_tipsiness_bar(bac_final, selected["name"])
