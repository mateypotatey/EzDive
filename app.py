from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import sqlite3
from sqlite3 import Error

app = Flask(__name__)

#The below line will enable debug mode which means the flask app will restart upon any code changes, so don't need to restart the flask run.
#type export FLASK_DEBUG=1 in terminal before typing flask run to enable debugger

#more complicated sqlite connection protocol.
"""
def create_connection(path):
    connection = None
    try:
        Using isolation_level = None so queries are sent without having to commit. Not a problem for single users but may need to be changed to connectio.commit() for multi user.
        Check_same_thread=False because I'm establishing a connection at the start. Ideally you'd combine the connection and query in one function to follow the motto "late to open, 
        early to close: https://stackoverflow.com/questions/48218065/objects-created-in-a-thread-can-only-be-used-in-that-same-thread?rq=1      
        
        connection = sqlite3.connect(path, isolation_level = None, check_same_thread = False)
        print("Connection to SQLITE DB successful")
    except Error as e:
        print(f"The error '{e}' occured")
    
    return connection"""

#The below is a template to use for late open early close philosophy for database
"""def sql_query(query):
    try:
        with sqlite3.connect("ezdive.db") as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            print("Query executed successfully")
    except Error as e:
        print(f"Query was unsuccessfull: {e}")"""

"""def sql_entry(query):
    try:
        cursor.execute(query)
        print("query executed")
    except Error as e:
        print(f"Error encountered: {e}")"""


def apology(message, code = 400):
    """Render message as an apology to user."""
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

#Function to check if all fields are empty. If they are, print error message.
def check_entry_validity(dive_entry):
    empty_counter = 0
    for entry in dive_entry:
        if entry == "":
            print("entry is empty")
            empty_counter += 1
        else:
            print("go on")
            continue
    
    if len(dive_entry) == empty_counter:
        print("Why did you even make this entry?")
        return False
    else:
        return True

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#add a global username variable to call on the page
username = None

#Change sqlite query result tuple to dict
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

#connect to server
connection = sqlite3.connect("ezdive.db", isolation_level=None, check_same_thread=False)

#https://docs.python.org/3/library/sqlite3.html#sqlite3-howto-row-factory the below code will turn tuple sql query result into dictionary
connection.row_factory = dict_factory
cursor = connection.cursor()

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    #the below function opens a connection only to execute the statement.
    """def sql_entry(query, user):
        try:
            with sqlite3.connect("ezdive.db") as connection:
                connection.row_factory = dict_factory
                cursor = connection.cursor()
                person = cursor.execute(query, user)
                connection.commit()
                print("Query executed successfully")
                return person
        except Error as e:
            print(f"Error encountered: {e}")
        print()"""

    current_user = cursor.execute("SELECT * FROM users WHERE user_id = ?", (session["user_id"],)).fetchone()
    dive_log = cursor.execute("SELECT * FROM entries WHERE diver_id = ?", (session["user_id"],)).fetchall()
    print(current_user)
    print(dive_log)
    
    #Below code changes 'None' in database to an empty string for better visualisation in HTML
    for dive_entry in dive_log:
        for parameter in dive_entry:
            if dive_entry[parameter] == None:
                dive_entry[parameter] = "-"
            else:
                continue

    return render_template("index.html", user=current_user["username"], dive_log=dive_log)

@app.route("/new", methods=["GET", "POST"])
@login_required
def new_entry():
    if request.method == "POST":
        date = request.form.get("date")
        location = request.form.get("location")
        time_in = request.form.get("time_in")
        dive_time = request.form.get("dive_time")
        max_depth = request.form.get("max_depth")
        avg_depth = request.form.get("avg_depth")
        visibility = request.form.get("visibility")
        deco_dive = request.form.get("deco")
        tank_type = request.form.get("tank_type")
        in_pressure = request.form.get("in_pressure")
        out_pressure = request.form.get("out_pressure")
        water_temp = request.form.get("water_temp")
        lead_weight = request.form.get("lead")
        suit_type = request.form.get("suit_type")
        hood = request.form.get("hood")
        wetsuit_thickness = request.form.get("thickness")
        ds_undergarment = request.form.get("undergarment")
        buddy = request.form.get("buddy")
        dive_notes = request.form.get("notes")

        dive_entry = [date, location, time_in, dive_time, max_depth, avg_depth, visibility, deco_dive, tank_type, in_pressure, out_pressure, water_temp, 
            lead_weight, suit_type, hood, wetsuit_thickness, ds_undergarment, buddy, dive_notes]


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username and password was submitted
        if not request.form.get("username") or not request.form.get("password"):
            return apology("must provide username and/or password", 403)

        # Query database for username
        entries = cursor.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()

        # Ensure username exists and password is correct
        if len(entries) != 1 or not check_password_hash(entries[0]["password_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = entries[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        """Not saving input variables from form to minimise saving sensitive info into memory"""

        #get list of usernames to compare if username aleady in database
        users_list = cursor.execute("SELECT username FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()

        #check to see if both username and password were entered
        if not request.form.get("username") or not request.form.get("password"):
            return apology("must provide username and/or password")

        #check to see if the password and confirmation password match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match. Try again")

        #check if the user is already in the database
        elif len(users_list) != 0:
            return apology("This username already exists. Please use another username.")

        #else generate account and insert into database
        else:
            password_hash = generate_password_hash(request.form.get("password"))
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (request.form.get("username"), password_hash))
            return redirect("/", )

    else:
        return render_template("register.html")