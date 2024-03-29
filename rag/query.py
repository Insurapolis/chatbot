import os
import pandas as pd
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine
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

QUERY_CREATE_CONVERSATION_TABLE = """
CREATE TABLE IF NOT EXISTS {conversation_table_name} (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    active BOOLEAN,
    FOREIGN KEY (user_id) REFERENCES {user_table_name}(id) ON DELETE CASCADE
)
"""

QUERY_CREATE_CONVERSATION_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS {conversation_messages_table_name} (
    id SERIAL PRIMARY KEY,
    conversation_uuid UUID NOT NULL,
    message JSONB NOT NULL,
    tokens INT NOT NULL,
    cost FLOAT NOT NULL,
    send_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    FOREIGN KEY (conversation_uuid) REFERENCES {conversation_table_name}(uuid) ON DELETE CASCADE
);"""

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
        self.insert_dummy_data()

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

    def get_conversation_by_uuid(self, uuid):

        query = """
        SELECT message FROM {table_messages} WHERE conversation_uuid = %s order by id
        """.format(
            table_messages=os.getenv("TABLE_NAME_CONVERSATION_MESSAGES")
        )

        self.cursor.execute(query, (uuid,))
        items = [record["message"] for record in self.cursor.fetchall()]

        return items

    def get_list_conversations_by_user(self, user_id: int):

        # Replace {table_name} with the actual property holding your table name, e.g.,
        query = """
        SELECT uuid FROM {conversation_table_name}
        WHERE user_id = %s""".format(
            conversation_table_name=os.getenv("TABLE_NAME_CONVERSATION")
        )
        # Execute the query with the provided user_id as a parameter to safely avoid SQL injection
        self.cursor.execute(query, (user_id,))

        # Fetch all rows of the query result
        rows = self.cursor.fetchall()

        return rows

    def get_total_tokens_used_per_user(self, user_id):
        query = """
        SELECT SUM(m.tokens) AS total_tokens
        FROM {table_conversation} AS c
        JOIN {table_messages} AS m ON c.uuid = m.conversation_uuid
        WHERE c.user_id = %s
        """.format(
            table_messages=os.getenv("TABLE_NAME_CONVERSATION_MESSAGES"),
            table_conversation=os.getenv("TABLE_NAME_CONVERSATION"),
        )

        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()

        if result and result["total_tokens"] is not None:
            return result["total_tokens"]
        else:
            return 0

    def insert_dummy_user_data(self, truncate: bool = False):
        if truncate:
            query_truncate = """
            TRUNCATE TABLE {table_user} CASCADE;
            """.format(
                table_user=os.getenv("TABLE_NAME_USER")
            )

            self.cursor.execute(query=query_truncate)
            self.connection.commit()

        FILEPATH_USER = "./data/users.csv"
        df_user = pd.read_csv(FILEPATH_USER)

        query_user = """
        INSERT INTO {table_user} (email, firstname, surname)
        VALUES (%s, %s, %s)""".format(
            table_user=os.getenv("TABLE_NAME_USER")
        )

        for i, row in df_user.iterrows():
            email = row["email"]
            firstname = row["firstname"]
            surnname = row["surname"]

            self.cursor.execute(query_user, (email, firstname, surnname))

        self.connection.commit()

    def insert_dummy_conversation_data(self, truncate: bool = False):

        if truncate:
            query_truncate = """
            TRUNCATE TABLE {table_conversation} CASCADE;
            """.format(
                table_conversation=os.getenv("TABLE_NAME_CONVERSATION")
            )

            self.cursor.execute(query=query_truncate)
            self.connection.commit()

        FILEPATH_USER = "./data/conversation.csv"
        df_conversation = pd.read_csv(FILEPATH_USER)

        query_user = """
        INSERT INTO {table_conversation} (uuid, user_id, active)
        VALUES (%s, %s, %s)""".format(
            table_conversation=os.getenv("TABLE_NAME_CONVERSATION")
        )

        for i, row in df_conversation.iterrows():
            uuid = row["uuid"]
            user_id = row["user_id"]
            active = row["active"]

            self.cursor.execute(query_user, (uuid, user_id, active))

        self.connection.commit()

    def insert_dummy_message_data(self, truncate: bool = False):

        if truncate:
            query_truncate = """
            TRUNCATE TABLE {table_message} CASCADE;
            """.format(
                table_message=os.getenv("TABLE_NAME_CONVERSATION_MESSAGES")
            )

            self.cursor.execute(query=query_truncate)
            self.connection.commit()

        FILEPATH_MESSAGES = "./data/messages.xls"
        df_messages = pd.read_excel(FILEPATH_MESSAGES)

        query_insert_messages = """
        INSERT INTO {table_message}  
        (conversation_uuid, message, tokens, cost, send_at)
        VALUES (%s, %s, %s, %s, %s);
        """.format(
            table_message=os.getenv("TABLE_NAME_CONVERSATION_MESSAGES")
        )

        for i, row in df_messages.iterrows():
            conversation_uuid = row["conversation_uuid"]
            message = row["message"]
            tokens = row["tokens"]
            cost = row["cost"]
            send_at = row["send_at"]

            self.cursor.execute(
                query_insert_messages,
                (conversation_uuid, message, tokens, cost, send_at),
            )

        self.connection.commit()

    def insert_dummy_data(self):

        query_empty_user = (
            """SELECT EXISTS (SELECT 1 FROM {table_user} LIMIT 1);""".format(
                table_user=os.getenv("TABLE_NAME_USER")
            )
        )

        query_empty_conv = (
            "SELECT EXISTS (SELECT 1 FROM {table_conversation} LIMIT 1);".format(
                table_conversation=os.getenv("TABLE_NAME_CONVERSATION")
            )
        )
        query_empty_message = (
            "SELECT EXISTS (SELECT 1 FROM {table_message} LIMIT 1);".format(
                table_message=os.getenv("TABLE_NAME_CONVERSATION_MESSAGES")
            )
        )

        user_is_not_empty = self.cursor.execute(query_empty_user).fetchone()["exists"]
        conv_is_not_empty = self.cursor.execute(query_empty_conv).fetchone()["exists"]
        message_is_not_empty = self.cursor.execute(query_empty_message).fetchone()[
            "exists"
        ]

        if not user_is_not_empty:
            self.insert_dummy_user_data()

        if not conv_is_not_empty:
            self.insert_dummy_conversation_data()

        if not message_is_not_empty:
            self.insert_dummy_message_data()
