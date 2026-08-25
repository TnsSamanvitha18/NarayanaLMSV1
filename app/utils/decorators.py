from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in') and not session.get('super_admin_logged_in'):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('super_admin_logged_in'):
            flash("Access denied: Please log in as an IT Super Administrator to access this page.", "danger")
            return redirect(url_for('super_admin.login'))
        return f(*args, **kwargs)
    return decorated_function
