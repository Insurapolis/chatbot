import os
from dotenv import load_dotenv
import logging
import psycopg
from psycopg.rows import dict_row

load_dotenv()

logger = logging.getLogger(__name__)


QUERY_CREATE_USER_TABLE = """
CREATE TABLE IF NOT EXISTS {user_table_name} (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    firstname TEXT NOT NULL,
    surname TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
"""

QUERY_CREATE_CONVERSATION_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS {conversation_messages_table_name} (
    id SERIAL PRIMARY KEY,
    conversation_uuid UUID NOT NULL,
    message JSONB NOT NULL,
    tokens INT NOT NULL,
    cost FLOAT NOT NULL,
    send_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    FOREIGN KEY (conversation_uuid) REFERENCES {conversation_table_name}(uuid)

);"""

QUERY_CREATE_CONVERSATION_TABLE = """
CREATE TABLE IF NOT EXISTS {conversation_table_name} (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    active BOOLEAN,
    FOREIGN KEY (user_id) REFERENCES {user_table_name}(id) -- This line adds the foreign key constraint
)
"""

QUERY_GET_LIST_CONVERSATION = """
SELECT * FROM {table_name} 
WHERE active = TRUE
AND user_id = {user_id}
"""


class QueryConversations:
    def __init__(self, connection_string: str) -> None:

        try:
            self.connection = psycopg.connect(connection_string)
            self.cursor = self.connection.cursor(row_factory=dict_row)
        except psycopg.OperationalError as error:
            logger.error(error)

        self.initiate_table_from_env()

    def initiate_table_from_env(self):
        self.cursor.execute(
            query=QUERY_CREATE_USER_TABLE.format(
                user_table_name=os.getenv("TABLE_NAME_USER")
            )
        )
        self.cursor.execute(
            query=QUERY_CREATE_CONVERSATION_TABLE.format(
                conversation_table_name=os.getenv("TABLE_NAME_CONVERSATION"),
                user_table_name=os.getenv("TABLE_NAME_USER"),
            )
        )
        self.cursor.execute(
            query=QUERY_CREATE_CONVERSATION_MESSAGES_TABLE.format(
                conversation_messages_table_name=os.getenv(
                    "TABLE_NAME_CONVERSATION_MESSAGES"
                ),
                conversation_table_name=os.getenv("TABLE_NAME_CONVERSATION"),
            )
        )
        self.connection.commit()

    def create_new_consersation(self, user_id: int, conv_uuid: str):
        query = """
        INSERT INTO {table_name} (uuid, user_id, created_at, active)
        VALUES (%s, %s, now(), TRUE);
        """.format(
            table_name=os.getenv("TABLE_NAME_CONVERSATION")
        )

        # Execute the query with the provided parameters to prevent SQL injection
        self.cursor.execute(query, (conv_uuid, user_id))
        self.connection.commit()

    def create_new_user(self, email: str, firstname: str, surname: str):
        query = """
        INSERT INTO {table_name} (email, firstname, surname, created_at)
        VALUES (%s, %s, %s, NOW());
        """.format(
            table_name=os.getenv("TABLE_NAME_USER")
        )
        self.cursor.execute(query, (email, firstname, surname))
        self.connection.commit()
