import sys
sys.path.append('..')
import json
import os
import time
import src.utils as utils

from src.constants import DATA_DIR

class SurveyManager:
    def __init__(self, global_date, db, mailer):
        self.global_date = global_date
        self.global_week = utils.week_string(global_date)
        self.db = db
        self.mailer = mailer

    def _get_course_questions(self):
        default_questions = (
            self.db.collection("shared")
                .document("defaultQuestions")
                .get().to_dict()
        )

        classes_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{self.global_week}.json'
        )
        classes_info = json.load(open(classes_info_path))
        week_questions = {}

        # read questions
        for class_hash, class_info in classes_info.items():
            week_of_query = utils.get_course_week_number(
                self.global_date, class_info
            )
            custom_questions = (
                self.db.collection("questions")
                    .document(class_hash)
                    .get().to_dict()
            )

            # combine default + custom questions
            class_default_q = default_questions['questions']
            class_custom_q = custom_questions['questions']
            week_questions[class_hash] = {
                'classWeek': week_of_query,
                'questions': class_default_q + class_custom_q
            }

            # make current week's questions the "previous-questions"
            custom_questions['previous-questions'] = class_custom_q
            (self.db
                .collection('questions')
                .document(class_hash)
                .set(custom_questions))

        return week_questions

    def populate_student_survey(self, init_answers=True):
        all_questions = self._get_course_questions()

        classes_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{self.global_week}.json'
        )
        classes_info = json.load(open(classes_info_path))

        questions_path = os.path.join(
            DATA_DIR, 'questions',
            f'{self.global_week}.questions.json'
        )
        json.dump(all_questions, open(questions_path, 'w'), indent=4)

        students_to_query_path = os.path.join(
            DATA_DIR, 'queried_students',
            f'{self.global_week}.queried_students.json'
        )
        students_to_query = json.load(open(students_to_query_path))

        for class_hash, class_info in classes_info.items():
            query_size = len(students_to_query[class_hash])
            print(f'Populating {class_info["callNumber"]}, {class_hash} ({query_size} students)')
            course_questions = all_questions[class_hash]
            for query_info in students_to_query[class_hash]:
                (
                    _,
                    _,
                    user_hash,
                    class_hash,
                    _,
                    _
                ) = query_info

                (self.db.collection('surveyQuestions')
                    .document(self.global_week)
                    .collection(class_hash)
                    .document(user_hash)
                    .set(course_questions))

                if not init_answers:
                    continue

                (self.db.collection('surveyAnswers')
                    .document(self.global_week)
                    .collection(class_hash)
                    .document(user_hash)
                    .set({
                        'answers': None,
                        'course': None
                    }))

    def notify_student_survey(self, skip_hashes=set(), courses=None, skip_until=None, fake_send=False):

        students_to_query_path = os.path.join(
            DATA_DIR, 'queried_students',
            f'{self.global_week}.queried_students.json'
        )
        students_to_query = json.load(open(students_to_query_path))

        num_emails_sent = 0
        send = (skip_until is None)

        for course, queried_list in students_to_query.items():
            if courses is not None and course not in courses:
                continue

            for query_info in queried_list:
                assert len(query_info) == 6
                user_hash = query_info[2]
                class_hash = query_info[3]

                if (class_hash, user_hash) in skip_hashes:
                    print(f'skipping user {user_hash} in class {class_hash}')
                    continue

                if send:
                    if num_emails_sent == 40:
                        print('sleeping after 40 mails...')
                        time.sleep(120)
                        num_emails_sent = 0
                    if not fake_send:
                        self.mailer.send_student_notice(*query_info)
                        num_emails_sent += 1
                    else:
                        print(f'fake send to user {user_hash} in class {class_hash}')
                else:
                    print(f'skipping {query_info[2]}')
                    if skip_until is not None:
                        send = (query_info[2] == skip_until)

    def remind_students(self, skip_until=None, skip_hashes=set(), fake_send=False):

        students_to_query_path = os.path.join(
            DATA_DIR, 'queried_students',
            f'{self.global_week}.queried_students.json'
        )
        students_to_query = json.load(open(students_to_query_path))

        num_emails_sent = 0
        send = (skip_until is None)

        for class_hash, class_queried in students_to_query.items():
            for query_info in class_queried:
                (
                    _,
                    _,
                    user_hash,
                    class_hash,
                    _,
                    _
                ) = query_info

                stud_doc = (self.db
                    .collection('surveyAnswers')
                    .document(self.global_week)
                    .collection(class_hash)
                    .document(user_hash)
                    .get().to_dict()
                )

                answered = (stud_doc['answers'] is not None)
                if (class_hash, user_hash) in skip_hashes:
                    print(f'skipping user {user_hash} in class {class_hash}')
                    continue

                if not answered and send:
                    # rate throttle
                    if num_emails_sent == 40:
                        print('sleeping after 40 mails...')
                        time.sleep(120)
                        num_emails_sent = 0

                    if not fake_send:
                        self.mailer.send_student_reminder(*query_info)
                        num_emails_sent += 1
                    else:
                        print(f'fake send to user {user_hash} in class {class_hash}')

                if not send:
                    print(f'skipping {user_hash}')
                if skip_until is not None and not send:
                    send = (user_hash == skip_until)

    def close_student_survey(self):

        students_queried_path = os.path.join(
            DATA_DIR, 'queried_students',
            f'{self.global_week}.queried_students.json'
        )
        students_queried = json.load(open(students_queried_path))

        for class_hash, class_queried in students_queried.items():
            for query_info in class_queried:
                (
                    _,
                    _,
                    user_hash,
                    class_hash,
                    _,
                    _
                ) = query_info

                (self.db
                    .collection('surveyQuestions')
                    .document(self.global_week)
                    .collection(class_hash)
                    .document(user_hash)
                    .set({'questions': 'closed'})
                )

        print('closed student survey')
