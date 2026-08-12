"""
Scheduler Service — APScheduler-based job runner.
Processes due scheduled transfers and recurring payments.
Call init_scheduler(app) from app.py after app creation.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

_scheduler = None


def _process_scheduled_transfers(app):
    from datetime import datetime
    with app.app_context():
        from models import db, ScheduledTransfer, Account, Transaction, User
        import services.notification_service as N
        from services.audit_service import log_action
        import services.audit_service as A

        now = datetime.utcnow()
        due = ScheduledTransfer.query.filter(
            ScheduledTransfer.status == 'pending',
            ScheduledTransfer.scheduled_date <= now
        ).all()

        for st in due:
            sender = User.query.get(st.sender_id)
            if not sender or not sender.account:
                st.status = 'failed'
                db.session.commit()
                continue

            sender_acc = sender.account
            receiver_acc = Account.query.filter_by(account_number=st.receiver_account).first()

            fail_reason = None
            if not receiver_acc:
                fail_reason = "Receiver account not found."
            elif not receiver_acc.is_active_account():
                fail_reason = "Receiver account is frozen."
            elif not sender_acc.is_active_account():
                fail_reason = "Sender account is frozen."
            elif sender_acc.balance < st.amount:
                fail_reason = "Insufficient balance."

            if fail_reason:
                st.status = 'failed'
                db.session.commit()
                N.create_notification(sender.id, "Scheduled Transfer Failed",
                                      f"Scheduled transfer of ৳{st.amount:,.2f} to "
                                      f"{st.receiver_account} failed: {fail_reason}",
                                      'account_frozen')
                log_action(sender.id, 'scheduled_transfer_failed',
                           f"ID {st.id}: {fail_reason}")
                continue

            # Execute
            sender_acc.balance -= st.amount
            receiver_acc.balance += st.amount
            tx = Transaction(
                sender_account=sender_acc.account_number,
                receiver_account=st.receiver_account,
                transaction_type='transfer',
                amount=st.amount,
                reference=(st.reference or f'Scheduled transfer to {st.receiver_account}'),
                category=st.category or 'Others'
            )
            db.session.add(tx)
            st.status = 'completed'
            db.session.commit()

            N.notify_transfer_sent(sender, sender_acc, st.amount, st.receiver_account)
            if receiver_acc.user:
                N.notify_transfer_received(receiver_acc.user, receiver_acc,
                                           st.amount, sender_acc.account_number)
            log_action(sender.id, A.TRANSFER,
                       f"Scheduled transfer ৳{st.amount:.2f} → {st.receiver_account}")


def _process_recurring_payments(app):
    from datetime import datetime
    with app.app_context():
        from dateutil.relativedelta import relativedelta
        from models import db, RecurringPayment, Account, Transaction, User
        import services.notification_service as N
        from services.audit_service import log_action
        import services.audit_service as A

        now = datetime.utcnow()
        due = RecurringPayment.query.filter(
            RecurringPayment.status == 'active',
            RecurringPayment.next_payment <= now
        ).all()

        for rp in due:
            sender = User.query.get(rp.sender_id)
            if not sender or not sender.account:
                continue

            sender_acc = sender.account
            receiver_acc = Account.query.filter_by(account_number=rp.receiver_account).first()

            def _advance_next(rp, from_date):
                freq = rp.frequency
                if freq == 'daily':
                    return from_date + relativedelta(days=1)
                elif freq == 'weekly':
                    return from_date + relativedelta(weeks=1)
                elif freq == 'monthly':
                    return from_date + relativedelta(months=1)
                elif freq == 'yearly':
                    return from_date + relativedelta(years=1)
                return from_date + relativedelta(months=1)

            fail_reason = None
            if not receiver_acc:
                fail_reason = "Receiver account not found."
            elif not receiver_acc.is_active_account():
                fail_reason = "Receiver account is frozen."
            elif not sender_acc.is_active_account():
                fail_reason = "Sender account is frozen."
            elif sender_acc.balance < rp.amount:
                fail_reason = "Insufficient balance."

            if fail_reason:
                rp.next_payment = _advance_next(rp, now)
                db.session.commit()
                N.create_notification(sender.id, "Recurring Payment Failed",
                                      f"Recurring payment of ৳{rp.amount:,.2f} to "
                                      f"{rp.receiver_account} failed: {fail_reason}",
                                      'account_frozen')
                log_action(sender.id, 'recurring_payment_failed',
                           f"ID {rp.id}: {fail_reason}")
                continue

            sender_acc.balance -= rp.amount
            receiver_acc.balance += rp.amount
            tx = Transaction(
                sender_account=sender_acc.account_number,
                receiver_account=rp.receiver_account,
                transaction_type='transfer',
                amount=rp.amount,
                reference=(rp.reference or f'Recurring payment to {rp.receiver_account}'),
                category=rp.category or 'Others'
            )
            db.session.add(tx)
            rp.last_payment = now
            rp.next_payment = _advance_next(rp, now)
            db.session.commit()

            N.notify_transfer_sent(sender, sender_acc, rp.amount, rp.receiver_account)
            if receiver_acc.user:
                N.notify_transfer_received(receiver_acc.user, receiver_acc,
                                           rp.amount, sender_acc.account_number)
            log_action(sender.id, A.TRANSFER,
                       f"Recurring payment ৳{rp.amount:.2f} → {rp.receiver_account}")


def init_scheduler(app):
    """Start the background scheduler. Called once from app factory."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        func=lambda: _process_scheduled_transfers(app),
        trigger=IntervalTrigger(minutes=1),
        id='scheduled_transfers',
        replace_existing=True
    )
    _scheduler.add_job(
        func=lambda: _process_recurring_payments(app),
        trigger=IntervalTrigger(minutes=1),
        id='recurring_payments',
        replace_existing=True
    )
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
