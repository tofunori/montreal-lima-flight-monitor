"""
Configuration helper for the Montreal to Lima Flight Price Monitor.
Loads environment variables from .env file if available.
"""

import os
from dotenv import load_dotenv

# Try to load environment variables from .env file
load_dotenv()

# Amadeus API credentials
AMADEUS_API_KEY = os.environ.get('AMADEUS_API_KEY', 'yUMQuHBLUG10cuUsfw8zM8Cr1MKBmoP0')  # Default to test key
AMADEUS_API_SECRET = os.environ.get('AMADEUS_API_SECRET', 'NUbxODHbGuBNvLtL')  # Default to test secret

# Flight monitor settings
ORIGIN = os.environ.get('ORIGIN', 'YUL')  # Montreal
DESTINATION = os.environ.get('DESTINATION', 'LIM')  # Lima
PRICE_THRESHOLD = float(os.environ.get('PRICE_THRESHOLD', '800'))  # CAD
CHECK_INTERVAL_HOURS = int(os.environ.get('CHECK_INTERVAL_HOURS', '24'))

# Email settings
SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
NOTIFICATION_EMAIL = os.environ.get('NOTIFICATION_EMAIL', '')

# Get SMTP settings dict if credentials are available
def get_smtp_settings():
    """Return SMTP settings as a dict if available, None otherwise."""
    if SMTP_SERVER and SMTP_USERNAME and SMTP_PASSWORD:
        return {
            'smtp_server': SMTP_SERVER,
            'smtp_port': SMTP_PORT,
            'sender_email': SMTP_USERNAME,
            'password': SMTP_PASSWORD
        }
    return None
