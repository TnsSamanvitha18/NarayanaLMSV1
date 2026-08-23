import sys
sys.path.insert(0, '.')
import io
import os
from run import app

def test_lms_with_test_client():
    client = app.test_client()

    print("1. Testing Admin Login...")
    res = client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"Dashboard" in res.data
    print("   -> Admin Login successful!")

    print("2. Testing Self-Paced Course Creation...")
    course_data = {
        'name': 'Full-Stack Web Development Self-Paced Masterclass',
        'description': 'Comprehensive self-paced course covering HTML, CSS, Python, and Flask.',
        'mode': 'Self Paced',
        'pass_percentage': '85.0',
        'feedback_repo_id': '1',
        'has_certificate': '1',
        'is_sequential': '1',
        'completion_date': '2026-12-31'
    }
    res = client.post('/courses/create', data=course_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Full-Stack Web Development" in res.data
    
    # Query created course from DB
    with app.app_context():
        from app.models.course import Course
        course = Course.query.filter_by(name='Full-Stack Web Development Self-Paced Masterclass').first()
        assert course is not None
        assert course.mode == 'Self Paced'
        assert course.is_sequential == True
        course_id = course.id
        print(f"   -> Course Created successfully! ID: {course_id}, Code: {course.course_id}")

    print("3. Testing Course End Assessment CSV Upload...")
    csv_content = (
        "Serial Number,Question,Option1,Option2,Option3,Option4,Correct Option\n"
        "1,What is Flask in Python?,Micro web framework,Database engine,CSS library,Operating system,Option1\n"
        "2,Which Jinja syntax outputs variables?,{{ var }},{% var %},{# var #},<% var %>,Option1\n"
    )
    data = {
        'assessment_csv': (io.BytesIO(csv_content.encode('utf-8')), 'test_course_end.csv')
    }
    res = client.post(f'/courses/{course_id}/upload_course_end_assessment', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert res.status_code == 200
    assert b"Course End Assessment Attached" in res.data
    assert b"What is Flask in Python?" in res.data
    print("   -> Course End Assessment CSV Upload & UI state sync verified!")

    print("4. Testing Lesson Creation with min viewing time & deadline...")
    lesson1_data = {
        'lesson_number': '1',
        'title': 'Introduction to HTML & Web Standards',
        'duration_hours': '1.5',
        'min_time_minutes': '0.5',
        'summary': 'Basic HTML elements, forms, and semantics.',
        'deadline': '2026-11-15'
    }
    res = client.post(f'/courses/{course_id}/add_lesson', data=lesson1_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Introduction to HTML" in res.data
    print("   -> Lesson 1 created successfully!")

    lesson2_data = {
        'lesson_number': '2',
        'title': 'CSS Styling and Responsive Design',
        'duration_hours': '2.0',
        'min_time_minutes': '0.5',
        'summary': 'Flexbox, Grid, and modern layouts.',
        'deadline': '2026-11-30'
    }
    res = client.post(f'/courses/{course_id}/add_lesson', data=lesson2_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"CSS Styling" in res.data
    print("   -> Lesson 2 created successfully!")

    print("5. Testing Course Assignment Validation (Manual Global IDs)...")
    assign_data = {
        'course_id': str(course_id),
        'global_ids': "10001\n10002\nINVALID_99999"
    }
    res = client.post('/learners/assign', data=assign_data, follow_redirects=True)
    assert res.status_code == 200
    assert b"Assignment Results" in res.data
    assert b"INVALID_99999" in res.data
    print("   -> Course Assignment Validation & Reporting verified!")

    print("6. Testing Learner Portal & Notifications...")
    client2 = app.test_client()
    res = client2.post('/learner/login', data={'global_id': '10001'}, follow_redirects=True)
    assert res.status_code == 200
    assert b"My Learning Portal" in res.data
    assert b"Notifications" in res.data
    assert b"Full-Stack Web Development" in res.data
    print("   -> Learner Login & Dashboard Notifications verified!")

    print("\nALL E2E VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_lms_with_test_client()
