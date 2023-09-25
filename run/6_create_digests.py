import traceback
import sys
from datetime import date

import argparse
from src.utils import get_db, get_date_from_string
from src.mailer import Mailer
from src.survey_manager import SurveyManager
from src.collector import FeedbackCollector
from src.analyzer import Analyzer
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
        analyzer = Analyzer(global_date)
        analyzer.get_group_mood_stats()
        analyzer.generate_digest_files()
        analyzer.save_digest_info()
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        mailer._send_custom_email(ADMIN_EMAILS, "[Error] 6. Create Digest", tb)
    else:
        mailer._send_custom_email(ADMIN_EMAILS, "[Action Required] 6. Create Digest", "Reply to send digest.")
