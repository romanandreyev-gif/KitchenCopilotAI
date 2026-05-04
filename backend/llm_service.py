import os
from dotenv import load_dotenv
from openai import OpenAI
from recipe_service import get_recipes_by_meal_type

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def generate_meals(family_profile=None):
    profile_text = family_profile or "No family profile provided."

    prompt = f"""
    Generate 6 family-friendly meal ideas.

    Family profile:
    {profile_text}

    Return ONLY a numbered list of meal names.
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.choices[0].message.content
    return [line.strip("0123456789. -") for line in text.split("\n") if line.strip()]


def generate_grocery_list(meals, family_profile=None):
    profile_text = family_profile or "Family size is not provided. Estimate for a family of 4."

    prompt = f"""
    Create a grocery shopping list with approximate quantities.

    Family profile:
    {profile_text}

    Selected meals:
    {', '.join(meals)}

    Return a clean checklist with quantities.
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def generate_cooking_steps(meals, family_profile=None):
    profile_text = family_profile or "Family preferences not provided."

    prompt = f"""
    Create short cooking steps for these meals.

    Family profile:
    {profile_text}

    Selected meals:
    {', '.join(meals)}

    Keep it practical and concise.
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def generate_day_meals(day, family_profile=None, used_meals=None, products_of_week=None):
    used_meals = used_meals or []
    products_of_week = products_of_week or []
    profile_text = family_profile or "Family preferences not specified."

    breakfast_recipes = get_recipes_by_meal_type("breakfast")
    lunch_recipes = get_recipes_by_meal_type("lunch")
    dinner_recipes = get_recipes_by_meal_type("dinner")

    prompt = f"""
    Select meal options for {day} from the recipe database below.

    Family profile:
    {profile_text}

    Products to prioritize this week:
    {products_of_week}

    Already selected meals this week:
    {used_meals}

    Breakfast recipes:
    {[recipe["name"] for recipe in breakfast_recipes]}

    Lunch recipes:
    {[recipe["name"] for recipe in lunch_recipes]}

    Dinner recipes:
    {[recipe["name"] for recipe in dinner_recipes]}

    Choose:
    - 3 breakfast options
    - 3 lunch options
    - 3 dinner options

    Rules:
    - Use ONLY recipe names from the provided database
    - Do NOT select meals from the already selected meals list
    - Prefer recipes that include products of the week, if such recipes exist
    - If there are no matching recipes, choose the best available recipes from the database
    - Do not invent new meals
    - Return ONLY meal names
    - Each meal name must be shorter than 80 characters

    Return format EXACTLY:

    Breakfast:
    1. ...
    2. ...
    3. ...

    Lunch:
    1. ...
    2. ...
    3. ...

    Dinner:
    1. ...
    2. ...
    3. ...
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


def parse_day_meals(text):
    sections = {"breakfast": [], "lunch": [], "dinner": []}
    current = None

    for line in text.split("\n"):
        line = line.strip()

        if line.lower().startswith("breakfast"):
            current = "breakfast"
        elif line.lower().startswith("lunch"):
            current = "lunch"
        elif line.lower().startswith("dinner"):
            current = "dinner"
        elif line and current:
            cleaned = line.lstrip("0123456789. -").strip()
            sections[current].append(cleaned)

    return sections