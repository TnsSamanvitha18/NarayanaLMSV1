import sys
sys.path.insert(0, '.')

from run import app, init_db_if_needed
from app.models import db
from app.models.course import Course
from app.models.feedback import FeedbackRepository, FeedbackQuestion, FeedbackResponse
from app.models.enrollment import LearnerEnrollment
from app.models.certificate import Certificate
from app.models.user import Learner

def test_feedback():
    init_db_if_needed()
    client = app.test_client()

    with app.app_context():
        course = Course.query.first()
        learner = Learner.query.first()
        repo = FeedbackRepository.query.first()

        assert course is not None
        assert learner is not None
        assert repo is not None

        print("Testing feedback submission route with string course_id (CRS-000001)...")
        # Log in learner
        with client.session_transaction() as sess:
            sess['learner_id'] = learner.id

        url = f'/learners/submit_feedback/{repo.id}?course_id={course.course_id}'
        res_get = client.get(url)
        print(f"GET {url} Status Code:", res_get.status_code)
        assert res_get.status_code == 200, f"Expected 200 GET, got {res_get.status_code}"

        # Submit Feedback
        post_data = {
            f'q_{q.id}': 'Excellent' if q.question_type == 'MCQ' else 'Great experience!'
            for q in repo.questions
        }
        res_post = client.post(url, data=post_data, follow_redirects=True)
        print(f"POST {url} Status Code:", res_post.status_code)
        assert res_post.status_code == 200

        # Verify GET request after submission shows submitted status & prefilled answers
        res_get_submitted = client.get(url)
        assert res_get_submitted.status_code == 200
        assert b"Feedback Previously Submitted" in res_get_submitted.data
        assert b"Great experience!" in res_get_submitted.data
        print("-> Pre-filled answers & Feedback Previously Submitted status banner verified!")

        # Update feedback response
        post_data_updated = {
            f'q_{q.id}': 'Good' if q.question_type == 'MCQ' else 'Updated feedback comment!'
            for q in repo.questions
        }
        res_post_upd = client.post(url, data=post_data_updated, follow_redirects=True)
        assert res_post_upd.status_code == 200
        resp_updated = FeedbackResponse.query.filter_by(repo_id=repo.id, learner_id=learner.id).first()
        assert "Updated feedback comment!" in resp_updated.responses_json
        print("-> Feedback resubmission & state update verified!")

        # Test Admin Feedback Detail View
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True

        admin_url = f'/feedback/{repo.id}'
        res_admin = client.get(admin_url)
        assert res_admin.status_code == 200
        assert b"Learner Feedback Submissions" in res_admin.data
        print("-> Admin Feedback Detail Page with learner responses table verified!")

        print("\nALL COURSE FEEDBACK FUNCTIONALITY TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_feedback()
