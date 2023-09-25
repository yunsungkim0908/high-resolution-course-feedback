import traceback
import sys
import json
import argparse
from datetime import date

from src.utils import get_db, get_date_from_string
from src.mailer import Mailer
from src.survey_manager import SurveyManager
from src.constants import ADMIN_EMAILS, TIME_FORMAT

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', type=str, default=None)
    parser.add_argument('--manual', action="store_true", default=False)
    parser.add_argument('--skip-until', type=str, default=None)
    parser.add_argument('--recovery', action="store_true", default=False)
    parser.add_argument('--simulate', action="store_true", default=False)
    args = parser.parse_args()
    return args

if __name__=='__main__':
    args = parse_args()
    if args.date is None:
        global_date = date.today()
    else:
        global_date = get_date_from_string(args.date)

    if args.recovery:
        with open('recovery_data.json') as f:
            data = json.load(f)
            data = set([tuple(l) for l in data])

        db = get_db()
        mailer = Mailer(global_date)
        querier = QueryManager(global_date, db, mailer)
        querier.notify_student_survey(
            skip_hashes=data, fake_send=args.simulate
        )
    else:
        mailer = Mailer(global_date, manual=args.manual)
        try:
            db = get_db()
            querier = QueryManager(global_date, db, mailer)
            querier.notify_student_survey(skip_until=args.skip_until)

        except Exception:
            tb = traceback.format_exc()
            print(tb)
            mailer._send_custom_email(
                ADMIN_EMAILS,
                "[Error] 3. Notify Students", tb
            )
        else:
            mailer._send_custom_email(
                ADMIN_EMAILS,
                "[Complete] 3. Notify students", ""
            )
