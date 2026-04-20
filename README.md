# 🤖 Annotator Pro

**Annotator Pro** is a high-performance Telegram Bot Orchestrator designed specifically for **Centific Annotation** workflows. Built with a robust state machine and a credit-based billing system, it enables users to perform complex AI evaluation and content generation tasks directly through Telegram.

---

## 🌟 Key Features

- 💳 **Credit-Based Billing**: Pay-per-hit system with dynamic pricing based on input length and model tier.
- 🏗️ **Multi-Project Support**: Seamlessly switch between different projects (e.g., Cherry Opal).
- 🛠️ **Diverse Task Types**:
  - **PR Fine Tuning**: Instruction following and localization evaluation.
  - **AFM (Safety Guide)**: Multi-modal safety and harm-free assessment.
  - **Text Composition (TA/TC)**: Proofreading, message replies, and writing QA.
  - **CYU (Website Topic)**: Topic identification and topline summarization.
  - **VCG (Visual Content Generation)**: Image analysis, editing, and variety review.
- 💎 **Multi-Tier AI Engine**:
  - **Basic**: Powered by Gemini 3 Flash.
  - **Pro**: Powered by Gemini 3.1 Pro.
  - **Premium**: Powered by Claude 3.5 Sonnet.
- 🛂 **Admin Dashboard**: Real-time balance management, maintenance mode, and usage statistics.
- 🌐 **Multi-Language Support**: Supports Indonesian, English, Thai, Japanese, Korean, and more.

---

## 🚀 Tech Stack

- **Language**: Python 3.10+
- **Framework**: [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- **Database**: PostgreSQL (via `asyncpg`)
- **ORM**: SQLModel / SQLAlchemy
- **AI Integration**: Custom KIE AI API (Gemini/Claude)
- **Environment**: python-dotenv

---

## 📂 Project Structure

```text
.
├── assets/                 # Prompt instructions, forms, and guidelines
│   ├── forms/              # Task-specific form definitions
│   ├── guidelines/         # Project guidelines
│   └── prompts/            # AI instruction templates
├── bot.py                  # Main Bot Orchestrator (State Machine)
├── database.py             # Database engine & session management
├── kie_api.py              # AI Model API integration layer
├── models.py               # SQLModel database schemas
├── prompt_assembler.py     # Dynamic prompt construction logic
├── user_service.py         # Business logic for user & credit management
├── requirements.txt        # Project dependencies
└── README.md               # You are here!
```

---

## 🛠️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/galang-pradhana/annotator-helper.git
   cd annotator-helper
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
   KIE_AI_API_KEY=your_api_key
   KIE_API_URL=https://api.your-ai-service.com
   ADMIN_ID=your_telegram_id
   ```

4. **Initialize Database**:
   ```bash
   python seed_db.py
   ```

5. **Run the Bot**:
   ```bash
   python bot.py
   ```

---

## 📖 Usage

1. Start the bot with `/start`.
2. Choose your target **Language**.
3. Select the **Project** and **Task** type.
4. Pick your preferred **AI Tier** (Basic/Pro).
5. Follow the step-by-step input guide provided by the bot.
6. Use `/cancel` to stop at any time or `/status` to check your balance.

---

## 🛡️ Admin Commands

- `/add_balance <user_id> <amount>`: Grant credits to a user.
- `/maintenance`: Toggle maintenance mode.
- `/stats`: View global usage statistics.
- `/broadcast <message>`: Send a message to all registered users.

---

## 📄 License

This project is private and intended for use by the **Centific Annotation** team.

---
*Created with ❤️ by Galang Pradhana*