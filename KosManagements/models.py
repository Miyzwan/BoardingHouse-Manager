from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    rooms = db.relationship('Room', backref='owner', lazy=True, cascade='all, delete-orphan')
    expenses = db.relationship('Expense', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    monthly_rent = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')  # available, occupied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    tenants = db.relationship('Tenant', backref='room', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='room', lazy=True, cascade='all, delete-orphan')
    
    @property
    def current_tenant(self):
        return Tenant.query.filter_by(room_id=self.id, is_active=True).first()
    
    @property
    def total_revenue(self):
        return db.session.query(func.sum(Payment.amount)).filter_by(room_id=self.id, status='paid').scalar() or 0

class Tenant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    
    # Relationships
    payments = db.relationship('Payment', backref='tenant', lazy=True, cascade='all, delete-orphan')
    
    @property
    def total_paid(self):
        return db.session.query(func.sum(Payment.amount)).filter_by(tenant_id=self.id, status='paid').scalar() or 0
    
    @property
    def outstanding_amount(self):
        return db.session.query(func.sum(Payment.amount)).filter_by(tenant_id=self.id, status='pending').scalar() or 0

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, paid, overdue
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)
    
    @property
    def is_overdue(self):
        return self.status == 'pending' and self.due_date < date.today()

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # utilities, maintenance, supplies, etc.
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
