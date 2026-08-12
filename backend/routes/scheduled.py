from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, ScheduledTransfer, RecurringPayment, Account, TRANSACTION_CATEGORIES
from datetime import datetime

scheduled_bp = Blueprint('scheduled', __name__)


# ── Scheduled Transfers ────────────────────────────────────────────

@scheduled_bp.route('/scheduled-transfers')
@login_required
def scheduled_list():
    transfers = ScheduledTransfer.query.filter_by(sender_id=current_user.id) \
        .order_by(ScheduledTransfer.scheduled_date.asc()).all()
    return render_template('customer/scheduled_transfers.html',
                           transfers=transfers, categories=TRANSACTION_CATEGORIES)


@scheduled_bp.route('/scheduled-transfers/create', methods=['POST'])
@login_required
def scheduled_create():
    receiver_num   = request.form.get('receiver_account', '').strip()
    reference      = request.form.get('reference', '').strip()
    category       = request.form.get('category', 'Others')
    scheduled_date = request.form.get('scheduled_date', '')

    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        flash('Invalid amount.', 'danger')
        return redirect(url_for('scheduled.scheduled_list'))

    if amount <= 0:
        flash('Amount must be positive.', 'danger')
        return redirect(url_for('scheduled.scheduled_list'))

    try:
        sched_dt = datetime.strptime(scheduled_date, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid date/time.', 'danger')
        return redirect(url_for('scheduled.scheduled_list'))

    if sched_dt <= datetime.utcnow():
        flash('Scheduled date must be in the future.', 'danger')
        return redirect(url_for('scheduled.scheduled_list'))

    if receiver_num == current_user.account.account_number:
        flash('Cannot schedule transfer to yourself.', 'danger')
        return redirect(url_for('scheduled.scheduled_list'))

    receiver = Account.query.filter_by(account_number=receiver_num).first()
    if not receiver:
        flash('Receiver account not found.', 'danger')
        return redirect(url_for('scheduled.scheduled_list'))

    st = ScheduledTransfer(
        sender_id=current_user.id,
        receiver_account=receiver_num,
        amount=amount,
        reference=reference,
        category=category if category in TRANSACTION_CATEGORIES else 'Others',
        scheduled_date=sched_dt,
        status='pending'
    )
    db.session.add(st)
    db.session.commit()
    flash(f'Transfer of ৳{amount:,.2f} to {receiver_num} scheduled for '
          f'{sched_dt.strftime("%b %d, %Y %H:%M")}.', 'success')
    return redirect(url_for('scheduled.scheduled_list'))


@scheduled_bp.route('/scheduled-transfers/<int:tid>/cancel', methods=['POST'])
@login_required
def scheduled_cancel(tid):
    st = ScheduledTransfer.query.filter_by(id=tid, sender_id=current_user.id).first_or_404()
    if st.status != 'pending':
        flash('Only pending transfers can be cancelled.', 'warning')
    else:
        st.status = 'cancelled'
        db.session.commit()
        flash('Scheduled transfer cancelled.', 'success')
    return redirect(url_for('scheduled.scheduled_list'))


@scheduled_bp.route('/scheduled-transfers/<int:tid>/edit', methods=['POST'])
@login_required
def scheduled_edit(tid):
    st = ScheduledTransfer.query.filter_by(id=tid, sender_id=current_user.id).first_or_404()
    if st.status != 'pending':
        flash('Only pending transfers can be edited.', 'warning')
        return redirect(url_for('scheduled.scheduled_list'))

    try:
        amount = float(request.form.get('amount', st.amount))
    except ValueError:
        amount = st.amount

    scheduled_date = request.form.get('scheduled_date', '')
    try:
        sched_dt = datetime.strptime(scheduled_date, '%Y-%m-%dT%H:%M')
        if sched_dt <= datetime.utcnow():
            flash('Scheduled date must be in the future.', 'danger')
            return redirect(url_for('scheduled.scheduled_list'))
        st.scheduled_date = sched_dt
    except ValueError:
        pass

    st.amount    = amount if amount > 0 else st.amount
    st.reference = request.form.get('reference', st.reference)
    st.category  = request.form.get('category', st.category)
    db.session.commit()
    flash('Scheduled transfer updated.', 'success')
    return redirect(url_for('scheduled.scheduled_list'))


# ── Recurring Payments ─────────────────────────────────────────────

@scheduled_bp.route('/recurring-payments')
@login_required
def recurring_list():
    payments = RecurringPayment.query.filter_by(sender_id=current_user.id) \
        .order_by(RecurringPayment.next_payment.asc()).all()
    return render_template('customer/recurring_payments.html',
                           payments=payments, categories=TRANSACTION_CATEGORIES)


@scheduled_bp.route('/recurring-payments/create', methods=['POST'])
@login_required
def recurring_create():
    receiver_num = request.form.get('receiver_account', '').strip()
    reference    = request.form.get('reference', '').strip()
    category     = request.form.get('category', 'Others')
    frequency    = request.form.get('frequency', 'monthly')
    start_date   = request.form.get('start_date', '')

    try:
        amount = float(request.form.get('amount', 0))
    except ValueError:
        flash('Invalid amount.', 'danger')
        return redirect(url_for('scheduled.recurring_list'))

    if amount <= 0:
        flash('Amount must be positive.', 'danger')
        return redirect(url_for('scheduled.recurring_list'))

    if frequency not in ('daily', 'weekly', 'monthly', 'yearly'):
        flash('Invalid frequency.', 'danger')
        return redirect(url_for('scheduled.recurring_list'))

    try:
        first_payment = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    except ValueError:
        flash('Invalid start date.', 'danger')
        return redirect(url_for('scheduled.recurring_list'))

    if first_payment <= datetime.utcnow():
        flash('Start date must be in the future.', 'danger')
        return redirect(url_for('scheduled.recurring_list'))

    if receiver_num == current_user.account.account_number:
        flash('Cannot set up recurring payment to yourself.', 'danger')
        return redirect(url_for('scheduled.recurring_list'))

    receiver = Account.query.filter_by(account_number=receiver_num).first()
    if not receiver:
        flash('Receiver account not found.', 'danger')
        return redirect(url_for('scheduled.recurring_list'))

    rp = RecurringPayment(
        sender_id=current_user.id,
        receiver_account=receiver_num,
        amount=amount,
        reference=reference,
        category=category if category in TRANSACTION_CATEGORIES else 'Others',
        frequency=frequency,
        next_payment=first_payment,
        status='active'
    )
    db.session.add(rp)
    db.session.commit()
    flash(f'Recurring {frequency} payment of ৳{amount:,.2f} to {receiver_num} created.', 'success')
    return redirect(url_for('scheduled.recurring_list'))


@scheduled_bp.route('/recurring-payments/<int:pid>/pause', methods=['POST'])
@login_required
def recurring_pause(pid):
    rp = RecurringPayment.query.filter_by(id=pid, sender_id=current_user.id).first_or_404()
    if rp.status == 'active':
        rp.status = 'paused'
        db.session.commit()
        flash('Recurring payment paused.', 'warning')
    return redirect(url_for('scheduled.recurring_list'))


@scheduled_bp.route('/recurring-payments/<int:pid>/resume', methods=['POST'])
@login_required
def recurring_resume(pid):
    rp = RecurringPayment.query.filter_by(id=pid, sender_id=current_user.id).first_or_404()
    if rp.status == 'paused':
        rp.status = 'active'
        db.session.commit()
        flash('Recurring payment resumed.', 'success')
    return redirect(url_for('scheduled.recurring_list'))


@scheduled_bp.route('/recurring-payments/<int:pid>/cancel', methods=['POST'])
@login_required
def recurring_cancel(pid):
    rp = RecurringPayment.query.filter_by(id=pid, sender_id=current_user.id).first_or_404()
    if rp.status != 'cancelled':
        rp.status = 'cancelled'
        db.session.commit()
        flash('Recurring payment cancelled.', 'success')
    return redirect(url_for('scheduled.recurring_list'))


@scheduled_bp.route('/recurring-payments/<int:pid>/edit', methods=['POST'])
@login_required
def recurring_edit(pid):
    rp = RecurringPayment.query.filter_by(id=pid, sender_id=current_user.id).first_or_404()
    if rp.status == 'cancelled':
        flash('Cannot edit a cancelled payment.', 'warning')
        return redirect(url_for('scheduled.recurring_list'))
    try:
        amount = float(request.form.get('amount', rp.amount))
        rp.amount = amount if amount > 0 else rp.amount
    except ValueError:
        pass
    rp.reference = request.form.get('reference', rp.reference)
    rp.category  = request.form.get('category', rp.category)
    db.session.commit()
    flash('Recurring payment updated.', 'success')
    return redirect(url_for('scheduled.recurring_list'))
