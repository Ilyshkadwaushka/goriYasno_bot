import logging
from typing import Optional, Dict, AnyStr, Tuple, List
from .database import Database
from psycopg2 import InterfaceError

logging.basicConfig(level=logging.INFO)

class UserDatabase(Database):

    def __init__(self, url: Optional[Dict]) -> None:
        super(UserDatabase, self).__init__(url)

    def user_exists(self, user_bot_id: int) -> Optional[Tuple]:
        """ User exists process """
        try:
            self.cursor.execute("SELECT * FROM users WHERE user_bot_id = %s", (user_bot_id,))
        except InterfaceError as exception:  # Updating connection
            # Logging exception
            logging.error(exception)
            self.connection()
            try:
                self.cursor.execute("SELECT * FROM users WHERE user_bot_id = %s", (user_bot_id,))
            except InterfaceError as ex:
                logging.error(ex)
                self.close()
                return

        result = self.cursor.fetchone()

        return result is not None

    def add_user(self, user_bot_id: int, token: AnyStr, username: AnyStr) -> None:
        """ User insert process """
        if username == None or username is None:
            username = token

        self.cursor.execute("INSERT INTO users (user_bot_id, token, username) VALUES (%s, %s, %s)",
                            (user_bot_id, token, username,))

        self.conn.commit()

    def update_user(self, user_bot_id: int, username: AnyStr) -> None:
        """ Проверка, существует ли объект в БД"""
        try:
            self.cursor.execute("UPDATE users SET username=%(username)s WHERE user_bot_id = %(user_bot_id)s", {
                "username": username,
                "user_bot_id": user_bot_id
            },)
        except InterfaceError as exception:  # Updating connection
            # Logging exception
            logging.error(exception)
            self.connection()
            try:
                self.cursor.execute("UPDATE users SET username=%(username)s WHERE user_bot_id = %(user_bot_id)s",{
                        "username": username,
                        "user_bot_id": user_bot_id
                    },)
            except InterfaceError as exception:
                logging.error(exception)
                self.close()
                return

        self.conn.commit()

    def valid_token(self, token: AnyStr) -> Optional[bool]:
        """ Проверка, существует ли объект в БД"""
        try:
            self.cursor.execute("SELECT * FROM users WHERE token = %s", (token,))
        except InterfaceError as exception:  # Updating connection
            # Logging exception
            logging.error(exception)
            self.connection()
            try:
                self.cursor.execute("SELECT * FROM users WHERE token = %s", (token,))
            except InterfaceError as ex:
                logging.error(ex)
                self.close()
                return

        result = self.cursor.fetchone()

        return result is None

    def get_token(self, user_bot_id: int) -> AnyStr:
        self.cursor.execute("SELECT token FROM users WHERE user_bot_id = %s", (user_bot_id,))

        result = self.cursor.fetchone()

        return result

    def get_user_bot_id(self, token: AnyStr) -> int:
        self.cursor.execute("SELECT user_bot_id FROM users WHERE token=%s", (token,))

        result = self.cursor.fetchone()[0]

        return result

    def set_score(self, token: AnyStr, score: int) -> None:
        self.cursor.execute("UPDATE users SET score=%(score)s WHERE token = %(token)s",
                            {
                                "score": score,
                                "token": token
                            },)

        self.conn.commit()

        return

    def get_score_by_user_bot_id(self, user_bot_id: int) -> int:
        self.cursor.execute("SELECT score FROM users WHERE user_bot_id = %s", (user_bot_id,))

        result = self.cursor.fetchone()[0]

        return result

    def get_score_by_token(self, token: AnyStr) -> int:
        self.cursor.execute("SELECT score FROM users WHERE token = %s", (token,))

        result = self.cursor.fetchone()[0]

        return result

    def isAdmin(self, user_bot_id: int) -> Optional[bool]:
        try:
            self.cursor.execute("SELECT isadmin FROM users WHERE user_bot_id = %s", (user_bot_id,))
        except InterfaceError as exception:  # Updating connection
            # Logging exception
            logging.error(exception)
            self.connection()
            try:
                self.cursor.execute("SELECT isadmin FROM users WHERE user_bot_id = %s", (user_bot_id,))
            except InterfaceError as ex:
                logging.error(ex)
                self.close()
                return

        result = self.cursor.fetchone()

        if result is not None:
            return result[0]
        return False

    def makeadmin(self, token: AnyStr, made_admin_by: int) -> None:
        self.cursor.execute("UPDATE users SET isadmin=%(isadmin)s, made_admin_by=%(made_admin_by)s WHERE token = %(token)s",
                            {
                                "isadmin": True,
                                "made_admin_by": made_admin_by,
                                "token": token
                            },)

        self.conn.commit()

        return

    def deladmin(self, token: AnyStr):
        self.cursor.execute("UPDATE users SET isadmin=%(isadmin)s, made_admin_by=%(made_admin_by)s WHERE token = %(token)s",
                            {
                                "isadmin": False,
                                "made_admin_by": None,
                                "token": token
                            }, )

        self.conn.commit()


    def get_all_players(self) -> List:
        self.cursor.execute("SELECT user_bot_id, username, score FROM users")

        result = self.cursor.fetchall()

        return result

    def delete_user(self, user_bot_id: int) -> None:
        self.cursor.execute("DELETE FROM users WHERE user_bot_id = %s", (user_bot_id,))
        self.conn.commit()

        return 