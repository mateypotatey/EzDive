from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from sqlite3 import Error
from helpers import check_entry_validity, login_required, apology, sql_select, sql_insert

app = Flask(__name__)

#The below line will enable debug mode which means the flask app will restart upon any code changes, so don't need to restart the flask run.
#type export FLASK_DEBUG=1 in terminal before typing flask run to enable debugger

#more complicated sqlite connection protocol.
"""
Using isolation_level = None so queries are sent without having to commit. Not a problem for single users but may need to be changed to connectio.commit() for multi user.
Check_same_thread=False because I'm establishing a connection at the start. Ideally you'd combine the connection and query in one function to follow the motto "late to open, 
early to close: https://stackoverflow.com/questions/48218065/objects-created-in-a-thread-can-only-be-used-in-that-same-thread?rq=1      
        
connection = sqlite3.connect(path, isolation_level = None, check_same_thread = False)"""

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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
     
    
    current_user = sql_select("SELECT * FROM users WHERE user_id = ?", (session["user_id"],)).fetchone()
    dive_log = sql_select("SELECT * FROM entries WHERE diver_id = ?", (session["user_id"],)).fetchall()
    
    dive_count = len(dive_log)
    
    return render_template("index.html", user=current_user["username"], dive_log=dive_log, dive_count=dive_count)

@app.route("/new", methods=["GET", "POST"])
@login_required
def new_entry():

    current_user = sql_select("SELECT * FROM users WHERE user_id = ?", (session["user_id"],)).fetchone()
    dive_log = sql_select("SELECT * FROM entries WHERE diver_id = ?", (session["user_id"],)).fetchall()

    dive_count = len(dive_log) + 1

    if request.method == "POST":
        date = request.form.get("date")
        location = request.form.get("location")
        time_in = request.form.get("time_in")
        dive_time = request.form.get("dive_time")
        max_depth = request.form.get("max_depth")
        avg_depth = request.form.get("avg_depth")
        visibility = request.form.get("visibility")
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

        dive_entry = [dive_count, date, location, time_in, dive_time, max_depth, avg_depth, visibility, tank_type, in_pressure, out_pressure, water_temp, 
            lead_weight, suit_type, hood, wetsuit_thickness, ds_undergarment, buddy, dive_notes, session["user_id"]]
        
        #Check to see if anything was entered. Return error message if all fields were left blank.
        if check_entry_validity(dive_entry) == False:
            return apology("You need to fill out something for the dive to count!")
        
        #insert the new entry into the database
        sql_insert("INSERT INTO entries"
                       "(dive_number, dive_date, dive_location, time_in, dive_time, max_depth, avg_depth,"
                       "visibility, tank_type, in_pressure, out_pressure, water_temp, lead_weight,"
                       "suit_type, hood, wetsuit_thickness, ds_undergarment, buddy, dive_notes, diver_id)"
                       "VALUES"
                       "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", dive_entry)
        
        return redirect("/")
        
    return render_template("new.html", dive_count=dive_count)


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
        entries = sql_select("SELECT * FROM users WHERE username = ?", (request.form.get("username"),)).fetchall()

        # Ensure username exists and password is correct
        if len(entries) != 1 or not check_password_hash(entries[0]["password_hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = entries[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        total_users = len(sql_select("SELECT * FROM users").fetchall())
        logged_dives = len(sql_select("SELECT * FROM entries").fetchall())
        return render_template("login.html", total_users = total_users, logged_dives = logged_dives)

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
        """Not saving password variable from form to minimise saving sensitive info into memory"""
        username = request.form.get("username")

        #get list of usernames to compare if username aleady in database
        users_list = sql_select("SELECT username FROM users WHERE username = ?", (username,)).fetchall()

        #check to see if both username and password were entered
        if not username or not request.form.get("password"):
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
            user_details = [username, password_hash]
            sql_insert("INSERT INTO users (username, password_hash) VALUES (?, ?)", user_details)

            entries = sql_select("SELECT * FROM users where username = ?", (username,)).fetchone()
            
            # Remember user so login occurs automatically
            session["user_id"] = entries["user_id"]
            return redirect("/", )

    else:
        return render_template("register.html")