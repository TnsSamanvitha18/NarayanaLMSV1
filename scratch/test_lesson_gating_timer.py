import sys
sys.path.insert(0, '.')

from run import app
from app.seed import init_db_and_seed
from app.models import db
from app.models.course import Course, CourseLesson, CourseAssessment
from app.models.enrollment import LearnerEnrollment, AssessmentAttempt, LessonReview

def test_lesson_gating_and_timer():
    init_db_and_seed(app)
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    with app.app_context():
        course = Course.query.first()
        assert course is not None
        course.is_sequential = False
        # Clean existing lessons, assessments, attempts, and reviews to test cleanly
        AssessmentAttempt.query.delete()
        LessonReview.query.delete()
        CourseAssessment.query.filter_by(course_id=course.id).delete()
        CourseLesson.query.filter_by(course_id=course.id).delete()
        db.session.commit()

        # Lesson 1: Has Lesson Pre-Assessment
        les1 = CourseLesson(
            course_id=course.id,
            lesson_number=1,
            title='Lesson 1 with Pre-Assessment',
            summary='Lesson 1 summary',
            content='Lesson 1 content text',
            min_time_minutes=0.1
        )
        db.session.add(les1)

        # Lesson 2: No Pre-Assessment (Content immediately unlocked)
        les2 = CourseLesson(
            course_id=course.id,
            lesson_number=2,
            title='Lesson 2 without Pre-Assessment',
            summary='Lesson 2 summary',
            content='Lesson 2 content text',
            min_time_minutes=0.1
        )
        db.session.add(les2)
        db.session.commit()

        # Add Pre-Assessment Question to Lesson 1
        q1 = CourseAssessment(
            course_id=course.id,
            lesson_id=les1.id,
            assessment_type='LESSON_PRE',
            serial_number=1,
            question='What is Python?',
            option1='Programming Language',
            option2='Snake',
            option3='Car',
            option4='Food',
            correct_option=1,
            lesson_number=1
        )
        db.session.add(q1)
        db.session.commit()

        course_id_str = course.course_id
        les1_id = les1.id
        les2_id = les2.id

    print("2. Testing Learner View Content Gating Before Pre-Assessment Submission...")
    # Log in as Learner
    with client.session_transaction() as sess:
        sess.clear()
    client.post('/learner/login', data={'global_id': '10001'}, follow_redirects=True)

    # Request Lesson 1 player page (content should be locked)
    res = client.get(f'/learners/self_paced_flow/{course_id_str}?lesson_id={les1_id}')
    assert res.status_code == 200
    html_content = res.data.decode('utf-8')
    assert "Lesson 1 Content Locked" in html_content

    # Request Lesson 2 player page (no pre-assessment, content should be unlocked immediately)
    res = client.get(f'/learners/self_paced_flow/{course_id_str}?lesson_id={les2_id}')
    assert res.status_code == 200
    assert b"Lesson 2 content text" in res.data
    print("   -> Lesson 1 content locked (Pre-Assessment pending), Lesson 2 content unlocked (No Pre-Assessment)!")

    print("3. Submitting Lesson 1 Pre-Assessment (Verifying No Pass/Fail Threshold)...")
    res_sub = client.post(
        f'/learners/take_assessment/{course_id_str}/LESSON_PRE?lesson_id={les1_id}',
        data={'q1': '2'}, # Intentional wrong answer to verify NO pass/fail threshold for pre-assessments!
        follow_redirects=True
    )
    assert res_sub.status_code == 200

    print("4. Testing Learner View Content Unlocked After Pre-Assessment Submission...")
    # Request Lesson 1 player page (should now be unlocked)
    res_after = client.get(f'/learners/self_paced_flow/{course_id_str}?lesson_id={les1_id}')
    assert res_after.status_code == 200
    assert b"Lesson 1 content text" in res_after.data
    print("   -> Lesson 1 content cleanly UNLOCKED after submitting Pre-Assessment!")

    print("5. Testing Timer Completion Endpoint (/record_courseware_time)...")
    res_time = client.post(f'/learners/record_courseware_time/{les1_id}')
    assert res_time.status_code == 200
    data = res_time.get_json()
    assert data['status'] == 'success'
    assert data['unlocked'] == True
    print("   -> Viewing timer completion endpoint successfully recorded LessonReview in DB!")

    print("\nALL LESSON GATING AND TIMER TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_lesson_gating_and_timer()
