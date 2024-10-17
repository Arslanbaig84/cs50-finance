import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


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
    """Show portfolio of stocks"""
    #Getting user history
    rows = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id = session["user_id"])

    # User's cash in wallet
    ciw = db.execute("SELECT cash from users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"]

    #Inititalizing total assets both stock vlaue and cash in wallet
    total_value = ciw
#    total = ciw

    #Getting total value updated with complete stock portfolio
    for row in rows:
        portfolio = lookup(row["symbol"])
        stock["name"] = portfolio["name"]
        stock["price"] = portfolio["price"]
        stock["value"] = row["price"] * row["total_shares"]

        total_value += stock["value"]
#        total += stock["value"]

    return render_template("index.html", stocks=rows, cash=ciw, total_value=total_value)
#   grand_total=total

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # getting stock and number of shares
        symbol = request.form.get("symbol").upper()
        shares = request.form.get("shares")
        quote = lookup(symbol)

        # Ascertaining conidtions for inputs
        if not quote:
            return apology("Please provide valid stock symbol", 400)
        if not shares or not share.isdigit() or int(shares) < 0:
            return apology("No of shares must be positive integer", 400)

        # getting cost of shares
        shares =  int(shares)
        price = quote["price"]

        cost = price * shares

        # getting cash in wallet
        ciw = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["cash"]

        # Ascertaining enough cash
        if ciw < cost:
            return apology("not enough cash in wallet", 400)

        # updating cash in wallet
        db.execute("UPDATE users SET cash = ciw - :cost WHERE id = :user_id", cost = cost, user_id = session["user_id"])

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    #getting data from transactions table
    rows = db.execute("SELECT * FROM transactions WHERE user_id = :user_id ORDER BY time DESC", user_id = session["user_id"])

    return render_template("history.html", transactions = rows)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

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
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "Post":
        symbol = request.method.get("symbol")
        quote = lookup(symbol)
        if not quote:
            return apology("Symbol doesn't exist, check spelling", 400)
        return render_template("quote.hmtl", quote=quote)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            return apology("Please fill out all fields username, password and confirmation", 400)
        if password != confirmation:
            return apology("password do not match confirmation", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 0:
            return apology("username already exist", 400)

        hashed_password = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hashed_password)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # getting data of symbol and shares from database
    rows = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id = session["user_id"])

    # When method is post, sell shares
    if request.method == "POST":
        symbol = request.form.get("symbol").upper() #getting input from sell.html for share symbol
        shares = request.form.get("shares") #getting input of number of shares from sell.html

        if not symbol or not shares or not shares.isdigit() or int(shares) <=0: #making sure input entered is correct
            return apology("Please provide complete information comprising stock symbol and number of share as positive integers")
        else:
            shares = int(shares)

        for row in rows:
            if row["symbol"] == symbol: # comparing symbol from sell.html with all symbol in your portfolio
                if stock["total_shares"] < shares: # checking that we have enough shares
                    return apology("You don't own enough shares")
                else:
                    quote = lookup(symbol) #looking up symbol online for most recent price of the share
                    if quote == None:
                        return apology("symbol not found")

                    price = quote["price"]
                    total_sale_value = shares * price

                    db.execute("UPDATE users SET cash = cash + :total_sale_value WHERE id = :user_id", total_sale_value=total_sale_value, user_id=session["user_id"])

                    return redirect("/")

        return apology("symbol not in your portfolio")
    else:
        return render_template("sell.html", stocks=rows)
