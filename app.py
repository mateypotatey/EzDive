from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import check_entry_validity, login_required, apology, sql_select, sql_insert, sql_init, next_dive_number
from datetime import datetime

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Creates database and tables
sql_init()

#dictionary for hard coded tank types
scuba_tanks = {"ali80" : "Aluminium 80", 
               "steel12" : "Steel 12L",
               "steel15" : "Steel 15L",
               "dbl12" : "Double 12",
               "dbl_al80" : "Double Ali 80"}

tank_volumes = {"ali80" : 11.1, 
               "steel12" : 12.0,
               "steel15" : 15.0,
               "dbl12" : 24.0,
               "dbl_al80" : 22.2}

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
    
    #Loop to change the date stored as YYYY-MM-DD to DD-MM-YYYY
    for dive in dive_log:
        try:
            dive_date = datetime.strptime(dive["dive_date"], "%Y-%m-%d")
            dive["dive_date"] = dive_date.strftime("%d-%m-%Y")
        except ValueError:
            continue

    dive_count = len(dive_log)
        
    return render_template("index.html", user=current_user["username"], dive_log=dive_log, dive_count=dive_count)

@app.route("/view", methods=["POST"])
@login_required
def view():
    dive_id = request.form.get("id")
    dive_log = sql_select("SELECT * FROM entries WHERE log_id = ?", (dive_id,)).fetchone()

    #Loop to change the date stored as YYYY-MM-DD to DD-MM-YYYY
    try:
        dive_date = datetime.strptime(dive_log["dive_date"], "%Y-%m-%d")
        dive_log["dive_date"] = dive_date.strftime("%d-%m-%Y")
    except ValueError:
        print("")

    return render_template("entry.html", dive_log = dive_log, scuba_tanks=scuba_tanks, tank_volumes=tank_volumes)


@app.route("/new", methods=["GET", "POST"])
@login_required
def new_entry():

    dive_log = sql_select("SELECT * FROM entries WHERE diver_id = ?", (session["user_id"],)).fetchall()
  
    dive_count = len(dive_log)

    #Auto-incrementing dive number to 'official' dive number
    try:
        next_dive = (next_dive_number(dive_log, idx = -1))
    except IndexError:
        next_dive = 1

    if request.method == "POST":
        dive_number = request.form.get("dive_number")
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
        lead_weight = request.form.get("lead_weight")
        suit_type = request.form.get("suit_type")
        hood = request.form.get("hood")
        wetsuit_thickness = request.form.get("wetsuit_thickness")
        ds_undergarment = request.form.get("ds_undergarment")
        buddy = request.form.get("buddy")
        dive_notes = request.form.get("notes")

        dive_entry = [dive_number, date, location, time_in, dive_time, max_depth, avg_depth, visibility, tank_type, in_pressure, out_pressure, water_temp, 
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
        
    return render_template("new.html", dive_count=dive_count, next_dive=next_dive, scuba_tanks=scuba_tanks, tank_volumes=tank_volumes)


@app.route("/editButton", methods=["POST"])
@login_required
def editBtn():

    dive_id = request.form.get("id")

    #making dive_log global so it can be called again in /edit route
    global dive_log
    dive_log = dive_id

    entry = sql_select("SELECT * FROM entries WHERE diver_id = ? AND log_id = ?", (session["user_id"], dive_log)).fetchone()
    dive_notes = entry["dive_notes"]

    #The below in conjuction with edit.html javascript fixes the "javascript throws a Uncaught SyntaxError: "
    #" string literal contains an unescaped line break error" because it's reading newline characters from sql.
    dive_notes = dive_notes.replace("\r\n", "qtab")

    return render_template("/edit.html", entry=entry, dive_notes=dive_notes, scuba_tanks=scuba_tanks)


@app.route("/edit", methods=["POST"])
@login_required
def edit():

    #Modify the existing entry using newly entered values. Update using the global dive_log number set above
    dive_number = request.form.get("dive_number")
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
    lead_weight = request.form.get("lead_weight")
    suit_type = request.form.get("suit_type")
    hood = request.form.get("hood")
    wetsuit_thickness = request.form.get("wetsuit_thickness")
    ds_undergarment = request.form.get("ds_undergarment")
    buddy = request.form.get("buddy")
    dive_notes = request.form.get("notes")

    dive_entry = [dive_number, date, location, time_in, dive_time, max_depth, avg_depth, visibility, tank_type, in_pressure, out_pressure, water_temp, 
        lead_weight, suit_type, hood, wetsuit_thickness, ds_undergarment, buddy, dive_notes, session["user_id"], dive_log]    

    #Check to see if anything was entered. Return error message if all fields were left blank.
    if check_entry_validity(dive_entry) == False:
        return apology("You need to fill out something for the dive to count!")

    #insert the new entry into the database
    sql_insert("UPDATE entries SET "
                    "dive_number = ?, dive_date = ?, dive_location = ?, time_in = ?, dive_time = ?, max_depth = ?, avg_depth = ?,"
                    "visibility = ?, tank_type = ?, in_pressure = ?, out_pressure = ?, water_temp = ?, lead_weight = ?,"
                    "suit_type = ?, hood = ?, wetsuit_thickness = ?, ds_undergarment = ?, buddy = ?, dive_notes = ?, diver_id = ?"
                    "WHERE log_id = ?", (dive_entry))
    
    return redirect("/")

@app.route("/delButton", methods=["POST"])
@login_required
def delBtn():

    dive_id = request.form.get("id")

    sql_select("DELETE FROM entries WHERE diver_id = ? AND log_id = ?", (session["user_id"], dive_id)).fetchone()

    return redirect("/")

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
    """Register user: This was copied from my CS50 - Finance codespace since it is essentially the same."""

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