""" Helper functions for app.py """

from functools import wraps
from flask import redirect, session, flash, request


def has_valid_length(password):
    """ Password Validator """
    return len(password) >= 8


def is_strong_password(password):
    """ special character checker """
    special_character = "@#$%^&*?><"
    return any(char in special_character for char in password)


def is_valid_username(username):
    """ Username validator """
    return not username.isdigit()


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


def is_admin(f):
    """ checking for admin """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        isAdmin = session.get("is_admin")
        if not isAdmin:
            flash("Only Admin Can Add Products", "Restriction")
            return redirect("/products")
        return f(*args, **kwargs)
    return decorated_function
