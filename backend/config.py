import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smartbank-dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, '..', 'database', 'banking.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email
    MAIL_SERVER   = os.environ.get('MAIL_SERVER',   '')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_FROM     = os.environ.get('MAIL_FROM',     'noreply@smartbank.com')

    # Profile picture uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'profile_pictures')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024   # 2 MB
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}
