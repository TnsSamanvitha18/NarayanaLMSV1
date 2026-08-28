import sys
sys.path.insert(0, '.')
from run import app, init_db_and_seed
from app.models import db
from flask import url_for

def inspect_all_routes():
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True

    with app.app_context():
        # Setup clean SQLite db and seed for comprehensive testing
        db.drop_all()
        db.create_all()
        init_db_and_seed(app)

        client = app.test_client()

        # Simulate Admin Session Login
        with client.session_transaction() as sess:
            sess['admin_logged_in'] = True
            sess['admin_username'] = 'admin'
            sess['learner_id'] = 1
            sess['learner_global_id'] = '10001'

        print("\n--- STARTING SITE-WIDE ROUTE INSPECTION ---")
        
        # Extract all GET endpoints registered in the app
        endpoints_to_test = []
        for rule in app.url_map.iter_rules():
            # Test GET routes that don't require parameters
            if "GET" in rule.methods and not rule.arguments:
                endpoints_to_test.append(rule.endpoint)

        print(f"Found {len(endpoints_to_test)} parameter-less GET endpoints. Testing responses...")
        
        failed_endpoints = []
        for ep in endpoints_to_test:
            try:
                with app.test_request_context():
                    url = url_for(ep)
                res = client.get(url, follow_redirects=True)
                if res.status_code != 200:
                    print(f"[FAIL] Endpoint: {ep} ({url}) returned Status: {res.status_code}")
                    failed_endpoints.append((ep, url, res.status_code))
                else:
                    print(f"[PASS] Endpoint: {ep} ({url}) - 200 OK")
            except Exception as e:
                print(f"[CRASH] Endpoint: {ep} failed with exception: {e}")
                failed_endpoints.append((ep, str(e)))

        # Parameterized Custom Endpoints for Super Admin and Learners
        parameterized_tests = [
            ('super_admin.view_table', {'table_name': 'learners'}),
            ('super_admin.view_table', {'table_name': 'courses'}),
            ('learners.learner_detail', {'learner_id': 1}),
            ('learners.self_paced_flow', {'course_id_str': 'CRS-000001'}),
            ('learners.take_assessment', {'course_id': 1, 'assessment_type': 'PRE'}),
            ('learners.submit_feedback', {'repo_id': 1})
        ]

        print("\nTesting parameterized custom endpoints for Super Admin and Learners...")
        for ep, args in parameterized_tests:
            try:
                with app.test_request_context():
                    url = url_for(ep, **args)
                res = client.get(url, follow_redirects=True)
                if res.status_code != 200:
                    print(f"[FAIL] Parameterized Endpoint: {ep} ({url}) returned Status: {res.status_code}")
                    failed_endpoints.append((ep, url, res.status_code))
                else:
                    print(f"[PASS] Parameterized Endpoint: {ep} ({url}) - 200 OK")
            except Exception as e:
                print(f"[CRASH] Parameterized Endpoint: {ep} failed with exception: {e}")
                failed_endpoints.append((ep, str(e)))

        print("\n--- INSPECTION SUMMARY ---")
        if not failed_endpoints:
            print("ALL MONITORED ENDPOINTS PASSED SITE-WIDE INSPECTION SUCCESSFULLY!")
        else:
            print(f"{len(failed_endpoints)} endpoints failed inspection. Please review details.")
            sys.exit(1)

if __name__ == '__main__':
    inspect_all_routes()
