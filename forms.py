from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import InputRequired, Length, Email
from flask_wtf import FlaskForm


class RegisterForm(FlaskForm):
    """Form for registering a user."""

    email = StringField("Email", validators=[
                        InputRequired(), Email(), Length(max=50)], render_kw={"placeholder": "Email"})
    password = PasswordField("Password", validators=[
                             InputRequired(), Length(min=6, max=50)], render_kw={"placeholder": "Password"})


class LoginForm(FlaskForm):
    """Form for logging in a user."""
    email = StringField("Email", validators=[
                        InputRequired(), Email(), Length(max=50)], render_kw={"placeholder": "Email"})
    password = PasswordField("Password", validators=[
                             InputRequired(), Length(min=6, max=50)], render_kw={"placeholder": "Password"})


class NewListForm(FlaskForm):
    """Form for creating a new list."""
    name = StringField("List Name", validators=[
        InputRequired(), Length(max=50)], render_kw={"placeholder": "Want To Read"})


class TrackProgressForm(FlaskForm):
    """Form for tracking progress on a book."""
    current_page = IntegerField("Progress", validators=[
        InputRequired()], render_kw={"placeholder": 0})
