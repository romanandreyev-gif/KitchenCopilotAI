import os
import random
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
from llm_service import generate_day_meals, parse_day_meals
from recipe_service import build_grocery_list_from_recipes, format_recipe_for_message


poll_data = {}
waiting_for_profile = set()
waiting_for_products = set()

DAYS_OF_WEEK = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday"
]

weekly_state = {
    "active": False,
    "current_day_index": 0,
    "menu": {},
    "polls": {},
    "products": [],
    "cook_id": None,
}

smart_plan_state = {
    "menu": {},
    "products": [],
    "cook_id": None,
}

final_menu_state = {
    "menu": {}
}

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
COOK_TELEGRAM_ID = os.getenv("COOK_TELEGRAM_ID")


INLINE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("👨‍🍳 Set me as cook", callback_data="set_cook")],
    [InlineKeyboardButton("🗳️ Plan with voting", callback_data="weekly_menu")],
    [InlineKeyboardButton("⚡ Smart weekly plan", callback_data="smart_plan")],
    [InlineKeyboardButton("👨‍👩‍👧‍👦 Profile", callback_data="profile")],
])

SMART_PLAN_REVIEW_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("👍 Looks good", callback_data="smart_accept"),
        InlineKeyboardButton("👎 Try again", callback_data="smart_retry"),
    ]
])

POST_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🛒 Shopping list", callback_data="show_shopping_list")],
    [InlineKeyboardButton("👨‍🍳 Sunday recipes", callback_data="recipes_Sunday")],
    [InlineKeyboardButton("👨‍🍳 Monday recipes", callback_data="recipes_Monday")],
    [InlineKeyboardButton("👨‍🍳 Tuesday recipes", callback_data="recipes_Tuesday")],
    [InlineKeyboardButton("👨‍🍳 Wednesday recipes", callback_data="recipes_Wednesday")],
    [InlineKeyboardButton("👨‍🍳 Thursday recipes", callback_data="recipes_Thursday")],
    [InlineKeyboardButton("👨‍🍳 Friday recipes", callback_data="recipes_Friday")],
    [InlineKeyboardButton("👨‍🍳 Saturday recipes", callback_data="recipes_Saturday")],
])


def get_cook_id():
    return (
        weekly_state.get("cook_id")
        or smart_plan_state.get("cook_id")
        or int(COOK_TELEGRAM_ID)
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I am KitchenCoPilot AI.\n\n"
        "I help families agree on what to cook — using AI + voting.\n\n"
        "Choose an option below:",
        reply_markup=INLINE_KEYBOARD,
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

    max_votes = max(vote_count)

    if max_votes == 0:
        return random.choice(meals)

    winners = [i for i, v in enumerate(vote_count) if v == max_votes]
    return meals[random.choice(winners)]


async def ask_products_before_planning(message_source, mode):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Add products of the week", callback_data=f"add_products_{mode}")],
        [InlineKeyboardButton("⏭ Skip", callback_data=f"skip_products_{mode}")],
    ])

    await message_source.reply_text(
        "Would you like to prioritize any products this week?\n\n"
        "Example: salmon, chicken, ribs\n\n"
        "You can add products or skip this step.",
        reply_markup=keyboard,
    )


async def generate_day_polls(message_source, day):
    await message_source.reply_text(f"🗓️ Planning {day}...")

    family_profile = load_profile()

    used_meals = []
    for meals in weekly_state["menu"].values():
        used_meals.extend([
            meals["breakfast"],
            meals["lunch"],
            meals["dinner"],
        ])

    products_of_week = weekly_state.get("products", [])

    raw = generate_day_meals(
        day,
        family_profile,
        used_meals,
        products_of_week,
    )

    meals = parse_day_meals(raw)

    breakfast_options = clean_poll_options(meals["breakfast"])
    lunch_options = clean_poll_options(meals["lunch"])
    dinner_options = clean_poll_options(meals["dinner"])

    await message_source.reply_text(f"🍳 {day} — Breakfast options:")
    breakfast_poll = await message_source.reply_poll(
        question=f"{day} Breakfast",
        options=breakfast_options,
        is_anonymous=False,
    )

    await message_source.reply_text(f"🥗 {day} — Lunch options:")
    lunch_poll = await message_source.reply_poll(
        question=f"{day} Lunch",
        options=lunch_options,
        is_anonymous=False,
    )

    await message_source.reply_text(f"🍝 {day} — Dinner options:")
    dinner_poll = await message_source.reply_poll(
        question=f"{day} Dinner",
        options=dinner_options,
        is_anonymous=False,
    )

    weekly_state["polls"][day] = {
        "breakfast": breakfast_poll.poll.id,
        "lunch": lunch_poll.poll.id,
        "dinner": dinner_poll.poll.id,
    }

    poll_data[breakfast_poll.poll.id] = {
        "day": day,
        "meal_type": "breakfast",
        "meals": breakfast_options,
        "votes": {},
    }

    poll_data[lunch_poll.poll.id] = {
        "day": day,
        "meal_type": "lunch",
        "meals": lunch_options,
        "votes": {},
    }

    poll_data[dinner_poll.poll.id] = {
        "day": day,
        "meal_type": "dinner",
        "meals": dinner_options,
        "votes": {},
    }

    finalize_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Finalize {day}", callback_data="finalize_day")]
    ])

    await message_source.reply_text(
        "When everyone has voted, press the button below.",
        reply_markup=finalize_keyboard,
    )


async def start_weekly_planning(message_source):
    weekly_state["active"] = True
    weekly_state["current_day_index"] = 0
    weekly_state["menu"] = {}
    weekly_state["polls"] = {}

    products = weekly_state.get("products", [])

    if products:
        await message_source.reply_text(
            "🛒 Products of the week:\n"
            + ", ".join(products)
            + "\n\nI will try to prioritize recipes with these ingredients."
        )

    await message_source.reply_text(
        "🗳️ Weekly menu with voting started.\n\n"
        "We will plan meals from Sunday to Saturday, one day at a time."
    )

    await generate_day_polls(message_source, DAYS_OF_WEEK[0])


async def generate_smart_weekly_menu(message_source):
    await message_source.reply_text("⚡ Generating smart weekly menu...")

    family_profile = load_profile()
    products = smart_plan_state.get("products", [])

    week_menu = {}
    used_meals = []

    for day in DAYS_OF_WEEK:
        raw = generate_day_meals(
            day,
            family_profile,
            used_meals,
            products,
        )

        meals = parse_day_meals(raw)

        selected = {
            "breakfast": meals["breakfast"][0],
            "lunch": meals["lunch"][0],
            "dinner": meals["dinner"][0],
        }

        week_menu[day] = selected

        used_meals.extend([
            selected["breakfast"],
            selected["lunch"],
            selected["dinner"],
        ])

    smart_plan_state["menu"] = week_menu

    text = "⚡ Smart weekly menu proposal:\n\n"

    for day, meals in week_menu.items():
        text += f"{day}:\n"
        text += f"🍳 {meals['breakfast']}\n"
        text += f"🥗 {meals['lunch']}\n"
        text += f"🍝 {meals['dinner']}\n\n"

    await message_source.reply_text(
        text,
        reply_markup=SMART_PLAN_REVIEW_KEYBOARD,
    )


def build_menu_text(title, menu):
    text = f"{title}\n\n"

    for day, meals in menu.items():
        text += f"{day}:\n"
        text += f"🍳 Breakfast: {meals['breakfast']}\n"
        text += f"🥗 Lunch: {meals['lunch']}\n"
        text += f"🍝 Dinner: {meals['dinner']}\n\n"

    return text


async def show_post_menu_options(message_source):
    await message_source.reply_text(
        "What would you like to receive?",
        reply_markup=POST_MENU_KEYBOARD,
    )


async def send_shopping_list_to_cook(message_source):
    menu = final_menu_state.get("menu", {})

    if not menu:
        await message_source.reply_text("No approved weekly menu found yet.")
        return

    all_week_meals = []

    for meals in menu.values():
        all_week_meals.append(meals["breakfast"])
        all_week_meals.append(meals["lunch"])
        all_week_meals.append(meals["dinner"])

    shopping_list = build_grocery_list_from_recipes(
        all_week_meals,
        family_size=4,
    )

    bot = message_source.get_bot()

    await bot.send_message(
        chat_id=get_cook_id(),
        text=shopping_list,
    )

    await message_source.reply_text("✅ Shopping list sent to the cook.")


async def send_day_recipes_to_cook(message_source, day):
    menu = final_menu_state.get("menu", {})

    if not menu or day not in menu:
        await message_source.reply_text(f"No recipes found for {day}.")
        return

    meals = menu[day]

    text = f"👨‍🍳 {day} recipes\n\n"
    text += format_recipe_for_message(meals["breakfast"], family_size=4)
    text += "\n\n"
    text += format_recipe_for_message(meals["lunch"], family_size=4)
    text += "\n\n"
    text += format_recipe_for_message(meals["dinner"], family_size=4)

    bot = message_source.get_bot()

    await bot.send_message(
        chat_id=get_cook_id(),
        text=text,
    )

    await message_source.reply_text(f"✅ {day} recipes sent to the cook.")


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        await query.answer()
    except Exception:
        pass

    if query.data == "set_cook":
        user_id = query.from_user.id
        weekly_state["cook_id"] = user_id
        smart_plan_state["cook_id"] = user_id

        await query.message.reply_text(
            "👨‍🍳 Done! You are now set as the cook for this session."
        )

    elif query.data == "profile":
        await run_profile(query.message, query.from_user.id)

    elif query.data == "weekly_menu":
        context.user_data["planning_mode"] = "voting"
        await ask_products_before_planning(query.message, "voting")

    elif query.data == "smart_plan":
        context.user_data["planning_mode"] = "smart"
        await ask_products_before_planning(query.message, "smart")

    elif query.data == "add_products_voting":
        waiting_for_products.add(query.from_user.id)
        context.user_data["planning_mode"] = "voting"

        await query.message.reply_text(
            "✏️ Please enter products separated by commas.\n\n"
            "Example: salmon, chicken, ribs"
        )

    elif query.data == "add_products_smart":
        waiting_for_products.add(query.from_user.id)
        context.user_data["planning_mode"] = "smart"

        await query.message.reply_text(
            "✏️ Please enter products separated by commas.\n\n"
            "Example: salmon, chicken, ribs"
        )

    elif query.data == "skip_products_voting":
        weekly_state["products"] = []
        await start_weekly_planning(query.message)

    elif query.data == "skip_products_smart":
        smart_plan_state["products"] = []
        await generate_smart_weekly_menu(query.message)

    elif query.data == "smart_retry":
        await generate_smart_weekly_menu(query.message)

    elif query.data == "smart_accept":
        final_menu_state["menu"] = smart_plan_state["menu"]

        await query.message.reply_text(
            "✅ Smart weekly menu approved."
        )

        await show_post_menu_options(query.message)

    elif query.data == "show_shopping_list":
        await send_shopping_list_to_cook(query.message)

    elif query.data.startswith("recipes_"):
        day = query.data.replace("recipes_", "")
        await send_day_recipes_to_cook(query.message, day)

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

        weekly_state["current_day_index"] += 1

        if weekly_state["current_day_index"] < len(DAYS_OF_WEEK):
            next_day = DAYS_OF_WEEK[weekly_state["current_day_index"]]

            await query.message.reply_text(f"➡️ Moving to {next_day}...")
            await generate_day_polls(query.message, next_day)

        else:
            weekly_state["active"] = False
            final_menu_state["menu"] = weekly_state["menu"]

            menu_text = build_menu_text(
                "🎉 Weekly menu completed!\n\n🗓️ Your weekly menu:",
                weekly_state["menu"],
            )

            await query.message.reply_text(menu_text)

            await show_post_menu_options(query.message)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_profile(update.message, update.effective_user.id)


async def run_profile(message_source, user_id):
    waiting_for_profile.add(user_id)

    await message_source.reply_text(
        "👨‍👩‍👧‍👦 Please describe your family and food preferences in one message.\n\n"
        "Example:\n"
        "We are a family of 4. Two kids aged 10 and 14. "
        "We like chicken, pasta, soups and vegetables. "
        "We avoid very spicy food. Max cooking time is 45 minutes."
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id in waiting_for_products:
        products = [
            product.strip().lower()
            for product in text.split(",")
            if product.strip()
        ]

        waiting_for_products.remove(user_id)

        mode = context.user_data.get("planning_mode")

        if mode == "voting":
            weekly_state["products"] = products

            await update.message.reply_text(
                "✅ Products saved:\n"
                + ", ".join(products)
                + "\n\n🗓️ Starting voting-based weekly planning..."
            )

            await start_weekly_planning(update.message)

        elif mode == "smart":
            smart_plan_state["products"] = products

            await update.message.reply_text(
                "✅ Products saved:\n"
                + ", ".join(products)
                + "\n\n⚡ Starting smart weekly planning..."
            )

            await generate_smart_weekly_menu(update.message)

        else:
            await update.message.reply_text(
                "I saved the products, but planning mode was not detected. Please start again with /start."
            )

        return

    if user_id in waiting_for_profile:
        save_profile(user_id, text)
        waiting_for_profile.remove(user_id)

        await update.message.reply_text(
            "✅ Family profile saved!\n\n"
            "Use /start to continue."
        )
        return


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer

    poll_id = answer.poll_id
    user_id = answer.user.id
    option_ids = answer.option_ids

    if poll_id not in poll_data:
        return

    if "day" in poll_data[poll_id]:
        poll_data[poll_id]["votes"][user_id] = option_ids
        return


def main():
    if not TOKEN:
        raise ValueError("❌ TELEGRAM_TOKEN not found in .env file")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    print("🚀 KitchenCoPilot AI is running...")
    app.run_polling()


if __name__ == "__main__":
    main()