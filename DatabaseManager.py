import sqlite3

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
            FOREIGN KEY (Sender_Id) REFERENCES USERS(ID),
            FOREIGN KEY (Receiver_Id) REFERENCES USERS(ID),
            UNIQUE (Sender_Id, Receiver_Id, Sent_Time)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS VITALS (
            Vitals_Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Patient_Id INTEGER NOT NULL,
            Record_Date DATETIME DEFAULT CURRENT_TIMESTAMP,
            Heart_Rate INTEGER,
            Blood_Pressure TEXT,
            Temperature REAL,
            Notes TEXT,
            FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(ID),
            UNIQUE (Patient_Id, Record_Date)
        )
        """)
        conn.commit()
        conn.close()

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
        cursor.execute("SELECT Medication_Id FROM mEDICATIONS WHERE Medication_Name = ?", (name,))
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

    def add_test_result(self, pat_id, prof_id, name, date, status, comments):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        #Status should be 'Pending' or 'Final'
        cursor.execute("""
        INSERT OR IGNORE INTO TEST_RESULTS (Patient_Id, Professional_Id, Test_Name,
                            Date_Conducted,Test_Status, Doctor_Comments)
        VALUES (?,?,?,?,?,?)
        """, (pat_id, prof_id, name, date, status, comments))

        conn.commit()
        conn.close()

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

    def add_message(self, s_id, r_id, time, text):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO MESSAGES (Sender_Id, Receiver_Id, Sent_Time, Message_Text)
        VALUES (?,?,?,?)
        """, (s_id, r_id, time, text))

        conn.commit()
        conn.close()

    def add_vital(self, p_id, date, hr, bp, temp, notes):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO VITALS (Patient_Id, Record_Date, Heart_Rate, Blood_Pressure, Temperature, Notes)
        VALUES (?,?,?,?,?,?)
        """, (p_id, date, hr, bp, temp, notes))

        conn.commit()
        conn.close()

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

        conn.close()

        # Merge all three, sort by date (newest first)
        history = prescriptions + results + appointments
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