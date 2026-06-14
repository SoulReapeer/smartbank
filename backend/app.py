from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db, User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.banking import banking_bp
    from routes.admin import admin_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(banking_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)

    @app.route('/')
    def landing():
        return render_template('landing.html')

    return app

app = create_app()

if __name__ == '__main__':
    import os
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'database'), exist_ok=True)
    with app.app_context():
        db.create_all()
        from models import User, Account
        # Admin — pre-verified
        if not User.query.filter_by(email='admin@smartbank.com').first():
            admin = User(full_name='SmartBank Admin', email='admin@smartbank.com',
                        phone='01700000000', role='admin', is_verified=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        else:
            # Ensure existing admin is verified
            a = User.query.filter_by(email='admin@smartbank.com').first()
            if not a.is_verified:
                a.is_verified = True
                db.session.commit()
        # Demo customer — pre-verified
        demo = User.query.filter_by(email='demo@smartbank.com').first()
        if demo and not demo.is_verified:
            demo.is_verified = True
            db.session.commit()
    app.run(debug=True)
