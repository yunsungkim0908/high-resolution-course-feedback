import traceback
import sys
from datetime import date
import argparse

from src.utils import get_db, get_date_from_string
from src.mailer import Mailer
from src.scheduler import Scheduler
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

    mailer = Mailer(global_date, manual=args.manual)
    try:
        db = get_db()

        scheduler = Scheduler(global_date, db)
        _,_ = scheduler.update_all_rosters()
        scheduler.get_students_to_query()
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        mailer._send_custom_email(ADMIN_EMAILS, "[Error] 1. Schedule", tb)
    else:
        mailer._send_custom_email(ADMIN_EMAILS, "[Complete] 1. Schedule", "")
