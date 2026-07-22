care_path.py
    - The main file for this application, creates and serves a server using Flask
    - Routes the user based on the url or an HTTP method
    - Added basic functionality for logging in and only allowing types of users to see their stuff
    - Can be tested by logging in with either:
        email: test_patient@test.com || password: password
        email: test_professional@test.com || password: password
    -trying to change the url to the other type will give an access error

DatabaseManager.py
    - A class for accessing and updating the database, so anything involing the db goes through it
    - Uses SQLite which is more lightweight than MySQL and is simple to implement with python
        also has some different syntax and less data types
    - Will create the tables if they don't exist and has methods for inserting data into each of the tables
    - Also had a space for functions that read from the database
        - Note, in every function a connection and cursor needs to be made because of threading
        - These connections should be closed at the end of each function

database_insertion.py
    - Used for testing and inserting mock data into the database

static folder
    - will hold js and css to send to the server once they exist
templates
    - holds the html files for the website
    
