DROP DATABASE IF EXISTS care_path_db;
CREATE DATABASE care_path_db;
USE care_path_db;

-- Create Tables
CREATE TABLE IF NOT EXISTS USERS (
	ID INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(255) NOT NULL,
    User_Password VARCHAR(255) NOT NULL, -- Hash password later
    Account_Type ENUM('Patient', 'Healthcare Professional') NOT NULL,
    UNIQUE (Email)
);

CREATE TABLE IF NOT EXISTS PATIENTS (
	Patient_Id INT PRIMARY KEY,
    First_Name VARCHAR(255) NOT NULL,
	Last_Name VARCHAR(255) NOT NULL,
    DOB DATE NOT NULL, 
    Health_Card_Num INT NOT NULL,
    Insurance_Num INT NOT NULL, 
    UNIQUE (Health_Card_Num),
    FOREIGN KEY (Patient_Id) REFERENCES USERS(ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS PROFESSIONALS (
	Professional_Id INT PRIMARY KEY,
    First_Name VARCHAR(255) NOT NULL,
	Last_Name VARCHAR(255) NOT NULL,
    Med_License_Num INT NOT NULL,
    UNIQUE (Med_License_Num),
    FOREIGN KEY (Professional_Id) REFERENCES USERS(ID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS MEDICATIONS (
    Medication_Id INT PRIMARY KEY AUTO_INCREMENT,
    Medication_Name VARCHAR(255) NOT NULL,
    Medication_Description VARCHAR(500),
    Recommended_Dosage INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS PRESCRIPTIONS (
	Prescription_Id INT PRIMARY KEY AUTO_INCREMENT, 
	Patient_Id INT NOT NULL,
	Professional_Id INT NOT NULL,
    Medication_Id INT NOT NULL,
    Dosage VARCHAR(255) NOT NULL,
    Date_Prescribed DATE NOT NULL, 
    Expiration_Date DATE NOT NULL,
    Remaining_Refills INT DEFAULT 0,
    FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(Patient_Id),
    FOREIGN KEY (Professional_Id) REFERENCES PROFESSIONALS(Professional_Id),
    FOREIGN KEY (Medication_Id) REFERENCES MEDICATIONS(Medication_Id)
);

CREATE TABLE IF NOT EXISTS TEST_RESULTS (
	Test_Id INT PRIMARY KEY AUTO_INCREMENT,
    Patient_Id INT NOT NULL,
	Professional_Id INT NOT NULL,
    Test_Name VARCHAR(255),
    Date_Conducted DATE NOT NULL,
    Test_Status ENUM('Pending', 'Final') NOT NULL,
    Doctor_Comments VARCHAR(255),
    FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(Patient_Id),
    FOREIGN KEY (Professional_Id) REFERENCES PROFESSIONALS(Professional_Id),
);

CREATE TABLE IF NOT EXISTS APPOINTMENTS (
	Appointment_Id INT AUTO_INCREMENT,
    Patient_Id INT NOT NULL,
	Professional_Id INT NOT NULL,
    Sched_Date DATE NOT NULL,
    Sched_Time TIME NOT NULL,
    Appvl_Status ENUM('Requested', 'Confirmed', 'Cancelled'),
    Notes VARCHAR(255), 
	FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(Patient_Id),
    FOREIGN KEY (Professional_Id) REFERENCES PROFESSIONALS(Professional_Id),
    PRIMARY KEY (Appointment_Id, Patient_Id, Professional_Id)
);

CREATE TABLE IF NOT EXISTS MESSAGES (
    Message_Id INT PRIMARY KEY AUTO_INCREMENT,
    Sender_Id INT NOT NULL,
    Receiver_Id INT NOT NULL,
    Sent_Time DATETIME DEFAULT CURRENT_TIMESTAMP,
    Message_Text VARCHAR(500) NOT NULL,
    FOREIGN KEY (Sender_Id) REFERENCES USERS(ID),
    FOREIGN KEY (Receiver_Id) REFERENCES USERS(ID)
);

CREATE TABLE IF NOT EXISTS VITALS (
    Vitals_Id Int PRIMARY KEY AUTO_INCREMENT,
    Patient_Id INT NOT NULL,
    Record_Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    Heart_Rate INT,
    Blood_Pressure VARCHAR(10),
    Temperature DECIMAL(3,1),
    Notes VARCHAR(255),
    FOREIGN KEY (Patient_Id) REFERENCES PATIENTS(ID)
);

-- STILL NEED TO ADD FOR VITALS LOG, AND MESSAGES
-- Mock Data