DROP DATABASE IF EXISTS care_path_db;
CREATE DATABASE care_path_db;
USE care_path_db;

-- Create Tables
CREATE TABLE USERS (
	ID INT AUTO_INCREMENT PRIMARY KEY,
    Email VARCHAR(255) NOT NULL,
    User_Password VARCHAR(255) NOT NULL, -- Hash password later
    Account_Type ENUM('Patient', 'Healthcare Professional') NOT NULL,
    UNIQUE (Email)
);

CREATE TABLE PATIENTS (
	Patient_Id INT PRIMARY KEY,
    First_Name VARCHAR(255) NOT NULL,
	Last_Name VARCHAR(255) NOT NULL,
    DOB DATE NOT NULL, 
    Health_Card_Num INT NOT NULL,
    Insurance_Num INT NOT NULL, 
    UNIQUE (Health_Card_Num),
    FOREIGN KEY (Patient_Id) REFERENCES USERS(ID) ON DELETE CASCADE
);

CREATE TABLE PROFESSIONALS (
	Professional_Id INT PRIMARY KEY,
    First_Name VARCHAR(255) NOT NULL,
	Last_Name VARCHAR(255) NOT NULL,
    Med_License_Num INT NOT NULL,
    UNIQUE (Med_License_Num),
    FOREIGN KEY (Professional_Id) REFERENCES USERS(ID) ON DELETE CASCADE
);

CREATE TABLE PRESCRIPTIONS (
	Prescription_Id INT AUTO_INCREMENT, 
	Patient_Id INT,
	Professional_Id INT,
    Medication_Name VARCHAR(255) NOT NULL,
    Dosage VARCHAR(255) NOT NULL,
    Date_Prescribed DATE NOT NULL, 
    Expiration_Date DATE NOT NULL,
    Remaining_Refills INT DEFAULT 0,
    FOREIGN KEY (Patient_Id) References PATIENTS(Patient_Id),
    FOREIGN KEY (Professional_Id) References PROFESSIONALS(Professional_Id),
    PRIMARY KEY (Prescription_Id, Patient_Id, Professional_Id)
);

CREATE TABLE TEST_RESULTS (
	Test_Id INT AUTO_INCREMENT,
    Patient_Id INT,
	Professional_Id INT,
    Test_Name VARCHAR(255),
    Date_Conducted DATE NOT NULL,
    Test_Status ENUM('Pending', 'Final') NOT NULL,
    Doctor_Comments VARCHAR(255),
    FOREIGN KEY (Patient_Id) References PATIENTS(Patient_Id),
    FOREIGN KEY (Professional_Id) References PROFESSIONALS(Professional_Id),
    PRIMARY KEY (Test_Id, Patient_Id, Professional_Id)
);

CREATE TABLE APPOINTMENTS (
	Appointment_Id INT AUTO_INCREMENT,
    Patient_Id INT,
	Professional_Id INT,
    Sched_Date DATE NOT NULL,
    Sched_Time TIME NOT NULL,
    Appvl_Status ENUM('Requested', 'Confirmed', 'Cancelled'),
    Notes VARCHAR(255), 
	FOREIGN KEY (Patient_Id) References PATIENTS(Patient_Id),
    FOREIGN KEY (Professional_Id) References PROFESSIONALS(Professional_Id),
    PRIMARY KEY (Appointment_Id, Patient_Id, Professional_Id)
);

-- STILL NEED TO ADD FOR VITALS LOG, AND MESSAGES
-- Mock Data