import os
import qrcode

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required



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

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    # """ABOUT PAGE"""
    return render_template("index.html")

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
#     # """Create a QR code"""
#     # """If by get, then just display the boxes: qr destination and desired name."""
#     # """if by post, create the qr code, and send the info to mycodes.html """
    if request.method == "GET":
        return render_template("create.html")
    else:
        link = request.form.get('link')
        name = request.form.get("codename")
        mycodes = db.execute("SELECT codename FROM mycodes WHERE id = ?", session["user_id"])

        # If user doesn't return input, return apology.
        if request.form.get('link') == '' or request.form.get('codename') == '':
            return apology("Please Provide Input.")
        # CHECK IF QR CODE NAME IS ALREADY USED
        # If a qr has already been created
        if len(mycodes) > 0:
            # loop over the list of codes
            for i in range(len(mycodes)):
                # if the name has been used already
                if name in mycodes[i]["codename"]:
                    # return an apology message
                    return apology("qr name already exists")
    # Else just insert the new qr code details.
    db.execute("INSERT INTO mycodes (id, link, codename) VALUES (?, ?, ?)", session["user_id"], link, name)
    flash ("Success!")
    return redirect("/create")




@app.route("/mycodes", methods=["GET", "POST"])
@login_required
def mycodes():
    if request.method == "GET":
        codes = db.execute("SELECT * FROM mycodes WHERE id = ?", session["user_id"])
        return render_template("mycodes.html", codes=codes)
    else:
        # store the link provided by user in variable
        link = db.execute("SELECT link FROM mycodes WHERE id = ? AND codename = ?", session["user_id"], request.form.get("codes"))
        # make qrqode
        img = qrcode.make(link)
        # save qrcode as png in static folder
        img.save("static/new.png", "PNG")
        return render_template("qrcode.html")





@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    # """ If by get, display dropbar containing qr codes owned by user"""
    # """ if by post, delete the qr code from the database. """
    if request.method == "GET":
        codes = db.execute("SELECT * FROM mycodes WHERE id = ?", session["user_id"])
        return render_template("delete.html", codes=codes)
    else:
        db.execute('DELETE FROM mycodes WHERE id = ? AND codename = ?', session['user_id'], request.form.get("delete"))
        flash("Deleted!")
        return redirect("/delete")




@app.route("/register", methods=["GET", "POST"])
def register():
    # """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Make sure not blank.
        if not request.form.get("username"):
            return apology("Must enter username.")
        elif not request.form.get("password"):
            return apology("Please enter a password.")
        elif not request.form.get("confirmation"):
            return apology("Please confirm password.")

        users = db.execute("SELECT username FROM users")

        # if username already exists, return apology.
        for foo in range(len(users)):
            if request.form.get("username") == users[foo]["username"]:
                return apology("username taken")


        # check if symbol in password. if there is no symbol, return apology.
        if any(not c.isalnum() for c in request.form.get("password")) == False:
            return apology("Please include symbol in password")

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match.")

        pass_hash = generate_password_hash(request.form.get("password"))

        rows = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                    username=request.form.get("username"), hash=pass_hash)


    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    # """Log user in"""

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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # I only want to show the footer on the login page.
        # Thus I will use the variable bellow to keep track
        # of that in the jinja template.
        remove_footer = 1
        return render_template("login.html", remove_footer=remove_footer)


@app.route("/logout")
def logout():
    # """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


def errorhandler(e):
    # """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
