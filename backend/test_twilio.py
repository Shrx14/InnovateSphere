import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_number = os.getenv('TWILIO_PHONE_NUMBER')

print(f"Account SID: {account_sid}")
print(f"Auth Token: {'*' * len(auth_token) if auth_token else 'Not set'}")
print(f"Twilio Number: {twilio_number}")

try:
    # Initialize the client
    client = Client(account_sid, auth_token)
    
    # Try to get account info
    account = client.api.accounts(account_sid).fetch()
    print("\nTwilio Account Status:", account.status)
    print("Account Type:", account.type)
    print("Connection successful!")
    
except Exception as e:
    print("\nError connecting to Twilio:", str(e))