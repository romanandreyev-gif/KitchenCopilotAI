🍽️ KitchenCoPilot AI

AI-powered Telegram bot for family meal planning through voting

⸻

🚀 Overview

KitchenCoPilot AI is a Telegram bot that helps families agree on what to cook by combining AI-generated meal suggestions with simple group voting.

Instead of spending time discussing and negotiating meals, families can:
	•	get smart meal suggestions
	•	vote on preferred dishes directly in Telegram
	•	receive a finalized weekly plan and grocery list

⸻

❗ Problem

Planning meals for a family is harder than it seems:
	•	different tastes (adults vs kids)
	•	repeated meals due to lack of ideas
	•	time wasted on daily decisions
	•	friction in agreeing on what to cook

Most tools focus on recipes — not on decision-making.

⸻

💡 Solution

KitchenCoPilot AI solves this by:
	1.	Generating meal options using AI
	2.	Turning them into a Telegram poll
	3.	Letting the whole family vote
	4.	Automatically creating:
	•	a final meal plan
	•	a grocery list

Key idea:
Reduce decision friction, not just suggest recipes.

⸻

🧠 Core Features (MVP)
	•	AI-generated weekly meal options
	•	Telegram poll for family voting
	•	Automatic selection of winning meals
	•	Smart grocery list generation

⸻

🏗️ Architecture (High-Level)

Users (Family Members)
↓
Telegram Group Chat
↓
Telegram Bot (bot.py)
↓
Business Logic (planner.py)
↓
LLM Service (OpenAI API)
↓
Storage (JSON / simple DB)

Key components:

Telegram Interface Layer
	•	Handles commands (/start, /plan)
	•	Creates polls
	•	Sends results

Planner (Business Logic)
	•	Manages flow
	•	Processes preferences
	•	Builds final plan

LLM Service
	•	Generates meal options
	•	Creates grocery lists

Storage
	•	Preferences
	•	Poll data
	•	Final menu

⸻

🔄 User Flow
	1.	User starts bot (/start)
	2.	Bot collects basic preferences
	3.	User triggers planning (/plan)
	4.	AI generates meal options
	5.	Bot creates Telegram poll
	6.	Family votes
	7.	Bot processes results
	8.	Bot sends:
	•	final meal plan
	•	grocery list

⸻

🧱 Tech Stack
	•	Python
	•	Telegram Bot API
	•	OpenAI API (LLM)
	•	JSON (lightweight storage)

⸻

📦 Project Structure

project/

bot.py              # Telegram interface
planner.py          # Business logic
llm_service.py      # AI integration
storage.py          # Data handling
prompts.py          # Prompt templates
config.py           # Settings / tokens

requirements.txt
README.md

⸻

⚖️ Scope (MoSCoW)

MUST
	•	Telegram bot
	•	Meal generation via AI
	•	Poll-based voting
	•	Final menu + grocery list

SHOULD
	•	Better personalization
	•	Cleaner UX

WON’T (for MVP)
	•	Store integrations (prices, discounts)
	•	Complex multi-user profiles
	•	Full database system

⸻

🔮 Future Improvements
	•	Integration with grocery stores (Migros / Coop)
	•	Price-aware meal planning
	•	Individual user profiles
	•	Day-by-day meal scheduling
	•	WhatsApp / mobile integration

⸻

🎯 Key Insight

This project is not about recipes.

It’s about:
Helping families make decisions faster and with less friction.

⸻

🧪 How to Run (example)

git clone 
cd project
pip install -r requirements.txt
python bot.py

⸻

👤 Author

Roman Andreyev
AI / Product / Sales background

⸻

💬 Final Note

KitchenCoPilot AI demonstrates how LLMs can be used not only for content generation,
but for solving real-world coordination problems in everyday life.
