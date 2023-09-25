import traceback
import sys
from datetime import date

import argparse
from src.utils import get_db, get_date_from_string
from src.mailer import Mailer
from src.survey_manager import SurveyManager
from src.constants import ADMIN_EMAILS, TIME_FORMAT

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, default=None)
    parser.add_argument('--manual', action="store_true", default=False)
    args = parser.parse_args()
    return args

if __name__=='__main__':
    args = parse_args()

    if args.date is None:
        global_date = date.today()
    else:
        global_date = get_date_from_string(args.date)

    mailer = Mailer(global_date)
    try:
        db = get_db()
        mailer = Mailer(global_date)
        querier = SurveyManager(global_date, db, mailer)
        querier.remind_students()
        mailer.send_all_instructors_update_reminder()

    except Exception:
        tb = traceback.format_exc()
        print(tb)
        mailer._send_custom_email(
            ADMIN_EMAILS,
            "[Error] 4. Remind Everyone", tb
        )
    else:
        mailer._send_custom_email(
            ADMIN_EMAILS,
            "[Complete] 4. Remind Everyone", ""
        )
