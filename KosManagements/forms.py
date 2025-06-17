from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, FloatField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError
from wtforms.widgets import TextArea
from models import User, Room
from datetime import date

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class RoomForm(FlaskForm):
    number = StringField('Room Number', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Description', widget=TextArea())
    monthly_rent = FloatField('Monthly Rent ($)', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Status', choices=[('available', 'Available'), ('occupied', 'Occupied')], 
                        validators=[DataRequired()])

class TenantForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    room_id = SelectField('Room', coerce=int, validators=[DataRequired()])

class PaymentForm(FlaskForm):
    tenant_id = SelectField('Tenant', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount ($)', validators=[DataRequired(), NumberRange(min=0)])
    due_date = DateField('Due Date', validators=[DataRequired()])
    paid_date = DateField('Paid Date', validators=[Optional()])
    status = SelectField('Status', choices=[('pending', 'Pending'), ('paid', 'Paid')], 
                        validators=[DataRequired()])
    notes = TextAreaField('Notes', widget=TextArea())

class ExpenseForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired(), Length(max=200)])
    amount = FloatField('Amount ($)', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[
        ('utilities', 'Utilities'),
        ('maintenance', 'Maintenance'),
        ('supplies', 'Supplies'),
        ('repairs', 'Repairs'),
        ('insurance', 'Insurance'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    notes = TextAreaField('Notes', widget=TextArea())
