from DatabaseManager import DatabaseManager
import os

#Testing file for inserting stuff into the database

dbm = DatabaseManager("care_path_db.db")


_sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data", "sample_result.pdf")
with open(_sample_path, "rb") as _f:
    sample_result_pdf = _f.read()

patient_id_one = dbm.add_user("test_patient@test.com","password","Patient")
prof_id_one = dbm.add_user("test_professional@test.com","password","Professional")
patient_id_two = dbm.add_user("test_patient_two@test.com","password","Patient")
prof_id_two = dbm.add_user("test_professional_two@test.com","password","Professional")

dbm.add_patient(patient_id_one, "John","Doe","01/01/2000",123,456)

dbm.add_professional(prof_id_one, "Gregory", "House", "6767")

dbm.add_patient(patient_id_two, "Jane","Doe","10/01/2005",456,123)

dbm.add_professional(prof_id_two, "Kyle", "Smith", "6969")

dbm.add_medication("Pills", "The good stuff", "Once daily")

dbm.add_prescription(patient_id_one,prof_id_one,1,"test dosage", "26/06/2026","26/07/2026",1)

dbm.add_test_result(patient_id_one,prof_id_one,"Test test results", "26/06/2026","Pending","These are the comments")

dbm.add_test_result(patient_id_one,prof_id_one,"Chest X-Ray", "27/06/2026","Final","No abnormalities detected.", file_name="chest_xray.pdf", file_data=sample_result_pdf)

dbm.add_appointement(patient_id_one,prof_id_one,"26/06/2026","14:05","Confirmed", "These are the notes")

dbm.add_prescription(patient_id_two,prof_id_two,1,"50mg", "28/06/2026","28/07/2026",1)

dbm.add_test_result(patient_id_two,prof_id_two,"Test results", "28/06/2026","Pending","These are the comments")

dbm.add_appointement(patient_id_two,prof_id_two,"28/06/2026","10:0","Confirmed", "These are the notes")

dbm.add_message(1,2,"2024-05-08 14:35:29.123", "This is a test message")

dbm.add_vital(1,"26/06/2026", 100, "120/80 mm Hg","36.5","These are the notes")
print("done")
