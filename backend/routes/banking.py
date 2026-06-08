from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Account, Transaction

banking_bp = Blueprint('banking', __name__)

@banking_bp.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    account = current_user.account
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return render_template('customer/deposit.html', account=account)
        if amount <= 0:
            flash('Amount must be positive.', 'danger')
        elif not account.is_active_account():
            flash('Your account is frozen. Contact support.', 'danger')
        else:
            account.balance += amount
            tx = Transaction(
                receiver_account=account.account_number,
                transaction_type='deposit',
                amount=amount,
                reference=f'Deposit to {account.account_number}'
            )
            db.session.add(tx)
            db.session.commit()
            flash(f'Successfully deposited ৳{amount:,.2f}.', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('customer/deposit.html', account=account)

@banking_bp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    account = current_user.account
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return render_template('customer/withdraw.html', account=account)
        if amount <= 0:
            flash('Amount must be positive.', 'danger')
        elif not account.is_active_account():
            flash('Your account is frozen. Contact support.', 'danger')
        elif amount > account.balance:
            flash('Insufficient balance.', 'danger')
        else:
            account.balance -= amount
            tx = Transaction(
                sender_account=account.account_number,
                transaction_type='withdrawal',
                amount=amount,
                reference=f'Withdrawal from {account.account_number}'
            )
            db.session.add(tx)
            db.session.commit()
            flash(f'Successfully withdrew ৳{amount:,.2f}.', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('customer/withdraw.html', account=account)

@banking_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    account = current_user.account
    if request.method == 'POST':
        receiver_num = request.form.get('receiver_account', '').strip()
        reference = request.form.get('reference', '').strip()
        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return render_template('customer/transfer.html', account=account)

        if amount <= 0:
            flash('Amount must be positive.', 'danger')
        elif not account.is_active_account():
            flash('Your account is frozen.', 'danger')
        elif receiver_num == account.account_number:
            flash('Cannot transfer to your own account.', 'danger')
        elif amount > account.balance:
            flash('Insufficient balance.', 'danger')
        else:
            receiver = Account.query.filter_by(account_number=receiver_num).first()
            if not receiver:
                flash('Receiver account not found.', 'danger')
            elif not receiver.is_active_account():
                flash('Receiver account is frozen.', 'danger')
            else:
                account.balance -= amount
                receiver.balance += amount
                tx = Transaction(
                    sender_account=account.account_number,
                    receiver_account=receiver_num,
                    transaction_type='transfer',
                    amount=amount,
                    reference=reference or f'Transfer to {receiver_num}'
                )
                db.session.add(tx)
                db.session.commit()
                flash(f'Successfully transferred ৳{amount:,.2f} to {receiver_num}.', 'success')
                return redirect(url_for('dashboard.index'))
    return render_template('customer/transfer.html', account=account)

@banking_bp.route('/transactions')
@login_required
def transactions():
    account = current_user.account
    tx_type = request.args.get('type', '')
    search = request.args.get('search', '').strip()

    query = Transaction.query.filter(
        (Transaction.sender_account == account.account_number) |
        (Transaction.receiver_account == account.account_number)
    )
    if tx_type in ('deposit', 'withdrawal', 'transfer'):
        query = query.filter_by(transaction_type=tx_type)
    if search:
        query = query.filter(Transaction.reference.ilike(f'%{search}%'))

    txs = query.order_by(Transaction.timestamp.desc()).all()
    return render_template('customer/transactions.html', transactions=txs, account=account,
                           tx_type=tx_type, search=search)
