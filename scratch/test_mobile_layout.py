import sys
sys.path.insert(0, '.')

from run import app, init_db_and_seed

def test_mobile_navbar_elements():
    init_db_and_seed(app)
    client = app.test_client()

    with client.session_transaction() as sess:
        sess['learner_id'] = 1
        sess['learner_name'] = 'Test Learner'

    res = client.get('/learners/portal')
    assert res.status_code == 200
    html = res.data.decode('utf-8')

    assert "admin-profile-btn" in html
    assert "admin-profile-avatar" in html
    assert "brand-title" in html
    assert "Narayana LMS" in html
    assert "Narayana Learning Hub" in html

    print("ALL MOBILE NAVBAR PROFILE LOGO ELEMENTS VERIFIED SUCCESSFULLY!")

if __name__ == '__main__':
    test_mobile_navbar_elements()
