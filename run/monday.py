from src.constants import ROOT_DIR
import os

if __name__=='__main__':
    exec(open(os.path.join(ROOT_DIR, '1_schedule_survey.py')).read())
    exec(open(os.path.join(ROOT_DIR, '2_populate_survey.py')).read())
    exec(open(os.path.join(ROOT_DIR, '3_notify_students.py')).read())
