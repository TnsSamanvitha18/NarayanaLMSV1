import io
import os
import requests

BASE_URL = "http://localhost:5000"

def test_full_lms_flow():
    session = requests.Session()

    print("1. Testing Admin Login...")
    res = session.post(f"{BASE_URL}/login", data={'username': 'admin', 'password': 'admin'}, allow_redirects=True)
    assert res.status_code == 200
    assert "Dashboard" in res.text
    print("   -> Admin Login successful!")

    print("2. Testing Self-Paced Course Creation...")
    course_data = {
        'name': 'Full-Stack Web Development Self-Paced Masterclass',
        'description': 'Comprehensive self-paced course covering HTML, CSS, Python, and Flask.',
        'mode': 'Self Paced',
        'pass_percentage': '85.0',
        'feedback_repo_id': '1',
        'has_certificate': '1',
        'is_sequential': '1', # Sequential mode ON
        'completion_date': '2026-12-31'
    }
    res = session.post(f"{BASE_URL}/courses/create", data=course_data, allow_redirects=True)
    if res.status_code != 200:
        print(f"Error status code: {res.status_code}, URL: {res.url}")
        print("Content snippet:", res.text[:500])
    assert res.status_code == 200
    assert "Full-Stack Web Development" in res.text
    # Extract Course internal ID from response URL or text
    course_url = res.url
    course_id = course_url.split('/')[-1]
    print(f"   -> Course Created successfully! Internal Course ID: {course_id}")

    print("3. Testing Course End Assessment CSV Upload...")
    csv_content = (
        "Serial Number,Question,Option1,Option2,Option3,Option4,Correct Option\n"
        "1,What is Flask in Python?,Micro web framework,Database engine,CSS library,Operating system,Option1\n"
        "2,Which Jinja syntax outputs variables?,{{ var }},{% var %},{# var #},<% var %>,Option1\n"
    )
    files = {'assessment_csv': ('test_course_end.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    res = session.post(f"{BASE_URL}/courses/{course_id}/upload_course_end_assessment", files=files, allow_redirects=True)
    assert res.status_code == 200
    assert "Course End Assessment Attached" in res.text
    assert "What is Flask in Python?" in res.text
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
    res = session.post(f"{BASE_URL}/courses/{course_id}/add_lesson", data=lesson1_data, allow_redirects=True)
    assert res.status_code == 200
    assert "Introduction to HTML" in res.text
    print("   -> Lesson 1 created successfully!")

    lesson2_data = {
        'lesson_number': '2',
        'title': 'CSS Styling and Responsive Design',
        'duration_hours': '2.0',
        'min_time_minutes': '0.5',
        'summary': 'Flexbox, Grid, and modern layouts.',
        'deadline': '2026-11-30'
    }
    res = session.post(f"{BASE_URL}/courses/{course_id}/add_lesson", data=lesson2_data, allow_redirects=True)
    assert res.status_code == 200
    assert "CSS Styling" in res.text
    print("   -> Lesson 2 created successfully!")

    print("5. Testing Course Assignment Validation (Manual Global IDs)...")
    assign_data = {
        'course_id': course_id,
        'global_ids': "10001\n10002\nINVALID_99999"
    }
    res = session.post(f"{BASE_URL}/learners/assign", data=assign_data, allow_redirects=True)
    assert res.status_code == 200
    assert "Assignment Results" in res.text
    assert "INVALID_99999" in res.text or "invalid" in res.text.lower()
    print("   -> Course Assignment Validation & Reporting verified!")

    print("6. Testing Learner Portal & Notifications...")
    learner_session = requests.Session()
    res = learner_session.post(f"{BASE_URL}/learner/login", data={'global_id': '10001'}, allow_redirects=True)
    assert res.status_code == 200
    assert "My Learning Portal" in res.text
    assert "Notifications" in res.text
    assert "Full-Stack Web Development" in res.text
    print("   -> Learner Login & Dashboard Notifications verified!")

    print("\nALL E2E VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_full_lms_flow()
