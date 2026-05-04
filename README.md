KitchenCoPilot AI

KitchenCoPilot AI is a Telegram bot that helps families plan weekly meals in a smart and collaborative way.

It combines AI-generated meal planning, family voting, automatic grocery lists, and structured recipe delivery to remove the daily question: “What should we cook?”

⸻

Features

1. Weekly Planning with Voting

* Generates meal options for each day
* Family members vote
* Most popular dishes form the weekly menu

2. Smart Weekly Plan (No Voting)

* Automatically generates a full weekly menu
* Based on family preferences
* Avoids repeating meals
* Can prioritize specific products (e.g. salmon, chicken)

3. Grocery List Generator

* Combines ingredients from all meals
* Removes duplicates
* Groups items by categories (meat, vegetables, dairy, etc.)

4. Cook Mode

* One user can assign themselves as the cook
* The cook receives:
    * Shopping list
    * Recipes (on demand)

5. Clean Recipe Experience

* No spam of 21 recipes at once
* Recipes are requested by day:
    * Sunday recipes
    * Monday recipes
    * etc.

⸻

How It Works

1. User starts the bot
2. Optionally sets:
    * Family profile
    * Weekly priority products
3. Chooses planning mode:
    * Voting OR Smart plan
4. Bot generates weekly menu
5. After approval:
    * Grocery list is generated
    * Recipes are available per day

⸻

Tech Stack

* Python 3.9+
* python-telegram-bot
* OpenAI API
* JSON-based recipe database

⸻

Project Structure

backend/

bot.py — main Telegram bot logic
llm_service.py — AI meal generation
recipe_service.py — recipe and grocery logic
storage.py — user profile handling

recipes/

* breakfast.json
* lunch.json
* dinner.json

.env — environment variables
requirements.txt — dependencies

⸻

Setup Instructions

1. Clone repository

git clone https://github.com/your-repo/KitchenCopilotAI.git
cd KitchenCopilotAI/backend

⸻

2. Create virtual environment

python -m venv .venv
source .venv/bin/activate

⸻

3. Install dependencies

pip install -r requirements.txt

⸻

4. Create .env file

TELEGRAM_TOKEN=your_telegram_bot_token
COOK_TELEGRAM_ID=your_telegram_id
OPENAI_API_KEY=your_openai_key

⸻

5. Run the bot

python bot.py

You should see:
“KitchenCoPilot AI is running…”

⸻

How to Use

Open Telegram → Start your bot

Option 1 — Voting mode

* Plan meals day-by-day
* Vote with family

Option 2 — Smart plan

* Get full weekly menu instantly
* Approve or regenerate

After approval:

* Request shopping list
* Request recipes by day

⸻

Future Improvements

* Better cooking instructions (step-by-step recipes)
* Save meal history to avoid repetition
* Nutrition tracking (calories, macros)
* Integration with supermarket promotions
* Export to PDF or Notion
* Multi-language support

⸻

Vision

KitchenCoPilot AI aims to become a full family food assistant:

* Plan smarter
* Shop faster
* Cook easier

⸻

Author

Roman Andreyev
Built as part of a Powercoders individual project