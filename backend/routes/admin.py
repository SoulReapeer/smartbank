from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from models import db, User, Account, Transaction, AuditLog
from functools import wraps
import io

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@login_required
@admin_required
def index():
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from dateutil.relativedelta import relativedelta

    total_users        = User.query.filter_by(role='customer').count()
    verified_users     = User.query.filter_by(role='customer', is_verified=True).count()
    total_accounts     = Account.query.count()
    active_accounts    = Account.query.filter_by(status='active').count()
    total_transactions = Transaction.query.count()
    total_funds        = db.session.query(func.sum(Account.balance)).scalar() or 0
    total_deposits     = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'deposit').scalar() or 0
    total_withdrawals  = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'withdrawal').scalar() or 0

    today = datetime.utcnow().date()
    todays_transactions = Transaction.query.filter(
        func.date(Transaction.timestamp) == today
    ).count()

    daily_labels, daily_counts = [], []
    for i in range(13, -1, -1):
        day   = datetime.utcnow().date() - timedelta(days=i)
        count = Transaction.query.filter(func.date(Transaction.timestamp) == day).count()
        daily_labels.append(day.strftime('%b %d'))
        daily_counts.append(count)

    monthly_labels, monthly_deposits, monthly_withdrawals = [], [], []
    reg_counts = []
    for i in range(5, -1, -1):
        ms = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0) \
             - relativedelta(months=i)
        me = ms + relativedelta(months=1)
        dep  = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_type == 'deposit',
            Transaction.timestamp >= ms, Transaction.timestamp < me).scalar() or 0
        wdraw = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_type == 'withdrawal',
            Transaction.timestamp >= ms, Transaction.timestamp < me).scalar() or 0
        reg = User.query.filter(User.role == 'customer',
                                User.created_at >= ms, User.created_at < me).count()
        monthly_labels.append(ms.strftime('%b %Y'))
        monthly_deposits.append(round(dep, 2))
        monthly_withdrawals.append(round(wdraw, 2))
        reg_counts.append(reg)

    most_active = []
    for acc in Account.query.join(User).filter(User.role == 'customer').all():
        cnt = Transaction.query.filter(
            (Transaction.sender_account == acc.account_number) |
            (Transaction.receiver_account == acc.account_number)
        ).count()
        if cnt > 0:
            most_active.append({'name': acc.user.full_name,
                                'account_number': acc.account_number, 'tx_count': cnt})
    most_active.sort(key=lambda x: x['tx_count'], reverse=True)
    most_active = most_active[:10]

    largest_transfers = []
    for tx in Transaction.query.filter_by(transaction_type='transfer') \
            .order_by(Transaction.amount.desc()).limit(10).all():
        sa = Account.query.filter_by(account_number=tx.sender_account).first()
        ra = Account.query.filter_by(account_number=tx.receiver_account).first()
        largest_transfers.append({
            'sender_account':   tx.sender_account,
            'sender_name':      sa.user.full_name if sa and sa.user else 'Unknown',
            'receiver_account': tx.receiver_account,
            'receiver_name':    ra.user.full_name if ra and ra.user else 'Unknown',
            'amount':           tx.amount,
            'timestamp':        tx.timestamp,
        })

    top_customer_labels = [c['name'].split()[0] for c in most_active[:5]]
    top_customer_counts = [c['tx_count'] for c in most_active[:5]]

    return render_template('admin/dashboard.html',
        total_users=total_users, verified_users=verified_users,
        total_accounts=total_accounts, active_accounts=active_accounts,
        total_transactions=total_transactions, total_funds=total_funds,
        total_deposits=total_deposits, total_withdrawals=total_withdrawals,
        todays_transactions=todays_transactions,
        daily_labels=daily_labels, daily_counts=daily_counts,
        monthly_labels=monthly_labels,
        monthly_deposits=monthly_deposits, monthly_withdrawals=monthly_withdrawals,
        reg_counts=reg_counts, most_active=most_active,
        largest_transfers=largest_transfers,
        top_customer_labels=top_customer_labels,
        top_customer_counts=top_customer_counts)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.filter_by(role='customer').all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/verify-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def manual_verify(user_id):
    """Admin can manually mark a user as verified."""
    user = User.query.get_or_404(user_id)
    if not user.is_verified:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        from services.audit_service import log_action
        log_action(current_user.id, 'admin_manual_verify',
                   f'Manually verified user {user.email}')
        flash(f'{user.email} has been manually verified.', 'success')
    else:
        flash(f'{user.email} is already verified.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/freeze/<int:user_id>')
@login_required
@admin_required
def freeze(user_id):
    from services.audit_service import log_action
    import services.audit_service as A
    import services.notification_service as N
    user = User.query.get_or_404(user_id)
    if user.account:
        user.account.status = 'frozen'
        db.session.commit()
        log_action(current_user.id, A.ACCOUNT_FREEZE,
                   f'Froze account {user.account.account_number}')
        N.notify_account_frozen(user, user.account)
        flash(f'Account {user.account.account_number} frozen.', 'warning')
    return redirect(url_for('admin.users'))


@admin_bp.route('/unfreeze/<int:user_id>')
@login_required
@admin_required
def unfreeze(user_id):
    from services.audit_service import log_action
    import services.audit_service as A
    import services.notification_service as N
    user = User.query.get_or_404(user_id)
    if user.account:
        user.account.status = 'active'
        db.session.commit()
        log_action(current_user.id, A.ACCOUNT_UNFREEZE,
                   f'Unfroze account {user.account.account_number}')
        N.notify_account_unfrozen(user, user.account)
        flash(f'Account {user.account.account_number} unfrozen.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/transactions')
@login_required
@admin_required
def transactions():
    tx_type = request.args.get('type', '')
    search  = request.args.get('search', '').strip()
    query   = Transaction.query
    if tx_type in ('deposit', 'withdrawal', 'transfer'):
        query = query.filter_by(transaction_type=tx_type)
    if search:
        query = query.filter(
            (Transaction.sender_account.ilike(f'%{search}%')) |
            (Transaction.receiver_account.ilike(f'%{search}%')) |
            (Transaction.reference.ilike(f'%{search}%'))
        )
    txs = query.order_by(Transaction.timestamp.desc()).all()
    return render_template('admin/transactions.html', transactions=txs,
                           tx_type=tx_type, search=search)


@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    search   = request.args.get('search', '').strip()
    action   = request.args.get('action', '')
    page     = request.args.get('page', 1, type=int)
    per_page = 25
    query = AuditLog.query
    if action:
        query = query.filter_by(action=action)
    if search:
        query = query.filter(
            (AuditLog.details.ilike(f'%{search}%')) |
            (AuditLog.ip_address.ilike(f'%{search}%'))
        )
    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    action_types = [r[0] for r in db.session.query(AuditLog.action).distinct().all()]
    return render_template('admin/audit_logs.html',
                           logs=pagination.items, pagination=pagination,
                           action_types=action_types, search=search, action=action)


@admin_bp.route('/export/excel')
@login_required
@admin_required
def export_excel():
    from services.excel_service import generate_excel
    txs = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    xlsx_bytes, fname = generate_excel(txs, filename_prefix='SmartBank_AllTransactions')
    return send_file(io.BytesIO(xlsx_bytes),
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=fname)
