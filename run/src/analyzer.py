import json
import os
import numpy as np
from pprint import pprint
from collections import defaultdict
import itertools
from textwrap import wrap

from src.utils import (
    week_string, get_course_week_number,
    survey_has_ended
)
from src.predictor import Predictor
from src.plotter import plot_rating, plot_mood
from src.constants import DATA_DIR

# TODO:
# 1. what if too few classes in a group have responses?

RATING_QUAL = {
    'Excellent': 5,
    'Good': 4,
    'Ok': 3,
    'Below Average': 2,
    'Poor': 1
}

MOOD_QID = 'default3'

def get_q_name(qid):
    header = ""
    if qid.startswith('default'):
        base = 0
        header = 'default'
    elif qid.startswith('custom'):
        base = 4
        header = 'custom'
    qnum = int(qid.split(header)[1])
    return f'question{qnum+base} ({header})'

def get_prompt_fname(prompt):
    return prompt.replace('/', '|')

class Analyzer:

    def __init__(self, global_date):
        global_week = week_string(global_date)

        classes_info_path = os.path.join(
            DATA_DIR, 'courses_info',
            f'{global_week}.json'
        )

        groups_info_path = os.path.join(
            DATA_DIR, 'groups_info.json',
        )

        answers_path = os.path.join(
            DATA_DIR, 'answers',
            f'{global_week}.answers.json'
        )

        questions_path = os.path.join(
            DATA_DIR, 'questions',
            f'{global_week}.questions.json',
        )

        queried_students_path = os.path.join(
            DATA_DIR, 'queried_students',
            f'{global_week}.queried_students.json'
        )

        classes_info = json.load(open(classes_info_path))
        answers = json.load(open(answers_path))
        questions = json.load(open(questions_path))
        queried_students = json.load(open(queried_students_path))
        groups_info = json.load(open(groups_info_path))
        class_to_group = defaultdict(
            lambda :None,
            dict(itertools.chain.from_iterable([
                [(clss, grp) for clss in clss_lst]
                 for grp, clss_lst in groups_info.items()
            ]))
        )
        # 'all' group has all classes in classes_info
        groups_info['all'] = list(classes_info.keys())

        queried_size = dict(
            (course, len(queries)) for course, queries
            in queried_students.items()
        )

        collected_answers = defaultdict(lambda: defaultdict(list))
        answered_size = {}
        for course, course_responses in answers.items():
            course_answered = 0
            for stud_hash, response in course_responses.items():
                if response is None:
                    continue
                course_answered += 1
                for qid, resp in response.items():
                    collected_answers[course][qid].append(resp)
            answered_size[course] = course_answered

        qid_to_question = defaultdict(dict)
        for course, course_questions in questions.items():
            for qinfo in course_questions['questions']:
                qid = qinfo['qid']
                qid_to_question[course][qid] = qinfo

        print('queried:')
        pprint(queried_size)
        print('answered:')
        pprint(answered_size)
        no_response = [clss for clss, cnt in answered_size.items() if cnt == 0]
        all_response_rate = sum(answered_size.values())/sum(queried_size.values())
        print(all_response_rate)
        print('no response: ', no_response)

        self.global_date = global_date
        self.global_week = global_week
        self.week_of_query = dict(
            (class_hash, get_course_week_number(global_date, course_info))
            for class_hash, course_info in classes_info.items()
        )
        self.classes_info = classes_info
        self.groups_info = groups_info
        self.class_to_group = class_to_group

        self.answers = answers
        self.questions = questions
        self.queried_students = queried_students
        self.qid_to_question = qid_to_question

        self.no_response = no_response
        self.collected_answers = collected_answers
        self.queried_size = queried_size
        self.answered_size = answered_size
        self.all_response_rate = all_response_rate

        self.mood_predictors = {}
        self.groups_stats = {}

    def generate_digest_files(self):
        for class_hash, q_answers in self.collected_answers.items():
            if class_hash not in self.classes_info:
                continue
            class_info = self.classes_info[class_hash]
            print(class_hash, class_info['callNumber'])
            for qid, answers in q_answers.items():
                q_info = self.qid_to_question[class_hash][qid]
                self.save_answers(class_hash, q_info, answers)
                if q_info['type'] in ['Rating (1-5)', 'Rating (Qualitative)']:
                    self.process_rating_answers(class_hash, q_info, answers)
            self.process_mood(class_hash, q_answers[MOOD_QID])

            if survey_has_ended(self.global_date, class_info):
                print(class_hash, 'last survey week')
                self._generate_participation(class_hash)

    def _generate_participation(self, class_hash):
        roster_path = os.path.join(
            DATA_DIR, 'rosters',
            self.global_week,
            f'{class_hash}.roster.json'
        )
        roster = json.load(open(roster_path))

        participation = {
            suid: {
                'responded' : len(set(s_info['weeks_completed'])),
                'total' : len(set(s_info['weeks_to_query']))
            }
            for suid, s_info in roster['active'].items()
        }

        total_responded = sum(v['total'] > 1 for v in participation.values())

        no_participation_fname = os.path.join(
            DATA_DIR, 'answers', self.global_week, 'no_participation_lst.txt'
        )
        if total_responded <= 3:
            with open(no_participation_fname, 'a') as f:
                f.write(class_hash + '\n')

        report_fname = os.path.join(
            DATA_DIR, 'answers', self.global_week,
            class_hash, 'participation.txt'
        )

        with open(report_fname, 'w') as f:
            f.write('suid,responded,queried\n')
            for suid, count in participation.items():
                if count['responded'] > count['total']:
                    pprint(roster['active'][suid])
                f.write(f'{suid},{count["responded"]},{count["total"]}\n')


    def get_group_mood_stats(self):
        """
            Get mood statistics per group for the current week only.
            Control which groups should be included in the figure.
                (e.g., omit groups that are too small)
        """
        course_moods = dict()
        # get current week's mood statistics per class
        for class_hash, q_answers in self.collected_answers.items():
            mood_pred = self.get_mood_predictor(
                class_hash, q_answers[MOOD_QID]
            )
            mu = mood_pred.mu[-1]
            var = mood_pred.var[-1]
            course_moods[class_hash] = (mu, var)

        groups_lst = list(self.groups_info.keys())
        average_moods = {grp: {} for grp in groups_lst}

        groups_stats = {}
        for grp in groups_lst:
            group_course_moods = [
                course_moods[class_hash]
                for class_hash in self.groups_info[grp]
                if class_hash in course_moods
            ]
            print(f'group: {grp}, size: {len(group_course_moods)}')

            # If a subgroup is too small, skip it!
            if len(group_course_moods) < 3 and grp != 'all':
                print(f'skip: {grp}')
                groups_stats[grp] = None
                continue

            week_mu_lst = [mu+3 for mu,_ in group_course_moods]
            week_var_lst = [var for _,var in group_course_moods]
            avg_mu = np.mean(week_mu_lst)
            avg_var = np.sum(week_var_lst)/(len(week_var_lst)**2)
            average_moods[grp] = (avg_mu, avg_var)

            groups_stats[grp] = {
                'avg_high': avg_mu + np.sqrt(avg_var),
                'avg': avg_mu,
                'avg_low': avg_mu - np.sqrt(avg_var)
            }

        groups_stats_path = os.path.join(
            DATA_DIR, 'answers',
            self.global_week, 'group_mood.json'
        )
        if not os.path.isdir(os.path.dirname(groups_stats_path)):
            os.makedirs(os.path.dirname(groups_stats_path))
        json.dump(groups_stats, open(groups_stats_path, 'w'), indent=4)
        pprint(groups_stats)
        self.groups_stats[self.global_week] = groups_stats

    def save_digest_info(self):
        info = {
            "no_response": self.no_response,
            "has_response": list(self.collected_answers.keys()),
            'queried_size': self.queried_size,
            "all_response_rate": self.all_response_rate,
            "week_of_query": self.week_of_query,
            "answered_size": self.answered_size
        }
        with open('digest_info.json', 'w') as f:
            json.dump(info, f, indent=4)

    def send_digests(self, mailer):
        for class_hash in self.no_response:
            print('no response: ', class_hash)
            admins = self.classes_info[class_hash]['admins']
            call_number = self.classes_info[class_hash]['callNumber']
            mailer._send_noresponse_instructor_weekly_digest(
                call_number,
                admins,
                self.queried_size[class_hash],
                self.all_response_rate,
                self.week_of_query[class_hash],
                class_hash
            )

        for class_hash in self.collected_answers.keys():
            contacts = self.classes_info[class_hash]['admins']
            print(class_hash)
            admins = self.classes_info[class_hash]['admins']
            call_number = self.classes_info[class_hash]['callNumber']
            mailer._send_instructor_weekly_digest(
                call_number,
                contacts,
                self.queried_size[class_hash],
                self.answered_size[class_hash],
                self.all_response_rate,
                self.week_of_query[class_hash],
                class_hash,
                send_participation=(survey_has_ended(
                    self.global_date, self.classes_info[class_hash]
                )))

    def save_answers(self, class_hash, q_info, answers):
        dirname = self._get_answer_dirname(class_hash)

        prompt_fname = get_prompt_fname(q_info["prompt"])[:100] # truncated
        fname = os.path.join(dirname,
            f'"{prompt_fname}"_week{self.week_of_query[class_hash]}.txt')

        with open(fname, 'w') as fp:
            fp.write((
                f'Prompt: {q_info["prompt"]}\n'
                f'Week: {self.week_of_query[class_hash]}\n'
                f'Response Count: {len(answers)}'
                f'(out of {self.queried_size[class_hash]}'
                 ' Students Queried)\n\n'))
            for response in answers:
                fp.write(response + '\n')

    def process_rating_answers(self, class_hash, q_info, answers):
        if q_info['type'] == 'Rating (1-5)':
            get_rating = dict((str(x),x) for x in [1, 2, 3, 4, 5])
            xtick_labels = [1, 2, 3, 4, 5]
        elif q_info['type'] == 'Rating (Qualitative)':
            get_rating = RATING_QUAL
            xtick_labels = ['Poor', 'Below Average', 'Ok', 'Good', 'Excellent']
        else:
            raise Exception(q_info['type'])

        dirname = self._get_answer_dirname(class_hash)

        answers = [get_rating[ans] for ans in answers]
        call_number = self.classes_info[class_hash]['callNumber']
        title = (
            f"[{call_number} Week {self.week_of_query[class_hash]}] "
            f"{q_info['prompt']}"
        )
        title = "\n".join(wrap(title,70))

        prompt_fname = get_prompt_fname(q_info["prompt"])
        fig = plot_rating(title, answers, xtick_labels)
        fname = os.path.join(
            dirname,
            f'"{prompt_fname}"_week{self.week_of_query[class_hash]}.png'
        )
        fig.savefig(fname)

    def process_mood(self, class_hash, answers, write_mood=True):
        predictor = self.get_mood_predictor(class_hash, answers)

        dirname = self._get_answer_dirname(class_hash)

        fig = plot_mood(class_hash, self, answers, predictor)
        fig.savefig(os.path.join(dirname, 'weekly_mood.png'))

        if write_mood:
            dirname = self._get_answer_dirname('mood')
            mood_path = os.path.join(dirname, f'{class_hash}.moods.json')
            json.dump(answers, open(mood_path, 'w'), indent=4)

    def get_mood_predictor(self, class_hash, answers):
        if class_hash in self.mood_predictors:
            return self.mood_predictors[class_hash]

        course_current_week = self.week_of_query[class_hash]
        predictor = Predictor()
        answers = [RATING_QUAL[ans] for ans in answers]

        course_info = self.classes_info[class_hash]

        first_survey_week = course_info['first_survey_week']

        # get previous weeks' moods
        for i in range(first_survey_week, course_current_week):
            curr_week_str = week_string(
                self.global_date, offset=i-course_current_week
            )
            prev_mood_path = os.path.join(
                DATA_DIR, 'answers',
                curr_week_str,
                'mood', f'{class_hash}.moods.json'
            )

            # add groups stats for past weeks
            if curr_week_str not in self.groups_stats:
                grp_stats_path = os.path.join(
                    DATA_DIR, 'answers',
                    curr_week_str, 'group_mood.json'
                )
                grp_stats = json.load(open(grp_stats_path))
                self.groups_stats[curr_week_str] = grp_stats

            if not os.path.isfile(prev_mood_path):
                continue

            moods = [RATING_QUAL[ans] for ans in json.load(open(prev_mood_path))]
            predictor.make_week_estimate(moods, i)

        # This week's group stats is already set
        predictor.make_week_estimate(answers, course_current_week)
        self.mood_predictors[class_hash] = predictor
        return predictor

    def _get_answer_dirname(self, class_hash):
        dirname = os.path.join(
            DATA_DIR, 'answers', self.global_week, class_hash
        )
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        return dirname

