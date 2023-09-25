from collections import defaultdict
import json
import os
import logging

import src.utils as utils
from src.constants import DATA_DIR

class FeedbackCollector:

    def __init__(self, global_date, db):
        self.global_date = global_date
        self.global_week = utils.week_string(global_date)
        self.db = db

    def collect_feedback(self):

        feedbacks = defaultdict(dict)

        students_to_query_path = os.path.join(
            DATA_DIR, 'queried_students',
            f'{self.global_week}.queried_students.json'
        )
        students_to_query = json.load(open(students_to_query_path))

        for course, query_infos in students_to_query.items():
            feedbacks[course] = {}
            for query_info in query_infos:
                (
                    _,
                    _,
                    user_hash,
                    class_hash,
                    _,
                    _
                ) = query_info
                assert course == class_hash

                answers = (self.db.collection('surveyAnswers')
                                .document(self.global_week)
                                .collection(class_hash)
                                .document(user_hash)
                                .get().to_dict())

                feedbacks[class_hash][user_hash] = answers['answers']

        feedbacks = dict(feedbacks)
        feedback_path = os.path.join(
            DATA_DIR, 'answers',
            f'{self.global_week}.answers.json'
        )
        json.dump(feedbacks, open(feedback_path, 'w'), indent=4)
        return feedbacks

    def update_rosters_with_feedback(self):

        courses_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{self.global_week}.json'
        )
        courses_info = json.load(open(courses_info_path))

        feedback_path = os.path.join(
            DATA_DIR, 'answers', f'{self.global_week}.answers.json'
        )
        feedback = json.load(open(feedback_path))

        hash_map_path = os.path.join(
            DATA_DIR, 'rosters',
            self.global_week,
            'hash_to_stud_info.json'
        )
        hash_map = json.load(open(hash_map_path))

        for class_hash, course_feedback in feedback.items():
            course_info = courses_info[class_hash]
            week_of_query = utils.get_course_week_number(
                self.global_date, course_info
            )

            roster_path = os.path.join(
                DATA_DIR, 'rosters', self.global_week,
                f'{class_hash}.roster.json'
            )
            course_roster = json.load(open(roster_path))

            for user_hash, resp in course_feedback.items():
                print(class_hash, user_hash)
                if resp is None:
                    continue
                name, suid, course, call_number = hash_map[user_hash]
                assert course == class_hash
                if week_of_query not in course_roster['active'][suid]['weeks_completed']:
                    course_roster['active'][suid]['weeks_completed'].append(week_of_query)

            json.dump(course_roster, open(roster_path, 'w'), indent=4)

