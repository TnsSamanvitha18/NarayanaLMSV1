import sys
sys.path.insert(0, '.')

from run import app, init_db_and_seed
from app.models import db
from app.models.user import Learner
from app.models.enrollment import LearnerEnrollment
from app.models.course import Course

def test_parameter_based_assignment():
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        # Clear DB and re-seed to ensure all columns (designation, location, branch) exist and have test values
        db.drop_all()
        db.create_all()
        init_db_and_seed(app)

        # Get seeded courses and test client
        course = Course.query.filter_by(mode='Self Paced').first()
        assert course is not None, "Seeded self-paced course should exist"
        course_id = course.id

        client = app.test_client()

        # Simulate Admin Session Login
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'admin'

        print("1. Testing Course Assignment: Filter by Department ('Physics Department')")
        # Anil Reddy (10003) belongs to 'Physics Department'
        res = client.post('/learners/assign', data={
            'course_id': course_id,
            'assignment_mode': 'parameters',
            'filter_department': 'Physics Department',
            'filter_designation': '',
            'filter_location': '',
            'filter_branch': ''
        }, follow_redirects=True)

        assert res.status_code == 200
        # Check database records
        anil = Learner.query.filter_by(global_id='10003').first()
        enrollment_anil = LearnerEnrollment.query.filter_by(learner_id=anil.id, course_id=course_id).first()
        assert enrollment_anil is not None, "Anil Reddy should be assigned to the course"
        print("   -> Successfully assigned learner by Department filter!")

        print("2. Testing Course Assignment: Filter by Location ('Bangalore')")
        # Sneha Patel (10004) is in Bangalore, and already assigned Anil Reddy (10003) is also in Bangalore
        res = client.post('/learners/assign', data={
            'course_id': course_id,
            'assignment_mode': 'parameters',
            'filter_department': '',
            'filter_designation': '',
            'filter_location': 'Bangalore',
            'filter_branch': ''
        }, follow_redirects=True)

        assert res.status_code == 200
        sneha = Learner.query.filter_by(global_id='10004').first()
        enrollment_sneha = LearnerEnrollment.query.filter_by(learner_id=sneha.id, course_id=course_id).first()
        assert enrollment_sneha is not None, "Sneha Patel should be newly assigned to the course"
        
        # Verify enrollment count for Bangalore learners
        bangalore_learners_count = LearnerEnrollment.query.join(Learner).filter(
            Learner.location == 'Bangalore',
            LearnerEnrollment.course_id == course_id
        ).count()
        assert bangalore_learners_count == 2, "Both Bangalore learners should now be enrolled"
        print("   -> Successfully verified batch parameters course assignment!")

if __name__ == '__main__':
    test_parameter_based_assignment()
    print("\nALL MULTI-PARAMETER COURSE ASSIGNMENT TESTS PASSED SUCCESSFULLY!")
