from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import AdminUser, Learner

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard.index'))
    return redirect(url_for('auth.admin_login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('dashboard.index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin = AdminUser.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_logged_in'] = True
            session['admin_username'] = admin.username
            flash('Successfully logged in as L&D Administrator.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            error = "Invalid Username or Password"

    return render_template('auth/admin_login.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.admin_login'))


@auth_bp.route('/learner/login', methods=['GET', 'POST'])
def learner_login():
    """
    Learner Login endpoint.
    URL format: http://localhost:5000/learner/login?classId=xxxxx
    Later this endpoint will be replaced by Google SSO.
    """
    class_id_str = request.args.get('classId') or request.form.get('class_id', '')
    course_id_str = request.args.get('courseId') or request.form.get('course_id', '')
    
    error = None
    if request.method == 'POST':
        global_id = request.form.get('global_id', '').strip()
        password = request.form.get('password', '').strip()
        class_id_str = request.form.get('class_id', '').strip() or class_id_str
        course_id_str = request.form.get('course_id', '').strip() or course_id_str

        if not global_id:
            error = "Please enter your Global ID."
        else:
            # Map learner01-learner05 aliases to 10001-10005
            alias_map = {
                'learner01': '10001',
                'learner02': '10002',
                'learner03': '10003',
                'learner04': '10004',
                'learner05': '10005',
            }
            target_gid = alias_map.get(global_id.lower(), global_id)

            # Find Learner in database
            learner = Learner.query.filter(
                (Learner.global_id == target_gid) | (Learner.global_id == global_id)
            ).first()

            if not learner:
                # Case-insensitive fallback lookup
                learner = Learner.query.filter(
                    (Learner.global_id.ilike(target_gid)) | (Learner.global_id.ilike(global_id))
                ).first()

            if not learner:
                error = f"Learner with Global ID '{global_id}' not found. Please use a valid learner login (e.g., 10001)."
            else:
                session['learner_id'] = learner.id
                session['learner_global_id'] = learner.global_id
                session['learner_name'] = learner.name

                # Daily Streak Logic
                from datetime import date, timedelta
                from app.models import db
                from app.utils.gamification import award_points, award_badge
                
                today = date.today()
                if not learner.last_active_date:
                    learner.current_streak = 1
                    learner.last_active_date = today
                    award_points(learner.id, 10, "First Daily Login")
                else:
                    if learner.last_active_date == today:
                        # Already logged in today
                        pass
                    elif learner.last_active_date == today - timedelta(days=1):
                        learner.current_streak += 1
                        learner.last_active_date = today
                        points_to_award = min(learner.current_streak * 5, 50)
                        award_points(learner.id, points_to_award, f"{learner.current_streak}-Day Login Streak")
                        if learner.current_streak >= 5:
                            award_badge(learner.id, "Streak Master 🔥", "fa-fire", "Logged in for 5 consecutive days!")
                    else:
                        learner.current_streak = 1
                        learner.last_active_date = today
                        award_points(learner.id, 10, "Daily Login (Streak Reset)")
                
                db.session.commit()

                flash(f"Welcome, {learner.name}!", "success")

                if class_id_str:
                    return redirect(url_for('learners.class_flow', class_id_str=class_id_str))
                elif course_id_str:
                    return redirect(url_for('learners.self_paced_flow', course_id_str=course_id_str))
                else:
                    return redirect(url_for('learners.my_portal'))


    return render_template('auth/learner_login.html', class_id=class_id_str, course_id=course_id_str, error=error)

