import traceback
import sys
from datetime import date

from src.utils import get_db, get_date_from_string
from src.mailer import Mailer
from src.scheduler import Scheduler
from src.collector import FeedbackCollector
from src.constants import ADMIN_EMAILS, TIME_FORMAT

if __name__=='__main__':
    if len(sys.argv) == 1:
        global_date = date.today()
    else:
        global_date = get_date_from_string(sys.argv[1])

    mailer = Mailer(global_date)
    try:
        db = get_db()
        scheduler = Scheduler(global_date, db)
        scheduler.finish_up_survey()
    except Exception:
        tb = traceback.format_exc()
        print(tb)
        mailer._send_custom_email(ADMIN_EMAILS, "[Error] 8. Fihish Week", tb)
    else:
        mailer._send_custom_email(ADMIN_EMAILS, "[Complete] 8. Finish Week", "")
