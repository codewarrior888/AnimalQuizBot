import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TOKEN = os.getenv('TOKEN')

ADMIN_ID = os.getenv('ADMIN_ID')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL')
SERVER_EMAIL = os.getenv('SERVER_EMAIL')

USER_EMAIL = os.getenv('USER_EMAIL')
MANAGER_EMAIL = os.getenv('MANAGER_EMAIL')
MANAGER_TEL = os.getenv('MANAGER_TEL')
