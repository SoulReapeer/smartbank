import secrets, random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Account, PasswordResetToken
from services.audit_service import log_action
import services.audit_service as A

auth_bp = Blueprint('auth', __name__)

def generate_account_number():
    year = datetime.utcnow().year
    rand = random.randint(1000, 9999)
    return f"ACC{year}{rand}"

# ── Register ──────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        if not all([full_name, email, phone, password, confirm]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        user = User(full_name=full_name, email=email, phone=phone, is_verified=False)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        acc_num = generate_account_number()
        while Account.query.filter_by(account_number=acc_num).first():
            acc_num = generate_account_number()
        account = Account(user_id=user.id, account_number=acc_num)
        db.session.add(account)
        db.session.commit()

        from services.otp_service import generate_otp_for_user
        generate_otp_for_user(user)
        log_action(user.id, A.REGISTER, f'New registration: {email}')

        # Store user_id in session so /verify-otp knows who to verify
        session['otp_user_id'] = user.id
        flash('Account created! Check your email (or terminal) for your 6-digit verification code.', 'success')
        return redirect(url_for('auth.verify_otp'))
    return render_template('auth/register.html')

# ── Verify OTP ────────────────────────────────────────────────────
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user_id = session.get('otp_user_id')
    if not user_id:
        flash('Session expired. Please register or log in again.', 'warning')
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.register'))

    if user.is_verified:
        session.pop('otp_user_id', None)
        flash('Your email is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        submitted = request.form.get('otp', '').strip()
        from services.otp_service import verify_otp as svc_verify
        success, error = svc_verify(user, submitted)
        if success:
            session.pop('otp_user_id', None)
            log_action(user.id, A.EMAIL_VERIFIED, f'Email verified via OTP: {user.email}')
            flash('Email verified! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        flash(error, 'danger')

    return render_template('auth/verify_otp.html', email=user.email)

# ── Resend OTP ────────────────────────────────────────────────────
@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    user_id = session.get('otp_user_id')
    if not user_id:
        flash('Session expired. Please register again.', 'warning')
        return redirect(url_for('auth.register'))
    user = User.query.get(user_id)
    if user and not user.is_verified:
        from services.otp_service import generate_otp_for_user
        generate_otp_for_user(user)
        flash('A new verification code has been sent.', 'info')
    return redirect(url_for('auth.verify_otp'))

# ── Legacy: resend-verification (redirect to OTP flow) ────────────
@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Kept for backward compat with Phase 2/3 links."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()
        if user and not user.is_verified:
            from services.otp_service import generate_otp_for_user
            generate_otp_for_user(user)
            session['otp_user_id'] = user.id
            return redirect(url_for('auth.verify_otp'))
        flash('If that email is registered and unverified, a code has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/resend_verification.html')

# ── Legacy verify-email link (graceful fallback) ──────────────────
@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    flash('Email verification now uses a 6-digit code. Please check your email for the code.', 'info')
    return redirect(url_for('auth.login'))

# ── Login ─────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index') if current_user.is_admin() else url_for('dashboard.index'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_verified and not user.is_admin():
                session['otp_user_id'] = user.id
                from services.otp_service import generate_otp_for_user
                generate_otp_for_user(user)
                flash('Please verify your email. A new code has been sent.', 'warning')
                return redirect(url_for('auth.verify_otp'))
            login_user(user)
            log_action(user.id, A.LOGIN, f'Login from {request.remote_addr}')
            return redirect(url_for('admin.index') if user.is_admin() else url_for('dashboard.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html')

# ── Logout ────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    log_action(current_user.id, A.LOGOUT)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# ── Change Password ───────────────────────────────────────────────
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_pw = request.form.get('current_password', '')
        new_pw     = request.form.get('new_password', '')
        confirm    = request.form.get('confirm_password', '')
        if not current_user.check_password(current_pw):
            flash('Current password is incorrect.', 'danger')
        elif new_pw != confirm:
            flash('New passwords do not match.', 'danger')
        elif len(new_pw) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            log_action(current_user.id, A.PASSWORD_CHANGE)
            import services.notification_service as N
            N.notify_password_changed(current_user)
            flash('Password changed successfully.', 'success')
            return redirect(url_for('dashboard.profile'))
    return render_template('auth/change_password.html')

# ── Forgot Password ───────────────────────────────────────────────
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()
        if user:
            PasswordResetToken.query.filter_by(user_id=user.id, used=False).update({'used': True})
            token   = secrets.token_urlsafe(48)
            expires = datetime.utcnow() + timedelta(hours=1)
            prt     = PasswordResetToken(user_id=user.id, token=token, expires_at=expires)
            db.session.add(prt)
            db.session.commit()
            from services.email_service import send_password_reset_email
            base_url = request.host_url.rstrip('/')
            send_password_reset_email(user, token, base_url)
        flash('If that email is registered, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')

# ── Reset Password ────────────────────────────────────────────────
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    prt = PasswordResetToken.query.filter_by(token=token).first()
    if not prt or not prt.is_valid():
        flash('This reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        new_pw  = request.form.get('new_password', '')
        confirm = request.form.get('confirm_password', '')
        if new_pw != confirm:
            flash('Passwords do not match.', 'danger')
        elif len(new_pw) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        else:
            prt.user.set_password(new_pw)
            prt.used = True
            db.session.commit()
            log_action(prt.user_id, A.PASSWORD_RESET, 'Password reset via email link')
            flash('Password reset successfully. Please log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', token=token)
