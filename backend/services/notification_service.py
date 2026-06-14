"""
Hybrid Notification Service
- create_notification(): saves an in-app notification (always succeeds independently)
- notify_*(): convenience helpers for each transaction type — create in-app notification
               AND attempt to send an email. Email failure never blocks the transaction.
"""
from models import db, Notification

# Notification type constants
DEPOSIT            = 'deposit'
WITHDRAWAL         = 'withdrawal'
TRANSFER_SENT      = 'transfer_sent'
TRANSFER_RECEIVED  = 'transfer_received'
PASSWORD_CHANGED   = 'password_changed'
ACCOUNT_FROZEN     = 'account_frozen'
ACCOUNT_UNFROZEN   = 'account_unfrozen'


def create_notification(user_id, title, message, ntype='info'):
    """Create an in-app notification. Always safe — never raises."""
    try:
        note = Notification(user_id=user_id, title=title, message=message, type=ntype)
        db.session.add(note)
        db.session.commit()
        return note
    except Exception as e:
        print(f"[NOTIFICATION ERROR] {e}")
        db.session.rollback()
        return None


def _safe_send_email(send_fn, *args, **kwargs):
    """Wrap email sending so failures never break the request."""
    try:
        send_fn(*args, **kwargs)
    except Exception as e:
        print(f"[EMAIL NOTIFY ERROR] {e}")


# ── Transaction-specific notification helpers ──────────────────────

def notify_deposit(user, account, amount):
    title = "Deposit Successful"
    msg = f"Your deposit of ৳{amount:,.2f} was successful. Current balance: ৳{account.balance:,.2f}."
    create_notification(user.id, title, msg, DEPOSIT)

    from services.email_service import send_transaction_email
    _safe_send_email(send_transaction_email, user, title, msg, 'deposit')


def notify_withdrawal(user, account, amount):
    title = "Withdrawal Successful"
    msg = f"You withdrew ৳{amount:,.2f}. Current balance: ৳{account.balance:,.2f}."
    create_notification(user.id, title, msg, WITHDRAWAL)

    from services.email_service import send_transaction_email
    _safe_send_email(send_transaction_email, user, title, msg, 'withdrawal')


def notify_transfer_sent(user, account, amount, receiver_account_number):
    title = "Transfer Successful"
    msg = f"You sent ৳{amount:,.2f} to {receiver_account_number}. Current balance: ৳{account.balance:,.2f}."
    create_notification(user.id, title, msg, TRANSFER_SENT)

    from services.email_service import send_transaction_email
    _safe_send_email(send_transaction_email, user, title, msg, 'transfer_sent')


def notify_transfer_received(user, account, amount, sender_account_number):
    title = "Money Received"
    msg = f"You received ৳{amount:,.2f} from {sender_account_number}. Current balance: ৳{account.balance:,.2f}."
    create_notification(user.id, title, msg, TRANSFER_RECEIVED)

    from services.email_service import send_transaction_email
    _safe_send_email(send_transaction_email, user, title, msg, 'transfer_received')


def notify_password_changed(user):
    title = "Password Changed"
    msg = "Your account password was changed successfully. If this wasn't you, contact support immediately."
    create_notification(user.id, title, msg, PASSWORD_CHANGED)

    from services.email_service import send_transaction_email
    _safe_send_email(send_transaction_email, user, title, msg, 'password_changed')


def notify_account_frozen(user, account):
    title = "Account Frozen"
    msg = f"Your account {account.account_number} has been frozen by an administrator. Contact support for assistance."
    create_notification(user.id, title, msg, ACCOUNT_FROZEN)

    from services.email_service import send_transaction_email
    _safe_send_email(send_transaction_email, user, title, msg, 'account_frozen')


def notify_account_unfrozen(user, account):
    title = "Account Unfrozen"
    msg = f"Your account {account.account_number} has been unfrozen and is active again."
    create_notification(user.id, title, msg, ACCOUNT_UNFROZEN)

    from services.email_service import send_transaction_email
    _safe_send_email(send_transaction_email, user, title, msg, 'account_unfrozen')
