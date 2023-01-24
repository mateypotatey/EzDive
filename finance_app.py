"""import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

#API KEY
#export API_KEY=pk_01d0d1ca298f4e63a87505046f7d1c10

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

#add a global username variable to call on the page
username = None

@app.after_request
def after_request(response):
    #Ensure responses aren't cached
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    #Show portfolio of stocks
    portfolio = []

    current_user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])
    holdings = db.execute("SELECT * FROM holdings WHERE user_id = ? ORDER BY symbol ASC", session["user_id"])
    total_value = current_user[0]["cash"]

    # Loop over the holdings and find out the current stock price
    for holding in holdings:
        stock = lookup(holding["symbol"])
        stock["total"] = stock["price"] * holding["owned"]
        total_value += stock["total"]
        stock["owned"] = holding["owned"]
        portfolio.append(stock)

    return render_template("index.html", current_user=current_user[0], portfolio=portfolio, total_value=total_value)

@app.route("/funds", methods=["GET", "POST"])
@login_required
def funds():
    #Add more funds to account

    if request.method == "POST":
        funds = request.form.get("add_funds")
        db.execute("UPDATE users set cash = cash + ? WHERE id = ?", funds, session["user_id"])

        return redirect("/")

    return redirect("/")



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    #Buy shares of stock
    #check what the user's current available cash balance is
    current_user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

    if request.method == "POST":
        units = request.form.get("shares")
        symbol = request.form.get("symbol")

        if not symbol:
            return apology("You must enter a valid stock symbol.")

        # Exception of no units entered, units aren't numeric, unit is a fractional (eg. 1.2) or is less than 1
        elif not units or units.isnumeric() == False or float(units).is_integer() == False or int(units) < 1:
            return apology("You must enter a valid number of units to buy.")

        else:
            stock = lookup(symbol)
            units = int(units)

            if stock == None:
                return apology("You did not enter a valid stock symbol. Try again.")

            stock_price = stock["price"]
            cash = current_user[0]["cash"]

            #determine if user has enough funds to purchase this many stocks
            if cash > (stock_price * units):

                #calculate total spend
                total_spend = stock_price * units

                #update both databases
                transaction_type = "BUY"

                # Update transaction ledger
                db.execute("INSERT INTO transactions (user_id, symbol, units, shareprice, total_value, tx_type) VALUES (?, ?, ?, ?, ?, ?)",
                    session["user_id"], stock["symbol"], units, stock_price, total_spend, transaction_type)

                # update holdings database
                if len(db.execute("SELECT * FROM holdings WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)) == 0:
                    db.execute("INSERT INTO holdings (user_id, symbol, owned) VALUES (?, ?, ?)",
                        session["user_id"], symbol, units)

                else:
                    # retrieve current count of stocks
                    owned = db.execute("SELECT owned FROM holdings WHERE user_id = ? AND symbol = ?",
                        session["user_id"], symbol)
                    owned = owned[0]["owned"]

                    # Update holdings for that particular stock
                    db.execute("UPDATE holdings SET user_id = ?, owned = ? WHERE symbol = ?",
                        session["user_id"], owned + units, symbol)

                # Update cash holding
                db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - total_spend, session["user_id"])

                #update stock price
                current_user = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

                return redirect("/")

            else:
                return apology("You do not have the required funds.")

    #need to select the first entry in current_user because the db search returns a list of length 1
    return render_template("buy.html", current_user=current_user[0])


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    #Sell shares of stock

    holdings = db.execute("SELECT * FROM holdings WHERE user_id = ? ORDER BY symbol ASC", session["user_id"])
    transaction_type = "SELL"

    if request.method == "POST":
        symbol = request.form.get("symbol")
        units = int(request.form.get("shares"))

        # check how many shares of that stock the user owns
        owned = db.execute("SELECT owned FROM holdings WHERE user_id = ? and symbol = ?", session["user_id"], symbol)
        len_owned = len(owned)
        owned = owned[0]["owned"]

        # check if a stock was selected or if the user has ANY of that stock
        if not symbol:
            print(symbol)
            return apology("You did not select a stock or do not own this stock.")

        elif len_owned == 0:
            return apology("You cannot sell what you don't have")

        # check if a positive quantity of shares was entered AND if the user has that many shares
        elif units < 1 or units > owned:
            return apology("You don't have this much of the stock to sell")

        else:
            stock = lookup(symbol)
            stock_price = stock["price"]
            total_sale = stock_price * units

            # update the user's bank balance to reflect the sale
            db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", total_sale, session["user_id"])

            # inser the transaction into the transaction ledger to reflect the sale
            db.execute("INSERT INTO transactions (user_id, symbol, units, shareprice, total_value, tx_type) VALUES (?, ?, ?, ?, ?, ?)",
                session["user_id"], stock["symbol"], units, stock_price, total_sale, transaction_type)

            # delete the entry from the holdings ledger if quantity owned = 0
            if units - owned == 0:
                db.execute("DELETE FROM holdings WHERE symbol = ? and user_id = ?", symbol, session["user_id"])

            else:
                # update the holdings of the user after the sale
                db.execute("UPDATE holdings SET owned = ? WHERE user_id = ? and symbol = ?",
                    owned - units, session["user_id"], symbol)

            return redirect("/")

    return render_template("sell.html", holdings=holdings)


@app.route("/history")
@login_required
def history():
    #Show history of transactions
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", session["user_id"])
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    #Log user in

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    #Log user out

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    #Get stock quote.
    #If data was entered into the form. ie. POST method
    if request.method == "POST":

        symbol = request.form.get("symbol")
        stock = lookup(symbol)

        if not symbol:
            return apology("You did not enter anything")

        if stock == None:
            return apology("You did not enter a valid stock symbol. Try again.")

        return render_template("quoted.html", stock=stock)

    #If user just clicked on the link to get here. Ie. no information entered.
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    #Register user

    if request.method == "POST":
        #retrieve the input variables from the form
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        #get list of usernames to compare if username aleady in database
        unames_list = db.execute("SELECT username FROM users WHERE username = ?", username)

        #check to see if both username and password were entered
        if not username or not password:
            return apology("must provide username and/or password")

        #check to see if the password and confirmation password match
        elif password != confirmation:
            return apology("passwords do not match. Try again")

        #check if the user is already in the database
        elif len(unames_list) != 0:
            return apology("This username already exists. Please use another username.")

        #else generate account and insert into database
        else:
            #this was my solution to check if the username is in the database already. A bit too complicated.
            #for user in unames_list:
            #    if username in user["username"]:
                   # return apology("This username already exists. Please use another username.")

            hash = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)" , username, hash)
            return redirect("/")

    else:
        return render_template("register.html")"""