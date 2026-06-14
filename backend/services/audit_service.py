"""
Audit logging service.
Call log_action() from any route to record user activity.
"""
from models import db, AuditLog
from flask import request as flask_request


def log_action(user_id, action, details=None):
    """Record an audit log entry."""
    try:
        ip = flask_request.headers.get('X-Forwarded-For', flask_request.remote_addr)
        entry = AuditLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=ip
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        print(f"[AUDIT LOG ERROR] {e}")


# Action constants for consistency
LOGIN           = 'login'
LOGOUT          = 'logout'
REGISTER        = 'register'
EMAIL_VERIFIED  = 'email_verified'
PASSWORD_CHANGE = 'password_change'
PASSWORD_RESET  = 'password_reset'
DEPOSIT         = 'deposit'
WITHDRAWAL      = 'withdrawal'
TRANSFER        = 'transfer'
PROFILE_UPDATE  = 'profile_update'
ACCOUNT_FREEZE  = 'account_freeze'
ACCOUNT_UNFREEZE= 'account_unfreeze'
STATEMENT_DOWNLOAD = 'statement_download'
EXCEL_EXPORT    = 'excel_export'
