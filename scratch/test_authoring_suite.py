import sys
sys.path.insert(0, '.')
import json
from run import app, init_db_and_seed
from app.models import db
from app.models.course import Course, CourseLesson, LessonCourseware

def test_course_authoring_suite():
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        # Clean and seed DB
        db.drop_all()
        db.create_all()
        init_db_and_seed(app)

        course = Course.query.filter_by(mode='Self Paced').first()
        assert course is not None, "Seeded self-paced course should exist"
        
        lesson = CourseLesson(
            course_id=course.id,
            lesson_number=1,
            title="Introduction to Programming Concepts",
            summary="A short preview of programming basics."
        )
        db.session.add(lesson)
        db.session.commit()

        client = app.test_client()

        # Simulate Admin Session Login
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'admin'

        print("1. Testing Course Authoring GET endpoint (Enabled state)...")
        app.config['ENABLE_CONTENT_AUTHORING'] = True
        res = client.get(f'/courses/{course.id}/lessons/{lesson.id}/author')
        assert res.status_code == 200
        assert b"Interactive Slide Deck Builder" in res.data
        print("   -> Authoring canvas loaded successfully!")

        print("2. Testing Course Authoring POST saving slide deck JSON data...")
        slides_payload = [
            {"title": "Intro to Python", "layout": "full", "body": "<p>Welcome to programming.</p>", "theme": "navy"},
            {"title": "Python Dicts", "layout": "split", "body": "<p>Key-Value stores.</p>", "theme": "emerald"}
        ]
        
        res = client.post(f'/courses/{course.id}/lessons/{lesson.id}/author', data={
            'slides_json': json.dumps(slides_payload)
        })
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['status'] == 'success'
        
        # Verify db contents
        cw = LessonCourseware.query.filter_by(lesson_id=lesson.id, courseware_type='Text').first()
        saved_slides = json.loads(cw.content_text)
        assert len(saved_slides) == 2
        assert saved_slides[1]['title'] == "Python Dicts"
        print("   -> Slide deck JSON saved and validated in DB successfully!")

        print("3. Testing Course Authoring toggle: DISABLE flag configuration...")
        app.config['ENABLE_CONTENT_AUTHORING'] = False
        
        # Accessing GET should redirect with warning
        res = client.get(f'/courses/{course.id}/lessons/{lesson.id}/author', follow_redirects=False)
        assert res.status_code == 302
        assert f'/courses/{course.id}' in res.location
        print("   -> Redirected correctly when authoring suite is toggled OFF!")

if __name__ == '__main__':
    test_course_authoring_suite()
    print("\nALL CONTENT AUTHORING SUITE TESTS PASSED SUCCESSFULLY!")
