import logging
import datetime
from typing import Dict, Optional
from .database import Database

logging.basicConfig(level=logging.INFO)

class ScoreLogsDatabase(Database):

    def __init__(self, url: Optional[Dict]) -> None:
        super(ScoreLogsDatabase, self).__init__(url)

    def create_log(self, user_bot_id_from: int, user_bot_id_to: int, score: int) -> None:
        self.cursor.execute("INSERT INTO scorelogs (user_bot_id_from, user_bot_id_to, score, date) VALUES (%s, %s, %s, %s)",
                            (user_bot_id_from, user_bot_id_to, score, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),))

        self.conn.commit()
        return

