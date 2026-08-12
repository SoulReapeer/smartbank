"""
Spending Insights Engine.
Computes per-user spending analytics for the Insights Dashboard.
"""
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from models import Transaction, TRANSACTION_CATEGORIES


def get_insights(account_number):
    """
    Returns a dict of spending insight data for a customer account.
    """
    now = datetime.utcnow()
    # Current month window
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Previous month window
    if month_start.month == 1:
        prev_month_start = month_start.replace(year=month_start.year - 1, month=12)
    else:
        prev_month_start = month_start.replace(month=month_start.month - 1)

    # ── Spending transactions = outgoing (withdrawal + transfer sent) ───
    def outgoing(txs):
        return [t for t in txs if (
            t.transaction_type == 'withdrawal' and t.sender_account == account_number
        ) or (
            t.transaction_type == 'transfer' and t.sender_account == account_number
        )]

    all_tx = Transaction.query.filter(
        (Transaction.sender_account == account_number) |
        (Transaction.receiver_account == account_number)
    ).order_by(Transaction.timestamp.desc()).all()

    this_month_out = outgoing([t for t in all_tx if t.timestamp >= month_start])
    prev_month_out = outgoing([t for t in all_tx
                                if prev_month_start <= t.timestamp < month_start])

    total_monthly_spending = sum(t.amount for t in this_month_out)
    prev_monthly_spending  = sum(t.amount for t in prev_month_out)

    largest_expense = max((t.amount for t in this_month_out), default=0)

    all_amounts = [t.amount for t in outgoing(all_tx)]
    avg_transaction = round(sum(all_amounts) / len(all_amounts), 2) if all_amounts else 0

    # Category breakdown this month
    cat_totals = defaultdict(float)
    for t in this_month_out:
        cat = t.category or 'Others'
        cat_totals[cat] += t.amount

    most_used_category = max(cat_totals, key=cat_totals.get) if cat_totals else 'N/A'

    # Most frequent recipient (transfer only)
    transfers_out = [t for t in all_tx
                     if t.transaction_type == 'transfer' and t.sender_account == account_number]
    recipient_counts = Counter(t.receiver_account for t in transfers_out)
    most_frequent_recipient = recipient_counts.most_common(1)[0][0] if recipient_counts else 'N/A'

    # Monthly spending trend — last 6 months
    monthly_labels, monthly_spending = [], []
    from dateutil.relativedelta import relativedelta
    for i in range(5, -1, -1):
        ms = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
              - relativedelta(months=i))
        me = ms + relativedelta(months=1)
        spent = sum(t.amount for t in outgoing(
            [t for t in all_tx if ms <= t.timestamp < me]
        ))
        monthly_labels.append(ms.strftime('%b'))
        monthly_spending.append(round(spent, 2))

    # Category chart data
    cat_labels = list(TRANSACTION_CATEGORIES)
    cat_amounts = [round(cat_totals.get(c, 0), 2) for c in cat_labels]

    # Smart insight messages
    insights = []
    if cat_totals:
        insights.append(f"Your highest spending category this month is <strong>{most_used_category}</strong>.")
    if prev_monthly_spending > 0:
        diff = total_monthly_spending - prev_monthly_spending
        pct  = abs(round(diff / prev_monthly_spending * 100, 1))
        if diff > 0:
            insights.append(f"Spending is up <strong>{pct}%</strong> compared to last month.")
        elif diff < 0:
            insights.append(f"Great job! Spending is down <strong>{pct}%</strong> vs last month. 🎉")
        else:
            insights.append("Spending is the same as last month.")
    if largest_expense > 0:
        insights.append(f"Your largest transaction this month was <strong>৳{largest_expense:,.2f}</strong>.")

    # Monthly savings estimate (income - spending this month)
    income_this_month = sum(
        t.amount for t in all_tx
        if t.timestamp >= month_start and (
            (t.transaction_type == 'deposit') or
            (t.transaction_type == 'transfer' and t.receiver_account == account_number)
        )
    )
    monthly_savings = round(income_this_month - total_monthly_spending, 2)

    if income_this_month > 0:
        pct_spent = round(total_monthly_spending / income_this_month * 100, 1)
        insights.append(f"You have spent <strong>{pct_spent}%</strong> of your income this month.")

    return {
        'total_monthly_spending':   round(total_monthly_spending, 2),
        'largest_expense':          round(largest_expense, 2),
        'avg_transaction':          avg_transaction,
        'most_used_category':       most_used_category,
        'most_frequent_recipient':  most_frequent_recipient,
        'monthly_savings':          monthly_savings,
        'monthly_labels':           monthly_labels,
        'monthly_spending':         monthly_spending,
        'cat_labels':               cat_labels,
        'cat_amounts':              cat_amounts,
        'smart_insights':           insights,
    }
