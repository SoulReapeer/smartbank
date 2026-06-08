from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import Transaction

dashboard_bp = Blueprint('dashboard', __name__)

def get_stats(account_number):
    all_tx = Transaction.query.filter(
        (Transaction.sender_account == account_number) |
        (Transaction.receiver_account == account_number)
    ).all()
    deposits = sum(t.amount for t in all_tx if t.transaction_type == 'deposit' and t.receiver_account == account_number)
    withdrawals = sum(t.amount for t in all_tx if t.transaction_type == 'withdrawal' and t.sender_account == account_number)
    transfers_out = sum(t.amount for t in all_tx if t.transaction_type == 'transfer' and t.sender_account == account_number)
    return deposits, withdrawals, transfers_out

@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.is_admin():
        return redirect(url_for('admin.index'))
    account = current_user.account
    recent = Transaction.query.filter(
        (Transaction.sender_account == account.account_number) |
        (Transaction.receiver_account == account.account_number)
    ).order_by(Transaction.timestamp.desc()).limit(5).all()
    deposits, withdrawals, transfers = get_stats(account.account_number)
    return render_template('customer/dashboard.html',
                           account=account,
                           recent=recent,
                           deposits=deposits,
                           withdrawals=withdrawals,
                           transfers=transfers)

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from flask import request, flash
    from models import db
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        if full_name:
            current_user.full_name = full_name
        if phone:
            current_user.phone = phone
        db.session.commit()
        flash('Profile updated.', 'success')
    return render_template('customer/profile.html', user=current_user, account=current_user.account)
