from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Transaction
from services.audit_service import log_action
import services.audit_service as A

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    if current_user.is_admin():
        return redirect(url_for('admin.index'))
    account = current_user.account
    acc_num = account.account_number

    all_tx = Transaction.query.filter(
        (Transaction.sender_account == acc_num) |
        (Transaction.receiver_account == acc_num)
    ).order_by(Transaction.timestamp.desc()).all()

    recent      = all_tx[:5]
    deposits    = sum(t.amount for t in all_tx if t.transaction_type == 'deposit')
    withdrawals = sum(t.amount for t in all_tx
                      if t.transaction_type == 'withdrawal' and t.sender_account == acc_num)
    transfers   = sum(t.amount for t in all_tx
                      if t.transaction_type == 'transfer' and t.sender_account == acc_num)

    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    now = datetime.utcnow()

    monthly_labels, monthly_counts = [], []
    for i in range(5, -1, -1):
        ms = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
              - relativedelta(months=i))
        me = ms + relativedelta(months=1)
        count = Transaction.query.filter(
            ((Transaction.sender_account == acc_num) |
             (Transaction.receiver_account == acc_num)),
            Transaction.timestamp >= ms,
            Transaction.timestamp < me
        ).count()
        monthly_labels.append(ms.strftime('%b'))
        monthly_counts.append(count)

    balance_labels, balance_values = [], []
    running = account.balance
    for tx in reversed(all_tx[:10]):
        if tx.transaction_type == 'deposit':
            running -= tx.amount
        elif tx.transaction_type == 'withdrawal' and tx.sender_account == acc_num:
            running += tx.amount
        elif tx.transaction_type == 'transfer' and tx.sender_account == acc_num:
            running += tx.amount
        elif tx.transaction_type == 'transfer' and tx.receiver_account == acc_num:
            running -= tx.amount
        balance_labels.insert(0, tx.timestamp.strftime('%b %d'))
        balance_values.insert(0, round(running, 2))
    balance_labels.append('Now')
    balance_values.append(round(account.balance, 2))

    return render_template('customer/dashboard.html',
                           account=account, recent=recent,
                           deposits=deposits, withdrawals=withdrawals, transfers=transfers,
                           monthly_labels=monthly_labels, monthly_counts=monthly_counts,
                           balance_labels=balance_labels, balance_values=balance_values)


@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action', 'update')

        if action == 'upload_image':
            file = request.files.get('profile_image')
            from services.profile_image_service import save_profile_image, delete_profile_image
            filename, error = save_profile_image(file)
            if error:
                flash(error, 'danger')
            else:
                if current_user.profile_image:
                    delete_profile_image(current_user.profile_image)
                current_user.profile_image = filename
                db.session.commit()
                log_action(current_user.id, A.PROFILE_UPDATE, 'Profile picture updated')
                flash('Profile picture updated.', 'success')

        elif action == 'remove_image':
            from services.profile_image_service import delete_profile_image
            if current_user.profile_image:
                delete_profile_image(current_user.profile_image)
                current_user.profile_image = None
                db.session.commit()
                flash('Profile picture removed.', 'success')

        else:
            full_name = request.form.get('full_name', '').strip()
            phone     = request.form.get('phone', '').strip()
            if full_name:
                current_user.full_name = full_name
            if phone:
                current_user.phone = phone
            db.session.commit()
            log_action(current_user.id, A.PROFILE_UPDATE, 'Profile updated')
            flash('Profile updated.', 'success')

    return render_template('customer/profile.html',
                           user=current_user, account=current_user.account)
