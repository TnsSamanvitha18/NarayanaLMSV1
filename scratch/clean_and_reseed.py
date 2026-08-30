import os
import sys

# Adjust paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db
from app.seed import init_db_and_seed

def clean_and_reseed():
    app = create_app()
    with app.app_context():
        print("Dropping all tables to ensure clean slate...")
        db.drop_all()
        print("Recreating database tables...")
        db.create_all()
        print("Triggering database seed...")
        # Since init_db_and_seed has an admin check, it will seed
        init_db_and_seed(app)
        print("Clean reseed completed successfully!")

if __name__ == '__main__':
    clean_and_reseed()
