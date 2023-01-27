from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
import sqlite3
from sqlite3 import Error

def apology(message, code = 400):
    #Render message as an apology to user.
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

#Function to check if all fields are empty. Returns False if all empty
def check_entry_validity(dive_entry):
    empty_counter = 0
    for entry in dive_entry[1:18]:
        if entry == "" or entry==None:
            empty_counter += 1
        else:
            continue
    
    if len(dive_entry[1:18]) == empty_counter:
        return False
    else:
        return True

"""SQL code from here on"""
#Change sqlite query result tuple to dict.
#https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

#The below function opens a connection only to execute the statement and then closes the connection
def sql_select(query, user = None):
    try:
        with sqlite3.connect("ezdive.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            if user != None:
                current_user = cursor.execute(query, user)
                print("Query executed successfully")
                return current_user
            else:
                current_user = cursor.execute(query)
                return current_user

    except Error as e:
        print(f"Error encountered: {e}")

#For inserting data into the sql table. 
def sql_insert(query, dive_log_entry):
    try:
        with sqlite3.connect("ezdive.db") as connection:
            connection.row_factory = dict_factory
            cursor = connection.cursor()
            cursor.execute(query, dive_log_entry)
            connection.commit()
            print("Query executed successfully")
            return
    except Error as e:
        print(f"Error encountered: {e}")