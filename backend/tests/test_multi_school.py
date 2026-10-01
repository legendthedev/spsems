import sqlite3
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 1. Verify KWASU in database
r1 = client.get('/api/institutions/pipeline/KWASU')
assert r1.status_code == 200, f'KWASU pipeline failed: {r1.text}'
data1 = r1.json()
assert data1['institution']['status'] == 'active'
assert data1['institution']['progress_percent'] == 100
assert data1['institution']['primary_color'] == '#16a34a'
assert len(data1['pipeline_stages']) == 7
print('TEST 1 PASSED: KWASU verified as live with 100% onboarding and 7 completed pipeline milestones.')

# 2. Test Onboarding a New Institution (e.g. UNILAG)
onboard_payload = {
    'name': 'University of Lagos',
    'code': 'UNILAG',
    'official_domain': 'unilag.edu.ng',
    'institution_type': 'Federal University',
    'country': 'Nigeria',
    'state': 'Lagos',
    'city': 'Akoka, Yaba',
    'contact_email': 'ict.director@unilag.edu.ng',
    'contact_phone': '+2348021112233',
    'logo_url': '/uploads/institutions/unilag_logo.png',
    'primary_color': '#991b1b',
    'secondary_color': '#f59e0b',
    'accent_color': '#dc2626',
    'admin_fullname': 'Prof. F. O. Ogundipe',
    'admin_username': 'unilag_admin',
    'admin_password': 'UnilagSecure2026!',
    'admin_designation': 'Director, Centre for Information Technology and Systems',
    'academic_session': '2025/2026',
    'current_semester': 'First Semester',
    'max_supervisor_load': 12,
    'dual_supervisor_for_postgrad': True,
    'auto_assign_co_supervisor': True,
    'instant_live_activation': True
}

# Clean any previous test run
conn = sqlite3.connect('spsems.db')
conn.execute("DELETE FROM users WHERE username='unilag_admin'")
conn.execute("DELETE FROM institutions WHERE code='UNILAG'")
conn.commit()
conn.close()

r2 = client.post('/api/institutions/onboard', json=onboard_payload)
assert r2.status_code == 201, f'Onboarding failed: {r2.text}'
data2 = r2.json()
assert data2['success'] is True
assert data2['institution_code'] == 'UNILAG'
assert data2['primary_color'] == '#991b1b'
print('TEST 2 PASSED: UNILAG self-onboarded successfully with extracted colors and admin account.')

# 3. Test Directory listing both KWASU and UNILAG
r3 = client.get('/api/institutions/directory')
assert r3.status_code == 200
schools = {s['code']: s for s in r3.json()['institutions']}
assert 'KWASU' in schools, 'KWASU missing from directory'
assert 'UNILAG' in schools, 'UNILAG missing from directory'
print(f'TEST 3 PASSED: Public directory includes both {len(schools)} institutions.')

# 4. Test Authenticating as the newly created Admin
r4 = client.post('/api/auth/login', json={'username': 'unilag_admin', 'password': 'UnilagSecure2026!'})
assert r4.status_code == 200, f'Login failed: {r4.text}'
login_data = r4.json()
assert login_data['user']['role'] == 'admin'
assert login_data['user']['full_name'] == 'Prof. F. O. Ogundipe'
print('TEST 4 PASSED: Newly created Institutional Super Admin authenticated successfully!')
print('\nALL INTEGRATION TESTS PASSED!')
