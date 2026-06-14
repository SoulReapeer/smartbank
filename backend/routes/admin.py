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

# ── Dashboard ─────────────────────────────────────────────────────
@admin_bp.route('/')
@login_required
@admin_required
def index():
    from datetime import datetime, timedelta
    from sqlalchemy import func

    total_users        = User.query.filter_by(role='customer').count()
    verified_users     = User.query.filter_by(role='customer', is_verified=True).count()
    total_accounts     = Account.query.count()
    active_accounts    = Account.query.filter_by(status='active').count()
    total_transactions = Transaction.query.count()
    total_funds        = db.session.query(func.sum(Account.balance)).scalar() or 0

    total_deposits    = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'deposit').scalar() or 0
    total_withdrawals = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'withdrawal').scalar() or 0

    today = datetime.utcnow().date()
    todays_transactions = Transaction.query.filter(
        func.date(Transaction.timestamp) == today
    ).count()

    # Daily transactions last 14 days
    daily_labels, daily_counts = [], []
    for i in range(13, -1, -1):
        day   = datetime.utcnow().date() - timedelta(days=i)
        count = Transaction.query.filter(
            func.date(Transaction.timestamp) == day
        ).count()
        daily_labels.append(day.strftime('%b %d'))
        daily_counts.append(count)

    # Monthly deposits & withdrawals last 6 months
    monthly_labels, monthly_deposits, monthly_withdrawals = [], [], []
    for i in range(5, -1, -1):
        from dateutil.relativedelta import relativedelta
        month_start = (datetime.utcnow().replace(day=1) - relativedelta(months=i))
        month_end   = month_start + relativedelta(months=1)
        label       = month_start.strftime('%b %Y')
        dep  = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_type == 'deposit',
            Transaction.timestamp >= month_start,
            Transaction.timestamp < month_end
        ).scalar() or 0
        wdraw = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.transaction_type == 'withdrawal',
            Transaction.timestamp >= month_start,
            Transaction.timestamp < month_end
        ).scalar() or 0
        monthly_labels.append(label)
        monthly_deposits.append(round(dep, 2))
        monthly_withdrawals.append(round(wdraw, 2))

    # User registrations per month (last 6)
    reg_counts = []
    for i in range(5, -1, -1):
        from dateutil.relativedelta import relativedelta
        month_start = (datetime.utcnow().replace(day=1) - relativedelta(months=i))
        month_end   = month_start + relativedelta(months=1)
        count = User.query.filter(
            User.role == 'customer',
            User.created_at >= month_start,
            User.created_at < month_end
        ).count()
        reg_counts.append(count)

    # ── Most Active Customers (top 10 by transaction count) ─────────
    most_active = []
    accounts_with_users = Account.query.join(User).filter(User.role == 'customer').all()
    for acc in accounts_with_users:
        tx_count = Transaction.query.filter(
            (Transaction.sender_account == acc.account_number) |
            (Transaction.receiver_account == acc.account_number)
        ).count()
        if tx_count > 0:
            most_active.append({
                'name': acc.user.full_name,
                'account_number': acc.account_number,
                'tx_count': tx_count
            })
    most_active.sort(key=lambda x: x['tx_count'], reverse=True)
    most_active = most_active[:10]

    # ── Largest Transfers (top 10) ───────────────────────────────────
    largest_transfers = Transaction.query.filter_by(transaction_type='transfer') \
        .order_by(Transaction.amount.desc()).limit(10).all()

    # Resolve sender/receiver names for largest transfers
    largest_transfers_data = []
    for tx in largest_transfers:
        sender_acc   = Account.query.filter_by(account_number=tx.sender_account).first()
        receiver_acc = Account.query.filter_by(account_number=tx.receiver_account).first()
        largest_transfers_data.append({
            'sender_account': tx.sender_account,
            'sender_name': sender_acc.user.full_name if sender_acc and sender_acc.user else 'Unknown',
            'receiver_account': tx.receiver_account,
            'receiver_name': receiver_acc.user.full_name if receiver_acc and receiver_acc.user else 'Unknown',
            'amount': tx.amount,
            'timestamp': tx.timestamp
        })

    # ── Top Customer Activity Chart (top 5 names + counts) ───────────
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
        reg_counts=reg_counts,
        most_active=most_active,
        largest_transfers=largest_transfers_data,
        top_customer_labels=top_customer_labels,
        top_customer_counts=top_customer_counts)

# ── Users ─────────────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.filter_by(role='customer').all()
    return render_template('admin/users.html', users=all_users)

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
                   f'Froze account {user.account.account_number} (user {user.email})')
        N.notify_account_frozen(user, user.account)
        flash(f'Account {user.account.account_number} has been frozen.', 'warning')
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
                   f'Unfroze account {user.account.account_number} (user {user.email})')
        N.notify_account_unfrozen(user, user.account)
        flash(f'Account {user.account.account_number} has been unfrozen.', 'success')
    return redirect(url_for('admin.users'))

# ── Transactions ──────────────────────────────────────────────────
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

# ── Audit Logs ────────────────────────────────────────────────────
@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    search  = request.args.get('search', '').strip()
    action  = request.args.get('action', '')
    page    = request.args.get('page', 1, type=int)
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
        page=page, per_page=per_page, error_out=False
    )
    # Distinct action types for filter dropdown
    action_types = [r[0] for r in db.session.query(AuditLog.action).distinct().all()]
    return render_template('admin/audit_logs.html',
                           logs=pagination.items, pagination=pagination,
                           action_types=action_types,
                           search=search, action=action)

# ── Admin Excel Export ────────────────────────────────────────────
@admin_bp.route('/export/excel')
@login_required
@admin_required
def export_excel():
    from services.excel_service import generate_excel
    txs = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    xlsx_bytes, fname = generate_excel(txs, filename_prefix='SmartBank_AllTransactions')
    return send_file(
        io.BytesIO(xlsx_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=fname
    )
