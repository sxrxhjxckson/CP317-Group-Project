import sqlite3
from cryptography.fernet import Fernet

# COM-001 - Secure Messaging: symmetric key used to encrypt Message_Text at
# rest, so raw message content is never stored as plain text in the .db file.
# NOTE: in a real deployment this key would come from an environment
# variable / secrets manager rather than being committed to source control.
# It's a fixed constant here so every team member's local copy can
# encrypt/decrypt the same MESSAGES data for this course project.
_MESSAGE_ENCRYPTION_KEY = b"E1zwtShmdRssNVWWo8gKva0BVV1YfdbbjnnN85ltCoM="
_fernet = Fernet(_MESSAGE_ENCRYPTION_KEY)

class DatabaseManager():
    '''
    Initializes the database manager by:
        - Saving the path to the db
        - Calling the create tables method to initialize tables if needed
    Each method should create its own connection to the database due to Flask threading
    '''
    def __init__(self, path):
        self.path = path
        self.create_tables()

    '''
    Creates the necessary tables for the app if they dont already exist:
        - USERS: basic user info like: email, password, account type
        - PATIENTS: patient's name, insurance details
        - PROFESSIONALS: profesional's name, license
        - MEDICATIONS: all medication and their description, dosage amount
        - PRESCRIPTIONS: prescriptions and their patient, medication, dates 
        - TEST RESULTS: test name, professional, patient, notes, date
        - APPOINTEMENTS: datetime, professional, patient, notes, date
        - MESSAGES: record of sender, receiver, message, datetime
        - VITALS: recorded vitals of patients
    '''
    def create_tables(self):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS USERS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Email TEXT NOT NULL,
            Password TEXT NOT NULL,
            Account_Type TEXT NOT NULL,
            UNIQUE (Email)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PATIENTS (
            Patient_Id INTEGER PRIMARY KEY,
            First_Name TEXT NOT NULL,
            Last_Name TEXT NOT NULL,
            DOB DATE NOT NULL, 
            Health_Card_Num INTEGER NOT NULL UNIQUE,
            Insurance_Num INTEGER NOT NULL,
            FOREIGN KEY (Patient_Id) REFERENCES USERS(ID) ON DELETE CASCADE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PROFESSIONALS (
            Professional_Id INTEGER PRIMARY KEY,
            First_Name TEXT NOT NULL,
            Last_Name TEXT NOT NULL,
            Med_License_Num INTEGER NOT NULL,
            UNIQUE (Med_License_Num),
            FOREIGN KEY (Professional_Id) REFERENCES USERS(ID) ON DELETE CASCADE
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS MEDICATIONS (
            Medication_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Medication_Name TEXT NOT NULL UNIQUE,
            Medication_Description TEXT,
            Recommended_Dosage TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS PRESCRIPTIONS (
            Prescription_Id INTEGER PRIMARY KEY AUTOINCREMENT, 
            Patient_Id INTEGER NOT NULL,
            Professional_Id INTEGER NOT NULL,
            Medication_Id INTEGER NOT NULL,
            Dosage TEXT NOT NULL,
            Prescription_Date DATE NOT NULL, 
            Expiration_Date DATE NOT NULL,
            Remaining_Refills INTEGER DEFAULT 0,
            FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(Patient_Id),
            FOREIGN KEY (Professional_Id) REFERENCES PROFESSIONALS(Professional_Id),
            FOREIGN KEY (Medication_Id) REFERENCES MEDICATIONS(Medication_Id),
            UNIQUE (Patient_Id, Medication_Id, Prescription_Date)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS TEST_RESULTS (
            Test_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Patient_Id INTEGER NOT NULL,
            Professional_Id INTEGER NOT NULL,
            Test_Name TEXT,
            Date_Conducted DATE NOT NULL,
            Test_Status TEXT NOT NULL,
            Doctor_Comments TEXT,
            File_Name TEXT,
            File_Data BLOB,
            FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(Patient_Id),
            FOREIGN KEY (Professional_Id) REFERENCES PROFESSIONALS(Professional_Id),
            UNIQUE (Patient_Id, Professional_Id, Test_Name, Date_Conducted)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS APPOINTMENTS (
            Appointment_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Patient_Id INTEGER NOT NULL,
            Professional_Id INTEGER NOT NULL,
            Sched_Date DATE NOT NULL,
            Sched_Time TIME NOT NULL,
            Appvl_Status TEXT NOT NULL,
            Notes TEXT, 
            FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(Patient_Id),
            FOREIGN KEY (Professional_Id) REFERENCES PROFESSIONALS(Professional_Id),
            UNIQUE (Patient_Id, Professional_Id, Sched_Date, Sched_Time)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS MESSAGES (
            Message_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Sender_Id INTEGER NOT NULL,
            Receiver_Id INTEGER NOT NULL,
            Sent_Time DATETIME DEFAULT CURRENT_TIMESTAMP,
            Message_Text TEXT NOT NULL,
            Is_Read INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (Sender_Id) REFERENCES USERS(ID),
            FOREIGN KEY (Receiver_Id) REFERENCES USERS(ID),
            UNIQUE (Sender_Id, Receiver_Id, Sent_Time)
        )
        """)
        # Defensive migration - see _ensure_columns note by the VITALS table.
        self._ensure_columns(cursor, "MESSAGES", {
            "Is_Read": "INTEGER NOT NULL DEFAULT 0",
        })
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS VITALS (
            Vitals_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Patient_Id INTEGER NOT NULL,
            Record_Date DATETIME DEFAULT CURRENT_TIMESTAMP,
            Heart_Rate INTEGER,
            Systolic INTEGER,
            Diastolic INTEGER,
            Temperature REAL,
            Oxygen_Level REAL,
            Weight REAL,
            Notes TEXT,
            FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(Patient_Id),
            UNIQUE (Patient_Id, Record_Date)
        )
        """)
        # Defensive migration: CREATE TABLE IF NOT EXISTS is a no-op if an
        # older VITALS table is already sitting in this .db file (e.g. from
        # before Sprint 3). Without this, inserting Systolic/Diastolic/
        # Oxygen_Level/Weight would crash the same way the old TEST_RESULTS
        # table did when File_Name/File_Data were added.
        self._ensure_columns(cursor, "VITALS", {
            "Systolic": "INTEGER",
            "Diastolic": "INTEGER",
            "Oxygen_Level": "REAL",
            "Weight": "REAL",
        })
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS MEDICAL_RECORDS (
            Record_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Patient_Id INTEGER NOT NULL,
            Professional_Id INTEGER NOT NULL,
            Record_Type TEXT NOT NULL,
            Description TEXT NOT NULL,
            Record_Date DATE NOT NULL,
            Created_At DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(Patient_Id),
            FOREIGN KEY (Professional_Id) REFERENCES PROFESSIONALS(Professional_Id)
        )
        """)
        conn.commit()
        conn.close()

    '''
    Defensive schema-migration helper.
    Looks at which columns already exist on `table` and ALTERs in any
    from `columns` (a dict of {column_name: sql_type}) that are missing.
    This is what prevents "table X has no column named Y" errors when a
    teammate's local .db file was created before a column was added.
    '''
    def _ensure_columns(self, cursor, table, columns):
        cursor.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cursor.fetchall()}
        for col_name, col_type in columns.items():
            if col_name not in existing:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")

    #==================================================
    #----------DATA INSERTION METHODS------------------
    #==================================================

    '''
    Adds a user to the database, ignores if their email exists already
    '''
    def add_user(self, email, password, user_type):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        new_id = None
        try:
            cursor.execute("""
            INSERT OR IGNORE INTO USERS (Email, Password, Account_Type)
            VALUES (?,?,?)
            """, (email,password,user_type))
            conn.commit()
            new_id = cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"User already exists or insertion failed: {e}")
            conn.rollback()
        finally:
            conn.close()
        return new_id

    def add_patient(self, pat_id,fname, lname, dob, hcnum, inum):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO PATIENTS (Patient_Id, First_Name, Last_Name, DOB,
                            Health_Card_Num, Insurance_Num)
        VALUES (?,?,?,?,?,?)
        """, (pat_id,fname,lname,dob,hcnum,inum))

        conn.commit()
        conn.close()

    def add_professional(self, prof_id, fname, lname, license):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO PROFESSIONALS (Professional_Id, First_Name, Last_Name, Med_License_Num)
        VALUES (?,?,?,?)
        """, (prof_id, fname,lname,license))

        conn.commit()
        conn.close()

    def add_medication(self, name, desc, dosage):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO MEDICATIONS (Medication_Name,
                            Medication_Description, Recommended_Dosage)
        VALUES (?,?,?)
        """, (name,desc,dosage))

        conn.commit()
        conn.close()

    def get_or_create_medication_id(self, name):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("SELECT Medication_Id FROM MEDICATIONS WHERE Medication_Name = ?", (name,))
        row = cursor.fetchone()
        if row:
            med_id = row[0]
        else:
            cursor.execute("""
            INSERT INTO MEDICATIONS (Medication_Name, Medication_Description, Recommended_Dosage)
                           VALUES (?, 'Prescribed via dashboard', 'As specified by script')
                           """, (name,))
            conn.commit()
            med_id = cursor.lastrowid
        conn.close()
        return med_id
    
    def add_prescription(self, pat_id, prof_id, med_id, dosage, pdate, edate, ref):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO PRESCRIPTIONS (Patient_Id, Professional_Id, Medication_Id,
                            Dosage, Prescription_Date, Expiration_Date, Remaining_Refills)
        VALUES (?,?,?,?,?,?,?)
        """, (pat_id, prof_id, med_id, dosage, pdate, edate, ref))

        conn.commit()
        conn.close()

    def add_test_result(self, pat_id, prof_id, name, date, status, comments,
                        file_name=None, file_data=None):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        #Status should be 'Pending' or 'Final'
        cursor.execute("""
        INSERT OR IGNORE INTO TEST_RESULTS (Patient_Id, Professional_Id, Test_Name,
                            Date_Conducted,Test_Status, Doctor_Comments, File_Name, File_Data)
        VALUES (?,?,?,?,?,?,?,?)
        """, (pat_id, prof_id, name, date, status, comments, file_name,
              sqlite3.Binary(file_data) if file_data is not None else None))

        inserted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return inserted

    def add_appointement(self, pat_id, prof_id, date, time, status, notes):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        #Status should be 'Requested' or 'Confirmed' or 'Cancelled'
        cursor.execute("""
        INSERT OR IGNORE INTO APPOINTMENTS (Patient_Id, Professional_Id, Sched_Date, Sched_Time,
                            Appvl_Status,Notes)
        VALUES (?,?,?,?,?,?)
        """, (pat_id, prof_id, date, time, status, notes))

        conn.commit()
        conn.close()

    '''
    Sends a message between two users (COM-001).
    Message_Text is encrypted before it touches the database, so a raw
    read of the .db file never exposes conversation content.
    sent_time defaults to now if not supplied (previously this was passed
    in as None from update_appointment_status, which silently stored NULL).
    '''
    def add_message(self, sender_id, receiver_id, text, sent_time=None):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        encrypted_text = _fernet.encrypt(text.encode()).decode()

        if sent_time:
            cursor.execute("""
            INSERT OR IGNORE INTO MESSAGES (Sender_Id, Receiver_Id, Sent_Time, Message_Text)
            VALUES (?,?,?,?)
            """, (sender_id, receiver_id, sent_time, encrypted_text))
        else:
            cursor.execute("""
            INSERT OR IGNORE INTO MESSAGES (Sender_Id, Receiver_Id, Message_Text)
            VALUES (?,?,?)
            """, (sender_id, receiver_id, encrypted_text))

        conn.commit()
        conn.close()

    '''
    Adds a vitals entry for a patient (VIT-001).
    All vital sign fields are optional individually (a patient might only
    log heart rate one day, and blood pressure the next) but the route
    calling this should ensure at least one was actually provided.
    record_date defaults to now if not supplied.
    '''
    def add_vital(self, patient_id, heart_rate=None, systolic=None, diastolic=None,
                  temperature=None, oxygen_level=None, weight=None, notes=None,
                  record_date=None):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        if record_date:
            cursor.execute("""
            INSERT OR IGNORE INTO VITALS (Patient_Id, Record_Date, Heart_Rate,
                                Systolic, Diastolic, Temperature, Oxygen_Level, Weight, Notes)
            VALUES (?,?,?,?,?,?,?,?,?)
            """, (patient_id, record_date, heart_rate, systolic, diastolic,
                  temperature, oxygen_level, weight, notes))
        else:
            cursor.execute("""
            INSERT OR IGNORE INTO VITALS (Patient_Id, Heart_Rate,
                                Systolic, Diastolic, Temperature, Oxygen_Level, Weight, Notes)
            VALUES (?,?,?,?,?,?,?,?)
            """, (patient_id, heart_rate, systolic, diastolic,
                  temperature, oxygen_level, weight, notes))

        inserted = cursor.rowcount
        conn.commit()
        conn.close()
        return inserted

    #==================================================
    #----------DATA RETRIEVAL METHODS-------------------
    #==================================================

    '''
    Gets the users type based on their login to confirm if they're a 
    patient, a professional, or if they dont't have an account

    returns string: either 'Professional' or 'Patient or 'Invalid''
    '''
    def get_user_type(self, email, password):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT ID, Account_Type FROM USERS WHERE Email = ? AND Password = ?
        """, (email,password))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0], result[1]
        else:
            return None, 'Invalid'
        
    def get_professional(self, professional_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        SELECT First_Name, Last_Name FROM PROFESSIONALS 
        WHERE Professional_Id = ?
        """, (professional_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'first_name': result[0],
                'last_name': result[1]
            }
        else:
            return {
                'first_name': 'Unknown',
                'last_name': 'Professional'
            }
    def get_patients_by_professional(self, professional_id, search_query=None):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        if search_query:
            cursor.execute("""
            SELECT DISTINCT p.Patient_Id, p.First_Name, p.Last_Name, p.Health_Card_Num, p.Insurance_Num
                        FROM PATIENTS p
                        WHERE (p.Patient_Id IN (
                            SELECT Patient_Id FROM PRESCRIPTIONS WHERE Professional_Id = ?
                            UNION
                            SELECT Patient_Id FROM APPOINTMENTS WHERE Professional_Id = ?
                            UNION
                            SELECT Patient_Id FROM TEST_RESULTS WHERE Professional_Id = ?
                        )) AND (p.First_Name LIKE ? OR P.Last_Name LIKE ?)
                           """, (professional_id, professional_id, professional_id, f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("""
            SELECT DISTINCT p.Patient_Id, p.First_Name, p.Last_Name, p.Health_Card_Num, p.Insurance_Num
                        FROM PATIENTS p
                        WHERE p.Patient_Id IN (
                        SELECT Patient_Id FROM PRESCRIPTIONS WHERE Professional_Id = ?
                        UNION
                        SELECT Patient_Id FROM APPOINTMENTS WHERE Professional_Id = ?
                        UNION
                        SELECT Patient_Id FROM TEST_RESULTS WHERE Professional_Id = ?
                        )""", (professional_id, professional_id, professional_id))
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'first_name': r[1], 'last_name': r[2], 'health_card': r[3], 'insurance_num': r[4]} for r in rows]
    
    # Inverse of get_patients_by_professional - the professionals a given
    # patient is linked to (via a shared prescription, appointment, or test
    # result). Used to restrict who a patient is allowed to message (COM-001).
    def get_professionals_by_patient(self, patient_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT DISTINCT pr.Professional_Id, pr.First_Name, pr.Last_Name
        FROM PROFESSIONALS pr
        WHERE pr.Professional_Id IN (
            SELECT Professional_Id FROM PRESCRIPTIONS WHERE Patient_Id = ?
            UNION
            SELECT Professional_Id FROM APPOINTMENTS WHERE Patient_Id = ?
            UNION
            SELECT Professional_Id FROM TEST_RESULTS WHERE Patient_Id = ?
        )
        """, (patient_id, patient_id, patient_id))
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'first_name': r[1], 'last_name': r[2]} for r in rows]

    def get_all_patients(self):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("SELECT Patient_Id, First_Name, Last_Name, Health_Card_Num FROM PATIENTS")
        rows = cursor.fetchall()
        conn.close()
        return[{'id': r[0], 'first_name': r[1], 'last_name': r[2], 'health_card': r[3]} for r in rows]

    def get_patient_prescriptions(self, patient_id, search_query=None):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        if search_query:
            cursor.execute("""
                    SELECT p.Prescription_Id, m.Medication_Name, p.Prescription_Date, p.Dosage
                    FROM PRESCRIPTIONS p
                    JOIN MEDICATIONS m ON p.Medication_Id = m.Medication_Id
                    WHERE p.Patient_Id = ? AND m.Medication_Name LIKE ?
            """, (patient_id, f"%{search_query}%"))
        else:
            cursor.execute("""
                        SELECT p.Prescription_Id, m.Medication_Name, p.Prescription_Date, p.Dosage
                        FROM PRESCRIPTIONS p
                        JOIN MEDICATIONS m ON p.Medication_Id = m.Medication_Id
                        WHERE p.Patient_Id = ?
            """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{
            'id': r[0], 'med_name': r[1], 'date': r[2], 'dosage': r[3]
        } for r in rows]
    
    def get_appointments_by_professional(self, professional_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
                SELECT a.Appointment_Id, p.First_Name, p.Last_Name,
                a.Sched_Date, a.Sched_Time, a.Appvl_Status, a.Notes
                FROM APPOINTMENTS a
                JOIN PATIENTS p ON a.Patient_Id = p.Patient_Id
                WHERE a.Professional_Id = ?
                ORDER BY a.Sched_Date, a.Sched_Time
                """, (professional_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{
            'id': r[0], 'first_name': r[1], 'last_name': r[2],
            'date': r[3], 'time': r[4], 'status': r[5], 'notes': r[6]
        } for r in rows]
    
    def get_all_medications(self):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("SELECT Medication_Id, Medication_Name, Medication_Description FROM MEDICATIONS")
        rows = cursor.fetchall()
        conn.close()
        return [{'id': r[0], 'name': r[1], 'desc': r[2]} for r in rows]

    def get_prescription_details(self, prescription_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
                    SELECT 
                       p.Prescription_Id, 
                       m.Medication_Name, 
                       p.Dosage, 
                       p.Prescription_Date, 
                       p.Expiration_Date, 
                       p.Remaining_Refills, 
                       p.Patient_Id
                    FROM PRESCRIPTIONS p
                    JOIN MEDICATIONS m ON p.Medication_Id = m.Medication_Id
                    WHERE p.Prescription_Id = ?
        """, (prescription_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0], 
                'med_name': row[1], 
                'dosage': row[2], 
                'date': row[3], 
                'expr_date': row[4], 
                'refills': row[5], 
                'patient_id': row[6]
            }
        return None
    
    # HIS-002 - the set of record types a professional can add. Enforced
    # server-side (in care_path.py) so arbitrary text can't be used here.
    MEDICAL_RECORD_TYPES = ("Diagnosis", "Allergy", "Procedure", "Note")

    '''
    Adds a new medical history entry for a patient (HIS-002) - a diagnosis,
    allergy, procedure, or free-text note from a professional.
    This is insert-only by design: there is no corresponding update/delete
    method, so a patient's existing history can never be overwritten, only
    added to. Professional_Id + Created_At double as the audit trail,
    since every entry always records who added it and when.
    '''
    def add_medical_record(self, patient_id, professional_id, record_type, description, record_date):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO MEDICAL_RECORDS (Patient_Id, Professional_Id, Record_Type, Description, Record_Date)
        VALUES (?,?,?,?,?)
        """, (patient_id, professional_id, record_type, description, record_date))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id

    # Gets a patient's diagnoses/allergies/procedures/notes, most recent
    # first, including which professional added each entry (HIS-002).
    def get_medical_records_by_patient(self, patient_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.Record_Id, m.Record_Type, m.Description, m.Record_Date,
                   m.Created_At, pr.First_Name, pr.Last_Name
            FROM MEDICAL_RECORDS m
            LEFT JOIN PROFESSIONALS pr ON m.Professional_Id = pr.Professional_Id
            WHERE m.Patient_Id = ?
            ORDER BY m.Record_Date DESC, m.Record_Id DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{
            'id': r[0], 'type': r[1], 'description': r[2], 'date': r[3],
            'created_at': r[4],
            'provider': f"Dr. {r[5]} {r[6]}" if r[5] else "—"
        } for r in rows]

    def get_patient_history(self, patient_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        # Prescriptions
        cursor.execute("""
            SELECT p.Prescription_Date, m.Medication_Name, p.Dosage
            FROM PRESCRIPTIONS p
            JOIN MEDICATIONS m ON p.Medication_Id = m.Medication_Id
            WHERE p.Patient_Id = ?
        """, (patient_id,))
        prescriptions = [{
            'date': r[0], 'type': 'Prescription',
            'detail': f"{r[1]} ({r[2]})"
        } for r in cursor.fetchall()]

        # Test results
        cursor.execute("""
            SELECT Date_Conducted, Test_Name, Test_Status
            FROM TEST_RESULTS
            WHERE Patient_Id = ?
        """, (patient_id,))
        results = [{
            'date': r[0], 'type': 'Test Result',
            'detail': f"{r[1]} - {r[2]}"
        } for r in cursor.fetchall()]

        # Appointments
        cursor.execute("""
            SELECT Sched_Date, Appvl_Status, Notes
            FROM APPOINTMENTS
            WHERE Patient_Id = ?
        """, (patient_id,))
        appointments = [{
            'date': r[0], 'type': 'Appointment',
            'detail': f"{r[1]} - {r[2]}"
        } for r in cursor.fetchall()]

        # Medical records (HIS-002: diagnoses, allergies, procedures, notes)
        cursor.execute("""
            SELECT m.Record_Date, m.Record_Type, m.Description, pr.First_Name, pr.Last_Name
            FROM MEDICAL_RECORDS m
            LEFT JOIN PROFESSIONALS pr ON m.Professional_Id = pr.Professional_Id
            WHERE m.Patient_Id = ?
        """, (patient_id,))
        medical_records = [{
            'date': r[0], 'type': r[1],
            'detail': f"{r[2]} (Dr. {r[3]} {r[4]})" if r[3] else r[2]
        } for r in cursor.fetchall()]

        conn.close()

        # Merge all four, sort by date (newest first)
        history = prescriptions + results + appointments + medical_records
        history.sort(key=lambda x: x['date'], reverse=True)
        return history
    
    # Gets the patient and professional tied to a specific appointment.
    # Used for notifications - we need to know WHO to notify when an
    # appointment's status changes (approve / cancel / reschedule).
    def get_appointment_parties(self, appt_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Patient_Id, Professional_Id
            FROM APPOINTMENTS
            WHERE Appointment_Id = ?
        """, (appt_id,))
        row = cursor.fetchone()
        conn.close()
        # Return as a dict, or None if no appointment found
        if row:
            return {'patient_id': row[0], 'professional_id': row[1]}
        return None

    # Gets a single test result
    def get_test_result(self, test_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Test_Id, Patient_Id, Professional_Id, Test_Name,
                   Date_Conducted, Test_Status, Doctor_Comments, File_Name, File_Data
            FROM TEST_RESULTS
            WHERE Test_Id = ?
        """, (test_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'test_id': row[0], 'patient_id': row[1], 'professional_id': row[2],
                'test_name': row[3], 'date': row[4], 'status': row[5],
                'comments': row[6], 'file_name': row[7], 'file_data': row[8]
            }
        return None

    # Gets a single patient's name, for display on their dashboard.
    def get_patient(self, patient_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT First_Name, Last_Name FROM PATIENTS WHERE Patient_Id = ?
        """, (patient_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'first_name': row[0], 'last_name': row[1]}
        return {'first_name': 'Unknown', 'last_name': 'Patient'}

    # Gets all test results for a patient, newest first, and the provider of the test.
    def get_test_results_by_patient(self, patient_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.Test_Id, t.Test_Name, t.Date_Conducted, t.Test_Status,
                   t.Doctor_Comments, t.File_Name, pr.First_Name, pr.Last_Name
            FROM TEST_RESULTS t
            LEFT JOIN PROFESSIONALS pr ON t.Professional_Id = pr.Professional_Id
            WHERE t.Patient_Id = ?
            ORDER BY t.Date_Conducted DESC
        """, (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            provider = f"Dr. {r[6]} {r[7]}" if r[6] else "—"
            results.append({
                'test_id': r[0], 'test_name': r[1], 'date': r[2],
                'status': r[3], 'comments': r[4], 'file_name': r[5],
                'provider': provider
            })
        return results

    # Gets a patient's logged vitals, most recent first (VIT-001).
    def get_vitals_by_patient(self, patient_id, limit=None):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        query = """
            SELECT Vitals_Id, Record_Date, Heart_Rate, Systolic, Diastolic,
                   Temperature, Oxygen_Level, Weight, Notes
            FROM VITALS
            WHERE Patient_Id = ?
            ORDER BY Record_Date DESC
        """
        if limit:
            query += " LIMIT ?"
            cursor.execute(query, (patient_id, limit))
        else:
            cursor.execute(query, (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{
            'id': r[0], 'date': r[1], 'heart_rate': r[2],
            'systolic': r[3], 'diastolic': r[4], 'temperature': r[5],
            'oxygen_level': r[6], 'weight': r[7], 'notes': r[8]
        } for r in rows]

    # Simple aggregate stats for the "Trends" panel on the My Health page:
    # average heart rate, average blood pressure, and total entries logged.
    def get_vitals_summary(self, patient_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT AVG(Heart_Rate), AVG(Systolic), AVG(Diastolic), COUNT(*)
            FROM VITALS
            WHERE Patient_Id = ?
        """, (patient_id,))
        row = cursor.fetchone()
        conn.close()
        avg_hr, avg_sys, avg_dia, count = row
        return {
            'avg_heart_rate': round(avg_hr) if avg_hr is not None else None,
            'avg_blood_pressure': (f"{round(avg_sys)}/{round(avg_dia)}"
                                    if avg_sys is not None and avg_dia is not None else None),
            'entries_logged': count
        }

    # Returns every message between two specific users, oldest first,
    # decrypting Message_Text on the way out (COM-001).
    def get_conversation(self, user_a_id, user_b_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Message_Id, Sender_Id, Receiver_Id, Sent_Time, Message_Text
            FROM MESSAGES
            WHERE (Sender_Id = ? AND Receiver_Id = ?)
               OR (Sender_Id = ? AND Receiver_Id = ?)
            ORDER BY Sent_Time ASC, Message_Id ASC
        """, (user_a_id, user_b_id, user_b_id, user_a_id))
        rows = cursor.fetchall()
        conn.close()
        messages = []
        for r in rows:
            try:
                text = _fernet.decrypt(r[4].encode()).decode()
            except Exception:
                text = "[Unable to decrypt message]"
            messages.append({
                'id': r[0], 'sender_id': r[1], 'receiver_id': r[2],
                'sent_time': r[3], 'text': text
            })
        return messages

    # Marks all messages sent TO receiver_id FROM sender_id as read.
    # Called when a conversation thread is opened (COM-001).
    def mark_messages_read(self, receiver_id, sender_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE MESSAGES SET Is_Read = 1
            WHERE Sender_Id = ? AND Receiver_Id = ? AND Is_Read = 0
        """, (sender_id, receiver_id))
        conn.commit()
        conn.close()

    # Builds the patient's message inbox: every linked professional, plus
    # a decrypted preview of the most recent message and an unread count,
    # for the contact list on the Messages page (COM-001).
    def get_message_contacts_for_patient(self, patient_id):
        professionals = self.get_professionals_by_patient(patient_id)
        return self._build_message_contacts(patient_id, professionals)

    # Same as above, for a professional's list of linked patients (COM-001).
    def get_message_contacts_for_professional(self, professional_id):
        patients = self.get_patients_by_professional(professional_id)
        return self._build_message_contacts(professional_id, patients)

    # Shared helper behind the two contact-list methods above.
    def _build_message_contacts(self, current_id, other_users):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        contacts = []
        for user in other_users:
            other_id = user['id']
            cursor.execute("""
                SELECT Message_Text, Sent_Time
                FROM MESSAGES
                WHERE (Sender_Id = ? AND Receiver_Id = ?)
                   OR (Sender_Id = ? AND Receiver_Id = ?)
                ORDER BY Sent_Time DESC, Message_Id DESC
                LIMIT 1
            """, (current_id, other_id, other_id, current_id))
            last = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) FROM MESSAGES
                WHERE Sender_Id = ? AND Receiver_Id = ? AND Is_Read = 0
            """, (other_id, current_id))
            unread_count = cursor.fetchone()[0]

            last_message, last_time = None, None
            if last:
                last_time = last[1]
                try:
                    last_message = _fernet.decrypt(last[0].encode()).decode()
                except Exception:
                    last_message = "[Unable to decrypt message]"

            contacts.append({
                'id': other_id,
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'last_message': last_message,
                'last_time': last_time,
                'unread_count': unread_count
            })
        conn.close()
        # Most recently active conversations first, contacts with no
        # messages yet fall to the bottom.
        contacts.sort(key=lambda c: c['last_time'] or '', reverse=True)
        return contacts

    #==================================================
    #----------DATA UPDATE METHODS------------------
    #==================================================

    def update_user(self, user_id, email, password):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE USERS
        SET Email = ?, Password = ?
        WHERE ID = ?
        """, (email,password,user_id))

        conn.commit()
        conn.close()

    def update_patient(self,fname, lname, hcnum, inum, pat_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE PATIENTS
        SET First_Name = ?, Last_Name = ?, Health_Card_Num = ?, Insurance_Num = ?
        WHERE Patient_Id = ?
        """, (fname,lname,hcnum,inum, pat_id))

        conn.commit()
        conn.close()

    def update_professional(self, prof_id, fname, lname, license):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE PROFESSIONALS
        SET First_Name = ?, Last_Name = ?, Med_License_Num = ?
        WHERE Professional_Id = ?
        """, (fname,lname,license, prof_id))

        conn.commit()
        conn.close()

    def update_medication(self, med_id, name, desc, dosage):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE MEDICATIONS
        SET Medication_Name = ?, Medication_Description = ?, Recommended_Dosage = ?
        WHERE Medication_Id = ?
        """, (name,desc,dosage,med_id))

        conn.commit()
        conn.close()

    def update_prescription(self, prescrpt_id, dosage, edate, ref):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE PRESCRIPTIONS
        SET Dosage = ?, Expiration_Date = ?, Remaining_Refills = ?
        WHERE Prescription_Id = ?
        """, (dosage, edate, ref, prescrpt_id))

        conn.commit()
        conn.close()

    def update_test_result(self, test_id, status, comments):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        #Status should be 'Pending' or 'Final'
        cursor.execute("""
        UPDATE TEST_RESULTS
        SET Test_Status = ?, Doctor_Comments = ?
        WHERE Test_Id = ?
        """, (status, comments, test_id))

        conn.commit()
        conn.close()

    def update_appointement(self, date, time, status, appt_id):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        #Status should be 'Requested' or 'Confirmed' or 'Cancelled'
        cursor.execute("""
        UPDATE APPOINTMENTS 
        SET Sched_Date = ?, Sched_Time = ?, Appvl_Status = ?
        WHERE Appointment_Id = ?
        """, (date, time, status, appt_id))

        conn.commit()
        conn.close()
    def update_appointment_status(self, appt_id, status):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE APPOINTMENTS
        SET Appvl_Status = ?
        WHERE Appointment_Id = ?
        """, (status, appt_id))
        conn.commit()
        conn.close()
