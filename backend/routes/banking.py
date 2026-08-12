from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from models import db, Account, Transaction, User, Beneficiary, TRANSACTION_CATEGORIES
from services.audit_service import log_action
import services.audit_service as A
import services.notification_service as N
import io

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
            tx = Transaction(receiver_account=account.account_number,
                             transaction_type='deposit', amount=amount,
                             reference=f'Deposit to {account.account_number}',
                             category='Others')
            db.session.add(tx)
            db.session.commit()
            log_action(current_user.id, A.DEPOSIT, f'Deposited ৳{amount:.2f}')
            N.notify_deposit(current_user, account, amount)
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
            return render_template('customer/withdraw.html', account=account,
                                   categories=TRANSACTION_CATEGORIES)
        category = request.form.get('category', 'Others')
        if amount <= 0:
            flash('Amount must be positive.', 'danger')
        elif not account.is_active_account():
            flash('Your account is frozen. Contact support.', 'danger')
        elif amount > account.balance:
            flash('Insufficient balance.', 'danger')
        else:
            account.balance -= amount
            tx = Transaction(sender_account=account.account_number,
                             transaction_type='withdrawal', amount=amount,
                             reference=f'Withdrawal from {account.account_number}',
                             category=category if category in TRANSACTION_CATEGORIES else 'Others')
            db.session.add(tx)
            db.session.commit()
            log_action(current_user.id, A.WITHDRAWAL, f'Withdrew ৳{amount:.2f}')
            N.notify_withdrawal(current_user, account, amount)
            flash(f'Successfully withdrew ৳{amount:,.2f}.', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('customer/withdraw.html', account=account,
                           categories=TRANSACTION_CATEGORIES)


@banking_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    account = current_user.account
    my_beneficiaries = Beneficiary.query.filter_by(user_id=current_user.id) \
        .order_by(Beneficiary.nickname).all()
    if request.method == 'POST':
        receiver_num = request.form.get('receiver_account', '').strip()
        reference    = request.form.get('reference', '').strip()
        category     = request.form.get('category', 'Others')
        try:
            amount = float(request.form.get('amount', 0))
        except ValueError:
            flash('Invalid amount.', 'danger')
            return render_template('customer/transfer.html', account=account,
                                   beneficiaries=my_beneficiaries,
                                   categories=TRANSACTION_CATEGORIES)
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
                account.balance  -= amount
                receiver.balance += amount
                tx = Transaction(
                    sender_account=account.account_number,
                    receiver_account=receiver_num,
                    transaction_type='transfer', amount=amount,
                    reference=reference or f'Transfer to {receiver_num}',
                    category=category if category in TRANSACTION_CATEGORIES else 'Others'
                )
                db.session.add(tx)
                db.session.commit()
                log_action(current_user.id, A.TRANSFER,
                           f'Transferred ৳{amount:.2f} to {receiver_num}')
                N.notify_transfer_sent(current_user, account, amount, receiver_num)
                if receiver.user:
                    N.notify_transfer_received(receiver.user, receiver, amount,
                                               account.account_number)
                flash(f'Successfully transferred ৳{amount:,.2f} to {receiver_num}.', 'success')
                return redirect(url_for('dashboard.index'))
    return render_template('customer/transfer.html', account=account,
                           beneficiaries=my_beneficiaries,
                           categories=TRANSACTION_CATEGORIES)


@banking_bp.route('/transfer/qr-decode', methods=['POST'])
@login_required
def qr_decode():
    from services.qr_service import decode_qr_image
    if 'qr_image' not in request.files or request.files['qr_image'].filename == '':
        return {'success': False, 'error': 'No file uploaded.'}, 400
    file = request.files['qr_image']
    allowed_ext = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
    if not any(file.filename.lower().endswith(e) for e in allowed_ext):
        return {'success': False, 'error': 'Invalid file type.'}, 400
    account_number, error = decode_qr_image(file.stream)
    if error:
        return {'success': False, 'error': error}, 400
    if account_number == current_user.account.account_number:
        return {'success': False, 'error': 'Cannot transfer to your own account.'}, 400
    receiver = Account.query.filter_by(account_number=account_number).first()
    if not receiver:
        return {'success': False, 'error': f'No account found for {account_number}.'}, 404
    return {
        'success': True,
        'account_number': receiver.account_number,
        'receiver_name': receiver.user.full_name if receiver.user else 'Unknown',
        'status': receiver.status,
        'is_active': receiver.is_active_account(),
    }


@banking_bp.route('/transactions')
@login_required
def transactions():
    account  = current_user.account
    tx_type  = request.args.get('type', '')
    search   = request.args.get('search', '').strip()
    category = request.args.get('category', '')
    query    = Transaction.query.filter(
        (Transaction.sender_account == account.account_number) |
        (Transaction.receiver_account == account.account_number)
    )
    if tx_type in ('deposit', 'withdrawal', 'transfer'):
        query = query.filter_by(transaction_type=tx_type)
    if search:
        query = query.filter(Transaction.reference.ilike(f'%{search}%'))
    if category in TRANSACTION_CATEGORIES:
        query = query.filter_by(category=category)
    txs = query.order_by(Transaction.timestamp.desc()).all()
    return render_template('customer/transactions.html', transactions=txs, account=account,
                           tx_type=tx_type, search=search, category=category,
                           categories=TRANSACTION_CATEGORIES)


@banking_bp.route('/statement/pdf')
@login_required
def download_pdf():
    from services.pdf_service import generate_statement
    account = current_user.account
    txs = Transaction.query.filter(
        (Transaction.sender_account == account.account_number) |
        (Transaction.receiver_account == account.account_number)
    ).order_by(Transaction.timestamp.desc()).all()
    pdf_bytes = generate_statement(current_user, account, txs)
    log_action(current_user.id, A.STATEMENT_DOWNLOAD,
               f'PDF statement for {account.account_number}')
    return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'SmartBank_Statement_{account.account_number}.pdf')


@banking_bp.route('/statement/excel')
@login_required
def download_excel():
    from services.excel_service import generate_excel
    account = current_user.account
    txs = Transaction.query.filter(
        (Transaction.sender_account == account.account_number) |
        (Transaction.receiver_account == account.account_number)
    ).order_by(Transaction.timestamp.desc()).all()
    xlsx_bytes, fname = generate_excel(txs, account_number=account.account_number,
                                       filename_prefix=f'SmartBank_{account.account_number}')
    log_action(current_user.id, A.EXCEL_EXPORT,
               f'Excel export for {account.account_number}')
    return send_file(io.BytesIO(xlsx_bytes),
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=fname)


@banking_bp.route('/qr-code')
@login_required
def my_qr_code():
    from services.qr_service import generate_qr_for_account
    png = generate_qr_for_account(current_user.account.account_number)
    return send_file(io.BytesIO(png), mimetype='image/png')


@banking_bp.route('/qr-code/download')
@login_required
def download_qr_code():
    from services.qr_service import generate_qr_for_account
    acc = current_user.account
    png = generate_qr_for_account(acc.account_number)
    return send_file(io.BytesIO(png), mimetype='image/png', as_attachment=True,
                     download_name=f'SmartBank_QR_{acc.account_number}.png')
