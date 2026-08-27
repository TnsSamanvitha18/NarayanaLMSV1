import sys
sys.path.insert(0, '.')

import os
from run import app, init_db_and_seed
from app.models import db
from app.models.course import Course, CourseMaterial
from app.services.gdrive_service import parse_gdrive_url

def test_google_drive_integration():
    init_db_and_seed(app)
    client = app.test_client()

    print("1. Testing Google Drive URL Parsing & Embed Conversion Service...")
    
    # Test case A: Standard Drive File view link
    url_file = "https://drive.google.com/file/d/1A2B3C4D5E6F/view?usp=sharing"
    is_gd, emb_url, g_type, file_id = parse_gdrive_url(url_file)
    assert is_gd == True
    assert emb_url == "https://drive.google.com/file/d/1A2B3C4D5E6F/preview"
    assert file_id == "1A2B3C4D5E6F"
    print("   -> Drive File URL parsed cleanly to /preview!")

    # Test case B: Google Slides Presentation
    url_ppt = "https://docs.google.com/presentation/d/1Pres12345/edit#slide=id.p"
    is_gd, emb_url, g_type, file_id = parse_gdrive_url(url_ppt)
    assert is_gd == True
    assert emb_url == "https://docs.google.com/presentation/d/1Pres12345/embed"
    assert file_id == "1Pres12345"
    assert "Slides" in g_type or "PPT" in g_type
    print("   -> Google Slides URL parsed cleanly to /embed!")

    # Test case C: Google Document
    url_doc = "https://docs.google.com/document/d/1Doc67890/edit?usp=drivesdk"
    is_gd, emb_url, g_type, file_id = parse_gdrive_url(url_doc)
    assert is_gd == True
    assert emb_url == "https://docs.google.com/document/d/1Doc67890/preview"
    print("   -> Google Document URL parsed cleanly to /preview!")

    # Test case D: Google Spreadsheet
    url_sheet = "https://docs.google.com/spreadsheets/d/1Sheet999/edit#gid=0"
    is_gd, emb_url, g_type, file_id = parse_gdrive_url(url_sheet)
    assert is_gd == True
    assert emb_url == "https://docs.google.com/spreadsheets/d/1Sheet999/preview"
    print("   -> Google Spreadsheet URL parsed cleanly to /preview!")

    # Test case E: Google Drive Folder
    url_folder = "https://drive.google.com/drive/folders/1Folder777"
    is_gd, emb_url, g_type, file_id = parse_gdrive_url(url_folder)
    assert is_gd == True
    assert "embeddedfolderview" in emb_url
    print("   -> Google Drive Folder URL parsed cleanly to embedded folder view!")

    print("2. Testing Admin Adding Google Drive Learning Material (No local file upload)...")
    # Log in as Admin
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)

    with app.app_context():
        course = Course.query.first()
        assert course is not None
        course_id = course.id

    gdrive_test_link = "https://drive.google.com/file/d/1TestDriveFileId99/view?usp=sharing"
    res = client.post(
        f'/courses/{course_id}/upload_material',
        data={
            'material_title': 'Advanced Python DSA Slide Deck (Google Drive)',
            'material_description': 'Official course presentation hosted on Google Drive.',
            'material_type': 'Google Drive',
            'external_url': gdrive_test_link
        },
        follow_redirects=True
    )
    assert res.status_code == 200

    with app.app_context():
        mat = CourseMaterial.query.filter_by(title='Advanced Python DSA Slide Deck (Google Drive)').first()
        assert mat is not None
        assert mat.external_url == gdrive_test_link
        assert mat.filename is None  # NO server file upload or download!
        assert mat.description == 'Official course presentation hosted on Google Drive.'
        print(f"   -> Material saved in DB cleanly without local server file creation! Material ID: {mat.id}")

    print("3. Testing Learner View & Embedded Viewer Output...")
    # Log in as Learner
    with client.session_transaction() as sess:
        sess.clear()
    client.post('/learner/login', data={'global_id': '10001'}, follow_redirects=True)

    with app.app_context():
        course = Course.query.first()

    res = client.get(f'/learners/self_paced_flow/{course.course_id}')
    assert res.status_code == 200
    assert b"Advanced Python DSA Slide Deck (Google Drive)" in res.data
    assert b"https://drive.google.com/file/d/1TestDriveFileId99/preview" in res.data
    assert b"Open in Google Drive" in res.data
    print("4. Testing Admin Adding Google Drive Link to Lesson Courseware...")
    # Log in as Admin
    with client.session_transaction() as sess:
        sess.clear()
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)

    with app.app_context():
        course = Course.query.first()
        from app.models.course import CourseLesson
        lesson = CourseLesson.query.filter_by(course_id=course.id).first()
        if not lesson:
            lesson = CourseLesson(
                course_id=course.id,
                lesson_number=1,
                title='Introductory Lesson',
                summary='Lesson summary',
                content='Lesson content text'
            )
            db.session.add(lesson)
            db.session.commit()
        lesson_id = lesson.id

    cw_gdrive_link = "https://docs.google.com/presentation/d/1LessonSlidesDrive999/edit?usp=sharing"
    res = client.post(
        f'/courses/lesson/{lesson_id}/add_courseware',
        data={
            'title': 'Lesson 1 Google Slides Deck',
            'courseware_type': 'Google Drive',
            'external_url': cw_gdrive_link
        },
        follow_redirects=True
    )
    assert res.status_code == 200

    print("5. Testing Learner View Rendering for Lesson Courseware Google Drive Link...")
    # Log in as Learner
    with client.session_transaction() as sess:
        sess.clear()
    client.post('/learner/login', data={'global_id': '10001'}, follow_redirects=True)

    with app.app_context():
        course_id_str = Course.query.first().course_id

    res = client.get(f'/learners/self_paced_flow/{course_id_str}')
    assert res.status_code == 200
    assert b"Lesson 1 Google Slides Deck" in res.data
    assert b"https://docs.google.com/presentation/d/1LessonSlidesDrive999/embed" in res.data
    print("   -> Lesson Courseware Google Slides rendered embedded iframe /embed link cleanly!")

    print("\nALL GOOGLE DRIVE INTEGRATION VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_google_drive_integration()
