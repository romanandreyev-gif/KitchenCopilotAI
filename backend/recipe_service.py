import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECIPES_DIR = os.path.join(BASE_DIR, "recipes")


def load_recipes():
    all_recipes = []

    for filename in os.listdir(RECIPES_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(RECIPES_DIR, filename)

            with open(file_path, "r", encoding="utf-8") as file:
                recipes = json.load(file)
                all_recipes.extend(recipes)

    return all_recipes


def get_recipes_by_meal_type(meal_type):
    recipes = load_recipes()
    return [recipe for recipe in recipes if recipe["meal_type"] == meal_type]


def get_recipe_by_name(name):
    recipes = load_recipes()

    for recipe in recipes:
        if recipe["name"] == name:
            return recipe

    return None


def normalize_ingredient_name(name):
    name = name.strip().lower()

    aliases = {
        "eggs": "egg",
        "tomatoes": "tomato",
        "potato": "potatoes",
        "carrots": "carrot",
    }

    return aliases.get(name, name)


def categorize_ingredient(name):
    categories = {
        "🥩 Meat & Fish": [
            "chicken", "chicken breast", "chicken thigh", "chicken mince",
            "salmon fillet", "white fish", "minced beef", "minced meat",
            "turkey mince", "sausage"
        ],
        "🥛 Dairy & Eggs": [
            "milk", "butter", "cheese", "cottage cheese", "sour cream",
            "cream", "mozzarella", "feta cheese", "parmesan", "egg"
        ],
        "🥦 Vegetables": [
            "carrot", "onion", "potatoes", "broccoli", "tomato",
            "cabbage", "beetroot", "zucchini", "bell peppers",
            "lettuce", "mixed vegetables", "vegetables", "cucumber",
            "mushrooms"
        ],
        "🍚 Grains & Bakery": [
            "oats", "rice", "buckwheat", "pasta", "spaghetti", "noodles",
            "flour", "bread", "tortilla", "croutons"
        ],
        "🍯 Pantry & Sauces": [
            "honey", "sugar", "jam", "soy sauce", "tomato sauce",
            "pesto", "curry sauce"
        ],
    }

    for category, keywords in categories.items():
        if name in keywords:
            return category

    return "🧂 Other"


def format_quantity(quantity, unit):
    if unit in ["pcs", "slices"]:
        return f"{round(quantity)} {unit}"

    if quantity == int(quantity):
        return f"{int(quantity)} {unit}"

    return f"{round(quantity, 1)} {unit}"


def format_recipe_for_message(recipe_name, family_size=4):
    recipe = get_recipe_by_name(recipe_name)

    if not recipe:
        return f"Recipe not found: {recipe_name}"

    scale_factor = family_size / recipe.get("servings", 1)

    text = f"🍽️ {recipe['name']}\n\n"
    text += "Ingredients:\n"

    for ingredient in recipe["ingredients"]:
        quantity = ingredient["quantity"] * scale_factor
        text += f"- {ingredient['name']}: {format_quantity(quantity, ingredient['unit'])}\n"

    text += "\nSteps:\n"

    for i, step in enumerate(recipe["steps"], 1):
        text += f"{i}. {step}\n"

    return text

def build_grocery_list_from_recipes(meal_names, family_size=1):
    recipes = load_recipes()
    ingredient_totals = {}
    ignored_items = {"water"}

    for meal_name in meal_names:
        recipe = next((r for r in recipes if r["name"] == meal_name), None)

        if not recipe:
            continue

        scale_factor = family_size / recipe.get("servings", 1)

        for ingredient in recipe["ingredients"]:
            name = normalize_ingredient_name(ingredient["name"])

            if name in ignored_items:
                continue

            unit = ingredient["unit"]
            quantity = ingredient["quantity"] * scale_factor

            key = (name, unit)
            ingredient_totals[key] = ingredient_totals.get(key, 0) + quantity

    grouped = {}

    for (name, unit), quantity in ingredient_totals.items():
        category = categorize_ingredient(name)

        if category not in grouped:
            grouped[category] = []

        grouped[category].append((name, quantity, unit))

    result = "🛒 Grocery list:\n\n"

    for category in sorted(grouped.keys()):
        result += f"{category}\n"

        for name, quantity, unit in sorted(grouped[category]):
            result += f"☐ {name}: {format_quantity(quantity, unit)}\n"

        result += "\n"

    return result