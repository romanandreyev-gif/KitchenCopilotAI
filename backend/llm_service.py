import os
from dotenv import load_dotenv
from openai import OpenAI
from recipe_service import get_recipes_by_meal_type

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def generate_meals(family_profile=None):
    profile_text = family_profile or "No family profile provided. Use general family-friendly preferences."

    prompt = f"""
    Generate 6 dinner meal options for this family profile:

    {profile_text}

    Requirements:
    - family-friendly
    - simple recipes
    - varied meals
    - suitable for kids
    - realistic for home cooking

    Return ONLY a numbered list of meal names.
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    text = response.choices[0].message.content

    meals = text.split("\n")
    meals = [m.strip("0123456789. -").strip() for m in meals if m.strip()]

    return meals

def generate_grocery_list(meals, family_profile=None):
    profile_text = family_profile or "Family size is not provided. Estimate for a family of 4."

    prompt = f"""
    Create a grocery shopping list with approximate quantities.

    Family profile:
    {profile_text}

    Selected meals:
    {', '.join(meals)}

    Requirements:
    - estimate quantities based on family size
    - group similar ingredients
    - use practical shopping units
    - keep it concise
    - no explanations

    Example format:
    ☐ Chicken breast: 600 g
    ☐ Pasta: 400 g
    ☐ Tomatoes: 6 pcs
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.choices[0].message.content

def generate_cooking_steps(meals, family_profile=None):
    profile_text = family_profile or "Family size is not provided."

    prompt = f"""
    Create simple cooking steps for these selected meals.

    Family profile:
    {profile_text}

    Selected meals:
    {', '.join(meals)}

    Requirements:
    - short and practical
    - suitable for home cooking
    - include preparation order
    - no long explanations
    """

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.choices[0].message.content

def generate_day_meals(day, family_profile=None, used_meals=None):
    profile_text = family_profile or "Family preferences not specified."

    breakfast_recipes = get_recipes_by_meal_type("breakfast")
    lunch_recipes = get_recipes_by_meal_type("lunch")
    dinner_recipes = get_recipes_by_meal_type("dinner")

    prompt = f"""
    Select meal options for {day} from the recipe database below.

    used_meals = used_meals or []

    Family profile:
    {profile_text}

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

    Already selected meals this week:
    {used_meals}

    Rules:
    - Use ONLY recipe names from the provided database
    - Do NOT select meals from the already selected meals list
    - Prefer variety across the week
    - Do not invent new meals
    - Return format EXACTLY:

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
            cleaned = line.lstrip("123. ").strip()
            sections[current].append(cleaned)

    return sections