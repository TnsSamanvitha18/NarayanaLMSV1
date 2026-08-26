from app import create_app
from app.models import db
from app.models.user import AdminUser

app = create_app()

with app.app_context():
    admin = AdminUser.query.filter_by(username='admin').first()
    if admin:
        print(f"Admin found. Current password_hash: {admin.password_hash}")
        # Update the password with secure hash
        admin.set_password('admin')
        db.session.commit()
        print(f"Updated password hash securely. New hash: {admin.password_hash}")
    else:
        print("Admin user not found. Seeding new admin...")
        admin = AdminUser(username='admin')
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("Seeded new admin user.")
