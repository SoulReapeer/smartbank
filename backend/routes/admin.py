from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Account, Transaction
from functools import wraps

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
    total_users = User.query.filter_by(role='customer').count()
    total_accounts = Account.query.count()
    total_transactions = Transaction.query.count()
    total_funds = db.session.query(db.func.sum(Account.balance)).scalar() or 0
    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_accounts=total_accounts,
                           total_transactions=total_transactions,
                           total_funds=total_funds)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.filter_by(role='customer').join(Account).all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/freeze/<int:user_id>')
@login_required
@admin_required
def freeze(user_id):
    user = User.query.get_or_404(user_id)
    if user.account:
        user.account.status = 'frozen'
        db.session.commit()
        flash(f'Account {user.account.account_number} has been frozen.', 'warning')
    return redirect(url_for('admin.users'))

@admin_bp.route('/unfreeze/<int:user_id>')
@login_required
@admin_required
def unfreeze(user_id):
    user = User.query.get_or_404(user_id)
    if user.account:
        user.account.status = 'active'
        db.session.commit()
        flash(f'Account {user.account.account_number} has been unfrozen.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/transactions')
@login_required
@admin_required
def transactions():
    tx_type = request.args.get('type', '')
    search = request.args.get('search', '').strip()
    query = Transaction.query
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
