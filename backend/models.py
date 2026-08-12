from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='customer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Phase 2
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(128), nullable=True)   # kept for migration compat

    # Phase 4
    profile_image = db.Column(db.String(256), nullable=True)

    account = db.relationship('Account', backref='user', uselist=False)
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')
    reset_tokens = db.relationship('PasswordResetToken', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    beneficiaries = db.relationship('Beneficiary', backref='user',
                                    foreign_keys='Beneficiary.user_id', lazy='dynamic')
    scheduled_transfers = db.relationship('ScheduledTransfer', backref='sender',
                                          foreign_keys='ScheduledTransfer.sender_id', lazy='dynamic')
    recurring_payments = db.relationship('RecurringPayment', backref='sender',
                                         foreign_keys='RecurringPayment.sender_id', lazy='dynamic')
    email_otps = db.relationship('EmailVerificationOTP', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def avatar_url(self):
        if self.profile_image:
            return f'/static/uploads/profile_pictures/{self.profile_image}'
        return None

    def initials(self):
        parts = self.full_name.strip().split()
        if len(parts) >= 2:
            return parts[0][0].upper() + parts[-1][0].upper()
        return parts[0][0].upper() if parts else '?'


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(10), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_active_account(self):
        return self.status == 'active'


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    sender_account = db.Column(db.String(20), nullable=True)
    receiver_account = db.Column(db.String(20), nullable=True)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reference = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Phase 4
    category = db.Column(db.String(30), nullable=True, default='Others')


TRANSACTION_CATEGORIES = [
    'Food', 'Shopping', 'Bills', 'Education', 'Medical',
    'Travel', 'Entertainment', 'Investment', 'Others'
]


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(30), nullable=False, default='info')
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── Phase 4 Models ────────────────────────────────────────────────

class EmailVerificationOTP(db.Model):
    __tablename__ = 'email_verification_otps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at


class Beneficiary(db.Model):
    __tablename__ = 'beneficiaries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    beneficiary_account = db.Column(db.String(20), nullable=False)
    nickname = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'beneficiary_account', name='uq_user_beneficiary'),
    )


class ScheduledTransfer(db.Model):
    __tablename__ = 'scheduled_transfers'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_account = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reference = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(30), nullable=True, default='Others')
    scheduled_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(15), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # status: pending | completed | cancelled | failed


class RecurringPayment(db.Model):
    __tablename__ = 'recurring_payments'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_account = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reference = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(30), nullable=True, default='Others')
    frequency = db.Column(db.String(10), nullable=False)   # daily|weekly|monthly|yearly
    next_payment = db.Column(db.DateTime, nullable=False)
    last_payment = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(10), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # status: active | paused | cancelled
