import os

HOST_NAME="" # host name for the HRCF app e.g., 'https://www.example.org'
EMAIL="" # email address used for sending survey requests and reminders
ADMIN_EMAILS=[] # email addresses of tool admins
FIREBASE_KEY_PATH="" # absolute path of the firebase JSON certificate key file
KEYS_PATH="" # absolute path of the directory where all private credential files (e.g., hrcf.txt storing the password to EMAIL) are stored
TIME_FORMAT="%m/%d/%Y"
EMAIL_DOMAIN="" # domain of the student emails e.g., "stanford.edu"

ROOT_DIR=os.path.dirname(os.path.dirname(__file__))
DATA_DIR=os.path.join(ROOT_DIR, 'data')
