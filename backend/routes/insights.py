from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.insights_service import get_insights

insights_bp = Blueprint('insights', __name__)

@insights_bp.route('/insights')
@login_required
def index():
    data = get_insights(current_user.account.account_number)
    return render_template('customer/insights.html', **data)
