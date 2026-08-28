import sys
sys.path.insert(0, '.')
import json
from run import app, init_db_and_seed
from app.models import db
from app.models.course import Course
from app.models.learning_wall import LearningWallPost

def test_local_share_course():
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True

    with app.app_context():
        # Setup clean SQLite db and seed for comprehensive testing
        db.drop_all()
        db.create_all()
        init_db_and_seed(app)

        client = app.test_client()

        # 1. TEST AS LEARNER
        with client.session_transaction() as sess:
            sess['learner_id'] = 1
            sess['learner_global_id'] = '10001'
            sess['learner_name'] = 'Rajesh Kumar'
            sess['admin_logged_in'] = False

        course = Course.query.first()
        assert course is not None, "A course must exist to share"

        print("Testing learner sharing a course...")
        res = client.post('/learning_wall/share_course', data={
            'course_id': course.id,
            'note': 'This is a great course!'
        }, follow_redirects=True)
        assert res.status_code == 200
        print("-> Learner course sharing passed successfully!")

        # 2. TEST AS ADMIN
        with client.session_transaction() as sess:
            sess.clear()
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'admin'

        print("Testing admin sharing a course...")
        res = client.post('/learning_wall/share_course', data={
            'course_id': course.id,
            'note': 'Highly recommended!'
        }, follow_redirects=True)
        assert res.status_code == 200
        print("-> Admin course sharing passed successfully!")

if __name__ == '__main__':
    test_local_share_course()
    print("\nALL LOCAL COURSE SHARING TESTS PASSED SUCCESSFULLY!")
