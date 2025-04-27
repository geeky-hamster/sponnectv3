import http.client
import json
import jwt
import datetime
from app import app

def generate_test_token(user_id=1, role='admin'):
    """Generate a test JWT token for API access"""
    with app.app_context():
        expiration = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        payload = {
            'sub': str(user_id),
            'user_id': user_id,
            'role': role,
            'exp': expiration
        }
        token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        return token

def make_api_request(endpoint, token):
    conn = http.client.HTTPConnection("localhost", 5000)
    headers = {"Authorization": f"Bearer {token}"}
    conn.request("GET", endpoint, headers=headers)
    
    response = conn.getresponse()
    print(f"Status: {response.status} {response.reason}")
    
    data = response.read().decode()
    try:
        json_data = json.loads(data)
        print(json.dumps(json_data, indent=2))
    except json.JSONDecodeError:
        print(data)
    
    conn.close()

# Test different user roles and endpoints
sponsor_id = 9
sponsor_token = generate_test_token(sponsor_id, 'sponsor')

print("\nTesting profile endpoint with sponsor token:")
make_api_request("/api/profile", sponsor_token)

print("\nTesting sponsor campaigns endpoint:")
make_api_request("/api/sponsor/campaigns", sponsor_token)

# Try another sponsor user
print("\nTrying with a different sponsor user (ID 4):")
other_sponsor_token = generate_test_token(4, 'sponsor')
make_api_request("/api/sponsor/campaigns", other_sponsor_token)

# Try with admin token for comparison
print("\nTrying with admin token for comparison:")
admin_token = generate_test_token(1, 'admin')
make_api_request("/api/sponsor/campaigns", admin_token) 