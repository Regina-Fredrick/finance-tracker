
import os
from dotenv import load_dotenv
load_dotenv()  # only loads .env locally, ignored on Render
import mysql.connector
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from AI import generate_insights

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "finance_tracker"),
        port=int(os.getenv("DB_PORT", 3306))
    )
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def index():
    return send_from_directory(".", "login.html")

@app.route("/app")
def frontend():
    return send_from_directory(".", "index.html")

@app.route("/dashboard_bg.jpeg")
def bg_image():
    return send_from_directory(".", "dashboard_bg.jpeg")
@app.route("/login.jpeg")
def login_bg_image():
    return send_from_directory(".", "login.jpeg")
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
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT user_id, full_name, email FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify(user)
    return jsonify({"error": "User not found"}), 404

@app.route("/users/update/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if data.get("password"):
            cursor.execute(
                "UPDATE users SET full_name=%s, email=%s, password=%s WHERE user_id=%s",
                (data["full_name"], data["email"], data["password"], user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET full_name=%s, email=%s WHERE user_id=%s",
                (data["full_name"], data["email"], user_id)
            )
        conn.commit()
        return jsonify({"message": "Profile updated successfully"}), 200
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
            "INSERT INTO income (user_id, source, amount, income_date, is_recurring) VALUES (%s, %s, %s, %s, %s)",
            (data["user_id"], data["source"], data["amount"], data["income_date"], data.get("is_recurring", False))
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
@app.route("/income/delete/<int:income_id>", methods=["DELETE"])
def delete_income(income_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM income WHERE income_id = %s", (income_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Income deleted"}), 200
@app.route("/income/update/<int:income_id>", methods=["PUT"])
def update_income(income_id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE income SET source=%s, amount=%s, income_date=%s WHERE income_id=%s",
        (data["source"], data["amount"], data["income_date"], income_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Income updated"}), 200

@app.route("/expenses", methods=["POST"])
def add_expense():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO expenses (user_id, category, amount, expense_date, description, is_recurring) VALUES (%s, %s, %s, %s, %s, %s)",
            (data["user_id"], data["category"], data["amount"], data["expense_date"], data["description"], data.get("is_recurring", False))
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
@app.route("/expenses/delete/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE expense_id = %s", (expense_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Expense deleted"}), 200
@app.route("/expenses/update/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET category=%s, amount=%s, expense_date=%s, description=%s WHERE expense_id=%s",
        (data["category"], data["amount"], data["expense_date"], data["description"], expense_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Expense updated"}), 200

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
def process_recurring(user_id, month):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT DISTINCT source, amount FROM income WHERE user_id=%s AND is_recurring=1",
        (user_id,)
    )
    for r in cursor.fetchall():
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM income WHERE user_id=%s AND source=%s AND is_recurring=1 AND DATE_FORMAT(income_date, '%%Y-%%m')=%s",
            (user_id, r["source"], month)
        )
        if cursor.fetchone()["cnt"] == 0:
            cursor.execute(
                "INSERT INTO income (user_id, source, amount, income_date, is_recurring) VALUES (%s, %s, %s, %s, 1)",
                (user_id, r["source"], r["amount"], f"{month}-01")
            )

    cursor.execute(
        "SELECT DISTINCT category, amount, description FROM expenses WHERE user_id=%s AND is_recurring=1",
        (user_id,)
    )
    for r in cursor.fetchall():
        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM expenses WHERE user_id=%s AND category=%s AND is_recurring=1 AND DATE_FORMAT(expense_date, '%%Y-%%m')=%s",
            (user_id, r["category"], month)
        )
        if cursor.fetchone()["cnt"] == 0:
            cursor.execute(
                "INSERT INTO expenses (user_id, category, amount, expense_date, description, is_recurring) VALUES (%s, %s, %s, %s, %s, 1)",
                (user_id, r["category"], r["amount"], f"{month}-01", r["description"])
            )

    conn.commit()
    conn.close()
@app.route("/dashboard/<int:user_id>", methods=["GET"])
def dashboard(user_id):
    month = request.args.get("month", "2025-06")
    process_recurring(user_id, month)  
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
@app.route("/goals/<int:user_id>", methods=["GET"])
def get_goals(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM savings_goals WHERE user_id = %s", (user_id,))
    goals = cursor.fetchall()
    conn.close()
    return jsonify(goals)

@app.route("/goals", methods=["POST"])
def add_goal():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO savings_goals (user_id, goal_name, target_amount, saved_amount, deadline) VALUES (%s, %s, %s, %s, %s)",
            (data["user_id"], data["goal_name"], data["target_amount"], data.get("saved_amount", 0), data["deadline"])
        )
        conn.commit()
        return jsonify({"message": "Goal added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route("/goals/update/<int:goal_id>", methods=["PUT"])
def update_goal(goal_id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE savings_goals SET saved_amount=%s WHERE goal_id=%s",
            (data["saved_amount"], goal_id)
        )
        conn.commit()
        return jsonify({"message": "Goal updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route("/goals/delete/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM savings_goals WHERE goal_id = %s", (goal_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Goal deleted"}), 200
@app.route("/insights/<int:user_id>", methods=["GET"])
def get_insights(user_id):
    month = request.args.get("month", "2025-06")
    insights = generate_insights(user_id, month)
    return jsonify(insights)
# Add account
@app.route("/accounts", methods=["POST"])
def add_account():
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO accounts (user_id, account_name, account_type, balance) VALUES (%s, %s, %s, %s)",
            (data["user_id"], data["account_name"], data["account_type"], data["balance"])
        )
        conn.commit()
        return jsonify({"message": "Account added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# Get all accounts for a user
@app.route("/accounts/<int:user_id>", methods=["GET"])
def get_accounts(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM accounts WHERE user_id = %s", (user_id,))
    accounts = cursor.fetchall()
    conn.close()
    total = sum(float(a["balance"]) for a in accounts)
    return jsonify({"accounts": accounts, "total_balance": total})

# Update account balance
@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    data = request.get_json()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE accounts SET balance = %s WHERE account_id = %s",
            (data["balance"], account_id)
        )
        conn.commit()
        return jsonify({"message": "Account updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

# Delete account
@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM accounts WHERE account_id = %s", (account_id,))
        conn.commit()
        return jsonify({"message": "Account deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)