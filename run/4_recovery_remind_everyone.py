import json
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
    parser.add_argument('--simulate', action="store_true", default=False)
    args = parser.parse_args()
    return args

if __name__=='__main__':
    args = parse_args()

    if args.date is None:
        global_date = date.today()
    else:
        global_date = get_date_from_string(args.date)

    with open('recovery_data.json') as f:
        data = json.load(f)
        data = set([tuple(l) for l in data])

    db = get_db()
    mailer = Mailer(global_date)
    querier = SurveyManager(global_date, db, mailer)
    querier.remind_students(skip_hashes=data, fake_send=args.simulate)
    if not args.simulate:
        mailer.send_all_instructors_update_reminder()

