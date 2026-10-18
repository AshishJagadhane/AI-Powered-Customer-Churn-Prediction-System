
import os
from functools import wraps
from pathlib import Path

import joblib
import pandas as pd
import psycopg2

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash


# -------------------- PATHS AND MODEL --------------------

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

model = joblib.load(MODEL_DIR / "random_forest_churn_model.pkl")
preprocessor = joblib.load(MODEL_DIR / "preprocessor.pkl")

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "ashish010203"
)


# -------------------- DATABASE CONNECTION --------------------

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        database=os.environ.get("DB_NAME", "customer_churn_db"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "root"),
        port=os.environ.get("DB_PORT", "5432")
    )


# -------------------- INITIALIZE USERS TABLE --------------------

def init_users_table():
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL
                        CHECK (role IN ('customer', 'admin')),
                    customer_id VARCHAR(20) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            admin_username = os.environ.get("ADMIN_USERNAME", "admin")
            admin_email = os.environ.get(
                "ADMIN_EMAIL", "admin@ashish.com"
            )

            # FIX: Read the password from the correct environment variable.
            admin_password = os.environ.get(
                "ADMIN_PASSWORD", "ashish010203"
            )

            cur.execute("""
                SELECT 1
                FROM users
                WHERE username = %s OR email = %s
            """, (admin_username, admin_email))

            if cur.fetchone() is None:
                cur.execute("""
                    INSERT INTO users
                        (username, email, password_hash, role)
                    VALUES (%s, %s, %s, 'admin')
                """, (
                    admin_username,
                    admin_email,
                    generate_password_hash(admin_password)
                ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# -------------------- LOGIN PROTECTION --------------------

def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))

            if role and session.get("role") != role:
                flash("You do not have permission to access that page.")
                return redirect(url_for("home"))

            return view(*args, **kwargs)

        return wrapped

    return decorator


# -------------------- HOME --------------------

@app.route("/")
def home():
    return render_template("index.html")


# -------------------- CUSTOMER REGISTRATION --------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        customer_id = request.form.get("customer_id", "").strip()

        if not all([username, email, password, customer_id]):
            flash("Please complete every field.")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.")
            return redirect(url_for("register"))

        conn = get_db_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 1
                    FROM customer_churn
                    WHERE customer_id = %s
                """, (customer_id,))

                if cur.fetchone() is None:
                    flash("Customer ID not found. Please check your ID.")
                    return redirect(url_for("register"))

                cur.execute("""
                    SELECT 1
                    FROM users
                    WHERE customer_id = %s
                """, (customer_id,))

                if cur.fetchone():
                    flash("An account already exists for this customer ID.")
                    return redirect(url_for("register"))

                cur.execute("""
                    INSERT INTO users
                        (username, email, password_hash, role, customer_id)
                    VALUES (%s, %s, %s, 'customer', %s)
                """, (
                    username,
                    email,
                    generate_password_hash(password),
                    customer_id
                ))

            conn.commit()

        except psycopg2.IntegrityError:
            conn.rollback()
            flash("That username, email, or customer ID is already registered.")
            return redirect(url_for("register"))

        finally:
            conn.close()

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


# -------------------- LOGIN --------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, username, password_hash, role, customer_id
                    FROM users
                    WHERE username = %s
                """, (username,))

                user = cur.fetchone()

        finally:
            conn.close()

        if user and check_password_hash(user[2], password):
            session.clear()
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[3]
            session["customer_id"] = user[4]

            if user[3] == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("customer_dashboard"))

        flash("Invalid username or password.", "danger")
        return render_template("login.html")

    return render_template("login.html")


# -------------------- CUSTOMER DASHBOARD --------------------

@app.route("/customer")
@login_required(role="customer")
def customer_dashboard():
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT customer_id, contract_type, tenure_months,
                       monthly_charges, satisfaction_score,
                       churn_probability, risk_level, retention_action
                FROM customer_churn
                WHERE customer_id = %s
            """, (session.get("customer_id"),))

            customer = cur.fetchone()

    finally:
        conn.close()

    if not customer:
        return "Customer record not found.", 404

    return render_template("customer_dashboard.html", customer=customer)


# -------------------- ADMIN DASHBOARD --------------------

@app.route("/admin")
@login_required(role="admin")
def admin_dashboard():
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*),
                    COUNT(*) FILTER (WHERE churn = 1),
                    COUNT(*) FILTER (WHERE risk_level = 'High Risk'),
                    COALESCE(AVG(churn_probability), 0)
                FROM customer_churn
            """)
            metrics = cur.fetchone()

            cur.execute("""
                SELECT customer_id, contract_type, churn_probability,
                       risk_level, retention_action
                FROM customer_churn
                ORDER BY churn_probability DESC
                LIMIT 20
            """)
            high_risk_customers = cur.fetchall()

            cur.execute("""
                SELECT
                    COUNT(*),
                    COUNT(*) FILTER (WHERE risk_level = 'High Risk'),
                    COUNT(*) FILTER (WHERE risk_level = 'Medium Risk'),
                    COUNT(*) FILTER (WHERE risk_level = 'Low Risk'),
                    COALESCE(AVG(churn_probability), 0),
                    COALESCE(
                        SUM(monthly_charges)
                        FILTER (WHERE risk_level = 'High Risk'),
                        0
                    )
                FROM prediction_history
            """)
            stats = cur.fetchone()

    finally:
        conn.close()

    total_predictions = stats[0]
    high_predictions = stats[1]
    medium_predictions = stats[2]
    low_predictions = stats[3]

    prediction_metrics = {
        "total": total_predictions,
        "high": high_predictions,
        "medium": medium_predictions,
        "low": low_predictions,
        "average_probability": float(stats[4]),
        "revenue_at_risk": float(stats[5])
    }

    if total_predictions:
        risk_widths = {
            "high": round(high_predictions / total_predictions * 100, 1),
            "medium": round(medium_predictions / total_predictions * 100, 1),
            "low": round(low_predictions / total_predictions * 100, 1)
        }
    else:
        risk_widths = {"high": 0, "medium": 0, "low": 0}

    return render_template(
        "admin_dashboard.html",
        metrics=metrics,
        customers=high_risk_customers,
        prediction_metrics=prediction_metrics,
        risk_widths=risk_widths
    )


# -------------------- CHURN PREDICTION --------------------

@app.route("/predict", methods=["GET", "POST"])
@login_required(role="admin")
def predict_churn():
    result = None
    error = None

    if request.method == "POST":
        try:
            gender = request.form["gender"]
            age = int(request.form["age"])
            tenure = int(request.form["tenure_months"])
            contract = request.form["contract_type"]
            monthly_charges = float(request.form["monthly_charges"])
            payment = request.form["payment_method"]
            internet = request.form["internet_service"]
            tickets = int(request.form["support_tickets"])
            complaints = int(request.form["complaints"])
            usage = float(request.form["avg_monthly_usage_gb"])
            logins = int(request.form["login_frequency"])
            discount = float(request.form["discount_percent"])
            satisfaction = int(request.form["satisfaction_score"])
            late_payments = int(request.form["late_payments"])
            total_charges = float(request.form["total_charges"])

            if not 18 <= age <= 100:
                raise ValueError("Age must be between 18 and 100.")

            if not 1 <= tenure <= 72:
                raise ValueError("Tenure must be between 1 and 72 months.")

            if not 0 <= discount <= 100:
                raise ValueError("Discount must be between 0 and 100.")

            if not 1 <= logins <= 30:
                raise ValueError("Login frequency must be between 1 and 30.")

            if not 1 <= satisfaction <= 10:
                raise ValueError("Satisfaction score must be between 1 and 10.")

            if min(
                monthly_charges, usage, total_charges,
                tickets, complaints, late_payments
            ) < 0:
                raise ValueError(
                    "Charges, usage and counts cannot be negative."
                )

            monthly_spend = monthly_charges * (1 - discount / 100)
            support_burden = tickets + complaints
            payment_risk = late_payments + complaints

            if tenure <= 12:
                tenure_group = "0-12 months"
            elif tenure <= 24:
                tenure_group = "13-24 months"
            elif tenure <= 48:
                tenure_group = "25-48 months"
            else:
                tenure_group = "49-72 months"

            if logins <= 10:
                engagement_level = "Low"
            elif logins <= 20:
                engagement_level = "Medium"
            else:
                engagement_level = "High"

            if satisfaction <= 3:
                satisfaction_level = "Low"
            elif satisfaction <= 7:
                satisfaction_level = "Medium"
            else:
                satisfaction_level = "High"

            input_data = pd.DataFrame([{
                "gender": gender,
                "age": age,
                "tenure_months": tenure,
                "contract_type": contract,
                "monthly_charges": monthly_charges,
                "payment_method": payment,
                "internet_service": internet,
                "support_tickets": tickets,
                "complaints": complaints,
                "avg_monthly_usage_gb": usage,
                "login_frequency": logins,
                "discount_percent": discount,
                "satisfaction_score": satisfaction,
                "late_payments": late_payments,
                "total_charges": total_charges,
                "tenure_group": tenure_group,
                "monthly_spend_after_discount": monthly_spend,
                "support_burden": support_burden,
                "payment_risk": payment_risk,
                "engagement_level": engagement_level,
                "satisfaction_level": satisfaction_level
            }])

            transformed_data = preprocessor.transform(input_data)

            # Find the probability for churn class 1.
            probabilities = model.predict_proba(transformed_data)[0]
            classes = list(model.classes_)
            positive_indices = [
                i for i, label in enumerate(classes)
                if str(label) == "1"
            ]

            if not positive_indices:
                raise ValueError(
                    "The trained model does not contain churn class 1."
                )

            probability = float(probabilities[positive_indices[0]])
            probability_percent = round(probability * 100, 2)

            if probability >= 0.70:
                risk = "High Risk"
                action = (
                    "Review customer concerns and offer a "
                    "personalized retention plan."
                )
            elif probability >= 0.40:
                risk = "Medium Risk"
                action = (
                    "Follow up with the customer and improve engagement."
                )
            else:
                risk = "Low Risk"
                action = "Continue regular customer engagement."

            conn = get_db_connection()

            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO prediction_history (
                            user_id, gender, age, tenure_months,
                            contract_type, monthly_charges,
                            payment_method, internet_service,
                            support_tickets, complaints,
                            avg_monthly_usage_gb, login_frequency,
                            discount_percent, satisfaction_score,
                            late_payments, total_charges,
                            churn_probability, risk_level, retention_action
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s
                        )
                    """, (
                        session["user_id"], gender, age, tenure,
                        contract, monthly_charges, payment, internet,
                        tickets, complaints, usage, logins,
                        discount, satisfaction, late_payments,
                        total_charges, probability_percent, risk, action
                    ))

                conn.commit()

            except Exception:
                conn.rollback()
                raise

            finally:
                conn.close()

            result = {
                "probability": probability_percent,
                "risk": risk,
                "action": action
            }

        except (ValueError, TypeError, KeyError) as exc:
            error = str(exc)

        except Exception:
            app.logger.exception("Churn prediction failed")
            error = (
                "Prediction or database saving failed. "
                "Check the Flask terminal for details."
            )

    return render_template("predict.html", result=result, error=error)


# -------------------- PREDICTION HISTORY --------------------

@app.route("/prediction-history")
@login_required(role="admin")
def prediction_history():
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT prediction_id, user_id, age, contract_type,
                       monthly_charges, churn_probability, risk_level,
                       retention_action, predicted_at
                FROM prediction_history
                ORDER BY predicted_at DESC
            """)
            rows = cur.fetchall()

    finally:
        conn.close()

    return render_template(
        "prediction_history.html",
        predictions=rows
    )


# -------------------- LOGOUT --------------------

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))


# -------------------- RUN APPLICATION --------------------

if __name__ == "__main__":
    init_users_table()
    app.run(debug=True)