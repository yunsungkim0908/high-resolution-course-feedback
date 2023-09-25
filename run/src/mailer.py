import sys
sys.path.append('..')
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import src.utils as utils
import getpass
import os
import glob
import json
from dotmap import DotMap

from src.constants import KEYS_PATH, DATA_DIR, HOST_NAME, EMAIL_DOMAIN, EMAIL
from src.mail_templates import (
    MAIL_INSTRUCTOR_INTRO, MAIL_INSTRUCTOR_REMINDER,
    MAIL_STUDENT_NOTICE, MAIL_STUDENT_REMINDER,
    get_digest_template
)
from src.utils import get_student_link, survey_has_ended

class Mailer:
    def __init__(self, global_date, manual=False):
        self.global_date = global_date
        self.global_week = utils.week_string(global_date)
        self.user = EMAIL
        self.password = None
        self.skip = True
        self.manual = manual
        self.authenticate()

    def authenticate(self):
        s = smtplib.SMTP(host='smtp.gmail.com', port=587)
        s.starttls()
        if self.password is None:
            if self.manual:
                self.password = getpass.getpass()
            else:
                self.password = open(os.path.join(KEYS_PATH, 'hrce.txt')).read().strip()
                # self.password = keyring.get_password('HRCE', self.user)
        s.login(self.user, self.password)

        self.address = self.user
        self.smtp_inst = s

    def _send_message(self, msg):
        # print(msg['Subject'])
        while True:
            try:
                self.smtp_inst.send_message(msg)
            except smtplib.SMTPServerDisconnected:
                self.authenticate()
            else:
                break

    def send_digests(self):
        with open('digest_info.json') as f:
            digest_info = DotMap(json.load(f))

        classes_info_path = os.path.join(
            DATA_DIR, 'courses_info', f'{self.global_week}.json'
        )
        classes_info = json.load(open(classes_info_path))

        no_participation_fname = os.path.join(
            DATA_DIR, 'answers', self.global_week, 'no_participation_lst.txt'
        )
        if os.path.isfile(no_participation_fname):
            with open(no_participation_fname) as f:
                no_participation_lst = f.read().split('\n')
        else:
            no_participation_lst = []

        for class_hash in digest_info.no_response:
            print('no response: ', class_hash)
            call_number = classes_info[class_hash]['callNumber']
            self.send_weekly_digest(
                call_number,
                classes_info[class_hash]['admins'],
                digest_info.queried_size[class_hash],
                0,
                digest_info.all_response_rate,
                digest_info.week_of_query[class_hash],
                class_hash,
                is_last=(survey_has_ended(
                    self.global_date, classes_info[class_hash]
                )),
                no_response=True,
                no_participation=(class_hash in no_participation_lst)
            )

        for class_hash in digest_info.has_response:
            print(class_hash, call_number)
            call_number = classes_info[class_hash]['callNumber']
            self.send_weekly_digest(
                call_number,
                classes_info[class_hash]['admins'],
                digest_info.queried_size[class_hash],
                digest_info.answered_size[class_hash],
                digest_info.all_response_rate,
                digest_info.week_of_query[class_hash],
                class_hash,
                is_last=(survey_has_ended(
                    self.global_date, classes_info[class_hash]
                )),
                no_response=False,
                no_participation=(class_hash in no_participation_lst)
            )

    def send_weekly_digest(
            self,
            call_number,
            admins,
            total_queried,
            answered,
            all_response_rate,
            week_of_query,
            class_hash,
            is_last,
            no_response=None,
            no_participation=None
    ):
        template = get_digest_template(is_last, no_response, no_participation)
        text = template.format(
            week_of_quiery=week_of_query,
            call_number=call_number.upper(),
            host_name=HOST_NAME,
            total_queried=total_queried,
            answered=answered,
            response_rate=answered/total_queried,
            all_response_rate=all_response_rate
        )

        msg = MIMEMultipart()
        msg['From'] = f'High Resolution Course Feedback <{self.address}>'
        msg['To'] = ", ".join(admins)
        msg['Subject'] = f'[{call_number.upper()}] Week {week_of_query}: High Resolution Course Feedback Weekly Digest'
        msg.attach(MIMEText(text, 'html'))

        results_dir = os.path.join(
            DATA_DIR, 'answers', self.global_week, class_hash
        )

        print(results_dir)
        if not no_response:
            for img_path in glob.glob(os.path.join(results_dir, '*.png')):
                img_name = os.path.basename(img_path)
                print(img_name)
                msgImage = MIMEImage(open(img_path, 'rb').read())
                msgImage.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=img_name
                )
                msg.attach(msgImage)

            for txt_path in glob.glob(os.path.join(results_dir, '*.txt')):
                if no_participation and txt_path.endswith('participation.txt'):
                    continue
                txt_name = os.path.basename(txt_path)
                print(txt_name)
                msgFile = MIMEText(open(txt_path).read())
                msgFile.add_header('Content-Disposition', 'attachment',
                                   filename=txt_name)
                msg.attach(msgFile)

        self._send_message(msg)

    # suid, name, user_hash, class_hash, call_number, week_of_query
    def send_student_notice(
            self,
            suid,
            name,
            user_hash,
            class_hash,
            call_number,
            week_of_query,
    ):
        link = get_student_link(
            call_number, class_hash, self.global_week, user_hash
        )
        student_name = f'{name.split(",")[1].strip()} {name.split(",")[0].strip()}'
        text = MAIL_STUDENT_NOTICE.format(
            student_name=student_name,
            call_number=call_number.upper(),
            week_of_query=week_of_query,
            link=link
        )
        msg = MIMEMultipart()
        msg['From'] = f'High Resolution Course Feedback <{self.address}>'
        msg['To'] = f'{suid}@{EMAIL_DOMAIN}'
        msg['Subject'] = f'[{call_number.upper()}] Please Submit Anonymous Feedback for Your Class'
        msg.attach(MIMEText(text, 'html'))
        print(suid, name, msg['Subject'], link)

        self._send_message(msg)

    def send_student_reminder(
            self,
            suid,
            name,
            user_hash,
            class_hash,
            call_number,
            week_of_query,
    ):
        link = get_student_link(
            call_number, class_hash, self.global_week, user_hash
        )
        student_name = f'{name.split(",")[1].strip()} {name.split(",")[0].strip()}'
        text = MAIL_STUDENT_REMINDER.format(
            student_name=student_name,
            call_number=call_number.upper(),
            link=link
        )
        msg = MIMEMultipart()
        msg['From'] = f'High Resolution Course Feedback <{self.address}>'
        msg['To'] = f'{suid}@{EMAIL_DOMAIN}'
        msg['Subject'] = f'[{call_number.upper()}] Reminder: Please Submit Anonymous Feedback for Your Class'
        msg.attach(MIMEText(text, 'html'))
        self._send_message(msg)
        print(suid, call_number, link)

    def send_all_instructors_update_reminder(self):
        courses_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{self.global_week}.json'
        )
        courses_info = json.load(open(courses_info_path))

        for course, info in courses_info.items():
            week_of_query = utils.get_course_week_number(
                self.global_date, info)
            if survey_has_ended(self.global_date, info):
                continue
            admins = info['admins']
            class_hash = info['hash']
            call_number = info["callNumber"]
            self.send_instructor_update_reminder(
                admins,
                call_number,
                week_of_query,
                class_hash
            )

    def send_instructor_update_reminder(
            self,
            admins,
            call_number,
            week_of_query,
            class_hash
    ):
        text = MAIL_INSTRUCTOR_REMINDER.format(
            call_number=call_number.upper(),
            next_week=week_of_query+1,
            host_name=HOST_NAME,
            week_of_query=week_of_query
        )
        msg = MIMEMultipart()
        msg['From'] = f'High Resolution Course Feedback <{self.address}>'
        msg['To'] = ", ".join(admins)
        msg['Subject'] = f'[{call_number.upper()}] Reminder: Please Update Your Roster and Questions of the Week'
        msg.attach(MIMEText(text, 'html'))
        self._send_message(msg)
        print(call_number)

    def send_all_instructors_intro(self):
        courses_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{self.global_week}.json'
        )
        courses_info = json.load(open(courses_info_path))

        for course, info in courses_info.items():
            admins = info['admins']
            class_hash = info['hash']
            call_number = info["callNumber"]
            self._send_instructor_intro(admins, call_number, class_hash)

    def _send_instructor_intro(
            self,
            admins,
            call_number,
            class_hash
    ):
        text = MAIL_INSTRUCTOR_INTRO.format(
            call_number=call_number.upper(), host_name=HOST_NAME
        )
        msg = MIMEMultipart()
        msg['From'] = f'High Resolution Course Feedback <{self.address}>'
        msg['To'] = ", ".join(admins)
        msg['Subject'] = 'Welcome to High Resolution Course Feedback!'
        msg.attach(MIMEText(text, 'html'))
        self._send_message(msg)
        print(call_number)

    def _send_custom_email(self, contacts, subject, text):
        msg = MIMEMultipart()
        msg['From'] = f'High Resolution Course Feedback <{self.address}>'
        msg['To'] = ", ".join(contacts)
        msg['Subject'] = subject
        msg.attach(MIMEText(text, 'html'))
        self._send_message(msg)
