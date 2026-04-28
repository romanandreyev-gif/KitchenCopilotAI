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


def build_grocery_list_from_recipes(meal_names, family_size=1):
    recipes = load_recipes()
    ingredient_totals = {}

    for meal_name in meal_names:
        recipe = next((r for r in recipes if r["name"] == meal_name), None)

        if not recipe:
            continue

        scale_factor = family_size / recipe.get("servings", 1)

        for ingredient in recipe["ingredients"]:
            key = (ingredient["name"], ingredient["unit"])
            quantity = ingredient["quantity"] * scale_factor

            ingredient_totals[key] = ingredient_totals.get(key, 0) + quantity

    result = "🛒 Grocery list:\n\n"

    for (name, unit), quantity in ingredient_totals.items():
        result += f"☐ {name}: {round(quantity, 1)} {unit}\n"

    return result