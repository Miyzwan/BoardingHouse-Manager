from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import User, Room, Tenant, Payment, Expense
from forms import LoginForm, RegisterForm, RoomForm, TenantForm, PaymentForm, ExpenseForm
from utils import update_payment_status
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract

# Authentication routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth_login'))

@app.route('/auth/login', methods=['GET', 'POST'])
def auth_login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@app.route('/auth/register', methods=['GET', 'POST'])
def auth_register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth_login'))
    
    return render_template('auth/register.html', form=form)

@app.route('/auth/logout')
@login_required
def auth_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_login'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Update payment statuses
    update_payment_status()
    
    # Get statistics
    total_rooms = Room.query.filter_by(user_id=current_user.id).count()
    occupied_rooms = Room.query.filter_by(user_id=current_user.id, status='occupied').count()
    available_rooms = total_rooms - occupied_rooms
    
    total_tenants = Tenant.query.join(Room).filter(Room.user_id == current_user.id, Tenant.is_active == True).count()
    
    # Payment statistics
    this_month = datetime.now().replace(day=1)
    monthly_revenue = db.session.query(func.sum(Payment.amount)).join(Room).filter(
        Room.user_id == current_user.id,
        Payment.status == 'paid',
        Payment.paid_date >= this_month
    ).scalar() or 0
    
    pending_payments = Payment.query.join(Room).filter(
        Room.user_id == current_user.id,
        Payment.status == 'pending'
    ).count()
    
    overdue_payments = Payment.query.join(Room).filter(
        Room.user_id == current_user.id,
        Payment.status == 'pending',
        Payment.due_date < date.today()
    ).count()
    
    # Recent payments
    recent_payments = Payment.query.join(Room).filter(
        Room.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).limit(5).all()
    
    # Most rented rooms (by total revenue)
    popular_rooms = db.session.query(
        Room,
        func.sum(Payment.amount).label('total_revenue')
    ).join(Payment).filter(
        Room.user_id == current_user.id,
        Payment.status == 'paid'
    ).group_by(Room.id).order_by(func.sum(Payment.amount).desc()).limit(3).all()
    
    return render_template('dashboard.html',
                         total_rooms=total_rooms,
                         occupied_rooms=occupied_rooms,
                         available_rooms=available_rooms,
                         total_tenants=total_tenants,
                         monthly_revenue=monthly_revenue,
                         pending_payments=pending_payments,
                         overdue_payments=overdue_payments,
                         recent_payments=recent_payments,
                         popular_rooms=popular_rooms)

# Room management
@app.route('/rooms')
@login_required
def rooms_index():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    query = Room.query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter(Room.status == status_filter)
    if min_price:
        query = query.filter(Room.monthly_rent >= min_price)
    if max_price:
        query = query.filter(Room.monthly_rent <= max_price)
    
    rooms = query.order_by(Room.number).paginate(page=page, per_page=10, error_out=False)
    return render_template('rooms/index.html', rooms=rooms, 
                         status_filter=status_filter, min_price=min_price, max_price=max_price)

@app.route('/rooms/new', methods=['GET', 'POST'])
@login_required
def rooms_new():
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(
            number=form.number.data,
            description=form.description.data,
            monthly_rent=form.monthly_rent.data,
            status=form.status.data,
            user_id=current_user.id
        )
        db.session.add(room)
        db.session.commit()
        flash('Room created successfully!', 'success')
        return redirect(url_for('rooms_index'))
    
    return render_template('rooms/form.html', form=form, title='Add New Room')

@app.route('/rooms/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def rooms_edit(id):
    room = Room.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = RoomForm(obj=room)
    
    if form.validate_on_submit():
        form.populate_obj(room)
        db.session.commit()
        flash('Room updated successfully!', 'success')
        return redirect(url_for('rooms_index'))
    
    return render_template('rooms/form.html', form=form, title='Edit Room', room=room)

@app.route('/rooms/<int:id>/delete', methods=['POST'])
@login_required
def rooms_delete(id):
    room = Room.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted successfully!', 'success')
    return redirect(url_for('rooms_index'))

# Tenant management
@app.route('/tenants')
@login_required
def tenants_index():
    page = request.args.get('page', 1, type=int)
    active_only = request.args.get('active_only', type=bool, default=True)
    
    query = Tenant.query.join(Room).filter(Room.user_id == current_user.id)
    
    if active_only:
        query = query.filter(Tenant.is_active == True)
    
    tenants = query.order_by(Tenant.name).paginate(page=page, per_page=10, error_out=False)
    return render_template('tenants/index.html', tenants=tenants, active_only=active_only)

@app.route('/tenants/new', methods=['GET', 'POST'])
@login_required
def tenants_new():
    form = TenantForm()
    # Populate room choices with available rooms
    form.room_id.choices = [(r.id, f"Room {r.number} - ${r.monthly_rent}") 
                           for r in Room.query.filter_by(user_id=current_user.id, status='available').all()]
    
    if form.validate_on_submit():
        tenant = Tenant(
            name=form.name.data,
            phone=form.phone.data,
            email=form.email.data,
            start_date=form.start_date.data,
            room_id=form.room_id.data
        )
        
        # Update room status to occupied
        room = Room.query.get(form.room_id.data)
        room.status = 'occupied'
        
        db.session.add(tenant)
        db.session.commit()
        flash('Tenant added successfully!', 'success')
        return redirect(url_for('tenants_index'))
    
    return render_template('tenants/form.html', form=form, title='Add New Tenant')

@app.route('/tenants/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def tenants_edit(id):
    tenant = Tenant.query.join(Room).filter(Room.user_id == current_user.id, Tenant.id == id).first_or_404()
    form = TenantForm(obj=tenant)
    
    # Populate room choices
    available_rooms = Room.query.filter_by(user_id=current_user.id, status='available').all()
    current_room = [tenant.room] if tenant.room else []
    all_rooms = available_rooms + current_room
    form.room_id.choices = [(r.id, f"Room {r.number} - ${r.monthly_rent}") for r in all_rooms]
    
    if form.validate_on_submit():
        old_room_id = tenant.room_id
        form.populate_obj(tenant)
        
        # Update room statuses if room changed
        if old_room_id != tenant.room_id:
            old_room = Room.query.get(old_room_id)
            if old_room:
                old_room.status = 'available'
            
            new_room = Room.query.get(tenant.room_id)
            new_room.status = 'occupied'
        
        db.session.commit()
        flash('Tenant updated successfully!', 'success')
        return redirect(url_for('tenants_index'))
    
    return render_template('tenants/form.html', form=form, title='Edit Tenant', tenant=tenant)

@app.route('/tenants/<int:id>/deactivate', methods=['POST'])
@login_required
def tenants_deactivate(id):
    tenant = Tenant.query.join(Room).filter(Room.user_id == current_user.id, Tenant.id == id).first_or_404()
    tenant.is_active = False
    tenant.end_date = date.today()
    
    # Update room status to available
    tenant.room.status = 'available'
    
    db.session.commit()
    flash('Tenant deactivated successfully!', 'success')
    return redirect(url_for('tenants_index'))

# Payment management
@app.route('/payments')
@login_required
def payments_index():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Payment.query.join(Room).filter(Room.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    
    payments = query.order_by(Payment.due_date.desc()).paginate(page=page, per_page=15, error_out=False)
    
    # Update payment statuses before displaying
    update_payment_status()
    
    return render_template('payments/index.html', payments=payments, status_filter=status_filter)

@app.route('/payments/new', methods=['GET', 'POST'])
@login_required
def payments_new():
    form = PaymentForm()
    
    # Populate choices with active tenants
    active_tenants = Tenant.query.join(Room).filter(
        Room.user_id == current_user.id,
        Tenant.is_active == True
    ).all()
    
    form.tenant_id.choices = [(t.id, f"{t.name} - Room {t.room.number}") for t in active_tenants]
    
    if form.validate_on_submit():
        tenant = Tenant.query.get(form.tenant_id.data)
        payment = Payment(
            amount=form.amount.data,
            due_date=form.due_date.data,
            status=form.status.data,
            notes=form.notes.data,
            room_id=tenant.room_id,
            tenant_id=tenant.id
        )
        
        if form.status.data == 'paid':
            payment.paid_date = form.paid_date.data or date.today()
        
        db.session.add(payment)
        db.session.commit()
        flash('Payment record created successfully!', 'success')
        return redirect(url_for('payments_index'))
    
    return render_template('payments/form.html', form=form, title='Add Payment Record')

@app.route('/payments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def payments_edit(id):
    payment = Payment.query.join(Room).filter(Room.user_id == current_user.id, Payment.id == id).first_or_404()
    form = PaymentForm(obj=payment)
    
    # Populate tenant choices
    active_tenants = Tenant.query.join(Room).filter(
        Room.user_id == current_user.id,
        Tenant.is_active == True
    ).all()
    form.tenant_id.choices = [(t.id, f"{t.name} - Room {t.room.number}") for t in active_tenants]
    
    if form.validate_on_submit():
        old_status = payment.status
        form.populate_obj(payment)
        
        # Handle status changes
        if payment.status == 'paid' and old_status != 'paid':
            payment.paid_date = form.paid_date.data or date.today()
        elif payment.status != 'paid':
            payment.paid_date = None
        
        db.session.commit()
        flash('Payment updated successfully!', 'success')
        return redirect(url_for('payments_index'))
    
    return render_template('payments/form.html', form=form, title='Edit Payment', payment=payment)

@app.route('/payments/<int:id>/mark_paid', methods=['POST'])
@login_required
def payments_mark_paid(id):
    payment = Payment.query.join(Room).filter(Room.user_id == current_user.id, Payment.id == id).first_or_404()
    payment.status = 'paid'
    payment.paid_date = date.today()
    db.session.commit()
    flash('Payment marked as paid!', 'success')
    return redirect(url_for('payments_index'))

# Financial Reports
@app.route('/reports/financial')
@login_required
def financial_reports():
    # Monthly revenue data for chart
    current_year = datetime.now().year
    monthly_data = []
    
    for month in range(1, 13):
        revenue = db.session.query(func.sum(Payment.amount)).join(Room).filter(
            Room.user_id == current_user.id,
            Payment.status == 'paid',
            extract('year', Payment.paid_date) == current_year,
            extract('month', Payment.paid_date) == month
        ).scalar() or 0
        
        expenses = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            extract('year', Expense.date) == current_year,
            extract('month', Expense.date) == month
        ).scalar() or 0
        
        monthly_data.append({
            'month': month,
            'revenue': float(revenue),
            'expenses': float(expenses),
            'profit': float(revenue - expenses)
        })
    
    # Recent expenses
    recent_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).limit(10).all()
    
    # Summary statistics
    total_revenue = db.session.query(func.sum(Payment.amount)).join(Room).filter(
        Room.user_id == current_user.id,
        Payment.status == 'paid'
    ).scalar() or 0
    
    total_expenses = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    
    return render_template('reports/financial.html',
                         monthly_data=monthly_data,
                         recent_expenses=recent_expenses,
                         total_revenue=total_revenue,
                         total_expenses=total_expenses)

@app.route('/expenses/new', methods=['GET', 'POST'])
@login_required
def expenses_new():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            description=form.description.data,
            amount=form.amount.data,
            category=form.category.data,
            date=form.date.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense recorded successfully!', 'success')
        return redirect(url_for('financial_reports'))
    
    return render_template('expenses/form.html', form=form, title='Add Expense')

# API endpoints for dashboard charts
@app.route('/api/dashboard/revenue-data')
@login_required
def api_revenue_data():
    # Last 6 months revenue data
    data = []
    for i in range(6):
        month_date = datetime.now().replace(day=1) - timedelta(days=i*30)
        revenue = db.session.query(func.sum(Payment.amount)).join(Room).filter(
            Room.user_id == current_user.id,
            Payment.status == 'paid',
            extract('year', Payment.paid_date) == month_date.year,
            extract('month', Payment.paid_date) == month_date.month
        ).scalar() or 0
        
        data.append({
            'month': month_date.strftime('%B'),
            'revenue': float(revenue)
        })
    
    return jsonify(list(reversed(data)))
