from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Notification

notifications_bp = Blueprint('notifications', __name__)


# ── Full notifications page ────────────────────────────────────────
@notifications_bp.route('/notifications')
@login_required
def index():
    search = request.args.get('search', '').strip()
    page   = request.args.get('page', 1, type=int)
    per_page = 15

    query = Notification.query.filter_by(user_id=current_user.id)
    if search:
        query = query.filter(
            (Notification.title.ilike(f'%{search}%')) |
            (Notification.message.ilike(f'%{search}%'))
        )
    pagination = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template('customer/notifications.html',
                           notifications=pagination.items,
                           pagination=pagination,
                           search=search,
                           unread_count=unread_count)


# ── Mark all as read ────────────────────────────────────────────────
@notifications_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))


# ── Mark single notification as read ────────────────────────────────
@notifications_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    return redirect(url_for('notifications.index'))


# ── AJAX: bell dropdown data ─────────────────────────────────────────
@notifications_bp.route('/api/notifications')
@login_required
def api_notifications():
    """Returns recent notifications + unread count for the navbar bell dropdown."""
    recent = Notification.query.filter_by(user_id=current_user.id) \
        .order_by(Notification.created_at.desc()).limit(6).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return jsonify({
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.type,
                'is_read': n.is_read,
                'time': n.created_at.strftime('%b %d, %H:%M'),
            }
            for n in recent
        ]
    })
