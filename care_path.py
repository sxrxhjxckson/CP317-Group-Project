from flask import Flask, render_template, request, session, redirect, send_file, abort
from DatabaseManager import DatabaseManager
from datetime import date
from werkzeug.utils import secure_filename
from urllib.parse import urlencode
import io
import mimetypes
app = Flask(__name__)

DB_PATH = "care_path_db.db"
dbm = DatabaseManager(DB_PATH)

# Uploaded test-result files are stored directly in the database (as a BLOB)
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB cap per upload


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


#Current user's info
current_user_type = "Patient"
current_user_email = ""
current_user_id = -1

# current_user = "Professional"

#Standard url
@app.route("/")
def login_view():
    return render_template("login.html")

@app.route("/professional/schedule")
def professional_schedule():
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403
    appointments = dbm.get_appointments_by_professional(current_user_id)
    pro_data = dbm.get_professional(current_user_id)
    full_name = f"{pro_data['first_name']} {pro_data['last_name']}"
    return render_template(
        "schedule.html",
        professional_name=full_name,
        appointments=appointments
    )

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



# Patient Medical History Timeline (HIS-001), merges prescriptions, results,
# appointments, and medical records (HIS-002) chronologically.
# Restricted to patients actually assigned to this professional - this was
# previously missing (flagged in Sprint 2 testing: any patient ID in the
# URL would load, regardless of who the professional actually treats).
@app.route("/professional/history")
def patient_history(patient_id=None):
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403
    patients = dbm.get_patients_by_professional(current_user_id)

    patient_search = request.args.get("patient_search", "").strip().lower()
    if patient_search:
        patients = [
            p for p in patients
            if patient_search in p["first_name"].lower() or patient_search in p["last_name"].lower()
        ]

    patient_id = request.args.get("patient_id", type=int)
    history = []

    if patient_id:
        allowed_ids = [p["id"] for p in dbm.get_patients_by_professional(current_user_id)]
        if patient_id not in allowed_ids:
            return "Unauthorized Access: This patient is not assigned to you.", 403
        history = dbm.get_patient_history(patient_id)

    pro_data = dbm.get_professional(current_user_id)
    full_name = f"{pro_data['first_name']} {pro_data['last_name']}"

    return render_template(
        "history.html",
        professional_name=full_name,
        patients=patients,
        patient_search=patient_search,
        history=history,
        patient_id=patient_id,
        selected_patient_id=patient_id,
        record_types=DatabaseManager.MEDICAL_RECORD_TYPES,
        record_error=request.args.get("error"),
    )


# HIS-002 - adds a diagnosis / allergy / procedure / note to a patient's
# medical history. Insert-only: prior entries are never touched. Restricted
# to patients assigned to this professional, same as the history view above.
@app.route("/professional/history/<int:patient_id>/add", methods=["POST"])
def add_medical_record(patient_id):
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403

    allowed_ids = [p["id"] for p in dbm.get_patients_by_professional(current_user_id)]
    if patient_id not in allowed_ids:
        return "Unauthorized Access: This patient is not assigned to you.", 403

    record_type = request.form.get("record_type", "")
    description = request.form.get("description", "").strip()

    if record_type not in DatabaseManager.MEDICAL_RECORD_TYPES:
        return redirect(f"/professional/history?patient_id={patient_id}&error=type")
    if not description:
        return redirect(f"/professional/history?patient_id={patient_id}&error=description")

    record_date = date.today().strftime("%Y-%m-%d")
    dbm.add_medical_record(patient_id, current_user_id, record_type, description, record_date)
    return redirect(f"/professional/history?patient_id={patient_id}")



#Redirection to patient dashboard with error for non patients
@app.route("/patient")
def patient_view():
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403
    pat = dbm.get_patient(current_user_id)
    patient_name = f"{pat['first_name']} {pat['last_name']}"

    contacts = dbm.get_message_contacts_for_patient(current_user_id)
    unread_messages_count = sum(c.get("unread_count", 0) for c in contacts)

    results = dbm.get_test_results_by_patient(current_user_id)
    test_results_count = len(results) if results else 0

    test_results_summary = (
        f"{test_results_count} report{'s' if test_results_count != 1 else ''} available"
        if test_results_count > 0
        else "No recent test results"
    )
    return render_template("patient_dash.html", patient_name=patient_name, unread_messages_count=unread_messages_count, test_results_count=test_results_count, test_results_summary=test_results_summary)


# Patient's Medical Records page (RES-002) - lists their test results,
# plus their medical history entries added by professionals (HIS-002)
@app.route("/patient/records")
def patient_records():
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403
    results = dbm.get_test_results_by_patient(current_user_id)
    medical_records = dbm.get_medical_records_by_patient(current_user_id)
    pat = dbm.get_patient(current_user_id)
    patient_name = f"{pat['first_name']} {pat['last_name']}"
    return render_template("patient_records.html", results=results,
                           medical_records=medical_records,
                           patient_name=patient_name)


# Upload Test Results (RES-002). Accepts a PDF/image, stores it in the database, and records the result against the patient
@app.route("/upload_test_result", methods=["POST"])
def upload_test_result():
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403

    patient_id = request.form.get("patient_id", type=int)
    test_name = request.form.get("test_name")
    comments = request.form.get("comments")
    file = request.files.get("result_file")

    if not patient_id or not test_name or file is None or file.filename == "":
        return redirect("/professional?error=missing")

    allowed_ids = [p["id"] for p in dbm.get_patients_by_professional(current_user_id)]
    if patient_id not in allowed_ids:
        return "Unauthorized Access: This patient is not assigned to you.", 403

    if not allowed_file(file.filename):
        return redirect("/professional?error=format")

    original_name = secure_filename(file.filename)
    file_data = file.read()

    today = date.today().strftime("%d/%m/%Y")
    inserted = dbm.add_test_result(
        patient_id, current_user_id, test_name, today, "Final", comments,
        file_name=original_name, file_data=file_data
    )
    if not inserted:
        return redirect("/professional?error=duplicate")

    return redirect("/professional?uploaded=1")


# VIT-001 - Log Vitals: sane physiological ranges used to reject bad input
# (e.g. negative blood pressure) rather than silently saving garbage data.
VITAL_RANGES = {
    "heart_rate": (20, 300, "Heart rate must be between 20 and 300 bpm."),
    "systolic": (40, 260, "Systolic pressure must be between 40 and 260 mmHg."),
    "diastolic": (20, 200, "Diastolic pressure must be between 20 and 200 mmHg."),
    "temperature": (30, 45, "Temperature must be between 30 and 45 \u00b0C."),
    "oxygen_level": (0, 100, "Oxygen level must be between 0 and 100%."),
    "weight": (1, 500, "Weight must be between 1 and 500 kg."),
}


def _parse_vital_field(form, field, errors):
    """
    Reads one vital field from the submitted form. Blank input is allowed
    (fields are individually optional) and returns None. Non-numeric input
    or a value outside VITAL_RANGES appends a message to `errors` and
    returns None so the bad value never reaches the database.
    """
    raw = form.get(field, "").strip()
    if raw == "":
        return None
    try:
        value = float(raw)
    except ValueError:
        errors.append(f"{field.replace('_', ' ').title()} must be a number.")
        return None

    low, high, message = VITAL_RANGES[field]
    if value < low or value > high:
        errors.append(message)
        return None
    return value


# My Health page (VIT-001) - log form, recent history, and trend summary
@app.route("/patient/health")
def patient_health():
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403
    pat = dbm.get_patient(current_user_id)
    patient_name = f"{pat['first_name']} {pat['last_name']}"
    vitals = dbm.get_vitals_by_patient(current_user_id)
    summary = dbm.get_vitals_summary(current_user_id)
    return render_template(
        "patient_health.html",
        patient_name=patient_name,
        vitals=vitals,
        summary=summary,
        errors=request.args.getlist("error"),
        saved=request.args.get("saved"),
    )


# Handles the "Save Entry" submission on the My Health page (VIT-001)
@app.route("/patient/vitals/add", methods=["POST"])
def add_vital_entry():
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403

    errors = []
    heart_rate = _parse_vital_field(request.form, "heart_rate", errors)
    systolic = _parse_vital_field(request.form, "systolic", errors)
    diastolic = _parse_vital_field(request.form, "diastolic", errors)
    temperature = _parse_vital_field(request.form, "temperature", errors)
    oxygen_level = _parse_vital_field(request.form, "oxygen_level", errors)
    weight = _parse_vital_field(request.form, "weight", errors)
    notes = request.form.get("notes", "").strip() or None

    # An entirely empty submission isn't useful - require at least one value
    if not errors and all(v is None for v in
                           [heart_rate, systolic, diastolic, temperature, oxygen_level, weight]):
        errors.append("Enter at least one vital sign before saving.")

    if errors:
        query = urlencode([("error", e) for e in errors])
        return redirect(f"/patient/health?{query}")

    dbm.add_vital(
        current_user_id,
        heart_rate=int(heart_rate) if heart_rate is not None else None,
        systolic=int(systolic) if systolic is not None else None,
        diastolic=int(diastolic) if diastolic is not None else None,
        temperature=temperature,
        oxygen_level=oxygen_level,
        weight=weight,
        notes=notes,
    )
    return redirect("/patient/health?saved=1")


# COM-001 - Secure Messaging: patient inbox showing every linked professional
@app.route("/patient/messages")
def patient_messages():
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403
    pat = dbm.get_patient(current_user_id)
    patient_name = f"{pat['first_name']} {pat['last_name']}"
    contacts = dbm.get_message_contacts_for_patient(current_user_id)
    return render_template(
        "patient_messages.html",
        patient_name=patient_name,
        contacts=contacts,
        active_contact_id=None,
        active_contact=None,
        messages=[],
        current_user_id=current_user_id
    )


# COM-001 - opens the conversation thread with one specific professional.
# Access is restricted to professionals this patient is actually linked to.
@app.route("/patient/messages/<int:professional_id>")
def patient_message_thread(professional_id):
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403

    contacts = dbm.get_message_contacts_for_patient(current_user_id)
    active_contact = next((c for c in contacts if c['id'] == professional_id), None)
    if active_contact is None:
        return "Unauthorized Access: This professional is not part of your care team.", 403

    dbm.mark_messages_read(current_user_id, professional_id)
    contacts = dbm.get_message_contacts_for_patient(current_user_id)
    active_contact = next((c for c in contacts if c['id'] == professional_id), None)

    pat = dbm.get_patient(current_user_id)
    patient_name = f"{pat['first_name']} {pat['last_name']}"
    messages = dbm.get_conversation(current_user_id, professional_id)
    return render_template(
        "patient_messages.html",
        patient_name=patient_name,
        contacts=contacts,
        active_contact_id=professional_id,
        active_contact=active_contact,
        messages=messages,
        current_user_id=current_user_id,
        current_user_type=current_user_type
    )


# COM-001 - sends a message from the patient to one of their professionals
@app.route("/patient/messages/<int:professional_id>/send", methods=["POST"])
def patient_send_message(professional_id):
    if current_user_type != "Patient":
        return "Error: User is not a Patient", 403

    allowed_ids = [c['id'] for c in dbm.get_message_contacts_for_patient(current_user_id)]
    if professional_id not in allowed_ids:
        return "Unauthorized Access: This professional is not part of your care team.", 403

    text = request.form.get("message_text", "").strip()
    if text:
        dbm.add_message(current_user_id, professional_id, text)
    return redirect(f"/patient/messages/{professional_id}")


# COM-001 - Secure Messaging: professional inbox showing every linked patient
@app.route("/professional/messages")
def professional_messages():
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403
    pro_data = dbm.get_professional(current_user_id)
    full_name = f"{pro_data['first_name']} {pro_data['last_name']}"
    contacts = dbm.get_message_contacts_for_professional(current_user_id)
    return render_template(
        "professional_messages.html",
        professional_name=full_name,
        contacts=contacts,
        active_contact_id=None,
        active_contact=None,
        messages=[],
        current_user_id=current_user_id
    )


# COM-001 - opens the conversation thread with one specific patient.
# Access is restricted to patients actually assigned to this professional.
@app.route("/professional/messages/<int:patient_id>")
def professional_message_thread(patient_id):
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403

    contacts = dbm.get_message_contacts_for_professional(current_user_id)
    active_contact = next((c for c in contacts if c['id'] == patient_id), None)
    if active_contact is None:
        return "Unauthorized Access: This patient is not assigned to you.", 403

    dbm.mark_messages_read(current_user_id, patient_id)
    contacts = dbm.get_message_contacts_for_professional(current_user_id)
    active_contact = next((c for c in contacts if c['id'] == patient_id), None)

    pro_data = dbm.get_professional(current_user_id)
    full_name = f"{pro_data['first_name']} {pro_data['last_name']}"
    messages = dbm.get_conversation(current_user_id, patient_id)
    return render_template(
        "professional_messages.html",
        professional_name=full_name,
        contacts=contacts,
        active_contact_id=patient_id,
        active_contact=active_contact,
        messages=messages,
        current_user_id=current_user_id,
        current_user_type=current_user_type
    )


# COM-001 - sends a message from the professional to one of their patients
@app.route("/professional/messages/<int:patient_id>/send", methods=["POST"])
def professional_send_message(patient_id):
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403

    allowed_ids = [c['id'] for c in dbm.get_message_contacts_for_professional(current_user_id)]
    if patient_id not in allowed_ids:
        return "Unauthorized Access: This patient is not assigned to you.", 403

    text = request.form.get("message_text", "").strip()
    if text:
        dbm.add_message(current_user_id, patient_id, text)
    return redirect(f"/professional/messages/{patient_id}")


# Serves an uploaded test-result file
@app.route("/results/file/<int:test_id>")
def serve_result_file(test_id):
    result = dbm.get_test_result(test_id)
    if not result or not result["file_data"]:
        abort(404)

    is_owner_patient = (current_user_type == "Patient"
                        and current_user_id == result["patient_id"])
    is_owner_professional = (current_user_type == "Professional"
                             and current_user_id == result["professional_id"])
    if not (is_owner_patient or is_owner_professional):
        return "Unauthorized Access", 403

    mimetype = mimetypes.guess_type(result["file_name"])[0] or "application/octet-stream"
    return send_file(
        io.BytesIO(result["file_data"]),
        mimetype=mimetype,
        download_name=result["file_name"]
    )

#Redirection to professional dashboard with error for non patients
@app.route("/professional")
def professional_view():
    if current_user_type != "Professional":
        return "Error: User is not a Professional", 403
    pro_data = dbm.get_professional(current_user_id)
    full_name = f"{pro_data['first_name']} {pro_data['last_name']}"
    patients = dbm.get_patients_by_professional(current_user_id)
    contacts = dbm.get_message_contacts_for_professional(current_user_id)
    unread_count = sum(c.get("unread_count", 0) for c in contacts)
    return render_template("professional_dash.html",
                           professional_name=full_name,
                           patients=patients,
                           upload_status=request.args.get("uploaded"),
                           upload_error=request.args.get("error"),
                           unread_count=unread_count)

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
@app.route("/professional/schedule/update/<int:appt_id>", methods=["POST"])
def update_appointment_status(appt_id):
    if current_user_type != "Professional":
        return "Unauthorized Access", 403

    status = request.form.get("status")

    # Update the appointment's status in the database
    dbm.update_appointment_status(appt_id, status)

    # --- Notification flag ---
    # Find out who this appointment belongs to, then notify the patient
    # that their appointment status changed (approve / cancel / reschedule).
    parties = dbm.get_appointment_parties(appt_id)
    if parties:
        notice = f"Your appointment status has been updated to: {status}"
        dbm.add_message(current_user_id, parties['patient_id'], notice)

    return redirect("/professional/schedule")

# Reschedule an appointment (APT-002) - updates the date and time
@app.route("/professional/schedule/reschedule/<int:appt_id>", methods=["POST"])
def reschedule_appointment(appt_id):
    if current_user_type != "Professional":
        return "Unauthorized Access", 403

    new_date = request.form.get("new_date")
    new_time = request.form.get("new_time")

    # Reuses the existing update method (date, time, status, appt_id)
    dbm.update_appointement(new_date, new_time, "Confirmed", appt_id)

    return redirect("/professional/schedule")

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

    details = dbm.get_prescription_details(prescrpt_id)
    patient_id = details['patient_id'] if details else ""
    #Redirect to dashboard
    return redirect(f"/professional/prescriptions?patient_id={patient_id}&action=list")

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
    #can use either
    #   localhost:port_num
    #   127.0.0.1:port_num
