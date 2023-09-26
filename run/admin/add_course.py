import sys
import argparse
sys.path.append('..')

from src.utils import get_db

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('course_id', type=str)
    return parser.parse_args()

if __name__=='__main__':
    args = parse_args()

    db = get_db()

    course_id = args.course_id
    course_doc_ref = db.collection("courses").document(course_id)
    course_doc = course_doc_ref.get()
    if not course_doc.exists:
        print("ERROR: courseDoc with course ID doesn't exist.")

    else:
        course_info = course_doc.to_dict()
        db.collection("approvedCourses").document(course_id).set({
            'ended': False,
            'callNumber': course_info['callNumber'],
            'firstWeek': course_info['firstWeek']
        })
        print("Done.")
