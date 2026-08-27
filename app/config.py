import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'narayana-lnd-lms-super-secret-key-2026')
    _db_url = os.environ.get('DATABASE_URL')
    if _db_url and _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url or f'sqlite:///{os.path.join(BASE_DIR, "lms.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENABLE_CONTENT_AUTHORING = os.environ.get('ENABLE_CONTENT_AUTHORING', 'True') == 'True'
    
    # Decoupled Storage Provider Configuration (MinIO / S3 compat)
    STORAGE_PROVIDER = os.environ.get('STORAGE_PROVIDER', 'local')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', '')
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', '')
    S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL', '')
    S3_BUCKET = os.environ.get('S3_BUCKET', 'narayana-lms')
    
    # Upload Directories
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    QR_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'qr_codes')
    CERT_FOLDER = os.path.join(BASE_DIR, 'uploads', 'certificates')
    MATERIALS_FOLDER = os.path.join(BASE_DIR, 'uploads', 'materials')
    
    # Maximum allowed payload size (50 MB for videos/PPT/PDF)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

    @staticmethod
    def init_app(app):
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.QR_FOLDER, exist_ok=True)
        os.makedirs(Config.CERT_FOLDER, exist_ok=True)
        os.makedirs(Config.MATERIALS_FOLDER, exist_ok=True)
