import sys
sys.path.append('..')
from hashlib import blake2s
import poplib
import time
from datetime import datetime, timedelta
import base64
import os

import firebase_admin
from firebase_admin import credentials, firestore

from email import parser
from email.utils import parsedate_to_datetime as parse_date

from src.constants import (
    KEYS_PATH, ADMIN_EMAILS, EMAIL,
    HOST_NAME, KEY_PATH, TIME_FORMAT
)

# -------------- Admin Utils ---------------

def wait_for_admin_email():
    start = datetime.now().timestamp()
    pw = open(os.path.join(KEYS_PATH, 'hrce.txt')).read().strip()

    received = False
    while not received:
        pop_conn = poplib.POP3_SSL('pop.gmail.com')
        pop_conn.user(EMAIL)
        pop_conn.pass_(pw)
        print(pop_conn.stat())
        count, _ = pop_conn.stat()
        i = count
        # retrieve latest emails
        while (i > 0):
            msg = "\n".join(line.decode('utf-8') for line in pop_conn.retr(i)[1])
            mail = parser.Parser().parsestr(msg)
            date = parse_date(mail['Date']).timestamp()
            sender = mail['From']
            print(sender)

            # don't retrieve emails that are too old
            if date <= start:
                break

            # if sender has admin email, that email is from an admin
            if any(admin in sender for admin in ADMIN_EMAILS):
                received=True
                break
            i -= 1
        pop_conn.quit()

        # return if unresponsive for more than 2 hours
        if datetime.now().timestamp() - start > 2*60*60:
            return
        time.sleep(120)
    return

# --------------- Auth Utils ---------------

def get_db():
    # os.environ["FIRESTORE_EMULATOR_HOST"]="localhost:8080"
    # os.environ["GCLOUD_PROJECT"]="my_project"
    # print("== EMULATOR IN USE ==")

    cred = credentials.Certificate(KEY_PATH)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()

    return db

# --------------- Date Utils ---------------
#
# Everything is in ISO calendar, so the week begins on Monday

def get_date_from_string(string):
    return datetime.strptime(string, TIME_FORMAT).date()

def week_string(this_date, offset=0):
    if isinstance(this_date, str):
        this_date = get_date_from_string(this_date)
    tgt_date = this_date + timedelta(weeks=offset)
    week = tgt_date.isocalendar()[1]
    year = tgt_date.isocalendar()[0]
    return f"{year:4d}-{week:02d}"

def survey_has_started(global_date, course_info):
    this_week = get_course_week_number(
        global_date, course_info
    )
    first_survey_week = get_course_week_number(
        course_info['firstWeek'], course_info
    )
    return (this_week >= first_survey_week)

def survey_has_ended(global_date, course_info):
    this_week = get_course_week_number(
        global_date, course_info
    )
    last_survey_week = get_course_week_number(
        course_info['lastWeek'], course_info
    )
    return (this_week >= last_survey_week)

def first_last_day_of_week(this_date):
    if isinstance(this_date, str):
        this_date = datetime.strptime(this_date, TIME_FORMAT).date()
    start = this_date - timedelta(days=this_date.isoweekday())
    end = start + timedelta(days=6)
    return start, end

def get_course_week_number(this_date, course_info):
    first_week_start, _ = first_last_day_of_week(course_info["classBegins"])
    this_week_start, _ = first_last_day_of_week(this_date)

    assert (this_week_start - first_week_start).days % 7 == 0

    week_of_query = (this_week_start - first_week_start).days//7 + 1
    return week_of_query

def get_final_survey_week_number(course_info):
    first_week_start, _ = first_last_day_of_week(course_info["classBegins"])
    last_week_start, _ = first_last_day_of_week(course_info["lastWeek"])

    assert (last_week_start - first_week_start).days % 7 == 0

    last_week = (last_week_start - first_week_start).days//7 + 1
    return last_week

# --------------- URL Utils ---------------
def get_hash(string):
    salt = os.urandom(blake2s.SALT_SIZE)
    hash_func = blake2s(salt=salt)
    hash_func.update(string.encode())
    digest = hash_func.digest()
    # blake2s digest is 256 bits
    return base64.urlsafe_b64encode(digest).decode('ascii')

def get_student_link(call_number, class_hash, global_week, user_hash):
    return f"{HOST_NAME}/survey?callNumber={call_number}&classHash={class_hash}&week={global_week}&user={user_hash}"

