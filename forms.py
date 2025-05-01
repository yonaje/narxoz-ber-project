# forms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm')])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Register')

class StudentForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Save')

class CourseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=128)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    material = FileField('Course Material')
    submit = SubmitField('Save')
