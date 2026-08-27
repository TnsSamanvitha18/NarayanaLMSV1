import sys
sys.path.insert(0, '.')
import json
from run import app, init_db_and_seed
from app.models import db
from app.models.course import Course, CourseLesson, LessonCourseware

def test_rise_authoring_suite():
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
            title="Interactive RISE Course Module",
            summary="A RISE block course module."
        )
        db.session.add(lesson)
        db.session.commit()

        client = app.test_client()

        # Simulate Admin Session Login
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'admin'

        print("1. Testing RISE Course Authoring GET endpoint...")
        app.config['ENABLE_CONTENT_AUTHORING'] = True
        res = client.get(f'/courses/{course.id}/lessons/{lesson.id}/author')
        assert res.status_code == 200
        assert b"Narayana RISE: Modular Course Authoring" in res.data
        print("   -> RISE authoring composer loaded successfully!")

        print("2. Testing RISE POST saving block deck JSON structures...")
        blocks_payload = [
            {"type": "header", "title": "Get Started", "body": "Overview description", "theme": "emerald"},
            {"type": "text", "body": "<p>A body block paragraph.</p>"},
            {
                "type": "knowledge_check",
                "question": "Is SQLite concurrent?",
                "option1": "Yes, with WAL mode",
                "option2": "No, never",
                "correct_option": "Option1",
                "explanation": "WAL mode allows concurrent reads."
            }
        ]
        
        res = client.post(f'/courses/{course.id}/lessons/{lesson.id}/author', data={
            'slides_json': json.dumps(blocks_payload)
        })
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['status'] == 'success'
        
        # Verify db contents
        cw = LessonCourseware.query.filter_by(lesson_id=lesson.id, courseware_type='Text').first()
        saved_blocks = json.loads(cw.content_text)
        assert len(saved_blocks) == 3
        assert saved_blocks[0]['type'] == "header"
        assert saved_blocks[2]['correct_option'] == "Option1"
        print("   -> Modular blocks JSON schema saved and validated in DB successfully!")

if __name__ == '__main__':
    test_rise_authoring_suite()
    print("\nALL RISE CONTENT AUTHORING TESTS PASSED SUCCESSFULLY!")
