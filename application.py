import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL(os.getenv("DATABASE_URL"))


# Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")

API_KEY = "pk_41ca5481ab1b4f06926903fe931ef911"

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # getting cash for the logged in user
    cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session['user_id'])

    # grouping same stocks as one stock and their total number of shares using GROUP BY function in sqlite
    # from the user portfolio for the logged in user
    rows = db.execute("SELECT symbol, SUM(shares) as shares FROM portfolio WHERE id = :id GROUP BY symbol", id=session['user_id'])

    quote = []
    grandtotal = 0

    # for each stocks' the user owns
    for line in rows:

        # total share of the stock if not zero
        if line['shares'] != 0:

            # checking the current value of a each share in the market via lookup function
            # and append in the stock list( a temporary list)
            stock = lookup(line['symbol'])

            # append number of each share
            stock['shares'] = line['shares']

            # append the total value of the stocks in the market, number of shares times current value
            stock['total'] = line['shares'] * stock['price']

            # append to quote list
            quote.append(stock)

            # calculating the grandtotal with total market investment
            grandtotal = grandtotal + stock['total']

    # calculating the grandtotal, cash in account + total investment in market
    grandtotal = grandtotal + cash[0]['cash']

    # return to the index.html page with all the information like toal cash in account,
    # grandtotal of cash and  total market investment, current market price of stock the user owned, its symbol, name
    return render_template("index.html", quote=quote, cash=cash[0]['cash'], grandtotal=grandtotal)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # if calling '/buy' route via post method
    if request.method == "POST":

        # getting user input from the buy.html page
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # if symbol is missing
        if symbol == "":
            return apology("Missing Symbol")

        # if number of shares is missing
        if shares == "":
            return apology("Missing shares")

        # Ensure that the number is positive
        elif not shares.isdigit():
            return apology("Invalid number of shares")

        # looking for the latest price of the stock
        quote = lookup(symbol)

        # if 'quote' list is empty( stock's symbol does not exist)
        if quote == None:
            return apology("Invalid symbol")

        # getting cash the user owns
        row = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])

        # if cash in the account is less than the amount spends for buying the stock's shares
        if int(row[0]["cash"]) < quote["price"] * int(shares):
            return apology("Insufficient balance")

        # if he has enough cash in his account
        else:
            # updating the cash after buying a no. of shares of a stock
            db.execute("UPDATE users SET cash = (:cash - :price * :shares) WHERE id = :id",
                       cash=row[0]['cash'], price=quote['price'], shares=shares, id=session['user_id'])

            # updating the user's portfolio after the transcation
            db.execute("INSERT INTO portfolio (id, symbol, name, shares, price) VALUES(:id, :symbol, :name, :shares, :price)",
                       id=session['user_id'], symbol=quote['symbol'], name=quote['name'], shares=shares, price=quote['price'])

            # flashing the success message of buying the stock
            flash(u"Bought!", "success")
            return redirect("/")
    # if calling '/buy' route via get method
    else:
        return render_template("buy.html")


# via $.get() method using AJAX
@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    # getting the username from the input
    username = request.args.get("username")

    if username == "":
        return jsonify("empty")
    # checking if the username already taken or not, if username is already taken then the 'result list' will be empty
    result = db.execute("SELECT username FROM users WHERE username = :username", username=username)

    # using json data for returning the result
    if not result:
        return jsonify(True)
    else:
        return jsonify(False)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # getting the data of all transactions data from portfolio table of the user
    quote = db.execute("SELECT * FROM portfolio WHERE id = :id", id=session['user_id'])
    return render_template("history.html", quote=quote)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Forget any user_id
        session.clear()

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # if calling '/quote' route via post method
    if request.method == "POST":

        # if stock is missing
        if request.form.get("symbol") == "":
            return apology("Missing Symbol")

        # using lookup function for the latest value of the stock
        quote = lookup(request.form.get("symbol"))

        # if stock symbol does not exist
        if quote == None:
            return apology("Invalid stock")
        # all goods return the latest price of the stock
        else:
            symbol = quote['symbol']
            price = usd(quote['price'])
            name = quote['name']
            return render_template("quoted.html", price=price, name=name, symbol=symbol)

    # if calling '/quote' route via get method
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # if calling '/register' route via post method
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Ensure password is resubmitted
        elif not request.form.get("confirmation"):
            return apology("must confirm your password")

        # Ensure there is no typos in password
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password not matched")

        # hashing the password
        hash = generate_password_hash(request.form.get("password"))

        # insert the data into database
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                            username=request.form.get("username"), hash=hash)

        # if username already taken
        if not result:
            return apology("username already taken")
        # Query database for username
        rows = db.execute("SELECT id FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = request.form.get("username")

        # flashing the success message to the next route with category as 'success'
        flash(u"Registered!", "success")

        # Redirect user to home page
        return redirect("/")

    # if calling '/register' route via get method
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # getting user data from the his portfolio like the stocks he owns
    rows = db.execute("SELECT symbol, SUM(shares) as shares FROM portfolio WHERE id = :id GROUP BY symbol", id=session['user_id'])

    # if calling '/sell' route via post method
    if request.method == "POST":

        # getting symbol and no. of shares submitted by the user via sell webpage
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # if symbol is missing
        if symbol == None:
            return apology("missing symbol")
        # if no of shares is missing
        elif shares == "":
            return apology("missing shares")

        # Ensure that no. of shares greater than 0
        if int(shares) < 1:
            return apology("invalid input for the number of shares")

        # Each stock own by user
        for stock in rows:

            # getting that particular stock that user submitted
            if stock['symbol'] == symbol:
                # if shares owned of that particular stock is less than no. of shares user optted for selling
                if int(stock['shares']) < int(shares):
                    return apology("too many shares")

                # if all goods, i.e. user have enough shares for selling
                else:

                    # looking for latest price of the stock
                    quote = lookup(symbol)

                    # looking for the cash the user have from his account
                    cash = db.execute("SELECT cash FROM users WHERE id = :id", id=session['user_id'])

                    # updating user's profile after selling shares
                    db.execute("UPDATE users SET cash = (:cash + :price * :shares) WHERE id = :id",
                               cash=cash[0]['cash'], price=quote['price'], shares=shares, id=session['user_id'])

                    db.execute("INSERT INTO portfolio (id, symbol, name, shares, price) VALUES(:id, :symbol, :name, -:shares, :price)",
                               id=session['user_id'], symbol=quote['symbol'], name=quote['name'], shares=shares, price=quote['price'])

                    # flashing the success message of selling
                    flash(u"SOLD!", "success")

                    # redirect to the index page
                    return redirect("/")

        # if user somehow try to sell stock that he does own
        return apology("do not have ownership of those stocks")

    # if calling '/sell' route via get method
    else:
        return render_template("sell.html", symbols=rows)


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    """changing user's password"""

    # if request '/changepassword' via post method
    if request.method == "POST":

        # Ensure old password is submitted
        if not request.form.get("old-password"):
            return apology("old password missing", 403)

        # Ensure new password is submitted
        elif not request.form.get("new-password"):
            return apology("new password missing", 403)

        # Ensure new password is resubmitted
        elif not request.form.get("new-password-confirmation"):
            return apology("must confirm your new password", 403)

        # Ensure there is no typos in password( confirm the new password)
        elif request.form.get("new-password") != request.form.get("new-password-confirmation"):
            return apology("New password not matched", 403)

        # hashing the new password
        hash = generate_password_hash(request.form.get("new-password"))

        # getting the hashed password from the database
        hashed_password = db.execute("SELECT hash FROM users WHERE id=:id", id=session["user_id"])

        # in case wrong password
        if not check_password_hash(hashed_password[0]["hash"], request.form.get("old-password")):
            flash(u"Incorrect password! please try again.", "failure")
            return redirect("/changepassword")

        # update the new hashed password into database
        db.execute("UPDATE users SET hash = :hash WHERE id = :id", hash=hash, id=session["user_id"])

        # forget the user's logging
        session.clear()

        # flashing the message of successful changed password
        flash(u"Password successfully changed!", "success")

        # Redirect user to login pages
        return redirect("/login")
    else:
        # if request '/changepassword' via get method
        return render_template("changepassword.html")


@app.route("/removeuser", methods=["GET", "POST"])
@login_required
def removeuser():

    # if calling '/removeuser' route via 'post' method
    if request.method == "POST":
        # if password is missing
        if request.form.get("password") == "":
            # flashing message of missing password with failure category to the next route, '/removeuser' in this case
            flash(u"Password Missing!", "failure")
            return redirect("/removeuser")

        # if user forget to confirm, if not tick the checkbox
        if request.form.get("check") == None:
            flash(u"Please! Tick the check Box", "failure")
            return redirect("/removeuser")

        # getting the hashed password from the database
        hashed_password = db.execute("SELECT hash FROM users WHERE id=:id", id=session["user_id"])

        # in case wrong password
        if not check_password_hash(hashed_password[0]["hash"], request.form.get("password")):
            flash(u"Incorrect password! please try again.", "failure")
            return redirect("/removeuser")

        # remove the user data from the users as well as from protfolio database
        db.execute("DELETE FROM users WHERE id= :id", id=session["user_id"])
        db.execute("DELETE FROM portfolio WHERE id= :id", id=session["user_id"])

        # forget the user's logging
        session.clear()

        # flashing message of successful account removable
        flash(u"Successfully Removed Your Account!", "success")

        # redirect to the the register page
        return redirect("/register")
    else:
        # if request '/remove' route via get method
        return render_template("removeuser.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
