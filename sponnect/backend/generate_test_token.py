import jwt
import datetime
import sys
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

if __name__ == '__main__':
    # Allow command line arguments for role and user_id
    user_id = 1
    role = 'admin'
    
    if len(sys.argv) > 1:
        role = sys.argv[1]
    
    if len(sys.argv) > 2:
        user_id = int(sys.argv[2])
    
    token = generate_test_token(user_id, role)
    print(f"\nGenerated test token for {role} (user_id: {user_id}):")
    print(token)
    print("\nUse it in curl like this:")
    print(f"curl -H 'Authorization: Bearer {token}' http://localhost:5000/api/profile") 