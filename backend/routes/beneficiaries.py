from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Beneficiary, Account

beneficiaries_bp = Blueprint('beneficiaries', __name__)


@beneficiaries_bp.route('/beneficiaries')
@login_required
def index():
    search = request.args.get('search', '').strip()
    q = Beneficiary.query.filter_by(user_id=current_user.id)
    if search:
        q = q.filter(
            (Beneficiary.nickname.ilike(f'%{search}%')) |
            (Beneficiary.beneficiary_account.ilike(f'%{search}%'))
        )
    bens = q.order_by(Beneficiary.nickname).all()
    # Enrich with account owner names
    enriched = []
    for b in bens:
        acc = Account.query.filter_by(account_number=b.beneficiary_account).first()
        enriched.append({
            'id': b.id,
            'nickname': b.nickname,
            'account': b.beneficiary_account,
            'owner': acc.user.full_name if acc and acc.user else 'Unknown',
            'status': acc.status if acc else 'unknown',
        })
    return render_template('customer/beneficiaries.html', beneficiaries=enriched, search=search)


@beneficiaries_bp.route('/beneficiaries/add', methods=['POST'])
@login_required
def add():
    acc_num  = request.form.get('beneficiary_account', '').strip()
    nickname = request.form.get('nickname', '').strip()

    if not acc_num or not nickname:
        flash('Account number and nickname are required.', 'danger')
        return redirect(url_for('beneficiaries.index'))
    if acc_num == current_user.account.account_number:
        flash('You cannot add your own account as a beneficiary.', 'danger')
        return redirect(url_for('beneficiaries.index'))

    acc = Account.query.filter_by(account_number=acc_num).first()
    if not acc:
        flash('Account not found.', 'danger')
        return redirect(url_for('beneficiaries.index'))

    existing = Beneficiary.query.filter_by(
        user_id=current_user.id, beneficiary_account=acc_num
    ).first()
    if existing:
        flash('This account is already in your beneficiaries.', 'warning')
        return redirect(url_for('beneficiaries.index'))

    ben = Beneficiary(user_id=current_user.id, beneficiary_account=acc_num, nickname=nickname)
    db.session.add(ben)
    db.session.commit()
    flash(f'Beneficiary "{nickname}" added.', 'success')
    return redirect(url_for('beneficiaries.index'))


@beneficiaries_bp.route('/beneficiaries/<int:bid>/edit', methods=['POST'])
@login_required
def edit(bid):
    ben = Beneficiary.query.filter_by(id=bid, user_id=current_user.id).first_or_404()
    nickname = request.form.get('nickname', '').strip()
    if not nickname:
        flash('Nickname cannot be empty.', 'danger')
    else:
        ben.nickname = nickname
        db.session.commit()
        flash('Beneficiary updated.', 'success')
    return redirect(url_for('beneficiaries.index'))


@beneficiaries_bp.route('/beneficiaries/<int:bid>/delete', methods=['POST'])
@login_required
def delete(bid):
    ben = Beneficiary.query.filter_by(id=bid, user_id=current_user.id).first_or_404()
    db.session.delete(ben)
    db.session.commit()
    flash('Beneficiary removed.', 'success')
    return redirect(url_for('beneficiaries.index'))


@beneficiaries_bp.route('/api/beneficiaries')
@login_required
def api_list():
    """JSON list — used by the Transfer page beneficiary picker."""
    bens = Beneficiary.query.filter_by(user_id=current_user.id).order_by(Beneficiary.nickname).all()
    result = []
    for b in bens:
        acc = Account.query.filter_by(account_number=b.beneficiary_account).first()
        result.append({
            'id': b.id,
            'nickname': b.nickname,
            'account': b.beneficiary_account,
            'owner': acc.user.full_name if acc and acc.user else 'Unknown',
            'is_active': acc.is_active_account() if acc else False,
        })
    return jsonify(result)
