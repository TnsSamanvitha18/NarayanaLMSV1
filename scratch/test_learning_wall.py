import sys
sys.path.insert(0, '.')

import json
from run import app
from app.seed import init_db_and_seed
from app.models import db
from app.models.user import Learner
from app.models.course import Course
from app.models.learning_wall import LearningWallPost, LearningWallReaction
from app.services.learning_wall_service import (
    create_completion_post,
    check_and_generate_birthday_posts,
    toggle_post_reaction
)

def test_learning_wall_feature():
    init_db_and_seed(app)
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()

    print("1. Testing Unauthenticated Access to Learning Wall (should redirect to login)...")
    res = client.get('/learning_wall/', follow_redirects=False)
    assert res.status_code == 302
    assert '/learner/login' in res.location
    print("   -> Redirected unauthenticated user to login cleanly!")

    print("2. Testing Learner Access to Learning Wall...")
    client.post('/learner/login', data={'global_id': '10001'}, follow_redirects=True)
    res = client.get('/learning_wall/')
    assert res.status_code == 200
    assert b"Learning Wall" in res.data
    assert b"System Bulletin" in res.data or b"Live News Bulletin Feed" in res.data
    print("   -> Learning Wall feed page rendered successfully for Learner view!")

    print("3. Testing Admin Access to Learning Wall...")
    with client.session_transaction() as sess:
        sess.clear()
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    res = client.get('/learning_wall/')
    assert res.status_code == 200
    assert b"Learning Wall" in res.data
    print("   -> Learning Wall feed page rendered successfully for Admin view!")

    print("4. Testing Automated Course Completion Post Trigger...")
    with app.app_context():
        learner = Learner.query.first()
        course = Course.query.first()
        assert learner is not None
        assert course is not None
        
        post = create_completion_post(learner.id, course.id, final_score=96.5)
        assert post is not None
        assert post.post_type == 'COURSE_COMPLETION'
        assert learner.name in post.content
        assert course.name in post.content
        post_id = post.id
        print(f"   -> Course completion post auto-created cleanly! Post ID: {post_id}")

    print("5. Testing Automated Birthday Post Generator...")
    with app.app_context():
        import datetime
        today = datetime.date.today()
        test_learner = Learner.query.filter_by(global_id='10002').first()
        if test_learner:
            test_learner.date_of_birth = today
            db.session.commit()

        bday_posts = check_and_generate_birthday_posts()
        print(f"   -> Birthday posts generated: {len(bday_posts)}")

    print("6. Testing Reaction Toggle API (Learner Session)...")
    with client.session_transaction() as sess:
        sess.clear()
    client.post('/learner/login', data={'global_id': '10001'}, follow_redirects=True)

    # React with 'celebrate'
    res = client.post('/learning_wall/react', data={'post_id': str(post_id), 'reaction_type': 'celebrate'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] == True
    assert data['counts']['celebrate'] >= 1
    assert data['user_reaction'] == 'celebrate'
    print("   -> Reaction 'celebrate' added successfully!")

    # Toggle reaction to 'fire'
    res = client.post('/learning_wall/react', data={'post_id': str(post_id), 'reaction_type': 'fire'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] == True
    assert data['user_reaction'] == 'fire'
    print("   -> Reaction toggled to 'fire' successfully!")

    # React again with 'fire' to remove it (toggle off)
    res = client.post('/learning_wall/react', data={'post_id': str(post_id), 'reaction_type': 'fire'})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] == True
    assert data['user_reaction'] is None
    print("   -> Reaction toggled off successfully!")

    print("7. Testing Clear All Events (Admin Session)...")
    with app.app_context():
        test_learner = Learner.query.filter_by(global_id='10002').first()
        if test_learner:
            test_learner.date_of_birth = None
            db.session.commit()
    with client.session_transaction() as sess:
        sess.clear()
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    res = client.post('/learning_wall/clear', follow_redirects=False)
    assert res.status_code == 302
    with app.app_context():
        count = LearningWallPost.query.count()
        assert count == 0
    print("   -> All Learning Wall events cleared successfully!")

    print("\nALL LEARNING WALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_learning_wall_feature()
