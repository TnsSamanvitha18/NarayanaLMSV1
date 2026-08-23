import sys
sys.path.insert(0, '.')

from run import app, init_db_if_needed

def test_bell_icon_visibility():
    init_db_if_needed()
    client = app.test_client()

    print("1. Checking login page (/learner/login)...")
    res_login = client.get('/learner/login')
    assert res_login.status_code == 200
    html_login = res_login.data.decode('utf-8')
    assert "fa-regular fa-bell" not in html_login, "Bell icon should NOT be on login page!"
    print("   -> Bell icon cleanly HIDDEN on Login Page!")

    print("2. Checking logged-in learner portal...")
    from app.models.user import Learner
    with app.app_context():
        learner = Learner.query.first()
        learner_id = learner.id if learner else 1
        learner_name = learner.name if learner else 'Test Learner'

    with client.session_transaction() as sess:
        sess['learner_id'] = learner_id
        sess['learner_name'] = learner_name

    res_portal = client.get('/learners/portal')
    assert res_portal.status_code == 200
    html_portal = res_portal.data.decode('utf-8')
    assert "notificationDropdown" in html_portal, "Notification dropdown SHOULD be rendered!"
    assert "dropdown-menu" in html_portal
    print("   -> Interactive Notification Dropdown menu cleanly rendered when logged in!")

    print("\nALL BELL ICON & DROPDOWN TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_bell_icon_visibility()
