
from dotenv import load_dotenv
import os
from dotenv import load_dotenv
load_dotenv()
import mysql.connector
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from AI import generate_insights

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def index():
    return send_from_directory(".", "login.html")

@app.route("/app")
def frontend():
    return send_from_directory(".", "index.html")

@app.route("/logout")
def logout():
    return '''<script>localStorage.removeItem("user_id");localStorage.removeItem("user_name");window.location.href="/";</script>'''

@app.route("/test-db")
def test_db():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        conn.close()
        return jsonify({"status": "Connected!", "tables": tables})
    except Exception as e:
        return jsonify({"status": "Failed", "error": str(e)}), 500

@app.route("/users/register", methods=["POST"])
def register():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (full_name, email, password) VALUES (%s, %s, %s)",
            (data["full_name"], data["email"], data["password"])
        )
        conn.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route("/users/login", methods=["POST"])
def login():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE email = %s AND password = %s",
        (data["email"], data["password"])
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"message": "Login successful", "user_id": user["user_id"], "name": user["full_name"]})
    return jsonify({"error": "Invalid email or password"}), 401

@app.route("/income", methods=["POST"])
def add_income():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO income (user_id, source, amount, income_date) VALUES (%s, %s, %s, %s)",
            (data["user_id"], data["source"], data["amount"], data["income_date"])
        )
        conn.commit()
        return jsonify({"message": "Income added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route("/income/<int:user_id>", methods=["GET"])
def get_income(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM income WHERE user_id = %s", (user_id,))
    income = cursor.fetchall()
    conn.close()
    return jsonify(income)

@app.route("/expenses", methods=["POST"])
def add_expense():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO expenses (user_id, category, amount, expense_date, description) VALUES (%s, %s, %s, %s, %s)",
            (data["user_id"], data["category"], data["amount"], data["expense_date"], data["description"])
        )
        conn.commit()
        return jsonify({"message": "Expense added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route("/expenses/<int:user_id>", methods=["GET"])
def get_expenses(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM expenses WHERE user_id = %s", (user_id,))
    expenses = cursor.fetchall()
    conn.close()
    return jsonify(expenses)

@app.route("/budgets", methods=["POST"])
def add_budget():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO budgets (user_id, category, budget_amount, month_year) VALUES (%s, %s, %s, %s)",
            (data["user_id"], data["category"], data["budget_amount"], data["month_year"])
        )
        conn.commit()
        return jsonify({"message": "Budget added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route("/budgets/<int:user_id>", methods=["GET"])
def get_budgets(user_id):
    month = request.args.get("month", "2025-06")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM budgets WHERE user_id = %s AND month_year = %s",
        (user_id, month)
    )
    budgets = cursor.fetchall()
    conn.close()
    return jsonify(budgets)

@app.route("/dashboard/<int:user_id>", methods=["GET"])
def dashboard(user_id):
    month = request.args.get("month", "2025-06")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total_income FROM income WHERE user_id = %s AND DATE_FORMAT(income_date, '%Y-%m') = %s",
        (user_id, month)
    )
    total_income = float(cursor.fetchone()["total_income"])

    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total_expenses FROM expenses WHERE user_id = %s AND DATE_FORMAT(expense_date, '%Y-%m') = %s",
        (user_id, month)
    )
    total_expenses = float(cursor.fetchone()["total_expenses"])

    cursor.execute(
        "SELECT category, COALESCE(SUM(amount), 0) AS spent FROM expenses WHERE user_id = %s AND DATE_FORMAT(expense_date, '%Y-%m') = %s GROUP BY category",
        (user_id, month)
    )
    by_category = cursor.fetchall()

    cursor.execute(
        "SELECT * FROM budgets WHERE user_id = %s AND month_year = %s",
        (user_id, month)
    )
    budgets = cursor.fetchall()
    budget_status = []
    for b in budgets:
        spent = next((float(c["spent"]) for c in by_category if c["category"] == b["category"]), 0)
        budget_status.append({
            "category": b["category"],
            "budget": float(b["budget_amount"]),
            "spent": spent,
            "remaining": float(b["budget_amount"]) - spent,
            "percent_used": round((spent / float(b["budget_amount"])) * 100, 1) if float(b["budget_amount"]) > 0 else 0
        })

    conn.close()
    return jsonify({
        "month": month,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "savings": total_income - total_expenses,
        "savings_rate": round(((total_income - total_expenses) / total_income) * 100, 1) if total_income > 0 else 0,
        "expenses_by_category": [{"category": c["category"], "spent": float(c["spent"])} for c in by_category],
        "budget_status": budget_status
    })

@app.route("/insights/<int:user_id>", methods=["GET"])
def get_insights(user_id):
    month = request.args.get("month", "2025-06")
    insights = generate_insights(user_id, month)
    return jsonify(insights)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)