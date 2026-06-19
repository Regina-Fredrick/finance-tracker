import mysql.connector
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "finance_tracker"),
        port=int(os.getenv("DB_PORT", 3306))
    )

def generate_insights(user_id, month="2025-06"):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    insights = []

    cursor.execute(
        "SELECT category, COALESCE(SUM(amount), 0) AS spent FROM expenses WHERE user_id = %s AND DATE_FORMAT(expense_date, '%%Y-%%m') = %s GROUP BY category",
        (user_id, month)
    )
    current = {row["category"]: float(row["spent"]) for row in cursor.fetchall()}

    current_date = datetime.strptime(month, "%Y-%m")
    first_day = current_date.replace(day=1)
    last_month = (first_day - timedelta(days=1)).strftime("%Y-%m")

    cursor.execute(
        "SELECT category, COALESCE(SUM(amount), 0) AS spent FROM expenses WHERE user_id = %s AND DATE_FORMAT(expense_date, '%%Y-%%m') = %s GROUP BY category",
        (user_id, last_month)
    )
    previous = {row["category"]: float(row["spent"]) for row in cursor.fetchall()}

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM income WHERE user_id = %s AND DATE_FORMAT(income_date, '%%Y-%%m') = %s",
        (user_id, month)
    )
    total_income = float(cursor.fetchone()["total"])

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = %s AND DATE_FORMAT(expense_date, '%%Y-%%m') = %s",
        (user_id, month)
    )
    total_expenses = float(cursor.fetchone()["total"])

    cursor.execute(
        "SELECT * FROM budgets WHERE user_id = %s AND month_year = %s",
        (user_id, month)
    )
    budgets = {row["category"]: float(row["budget_amount"]) for row in cursor.fetchall()}

    for category, limit in budgets.items():
        spent = current.get(category, 0)
        percent = (spent / limit) * 100 if limit > 0 else 0
        if percent >= 100:
            insights.append({"type": "danger", "message": f"You have exceeded your {category} budget. Spent KES {spent:,.0f} of KES {limit:,.0f}."})
        elif percent >= 90:
            insights.append({"type": "warning", "message": f"You have used {percent:.0f}% of your {category} budget. Only KES {limit - spent:,.0f} remaining."})

    for category, spent in current.items():
        prev_spent = previous.get(category, 0)
        if prev_spent > 0:
            change = ((spent - prev_spent) / prev_spent) * 100
            if change >= 30:
                insights.append({"type": "alert", "message": f"Your {category} spending increased by {change:.0f}% compared to last month."})

    if total_income > 0:
        savings_rate = ((total_income - total_expenses) / total_income) * 100
        if savings_rate < 20:
            insights.append({"type": "advice", "message": f"Your savings rate is {savings_rate:.1f}%. Try to save at least 20% of your income."})
        elif savings_rate >= 30:
            insights.append({"type": "positive", "message": f"Great job! Your savings rate is {savings_rate:.1f}%. Consider investing the surplus."})

    cursor.execute(
        "SELECT DATE_FORMAT(expense_date, '%%Y-%%m') AS month, SUM(amount) AS total FROM expenses WHERE user_id = %s GROUP BY month ORDER BY month DESC LIMIT 3",
        (user_id,)
    )
    history = [float(row["total"]) for row in cursor.fetchall()]
    if len(history) >= 2:
        predicted = sum(history) / len(history)
        insights.append({"type": "prediction", "message": f"Based on your recent spending, estimated expenses next month: KES {predicted:,.0f}."})

    conn.close()
    return insights