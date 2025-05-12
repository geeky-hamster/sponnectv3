from task import send_test_email; from models import User; user = User.query.first(); print(f"Sending test email to {user.email}"); result = send_test_email(user.email); print(f"Result: {result}")
