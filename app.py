""" Control All Website"""
import os
from cs50 import SQL
from flask import Flask, render_template, redirect, session, request
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from utility import (has_valid_length, is_strong_password, is_valid_username,
                     login_required, is_admin)


# configure application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images'
UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# tells cs50 libraray to user sqlitse database
db = SQL("sqlite:///project.db")
db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT  NOT NULL ,\
    username TEXT NOT NULL UNIQUE,hash_password TEXT NOT NULL,is_admin BOOL DEFAULT FALSE)")

db.execute("CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY NOT NULL,\
 firstname TEXT NOT NULL, lastname TEXT NOT NULL,email TEXT NOT NULL,\
 phone_number TEXT NOT NULL, address TEXT NOT NULL, cnic TEXT NOT NULL,\
 profile_image TEXT NOT NULL,user_id INTEGER NOT NULL UNIQUE REFERENCES users(id)) ")

db.execute("CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY NOT NULL,\
 name TEXT NOT NULL, image TEXT NOT NULL,origin TEXT, color TEXT, price REAL NOT NULL,\
 added_at TEXT DEFAULT CURRENT_TIMESTAMP)")

db.execute("CREATE TABLE IF NOT EXISTS purchases(id INTEGER NOT NULL,name TEXT NOT NULL,\
 image TEXT NOT NULL,origin TEXT,color TEXT,price REAL NOT NULL)")

db.execute("CREATE TABLE IF NOT EXISTS cart(id INTEGER NOT NULL,\
    card_id INTEGER PRIMARY KEY NOT NULL,\
    name TEXT NOT NULL,image TEXT NOT NULL,origin TEXT,color TEXT,price REAL NOT NULL)")


@app.route("/home")
@app.route("/")
def index():
    """ Show Index page """
    print(request.referrer)
    return render_template("index.html")


@app.route("/profile")
@login_required
def profile():
    """ Show Profile page """
    profile_data = db.execute(
        "SELECT * FROM profile WHERE user_id = ?", session["user_id"])
    if profile_data:
        return render_template("profile.html", profile=profile_data)
    return redirect("/edit")


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    """ Access to edit your profile """
    if request.method == "POST":
        data = {}
        data["firstname"] = request.form.get("firstName")
        data["lastname"] = request.form.get("lastName")
        data["email"] = request.form.get("emailAddress")
        data["phone_number"] = request.form.get("phoneNumber")
        data["home_address"] = request.form.get("homeAddress")
        data["cnic"] = request.form.get("cnicNumber")
        data["profile_Image"] = request.files['file'].filename
        create_profile(data)
        # saving the picture in the static directory of the project
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect("/profile")
    profile_data = db.execute(
        "SELECT * FROM profile WHERE user_id = ?", session["user_id"])
    profile_data = profile_data[0] if profile_data else None
    return render_template("edit_profile.html", profile=profile_data)


@app.route("/add_product", methods=["GET", "POST"])
@is_admin
def add_product():
    """Access to add products"""
    if request.method == "POST":
        product_name = request.form.get("product_name")
        origin = request.form.get("origin")
        color = request.form.get("color")
        price = request.form.get("price")
        product_image = request.files['file'].filename
        db.execute("INSERT INTO products(name,image,origin,color,price) VALUES(?,?,?,?,?)",
                   product_name, product_image, origin, color, price)
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect("/products")
    return render_template("add_product.html")


@app.route("/about")
@login_required
def about():
    """ Access to about page """
    return render_template("about.html")


@app.route("/products")
def products():
    """ render to lookup page """
    product1 = db.execute("SELECT * FROM products")
    return render_template("products.html", products=product1)


@app.route("/buy/<product_id>")
def product(product_id):
    """ Shows Product Detail page """
    item = db.execute(
        "SELECT * FROM products WHERE id = ? LIMIT 1", product_id)[0]
    return render_template("buy.html", product=item)


@app.route("/purchases", methods=["POST", "GET"])
@login_required
def purchase():
    """ Add items to purchase """
    message = "No data available"
    if request.method == "POST":
        product_id = request.form.get("product_id")
        product_purchase = db.execute(
            "SELECT * FROM products WHERE id = ?", int(product_id))[0]
        db.execute("INSERT INTO purchases(id,name,image,origin,color,price) VALUES(?,?,?,?,?,?)",
                   session["user_id"], product_purchase['name'], product_purchase['image'],
                   product_purchase['origin'], product_purchase['color'], product_purchase['price'])
        purchase_history = db.execute(
            "SELECT * FROM purchases WHERE id = ?", session["user_id"])
        success = "Product Successfully added"
        return render_template("purchases.html", product=purchase_history, success=success)
    purchase_history = db.execute(
        "SELECT * FROM purchases WHERE id = ?", session["user_id"])
    if len(purchase_history) < 1:
        return render_template("purchases.html", message=message)
    return render_template("purchases.html", product=purchase_history)


@app.route("/cart", methods=["POST", "GET"])
@login_required
def cart():
    """ Add item to the cart """
    message = "No data avaiable"
    if request.method == "POST":
        product_id = request.form.get("product_id")
        product_purchase = db.execute(
            "SELECT * FROM products WHERE id = ?", int(product_id))[0]

        db.execute("INSERT INTO cart(id,name,image,origin,color,price) VALUES(?,?,?,?,?,?)",
                   session["user_id"], product_purchase['name'], product_purchase['image'],
                   product_purchase['origin'], product_purchase['color'], product_purchase['price'])
        cart_history = db.execute(
            "SELECT * FROM cart WHERE id = ?", session["user_id"])
        success = "Product Successfully added"
        return render_template("cart.html", carts=cart_history, success=success)

    cart_history = db.execute(
        "SELECT * FROM cart WHERE id = ?", session["user_id"])
    if len(cart_history) < 1:
        return render_template("cart.html", message=message)
    return render_template("cart.html", carts=cart_history)


@app.route("/delete", methods=["POST"])
@login_required
def remove_product():
    """ delete product from cart """
    product_id = request.form.get("product_id")
    db.execute("DELETE FROM cart WHERE card_id = ?", int(product_id))
    return redirect("/cart")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ User Login """

    # forget user id
    session.clear()
    message = ""

    # If user request is post
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            message = "Username can't be empty"
        elif not password:
            message = "Enter your password"
        else:
            rows = db.execute(
                "SELECT * FROM users WHERE username = ?", username.lower())
            if len(rows) != 1:
                message = "This username Doesnot exist"
            elif not check_password_hash(rows[0]["hash_password"], password):
                message = "Invalid password"
            else:
                session["user_id"] = rows[0]["id"]
                session["is_admin"] = rows[0]["is_admin"]

                return redirect("/")
    return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    """ Log out user """

    # Forget session
    session.clear()

    # redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def registeration():
    """ Register User """
    message = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        checkbox = request.form.get("checkbox")

        if not username:
            message = "Enter Username"
        elif not password:
            message = "Enter Password"
        elif not confirmation:
            message = "Enter Password Confirmation"
        elif password != confirmation:
            message = "Password doesn't match"
        elif checkbox is None:
            message = "Accept Terms And conditions"
        elif not has_valid_length(password):
            message = "Minimium length of the password will be 8"
        elif not is_strong_password(password):
            message = "Password must contain special character"
        elif not is_valid_username(username):
            message = "Not valid username"
        else:
            password = generate_password_hash(password)
            try:
                user_id = db.execute(
                    "INSERT INTO users(username,hash_password) VALUES(?,?)", username.lower(
                    ),
                    password)
            except ValueError:
                message = "username already taken"
            else:
                session["user_id"] = user_id
                session["is_admin"] = 0
                return redirect("/edit")

    return render_template("registeration.html", message=message)


def create_profile(arg):
    """ Insert data into table """
    try:
        db.execute("INSERT INTO profile(user_id,firstname,lastname,email,phone_number,address\
            ,cnic,profile_image) VALUES(?,?,?,?,?,?,?,?)", session["user_id"], arg["firstname"],
                   arg["lastname"], arg["email"], arg["phone_number"], arg["home_address"],
                   arg["cnic"],
                   arg["profile_Image"])
    except ValueError:
        db.execute("UPDATE profile SET firstname = ?,lastname=?,email=?,phone_number=?,address=?,\
            cnic=?,profile_image=? WHERE user_id = ?", arg["firstname"], arg["lastname"],
                   arg["email"], arg["phone_number"], arg["home_address"], arg["cnic"],
                   arg["profile_Image"], session["user_id"])


if __name__ == "__main__":
    # or setting host to '0.0.0.0'
    app.run(host='localhost', port=5000, debug=True)
