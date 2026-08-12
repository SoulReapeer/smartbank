"""
Email OTP Verification Service (replaces Phase 2 link-based verification).
- generate_otp_for_user(): creates a 6-digit OTP, saves it, sends email
- verify_otp(): validates user-submitted OTP and marks user as verified
"""
import random
import string
from datetime import datetime, timedelta
from models import db, EmailVerificationOTP

OTP_EXPIRY_MINUTES = 5


def _make_otp():
    return ''.join(random.choices(string.digits, k=6))


def generate_otp_for_user(user, base_url=None):
    """
    Invalidate any existing OTPs, generate a fresh one, save it, send email.
    Returns the OTP string (useful for tests; email prints to console in dev).
    """
    # Invalidate previous OTPs for this user
    EmailVerificationOTP.query.filter_by(user_id=user.id, used=False).update({'used': True})
    db.session.commit()

    otp = _make_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    record = EmailVerificationOTP(user_id=user.id, otp=otp, expires_at=expires_at)
    db.session.add(record)
    db.session.commit()

    from services.email_service import send_otp_email
    send_otp_email(user, otp, OTP_EXPIRY_MINUTES)
    return otp


def verify_otp(user, submitted_otp):
    """
    Check the most recent valid OTP for user.
    Returns (success: bool, error_message: str | None)
    """
    submitted_otp = submitted_otp.strip()
    record = (EmailVerificationOTP.query
              .filter_by(user_id=user.id, used=False)
              .order_by(EmailVerificationOTP.created_at.desc())
              .first())

    if not record:
        return False, "No verification code found. Please request a new one."
    if not record.is_valid():
        return False, "This code has expired. Please request a new one."
    if record.otp != submitted_otp:
        return False, "Incorrect code. Please try again."

    record.used = True
    user.is_verified = True
    user.verification_token = None   # clear legacy field
    db.session.commit()
    return True, None
