from flask import Flask, render_template, request, session, redirect
from DatabaseManager import DatabaseManager

app = Flask(__name__)

DB_PATH = "care_path_db.db"
dbm = DatabaseManager(DB_PATH)


# Current user's info
current_user_type = "Patient"
current_user_email = ""
current_user_id = -1

# current_user = "Professional"


# Standard url
@app.route("/")
def login_view():
    return render_template("login.html")


# Login POST functionality
@app.route("/login", methods=["POST"])
def login():
    global current_user_type

    # Reads from form
    email = request.form["email"]
    password = request.form["password"]

    print(f"Email: {email}, Password:{password}")

    # Check db for valid user
    retrieved_type = dbm.get_user_type(email, password)

    if retrieved_type == "Patient":
        current_user_type = "Patient"
        return redirect("/patient")
    elif retrieved_type == "Professional":
        current_user_type = "Professional"
        return redirect("/professional")
    else:
        # Later the login page can show invalid user
        return render_template("login.html")


# Redirection to patient dashboard with error for non patients
@app.route("/patient")
def patient_view():
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403
    return render_template("patient_dash.html")


# Redirection to professional dashboard with error for non professionals
@app.route("/professional")
def professional_view():
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403
    return render_template("professional_dash.html")


# Patient monitoring dashboard added by Abia
patients = [
    {
        "name": "Aisha Khan",
        "age": 67,
        "condition": "High Blood Pressure",
        "heart_rate": 92,
        "status": "Needs Review"
    },
    {
        "name": "Omar Ahmed",
        "age": 54,
        "condition": "Diabetes",
        "heart_rate": 78,
        "status": "Stable"
    },
    {
        "name": "Sarah Lee",
        "age": 72,
        "condition": "Post-Surgery Recovery",
        "heart_rate": 105,
        "status": "Alert"
    }
]


@app.route("/abia-dashboard")
def abia_dashboard():
    return render_template("abia_dashboard.html", patients=patients)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
    # Can use either:
    #   localhost:port_num
    #   127.0.0.1:port_num