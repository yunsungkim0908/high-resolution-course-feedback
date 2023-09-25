from src.constants import ROOT_DIR
from src.utils import wait_for_admin_email
import os

if __name__=='__main__':
    exec(open(os.path.join(ROOT_DIR, '5_collect_survey.py')).read())
    exec(open(os.path.join(ROOT_DIR, '6_create_digests.py')).read())
    wait_for_admin_email()
    exec(open(os.path.join(ROOT_DIR, '7_send_digests.py')).read())
    exec(open(os.path.join(ROOT_DIR, '8_finish_week.py')).read())
