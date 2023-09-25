import sys
sys.path.append('..')
import os
import json
from copy import deepcopy
from pprint import pprint
from datetime import date, timedelta
import numpy as np

import src.utils as utils
from src.constants import DATA_DIR

# TODO: WEEKLY_WEIGHTS are fixed to 10 weeks --> fix

class Scheduler:
    # WEEKLY_WEIGHTS = np.array([0, 5, 7, 6, 5, 4, 3, 3, 3, 5])
    WEEKLY_WEIGHTS = np.array([1]*20)

    def __init__(self, global_date, db):
        self.global_date = global_date
        self.global_week = utils.week_string(global_date)
        self.db = db

    def update_all_rosters(self):
        all_rosters = {}
        old_hash_map_path = os.path.join(
            DATA_DIR, 'rosters',
            utils.week_string(self.global_date, offset=-1),
            'hash_to_stud_info.json'
        )
        hash_to_stud_info = (
            json.load(open(old_hash_map_path))
            if os.path.isfile(old_hash_map_path) else {}
        )

        # class_hash of courses that have not ended
        approved_course_hash = [
            doc.id for doc in self.db
                                .collection("approvedCourses")
                                .where("ended", "==", False)
                                .stream()
        ]

        courses_info_dict = {}
        for class_hash in approved_course_hash:
            course_info = (self.db
                          .collection("courses")
                          .document(class_hash)
                          .get().to_dict())

            # if survey hasn't started, don't include it in courses_info
            if not utils.survey_has_started(
                self.global_date, course_info
            ):
                continue

            first_survey_week = utils.get_course_week_number(
                course_info['firstWeek'], course_info
            )

            last_survey_week = utils.get_course_week_number(
                course_info['lastWeek'], course_info
            )
            course_info['first_survey_week'] = first_survey_week
            course_info['last_survey_week'] = last_survey_week

            print(class_hash, course_info['callNumber'])
            # Roster
            # pull out the roster from the week prior
            prev_roster_path = os.path.join(
                DATA_DIR, 'rosters',
                utils.week_string(self.global_date, offset=-1),
                f'{class_hash}.roster.json'
            )
            new_roster_path = os.path.join(
                DATA_DIR, 'rosters',
                self.global_week,
                f'{class_hash}.roster.json'
            )

            if not os.path.isdir(os.path.dirname(new_roster_path)):
                os.makedirs(os.path.dirname(new_roster_path))

            class_roster = (
                json.load(open(prev_roster_path))
                if os.path.isfile(prev_roster_path)
                else None
            )
            new_roster, hash_to_stud_info = self._update_roster(
                course_info,
                class_roster,
                hash_to_stud_info
            )
            json.dump(new_roster, open(new_roster_path, 'w'), indent=4)

            all_rosters[class_hash] = new_roster

            # Course Info
            # all approved course_doc gets dumped in classes_info.json
            courses_info_dict[class_hash] = course_info

        courses_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{self.global_week}.json'
        )
        json.dump(courses_info_dict, open(courses_info_path, 'w'), indent=4)

        new_hash_map_path = os.path.join(
            DATA_DIR, 'rosters',
            self.global_week,
            'hash_to_stud_info.json'
        )
        json.dump(hash_to_stud_info, open(new_hash_map_path, 'w'), indent=4)

        return all_rosters, hash_to_stud_info

    def get_students_to_query(self):
        """
            returns:
                students_to_query: a list of (suid, name, user_hash, class_hash, call_number)
                                    tuples for students queried this week
        """

        courses_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{self.global_week}.json'
        )
        courses_info = json.load(open(courses_info_path))

        # contains the state of the query for each student
        students_to_query = {}
        queried_students_path = os.path.join(
            DATA_DIR, 'queried_students',
            f'{self.global_week}.queried_students.json'
        )

        # for each course, pick out the state info of students to be queried
        # that will be used to send surveys
        for class_hash, course_info in courses_info.items():
            week_of_query = utils.get_course_week_number(
                self.global_date, course_info)

            roster_path = os.path.join(
                DATA_DIR, 'rosters',
                self.global_week,
                f'{class_hash}.roster.json'
            )
            class_roster = json.load(open(roster_path))
            class_queries = []

            # loop through items in roster for students to query
            # students_to_query format: (
            #   suid
            #   name
            #   user_hash
            #   class_hash
            #   call_number
            #   week_of_query
            # )
            for suid, s_info in class_roster['active'].items():
                if week_of_query in s_info['weeks_to_query']:
                    class_queries.append((
                        suid,
                        s_info['name'],
                        s_info['user_hash'],
                        s_info['class_hash'],
                        s_info['call_number'],
                        week_of_query))
            students_to_query[class_hash] = class_queries

        json.dump(students_to_query, open(queried_students_path, 'w'), indent=4)
        return students_to_query

    def finish_up_survey(self):
        classes_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{self.global_week}.json'
        )
        classes_info = json.load(open(classes_info_path))

        print('finishing for the week...')
        for class_hash, class_info in classes_info.items():
            print(class_hash, class_info['callNumber'])

            # updated "completed" field
            (self.db
                .collection('courses')
                .document(class_hash)
                .update({ 'completed': class_info['completed'] + 1})
            )

            if not utils.survey_has_ended(self.global_date, class_info):
                continue

            print('(Survey Complete)')
            # if we just completed the last survey, update the stataus
            (self.db
                .collection('approvedCourses')
                .document(class_hash)
                .update({'ended': True})
            )

    def _update_roster(self, course_info, roster, hash_to_stud_info):
        """
            @param roster:
                - "active" (dict): students to query (name and which weeks to query)
                - "inactive" (dict): students no longer in roster
        """
        num_query = course_info["numQuery"]
        class_hash = course_info["hash"]
        course_name = course_info["courseName"]
        call_number = course_info["callNumber"]

        week_of_query = utils.get_course_week_number(
            self.global_date, course_info
        )
        last_week = utils.get_final_survey_week_number(course_info)

        new_roster = self.db.collection("rosters").document(class_hash).get().to_dict()
        new_suid_to_name = dict((new_roster['id'][i], new_roster['name'][i])
                                for i in range(len(new_roster['id'])))

        raw_roster_dir = os.path.join(DATA_DIR, 'rosters', 'raw_rosters')
        if not os.path.isdir(raw_roster_dir):
            os.makedirs(raw_roster_dir)
        json.dump(new_roster, open(os.path.join(raw_roster_dir, f'{class_hash}.raw.json'), 'w'), indent=4)

        if roster is None:
            roster = {'active': {}, 'inactive': {}}

        # keep track of who went active/inactive
        prev_active = set(roster['active'].keys())
        prev_inactive = set(roster['inactive'].keys())
        curr_active = set(new_roster['id'])
        curr_inactive = prev_active.union(prev_inactive) - curr_active
        new_students = curr_active - prev_active.union(prev_inactive)

        # use this function to determine whether a student should be queried
        # this week given how many queries remain
        def query_this_week(queries_remaining):
            p_lst = deepcopy(self.WEEKLY_WEIGHTS[week_of_query-1:last_week])
            # sampling conditioned on not being queried next week
            p_lst[1] = 0
            p = p_lst / p_lst.sum()
            query_weeks = np.random.choice(
                np.arange(week_of_query, last_week+1),
                size=queries_remaining, replace=False, p=p)
            return (week_of_query in query_weeks)

        # new students. create query info
        for suid in new_students:
            user_hash = utils.get_hash(class_hash + suid)
            roster['active'][suid] = {
                'name': new_suid_to_name[suid],
                'class_hash': class_hash,
                'call_number': call_number,
                'course_name': course_name,
                'user_hash': user_hash,
                'weeks_to_query': [],
                'weeks_completed': [],
                'weeks_active': [],
                'weeks_inactive': [],
                'note': []
            }

            # hash_to_stud_info: (
            #   name
            #   suid
            #   class_hash
            #   call_number
            # )
            hash_to_stud_info[user_hash] = (
                new_suid_to_name[suid],
                suid,
                class_hash,
                call_number
            )

        # students currently in class
        for suid in curr_active:
            # who came back to class?
            if suid in prev_inactive:
                roster['active'][suid] = roster['inactive'][suid]
                del roster['inactive'][suid]

            s_query_info = roster['active'][suid]
            s_query_info['weeks_active'].append(week_of_query)

            queries_remaining = num_query - len(s_query_info['weeks_to_query'])
            weeks_remaining = last_week - week_of_query + 1

            # skip this week if the student was queried the prior week
            if (week_of_query - 1) in s_query_info['weeks_to_query']:
                pass
            # make a note if too few weeks remain to query every other week
            elif weeks_remaining < (2*queries_remaining-1):
                msg = "Not enough weeks for all queries since last joined"
                if msg not in s_query_info["note"]:
                    s_query_info["note"].append(msg)
                s_query_info['weeks_to_query'].append(week_of_query)
            # student *must* be queried every other week from this point on
            elif weeks_remaining == (2*queries_remaining-1):
                s_query_info['weeks_to_query'].append(week_of_query)
            elif queries_remaining > 0:
                if query_this_week(queries_remaining):
                    s_query_info['weeks_to_query'].append(week_of_query)

        for suid in curr_inactive:
            if suid in prev_active:
                roster['inactive'][suid] = roster['active'][suid]
                del roster['active'][suid]
            roster['inactive'][suid]['weeks_inactive'].append(week_of_query)

        return roster, hash_to_stud_info
