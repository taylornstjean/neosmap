from flask import Blueprint, request, render_template, redirect
from flask_login import login_user, logout_user, login_required, current_user
from neosmap.web_interface.models import User, db
from neosmap.web_interface.utils import _hash
from .forms import LoginForm, RegisterForm

###########################################################################
# INITIALIZE BLUEPRINT

mod_auth = Blueprint("auth", __name__, url_prefix="/auth/", template_folder="./templates")

###########################################################################
# DEFINE ROUTES


@mod_auth.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect('/data')
    if form.validate_on_submit():

        email = request.form["email"]
        password = request.form["password"]
        remember = True if request.form.get("remember") else False

        user = User.query.filter_by(email=email).first()

        if not user or user.password != _hash(password):
            form.email.errors.append("Invalid email or password.")
            return render_template("login.html", form=form), 401
        elif user.password == _hash(password):
            login_user(user, remember=remember)
            return redirect("/data")

    return render_template("login.html", form=form), 200


@mod_auth.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    current_user.wipe_instances()
    logout_user()
    return redirect("/auth/login")


@mod_auth.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if current_user.is_authenticated:
        return redirect('/data')

    if form.validate_on_submit():
        password = _hash(request.form["password"])
        email = request.form["email"]

        tmp_user = User.query.filter_by(email=email).first()
        if tmp_user:
            form.email.errors.append("Email already in use.")
            return render_template("register.html", form=form), 401

        new_user = User()
        new_user.save(
            email=email,
            password=password
        )

        return redirect("/auth/login")

    return render_template("register.html", form=form), 200


@mod_auth.route("/check", methods=["GET"])
@login_required
def check():
    return f'User logged in as {current_user.email}.', 200

# ------------------------------ END OF FILE ------------------------------
