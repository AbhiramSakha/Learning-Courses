# database.py
import sqlite3

class LearnerDatabase:
    def __init__(self, db_name="learners.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS learners (
                learner_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                course TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def add_learner(self, learner):
        try:
            self.conn.execute("INSERT INTO learners VALUES (?, ?, ?)",
                              (learner.learner_id, learner.name, learner.course))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_all_learners(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM learners")
        return cursor.fetchall()

    def update_learner(self, learner_id, name, course):
        self.conn.execute("UPDATE learners SET name=?, course=? WHERE learner_id=?",
                          (name, course, learner_id))
        self.conn.commit()

    def delete_learner(self, learner_id):
        self.conn.execute("DELETE FROM learners WHERE learner_id=?", (learner_id,))
        self.conn.commit()
