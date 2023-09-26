import sys
import argparse
sys.path.append('..')

from src.utils import get_db
from datetime import date, timedelta, datetime

def surveyed_next_week(doc_dict):
    today = date.today()
    format_str = '%m/%d/%Y'
    first = datetime.strptime(doc_dict['firstWeek'], format_str).date()
    last = datetime.strptime(doc_dict['lastWeek'], format_str).date()

    next_monday = date.today() + timedelta(days=7-today.weekday())
    first_monday = first + timedelta(days=-first.weekday())
    last_monday = last + timedelta(days=-last.weekday())

    return first_monday <= next_monday and next_monday <= last_monday

if __name__=='__main__':
    db = get_db()

    approved_course_hash = [
        doc.id for doc in
        db.collection('approvedCourses')
        .where('ended', '==', False)
        .stream()
    ]

    for course_hash in approved_course_hash:
        doc_dict = (db.collection('courses')
                    .document(course_hash)
                    .get().to_dict())

        if not surveyed_next_week(doc_dict):
            continue
        print(doc_dict['createdByEmail'])
        # print(doc_dict)
        roster = (db.collection('rosters')
                  .document(course_hash)
                  .get().to_dict())
        print(len(roster['id']))

