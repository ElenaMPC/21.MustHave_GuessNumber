from flask import Flask, render_template, make_response, request, redirect, url_for
from model import User, db
import random
import uuid
import hashlib


app = Flask(__name__)
db.create_all()


@app.route("/", methods=["GET"])
def index():
    session_token = request.cookies.get("session_token")

    if session_token:
        user = db.query(User).filter_by(session_token=session_token, deleted=False).first()
    else:
        user = None
    return render_template("index.html", user=user)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")

    # hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # create a secret number
    secret_number = random.randint(1, 30)

    # see if user already exists
    user = db.query(User).filter_by(email=email).first()

    if not user:
        # create a User object
        user = User(name=name, email=email, secret_number=secret_number, password=hashed_password)
        # save the user object into a database
        db.add(user)
        db.commit()

    # check if password is incorrect
    if hashed_password != user.password:
        return "WRONG PASSWORD! Go back and try again."

    elif hashed_password == user.password:
        # create a random session token for this user
        session_token = str(uuid.uuid4())

        # save the session token in a database
        user.session_token = session_token
        db.add(user)
        db.commit()

        # save user's session token into a cookie
        response = make_response(redirect(url_for('index')))
        response.set_cookie("session_token", session_token, httponly=True)

        return response

@app.route("/result", methods=["POST"])
def result():
    user_number = int(request.form.get("user-number"))
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if user_number == user.secret_number:
        message = "Correct! The secret number is {0}".format(str(user_number))

        # create a new random secret number
        new_secret = random.randint(1, 30)

        # update the user's secret number
        user.secret_number = new_secret

        # update the user object in a database
        db.add(user)
        db.commit()
    elif user_number > user.secret_number:
        message = "Your guess is not correct... try something smaller."
    elif user_number < user.secret_number:
        message = "Your guess is not correct... try something bigger."

    return render_template("result.html", message=message)


@app.route("/profile", methods=["GET"])
def profile():
    session_token = request.cookies.get("session_token")

    # get user from the database based on her/his email address
    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("index"))

@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    session_token = request.cookies.get("session_token")

    # get user from the database based on her/his email address
    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if request.method == "GET":
        if user:  # if user is found
            return render_template("profile_edit.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        name = request.form.get("profile-name")
        email = request.form.get("profile-email")
        old_password = request.form.get("old-password")
        new_password = request.form.get("new-password")
        # update the user object
        user.name = name
        user.email = email

        if old_password and new_password:
            hashed_old_password = hashlib.sha256(old_password.encode()).hexdigest()  # hash the old password
            hashed_new_password = hashlib.sha256(new_password.encode()).hexdigest()  # hash the old password

            # check if old password hash is equal to the password hash in the database
            if hashed_old_password == user.password:
                # if yes, save the new password hash in the database
                user.password = hashed_new_password
            else:
                # if not, return error
                return "Wrong (old) password! Go back and try again."

                    # store changes into the database
        db.add(user)
        db.commit()

        return redirect(url_for("profile"))

@app.route("/profile/delete", methods=["GET", "POST"])
def profile_delete():
    session_token = request.cookies.get("session_token")

    # get user from the database based on her/his email address
    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if request.method == "GET":
        if user:  # if user is found
            return render_template("profile_delete.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        # delete the user in the database
        user.deleted = True
        db.add(User)
        db.commit()

        return redirect(url_for("index"))

@app.route("/users", methods=["GET"])
def all_users():
    users = db.query(User).all()  # find all un-deleted users

    return render_template("users.html", users=users)

@app.route("/user/<user_id>", methods=["GET"])
def user_details(user_id):
    user = db.query(User).get(int(user_id))  # .get() can help you query by the ID

    return render_template("user_details.html", user=user)

if __name__ == '__main__':
    app.run()