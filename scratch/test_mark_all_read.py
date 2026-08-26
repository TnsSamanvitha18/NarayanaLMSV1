import os
import sys
sys.path.insert(0, '.')
from app import create_app
from app.models import db
from app.models.user import Learner
from app.models.notification import LearnerNotification

app = create_app()

with app.app_context():
    l1 = Learner.query.filter_by(global_id='10001').first()
    if not l1:
        print("Learner 10001 not found!")
        sys.exit(1)

    # Ensure at least 1 test notification exists
    n1 = LearnerNotification(learner_id=l1.id, title='Test Notification', message='Testing read all', is_read=False)
    db.session.add(n1)
    db.session.commit()

    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['learner_id'] = l1.id
        sess['learner_name'] = l1.name
        sess['learner_global_id'] = l1.global_id

    res = client.post('/learners/notifications/mark_read/0')
    print(f"Mark All Read Endpoint Status: {res.status_code}")
    print(f"Response Data: {res.get_json()}")

    unread = LearnerNotification.query.filter_by(learner_id=l1.id, is_read=False).count()
    print(f"Remaining Unread Notifications for Learner 10001: {unread}")

    assert res.status_code == 200
    assert res.get_json().get('status') == 'success'
    assert unread == 0
    print("MARK ALL NOTIFICATIONS AS READ TEST PASSED CLEANLY!")
