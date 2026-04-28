import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    PollAnswerHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from storage import save_profile, load_profile
from llm_service import generate_meals, generate_grocery_list
from llm_service import generate_meals, generate_grocery_list, generate_cooking_steps
from llm_service import generate_day_meals, parse_day_meals
from recipe_service import build_grocery_list_from_recipes

# In-memory storage for polls and user votes
poll_data = {}

# Tracks users who are currently entering their profile
waiting_for_profile = set()

DAYS_OF_WEEK = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
]

MEAL_TYPES = [
    "breakfast",
    "lunch",
    "dinner"
]

weekly_state = {
    "active": False,
    "current_day_index": 0,
    "menu": {},
    "polls": {}
}

# Load environment variables (.env)
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
COOK_TELEGRAM_ID = os.getenv("COOK_TELEGRAM_ID")

# Inline buttons shown inside chat messages
INLINE_KEYBOARD = InlineKeyboardMarkup([
   [
        InlineKeyboardButton("🗓️ Weekly menu", callback_data="weekly_menu"),
    ],
    [
        InlineKeyboardButton("🍽️ Plan meals", callback_data="plan"),
        InlineKeyboardButton("👨‍👩‍👧‍👦 Profile", callback_data="profile"),
    ]
])


# /start command — entry point of the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I am KitchenCoPilot AI.\n\n"
        "I help families agree on what to cook — using AI + voting.\n\n"
        "Choose an option below:",
        reply_markup=INLINE_KEYBOARD
    )


def clean_poll_options(options):
    cleaned = []

    for option in options:
        option = option.strip()

        if len(option) > 95:
            option = option[:92].strip() + "..."

        cleaned.append(option)

    return cleaned[:3]

def get_poll_winner(poll_id):
    if poll_id not in poll_data:
        return None

    meals = poll_data[poll_id]["meals"]
    votes = poll_data[poll_id]["votes"]

    vote_count = [0] * len(meals)

    for user_votes in votes.values():
        for option in user_votes:
            vote_count[option] += 1

    if max(vote_count) == 0:
        return meals[0]

    winner_index = vote_count.index(max(vote_count))
    return meals[winner_index]


async def generate_day_polls(message_source, day):
    await message_source.reply_text(f"🗓️ Planning {day}...")

    family_profile = load_profile()
    used_meals = []
    
    for meals in weekly_state["menu"].values():
        used_meals.extend([
            meals["breakfast"],
            meals["lunch"],
            meals["dinner"]
        ])

    raw = generate_day_meals(day, family_profile, used_meals)
    meals = parse_day_meals(raw)

    breakfast_options = clean_poll_options(meals["breakfast"])
    lunch_options = clean_poll_options(meals["lunch"])
    dinner_options = clean_poll_options(meals["dinner"])

    await message_source.reply_text(f"🍳 {day} — Breakfast options:")
    breakfast_poll = await message_source.reply_poll(
        question=f"{day} Breakfast",
        options=breakfast_options,
        is_anonymous=False
    )

    await message_source.reply_text(f"🥗 {day} — Lunch options:")
    lunch_poll = await message_source.reply_poll(
        question=f"{day} Lunch",
        options=lunch_options,
        is_anonymous=False
    )

    await message_source.reply_text(f"🍝 {day} — Dinner options:")
    dinner_poll = await message_source.reply_poll(
        question=f"{day} Dinner",
        options=dinner_options,
        is_anonymous=False
    )

    weekly_state["polls"][day] = {
        "breakfast": breakfast_poll.poll.id,
        "lunch": lunch_poll.poll.id,
        "dinner": dinner_poll.poll.id
    }

    poll_data[breakfast_poll.poll.id] = {
        "day": day,
        "meal_type": "breakfast",
        "meals": breakfast_options,
        "votes": {}
    }

    poll_data[lunch_poll.poll.id] = {
        "day": day,
        "meal_type": "lunch",
        "meals": lunch_options,
        "votes": {}
    }

    poll_data[dinner_poll.poll.id] = {
        "day": day,
        "meal_type": "dinner",
        "meals": dinner_options,
        "votes": {}
    }

    finalize_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Finalize {day}", callback_data="finalize_day")]
    ])

    await message_source.reply_text(
        "When everyone has voted, press the button below.",
        reply_markup=finalize_keyboard
    )

# Handles clicks on inline buttons
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass

    if query.data == "plan":
        await run_plan(query.message)

    elif query.data == "profile":
        user_id = query.from_user.id
        await run_profile(query.message, user_id)

    elif query.data == "weekly_menu":
        weekly_state["active"] = True
        weekly_state["current_day_index"] = 0
        weekly_state["menu"] = {}
        weekly_state["polls"] = {}

        day = DAYS_OF_WEEK[0]

        await query.message.reply_text(
            "🗓️ Weekly menu planning started.\n\n"
            "We will plan meals from Sunday to Saturday, one day at a time."
        )

        await generate_day_polls(query.message, day)

    elif query.data == "finalize_day":
        day = DAYS_OF_WEEK[weekly_state["current_day_index"]]

        breakfast_poll_id = weekly_state["polls"][day]["breakfast"]
        lunch_poll_id = weekly_state["polls"][day]["lunch"]
        dinner_poll_id = weekly_state["polls"][day]["dinner"]

        weekly_state["menu"][day] = {
            "breakfast": get_poll_winner(breakfast_poll_id),
            "lunch": get_poll_winner(lunch_poll_id),
            "dinner": get_poll_winner(dinner_poll_id),
        }

        day_menu = weekly_state["menu"][day]

        await query.message.reply_text(
            f"✅ {day} finalized:\n\n"
            f"🍳 Breakfast: {day_menu['breakfast']}\n"
            f"🥗 Lunch: {day_menu['lunch']}\n"
            f"🍝 Dinner: {day_menu['dinner']}"
        )
                # Move to the next day
        weekly_state["current_day_index"] += 1

        # If there are more days, generate the next day polls
        if weekly_state["current_day_index"] < len(DAYS_OF_WEEK):
            next_day = DAYS_OF_WEEK[weekly_state["current_day_index"]]

            await query.message.reply_text(f"➡️ Moving to {next_day}...")
            await generate_day_polls(query.message, next_day)

        # If Saturday is finalized, finish weekly planning
        else:
            weekly_state["active"] = False

            text = "🎉 Weekly menu completed!\n\n"
            text += "🗓️ Your weekly menu:\n\n"

            for day, meals in weekly_state["menu"].items():
                text += f"{day}:\n"
                text += f"🍳 Breakfast: {meals['breakfast']}\n"
                text += f"🥗 Lunch: {meals['lunch']}\n"
                text += f"🍝 Dinner: {meals['dinner']}\n\n"

            await query.message.reply_text(text)
            all_week_meals = []

            for day, meals in weekly_state["menu"].items():
                all_week_meals.append(meals["breakfast"])
                all_week_meals.append(meals["lunch"])
                all_week_meals.append(meals["dinner"])

            family_profile = load_profile()
            from recipe_service import build_grocery_list_from_recipes

            weekly_grocery_list = build_grocery_list_from_recipes(
                all_week_meals,
                family_size=4  # later we’ll extract from profile
            )

            await context.bot.send_message(
                chat_id=int(COOK_TELEGRAM_ID),
                text=weekly_grocery_list
            )

# /plan command (fallback if user types command manually)
async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_plan(update.message)


# /profile command (fallback)
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await run_profile(update.message, user_id)


# Core logic: generate meals and create poll
async def run_plan(message_source):
    await message_source.reply_text("🍽️ Generating meal options...")

    # Load user profile and generate meals via LLM
    family_profile = load_profile()
    meals = generate_meals(family_profile)
    meals = meals[:6]  # limit to Telegram poll max

    # Send poll to user
    message = await message_source.reply_poll(
        question="What should we cook this week?",
        options=meals,
        is_anonymous=False,
        allows_multiple_answers=True,
    )

    # Store poll metadata
    poll_data[message.poll.id] = {
        "meals": meals,
        "votes": {},
        "sent": False
    }


# Core logic: ask user to input family profile
async def run_profile(message_source, user_id):
    waiting_for_profile.add(user_id)

    await message_source.reply_text(
        "👨‍👩‍👧‍👦 Please describe your family and food preferences in one message.\n\n"
        "Example:\n"
        "We are a family of 4. Two kids aged 10 and 14. "
        "We like chicken, pasta, soups and vegetables. "
        "We avoid very spicy food. Max cooking time is 45 minutes."
    )


# Handles user text input (used for saving profile)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # If user is expected to send profile → save it
    if user_id in waiting_for_profile:
        profile_text = update.message.text
        save_profile(user_id, profile_text)
        waiting_for_profile.remove(user_id)

        await update.message.reply_text(
            "✅ Family profile saved!\n\n"
            "Use /start to continue."
        )


# Handles votes in poll
async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer

    poll_id = answer.poll_id
    user_id = answer.user.id
    option_ids = answer.option_ids

    if poll_id not in poll_data:
        return

    # Weekly menu polls: only save votes
    if "day" in poll_data[poll_id]:
        poll_data[poll_id]["votes"][user_id] = option_ids
        return

    # 🚫 Prevent sending multiple times
    if poll_data[poll_id].get("sent"):
        return

    # Save user vote
    poll_data[poll_id]["votes"][user_id] = option_ids

    # Count votes
    vote_count = [0] * len(poll_data[poll_id]["meals"])

    for votes in poll_data[poll_id]["votes"].values():
        for option in votes:
            vote_count[option] += 1

    meals = poll_data[poll_id]["meals"]

    # Sort meals by popularity
    ranked = sorted(
        zip(meals, vote_count),
        key=lambda x: x[1],
        reverse=True
    )

    # Select meals with at least one vote
    top_meals = [meal for meal, count in ranked if count > 0]

    if top_meals:
        family_profile = load_profile()
        grocery_list = generate_grocery_list(top_meals, family_profile)
        cooking_steps = generate_cooking_steps(top_meals, family_profile)

        text = "🏆 Final meal plan:\n\n"
        for meal in top_meals:
            text += f"🍽️ {meal}\n"

        text += "\n🛒 Grocery list:\n"
        text += grocery_list

        text += "\n\n👨‍🍳 Cooking steps:\n"
        text += cooking_steps

        # ✅ Mark as sent BEFORE sending
        poll_data[poll_id]["sent"] = True

        print("Sending grocery list to cook:", COOK_TELEGRAM_ID)

        await context.bot.send_message(
            chat_id=int(COOK_TELEGRAM_ID),
            text=text
        )

# App entry point
def main():
    if not TOKEN:
        raise ValueError("❌ TELEGRAM_TOKEN not found in .env file")

    app = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    print("🚀 KitchenCoPilot AI is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
