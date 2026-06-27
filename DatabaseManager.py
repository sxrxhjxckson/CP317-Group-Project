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

        cursor.execute("""
        INSERT OR IGNORE INTO USERS (Email, Password, Account_Type)
        VALUES (?,?,?)
        """, (email,password,user_type))

        conn.commit()
        conn.close()

    def add_patient(self,fname, lname, dob, hcnum, inum):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO PATIENTS (First_Name, Last_Name, DOB,
                            Health_Card_Num, Insurance_Num)
        VALUES (?,?,?,?,?)
        """, (fname,lname,dob,hcnum,inum))

        conn.commit()
        conn.close()

    def add_professional(self, fname, lname, license):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR IGNORE INTO PROFESSIONALS (First_Name, Last_Name, Med_License_Num)
        VALUES (?,?,?)
        """, (fname,lname,license))

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
        
        account_type = 'Invalid'
        cursor.execute("""
        SELECT Account_Type FROM USERS WHERE Email = ? AND Password = ?
        """, (email,password))
        result = cursor.fetchone()
        conn.close()
        if result:
            account_type = result[0]
            return account_type
        else:
            return account_type