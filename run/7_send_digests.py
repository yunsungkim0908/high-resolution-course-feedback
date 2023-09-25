import traceback
import sys
from datetime import date

from src.utils import get_db, get_date_from_string
from src.mailer import Mailer
from src.survey_manager import SurveyManager
from src.collector import FeedbackCollector
from src.analyzer import Analyzer
from src.constants import ADMIN_EMAILS, TIME_FORMAT

if __name__=='__main__':
    if len(sys.argv) == 1:
        global_date = date.today()
    else:
        global_date = get_date_from_string(sys.argv[1])

    mailer = Mailer(global_date)
    try:
        mailer.send_digests()
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        mailer._send_custom_email(ADMIN_EMAILS, "[Error] 7. Send Digest", tb)
    else:
        mailer._send_custom_email(ADMIN_EMAILS, "[Complete] 7. Send Digest", "")
