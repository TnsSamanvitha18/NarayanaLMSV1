import sys
sys.path.insert(0, '.')

from run import app, init_db_if_needed
from app.models import db
from app.models.user import Learner

def test_site_routes_responsive():
    init_db_if_needed()
    client = app.test_client()

    with app.app_context():
        learner = Learner.query.first()
        learner_id = learner.id if learner else 1
        learner_name = learner.name if learner else 'Test Learner'

    print("1. Testing Learner Login Route...")
    res1 = client.get('/learner/login')
    assert res1.status_code == 200

    print("2. Testing Learner Portal Route...")
    with client.session_transaction() as sess:
        sess['learner_id'] = learner_id
        sess['learner_name'] = learner_name

    res2 = client.get('/learners/portal')
    assert res2.status_code == 200

    print("3. Testing Learning Wall Route...")
    res3 = client.get('/learning_wall/')
    assert res3.status_code == 200

    print("4. Testing Admin Login & Dashboard...")
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_username'] = 'admin'

    res4 = client.get('/dashboard')
    print("Dashboard Status:", res4.status_code)
    assert res4.status_code == 200

    print("5. Testing Self Paced Flow Course Lessons Overview...")
    with client.session_transaction() as sess:
        sess['learner_id'] = learner_id
        sess['learner_name'] = learner_name

    res5 = client.get('/learners/self_paced_flow/CRS-000001')
    assert res5.status_code == 200

    print("6. Testing Self Paced Flow Single Lesson View (?lesson_id=3)...")
    res6 = client.get('/learners/self_paced_flow/CRS-000001?lesson_id=3')
    assert res6.status_code == 200

    res5 = client.get('/courses/')
    assert res5.status_code == 200

    res6 = client.get('/classes/')
    assert res6.status_code == 200

    res7 = client.get('/learners/')
    assert res7.status_code == 200

    res8 = client.get('/reports/')
    assert res8.status_code == 200

    print("\nALL 8 MAJOR PORTAL ROUTES RESPONDED CLEANLY WITH HTTP 200!")

if __name__ == '__main__':
    test_site_routes_responsive()
