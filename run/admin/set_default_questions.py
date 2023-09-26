import sys
sys.path.append('..')
import os
import json

from src.utils import get_db
from src.constants import DATA_DIR

if __name__=='__main__':
    db = get_db()

    default_questions_path = os.path.join(DATA_DIR, 'default_questions.json')
    default_questions = json.load(open(default_questions_path))
    db.collection('shared').document('defaultQuestions').set(default_questions)
