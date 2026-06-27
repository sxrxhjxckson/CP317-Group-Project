from DatabaseManager import DatabaseManager

#Testing file for inserting stuff into the database

dbm = DatabaseManager("care_path_db.db")

dbm.add_user("test_patient@test.com","password","Patient")
dbm.add_user("test_professional@test.com","password","Professional")

dbm.add_patient("John","Doe","01/01/2000",123,456)

dbm.add_professional("Gregory", "House", "6767")

dbm.add_medication("Pills", "The good stuff", "Once daily")

dbm.add_prescription(1,2,1,"test dosage", "26/06/2026","26/07/2026",1)

dbm.add_test_result(1,2,"Test test results", "26/06/2026","Pending","These are the comments")

dbm.add_appointement(1,2,"26/06/2026","14:05","Confirmed", "These are the notes")

dbm.add_message(1,2,"2024-05-08 14:35:29.123", "This is a test message")

dbm.add_vital(1,"26/06/2026", 100, "120/80 mm Hg","36.5","These are the notes")
print("done")
