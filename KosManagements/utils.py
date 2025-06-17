import os
from datetime import date
from models import Payment
from app import db

def update_payment_status():
    """Update payment status based on due dates"""
    overdue_payments = Payment.query.filter(
        Payment.status == 'pending',
        Payment.due_date < date.today()
    ).all()
    
    for payment in overdue_payments:
        payment.status = 'overdue'
    
    db.session.commit()

def send_payment_reminder(tenant, payment):
    """
    Mock implementation for payment reminders
    In production, this would integrate with Twilio or SendGrid
    """
    # Mock notification - in production, implement actual email/SMS
    print(f"REMINDER: Payment of ${payment.amount} is due for {tenant.name} in Room {payment.room.number}")
    
    # Example Twilio integration (would require twilio package):
    # from twilio.rest import Client
    # client = Client(os.getenv('TWILIO_SID'), os.getenv('TWILIO_TOKEN'))
    # message = client.messages.create(
    #     body=f"Hi {tenant.name}, your rent payment of ${payment.amount} is due on {payment.due_date}",
    #     from_=os.getenv('TWILIO_PHONE'),
    #     to=tenant.phone
    # )
    
    # Example SendGrid integration (would require sendgrid package):
    # import sendgrid
    # from sendgrid.helpers.mail import Mail
    # sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
    # message = Mail(
    #     from_email='noreply@boardinghouse.com',
    #     to_emails=tenant.email,
    #     subject='Rent Payment Reminder',
    #     html_content=f'<p>Hi {tenant.name}, your rent payment of ${payment.amount} is due on {payment.due_date}</p>'
    # )
    # sg.send(message)

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"

def calculate_occupancy_rate(total_rooms, occupied_rooms):
    """Calculate occupancy rate percentage"""
    if total_rooms == 0:
        return 0
    return (occupied_rooms / total_rooms) * 100
