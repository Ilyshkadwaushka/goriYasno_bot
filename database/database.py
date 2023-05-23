import logging
import psycopg2
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)

class Database:

    def __init__(self, url: Optional[Dict] = None) -> None:
        """ DataBase configuration initialization  """
        if url is None:
            url = {}
        self.db_name = url.get('db_name', '')
        self.user = url.get('user', '')
        self.password = url.get('password', '')
        self.host = url.get('host', '')
        self.port = url.get('port', '')

        """ Connection initialization """
        self.connection()

    def connection(self) -> None:
        """ Set connection with database """
        try:
            self.conn = psycopg2.connect(dbname=self.db_name, user=self.user, password=self.password, host=self.host,
                                         port=self.port, sslmode='require')
        except psycopg2.OperationalError as exception:
            logging.error(exception)
            return
        self.cursor = self.conn.cursor()


    def close(self) -> None:
        """ Close connection with database """
        self.conn.close()
        self.cursor.close()
