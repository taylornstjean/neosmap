from flask_wtf import FlaskForm
from wtforms import PasswordField, EmailField, BooleanField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Email, Length


###########################################################################
# FLASK FORMS

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email("Not a valid email.")])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Length(max=64, message="Email must be no longer than 64 characters.")])
    password = PasswordField("Password", validators=[DataRequired(), EqualTo('confirm', message='Passwords do not match.')])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), Length(min=8, max=64, message="Password must be between 8 and 64 characters long.")])
    submit = SubmitField("Register")


# ------------------------------ END OF FILE ------------------------------
