import sys
sys.path.insert(0, '.')
import json
from run import app, init_db_and_seed
from app.models import db
from app.models.course import Course, CourseLesson, LessonCourseware

def test_rise_deployment_and_media_blocks():
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        # Clean and seed DB
        db.drop_all()
        db.create_all()
        init_db_and_seed(app)

        course = Course.query.filter_by(mode='Self Paced').first()
        assert course is not None
        
        lesson = CourseLesson(
            course_id=course.id,
            lesson_number=1,
            title="Complex Interactive RISE Module",
            summary="A RISE block course module with carousels and backdrops."
        )
        db.session.add(lesson)
        db.session.commit()

        # Seed content blocks
        blocks_payload = [
            {"type": "header", "title": "Interactive Welcome", "body": "Starting course", "theme": "navy"},
            {"type": "video", "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {
                "type": "image_carousel",
                "items": [
                    {"url": "https://images.unsplash.com/photo-1", "caption": "Workspace A"},
                    {"url": "https://images.unsplash.com/photo-2", "caption": "Workspace B"}
                ]
            },
            {
                "type": "animated_backdrop",
                "title": "Warp Speed Background",
                "body": "<p>Animated particles content</p>",
                "animation_type": "particles"
            }
        ]

        cw = LessonCourseware(
            lesson_id=lesson.id,
            title="Interactive Blocks Package",
            courseware_type='Text',
            content_text=json.dumps(blocks_payload)
        )
        db.session.add(cw)
        db.session.commit()

        client = app.test_client()

        # Simulate Admin Session Login
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'admin'

        print("1. Triggering deploy POST endpoint to create standalone self-paced course...")
        res = client.post(f'/courses/lesson/{lesson.id}/deploy')
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data['status'] == 'success'
        assert "deployed" in data['message']
        print(f"   -> Deploy Successful! {data['message']}")

        # Verify new course created
        new_courses = Course.query.filter(Course.name.like('%Deployed Course%')).all()
        assert len(new_courses) > 0, "A new deployed course should exist"
        new_course = new_courses[0]
        assert new_course.mode == 'Self Paced'
        
        # Verify copied lesson and blocks
        assert len(new_course.lessons) == 1
        new_lesson = new_course.lessons[0]
        assert new_lesson.title == "Complex Interactive RISE Module"
        
        copied_cw = LessonCourseware.query.filter_by(lesson_id=new_lesson.id, courseware_type='Text').first()
        assert copied_cw is not None
        copied_blocks = json.loads(copied_cw.content_text)
        assert len(copied_blocks) == 4
        assert copied_blocks[1]['type'] == "video"
        assert copied_blocks[3]['animation_type'] == "particles"
        print("   -> Successfully verified new course structures, metadata, and copied RISE blocks!")

if __name__ == '__main__':
    test_rise_deployment_and_media_blocks()
    print("\nALL RISE DEPLOYMENT AND MEDIA BLOCKS TESTS PASSED SUCCESSFULLY!")
