# 💸 Spendly — Expense Tracker

A mini full-stack expense tracker built with **Flask + SQLite**.

## Features
- ✅ Add / Edit / Delete expenses
- 🏷️ Categories with custom icons & colors
- 🔖 Tags per expense
- 📊 Analytics — donut chart, monthly bar chart, category breakdown
- 🌙 Dark UI

## Project Structure
```
expense_tracker/
├── app.py               # Flask app, models, API routes
├── requirements.txt
├── templates/
│   └── index.html       # Single-page frontend (HTML + JS + Chart.js)
└── instance/
    └── expenses.db      # SQLite DB (auto-created on first run)
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/expenses` | List expenses (filter: `?category=&tag=`) |
| POST | `/api/expenses` | Create expense |
| PUT | `/api/expenses/<id>` | Update expense |
| DELETE | `/api/expenses/<id>` | Delete expense |
| GET | `/api/categories` | List categories |
| POST | `/api/categories` | Create category |
| DELETE | `/api/categories/<id>` | Delete category |
| GET | `/api/analytics` | Analytics data |

## Setup & Run
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open browser
http://localhost:5000
```

The database is auto-created and seeded with sample data on first run.
