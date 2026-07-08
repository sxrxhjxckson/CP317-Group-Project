from flask import Flask, render_template, request, session, redirect
from DatabaseManager import DatabaseManager
from datetime import date
app = Flask(__name__)

DB_PATH = "care_path_db.db"
dbm = DatabaseManager(DB_PATH)


#Current user's info
current_user_type = "Patient"
current_user_email = ""
current_user_id = -1

# current_user = "Professional"

#Standard url
@app.route("/")
def login_view():
    return render_template("login.html")

#Login POST functionality
@app.route("/login", methods=["POST"])
def login():
    global current_user_type, current_user_id

    #Reads from form
    email = request.form["email"]
    password = request.form["password"]

    print(f"Email: {email}, Password:{password}")
    
    #Check db for valid user
    user_id, retrieved_type = dbm.get_user_type(email,password)
    print(f"DB Output -> ID: {user_id} | Type: {retrieved_type} (Type: {type(retrieved_type)})")
    if retrieved_type == "Patient":
        current_user_type = "Patient"
        current_user_id = user_id
        return redirect("/patient")
    elif retrieved_type == "Professional":
        current_user_type = "Professional"
        current_user_id = user_id
        return redirect("/professional")
    else:
        # later the login page can show invalid user
        return render_template("login.html")



#Redirection to patient dashboard with error for non patients
@app.route("/patient")
def patient_view():
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403
    return render_template("patient_dash.html")

#Redirection to professional dashboard with error for non patients
@app.route("/professional")
def professional_view():
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403
    pro_data = dbm.get_professional(current_user_id)
    full_name = f"{pro_data['first_name']} {pro_data['last_name']}"
    return render_template("professional_dash.html", professional_name=full_name)

@app.route("/professional/prescriptions", methods=['GET', 'POST'])
def professional_prescriptions():
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403
    if request.method == 'POST':
        presc_id = request.form.get('prescription_id')
        dosage = request.form.get('dosage')
        expr_date = request.form.get('expiration_date')
        refills = request.form.get('refills')
        patient_id = request.form.get('patient_id')
        
        dbm.update_prescription(presc_id, dosage, expr_date, refills)
        return redirect(f'/professional/prescriptions?patient_id={patient_id}&prescription_id={presc_id}')
    selected_patient_id = request.args.get('patient_id', type=int)
    selected_presc_id = request.args.get('prescription_id', type=int)
    
    patients = dbm.get_patients_by_professional(current_user_id)
    prescriptions = []
    presc_details = None

    if selected_patient_id:
        allowed_ids = [p['id'] for p in patients]
        if selected_patient_id not in allowed_ids:
            return "Unauthorized Access: This patient is not assigned to you.", 403
        prescriptions = dbm.get_patient_prescriptions(selected_patient_id)
    
    if selected_presc_id:
        presc_details = dbm.get_prescription_details(selected_presc_id)
    pro_data = dbm.get_professional(current_user_id)
    full_name = f"{pro_data['first_name']} {pro_data['last_name']}"
    return render_template(
        'prof_prescriptions.html',
        professional_name=full_name,
        patients=patients,
        prescriptions=prescriptions,
        presc_details=presc_details,
        selected_patient_id=selected_patient_id,
        selected_presc_id=selected_presc_id
    )

@app.route("/professional/prescriptions/add", methods=["GET", "POST"])
def process_add_prescriptions():
    if current_user_type != "Professional":
        return "Unauthorized Access", 403
    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        medication_id = request.form.get("medication_id")
        dosage = request.form.get("dosage")
        expr_date = request.form.get("expiration_date")
        refills = request.form.get("refills")
        current_date = date.today().strftime("%d/%m/%Y")

        dbm.add_prescription(
            patient_id, 
            current_user_id, 
            medication_id, 
            dosage, 
            current_date,
            expr_date,
            refills
            )

        return redirect(f"/professional/prescriptions?patient_id={patient_id}")
    selected_patient_id = request.args.get('patient_id', type=int)
    patients = dbm.get_patients_by_professional(current_user_id)
    medications = dbm.get_all_medications()
    prescriptions = []
    if selected_patient_id:
        allowed_ids = [p['id'] for p in patients]
        if selected_patient_id not in allowed_ids:
            return "Unauthorized Access: This patient is not assigned to you.", 403
        prescriptions = dbm.get_patient_prescriptions(selected_patient_id)
    pro_data = dbm.get_professional(current_user_id)
    full_name = f"{pro_data['first_name']} {pro_data['last_name']}"
    return render_template(
        'prof_prescriptions.html',
        professional_name=full_name,
        patients=patients,
        medications=medications,
        prescriptions=prescriptions,
        presc_details=None,
        selected_patient_id=selected_patient_id,
        selected_presc_id=None,
        show_add_form=True
    )

#Update Prescription
@app.route("/update_prescription/<int:prescrpt_id>", methods=["POST"])
def handle_update_prescription(prescrpt_id):
    #Security Check
    if current_user_type != "Professional":
        return "Unauthorized Access", 403
    
    #Extract Form Values
    dosage = request.form.get("dosage")
    expiration_date = request.form.get("expiration_date")
    remaining_refills = request.form.get("remaining_refills")

    #Call Method from DatabaseManager.py
    dbm.update_prescription(prescrpt_id, dosage, expiration_date, remaining_refills)

    #Redirect to dashboard
    return redirect("/professional/prescriptions?patient_id={patient_id}&action=list")

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
    #can use either
    #   localhost:port_num
    #   127.0.0.1:port_num
