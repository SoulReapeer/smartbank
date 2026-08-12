from models import db, Notification

DEPOSIT           = 'deposit'
WITHDRAWAL        = 'withdrawal'
TRANSFER_SENT     = 'transfer_sent'
TRANSFER_RECEIVED = 'transfer_received'
PASSWORD_CHANGED  = 'password_changed'
ACCOUNT_FROZEN    = 'account_frozen'
ACCOUNT_UNFROZEN  = 'account_unfrozen'


def create_notification(user_id, title, message, ntype='info'):
    try:
        note = Notification(user_id=user_id, title=title, message=message, type=ntype)
        db.session.add(note)
        db.session.commit()
        return note
    except Exception as e:
        print(f"[NOTIFICATION ERROR] {e}")
        db.session.rollback()
        return None


def _safe_email(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except Exception as e:
        print(f"[EMAIL NOTIFY ERROR] {e}")


def notify_deposit(user, account, amount):
    msg = f"Your deposit of ৳{amount:,.2f} was successful. Current balance: ৳{account.balance:,.2f}."
    create_notification(user.id, "Deposit Successful", msg, DEPOSIT)
    from services.email_service import send_transaction_email
    _safe_email(send_transaction_email, user, "Deposit Successful", msg, 'deposit')


def notify_withdrawal(user, account, amount):
    msg = f"You withdrew ৳{amount:,.2f}. Current balance: ৳{account.balance:,.2f}."
    create_notification(user.id, "Withdrawal Successful", msg, WITHDRAWAL)
    from services.email_service import send_transaction_email
    _safe_email(send_transaction_email, user, "Withdrawal Successful", msg, 'withdrawal')


def notify_transfer_sent(user, account, amount, receiver_account_number):
    msg = f"You sent ৳{amount:,.2f} to {receiver_account_number}. Current balance: ৳{account.balance:,.2f}."
    create_notification(user.id, "Transfer Successful", msg, TRANSFER_SENT)
    from services.email_service import send_transaction_email
    _safe_email(send_transaction_email, user, "Transfer Successful", msg, 'transfer_sent')


def notify_transfer_received(user, account, amount, sender_account_number):
    msg = f"You received ৳{amount:,.2f} from {sender_account_number}. Current balance: ৳{account.balance:,.2f}."
    create_notification(user.id, "Money Received", msg, TRANSFER_RECEIVED)
    from services.email_service import send_transaction_email
    _safe_email(send_transaction_email, user, "Money Received", msg, 'transfer_received')


def notify_password_changed(user):
    msg = "Your account password was changed successfully. If this wasn't you, contact support immediately."
    create_notification(user.id, "Password Changed", msg, PASSWORD_CHANGED)
    from services.email_service import send_transaction_email
    _safe_email(send_transaction_email, user, "Password Changed", msg, 'password_changed')


def notify_account_frozen(user, account):
    msg = f"Your account {account.account_number} has been frozen by an administrator."
    create_notification(user.id, "Account Frozen", msg, ACCOUNT_FROZEN)
    from services.email_service import send_transaction_email
    _safe_email(send_transaction_email, user, "Account Frozen", msg, 'account_frozen')


def notify_account_unfrozen(user, account):
    msg = f"Your account {account.account_number} has been unfrozen and is active again."
    create_notification(user.id, "Account Unfrozen", msg, ACCOUNT_UNFROZEN)
    from services.email_service import send_transaction_email
    _safe_email(send_transaction_email, user, "Account Unfrozen", msg, 'account_unfrozen')
