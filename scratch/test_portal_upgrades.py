import sys
sys.path.insert(0, '.')
from run import app, init_db_and_seed
from app.models import db
from app.models.issue import LmsIssue
from app.models.notification import LearnerNotification
from app.models.user import Learner

def test_portal_upgrades():
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True

    with app.app_context():
        # Setup clean SQLite db and seed
        db.drop_all()
        db.create_all()
        init_db_and_seed(app)

        client = app.test_client()

        # 1. Simulate Learner Session
        with client.session_transaction() as sess:
            sess['learner_id'] = 1
            sess['learner_global_id'] = '10001'
            sess['learner_name'] = 'Rajesh Kumar'
            sess['admin_logged_in'] = False

        # Test theme toggling
        print("Testing theme selector endpoint...")
        res = client.post('/learners/set_theme', json={'theme': 'emerald'})
        assert res.status_code == 200
        learner = Learner.query.get(1)
        assert learner.theme == 'emerald'
        print("-> Theme switching passed!")

        # Test raising an issue ticket
        print("Testing raising support ticket...")
        res = client.post('/learners/raise_issue', data={
            'category': 'Technical',
            'description': 'The course content does not load properly.'
        }, follow_redirects=True)
        assert res.status_code == 200
        issue = LmsIssue.query.filter_by(learner_id=1).first()
        assert issue is not None
        assert issue.category == 'Technical'
        assert issue.status == 'Open'
        print("-> Support ticket logging passed!")

        # 2. Simulate Admin Session
        with client.session_transaction() as sess:
            sess.clear()
            sess['super_admin_logged_in'] = True
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'admin'

        # Test viewing the helpdesk issues queue
        print("Testing admin viewing issues list...")
        res = client.get('/super-admin/issues')
        assert res.status_code == 200
        print("-> View support ticket list passed!")

        # Test resolving a ticket
        print("Testing admin resolving issue ticket...")
        res = client.post(f'/super-admin/issues/resolve/{issue.id}', follow_redirects=True)
        assert res.status_code == 200
        issue_updated = LmsIssue.query.get(issue.id)
        assert issue_updated.status == 'Resolved'
        print("-> Ticket resolution and notifier passed!")

        # Test manual notification broadcast
        print("Testing admin broadcasting manual alerts...")
        res = client.post('/super-admin/broadcast_notification', data={
            'audience': 'all',
            'title': 'Test Global Alert',
            'message': 'This is a system-wide test alert.'
        }, follow_redirects=True)
        assert res.status_code == 200
        # Check that learner received the system update notification
        notif = LearnerNotification.query.filter_by(learner_id=1, title='Test Global Alert').first()
        assert notif is not None
        print("-> Global manual notifications broadcast passed!")

        # Test custom report filters
        print("Testing report builder with course/class filters...")
        res = client.get('/reports/?course_id=1&class_id=1')
        assert res.status_code == 200
        print("-> Filtered reports dataset passed!")

if __name__ == '__main__':
    test_portal_upgrades()
    print("\nALL PORTAL UX UPGRADES & HELP-DESK TESTS PASSED SUCCESSFULLY!")
