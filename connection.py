import database_common
from psycopg2 import sql


@database_common.connection_handler
def get_questions_list(cursor, limit=None):
    query = """
    SELECT q.id, q.title, q.message, q.submission_time, q.view_number, q.vote_number, COUNT(a.id) AS answers
    FROM question q
    LEFT JOIN answer a on q.id = a.question_id
    GROUP BY q.id
    ORDER BY submission_time DESC  
    """

    if limit:
        query += " LIMIT 5"

    cursor.execute(query)
    questions = cursor.fetchall()
    return questions


@database_common.connection_handler
def get_answer_comments(cursor):
    cursor.execute(
        """
        SELECT id, answer_id, message, submission_time, edited_count, user_id
        FROM comment
        WHERE question_id IS NULL 
        """
    )
    comments = cursor.fetchall()
    return comments


@database_common.connection_handler
def get_answer_ids(cursor, question_id):
    cursor.execute(
        """
        SELECT a.id
        FROM answer a
        JOIN question q on a.question_id = q.id
        WHERE q.id = %(question_id)s;
        """, {"question_id": question_id}
    )
    answer_ids = cursor.fetchall()
    return answer_ids


@database_common.connection_handler
def get_question_id(cursor, table, entry_id):
    cursor.execute(
        sql.SQL(
            """
            SELECT question_id
            FROM {}
            WHERE id = %(entry_id)s
            """
        ).format(sql.Identifier(table)), {"entry_id": entry_id}
    )
    question_id = cursor.fetchall()
    return question_id


@database_common.connection_handler
def get_question_id_from_answer_comment(cursor, comment_id):
    cursor.execute(
        """
        SELECT a.question_id
        FROM comment c
        JOIN answer a on c.answer_id = a.id
        WHERE c.id = %(comment_id)s;
        """, {"comment_id": comment_id}
    )
    question_id = cursor.fetchall()
    return question_id


@database_common.connection_handler
def get_question_tags(cursor, question_id):
    cursor.execute(
        """
        SELECT *
        FROM tag t
        LEFT JOIN question_tag q on t.id = q.tag_id
        WHERE q.question_id = %(question_id)s;
        """, {"question_id": question_id}
    )
    tags = cursor.fetchall()
    return tags


@database_common.connection_handler
def get_all_tags(cursor):
    cursor.execute(
        """
        SELECT DISTINCT *
        FROM tag
        """
    )
    tags = cursor.fetchall()
    return tags


@database_common.connection_handler
def get_tag_id(cursor, attribute):
    cursor.execute(
            """
            SELECT id
            FROM tag
            WHERE name = %(attribute)s
            """, {"attribute": attribute}
    )
    question_id = cursor.fetchall()
    return question_id


@database_common.connection_handler
def get_tags_with_question_ids(cursor):
    cursor.execute(
        """
        SELECT q.question_id, t.name
        FROM question_tag q
        FULL JOIN tag t on q.tag_id = t.id
        """
    )
    tags = cursor.fetchall()
    return tags


@database_common.connection_handler
def get_user_name(cursor, name):
    cursor.execute("SELECT user_name FROM users WHERE user_name=%(name)s", {"name": name})
    user_names = cursor.fetchall()
    return user_names


@database_common.connection_handler
def get_user_password(cursor, name):
    cursor.execute("SELECT password FROM users WHERE user_name=%(name)s", {"name": name})
    password = cursor.fetchall()
    return password


@database_common.connection_handler
def get_users(cursor):
    cursor.execute("SELECT id, user_name FROM users")
    users = cursor.fetchall()
    return users


####################################################################################
# Multifunction queries
####################################################################################


@database_common.connection_handler
def simple_select(cursor, table, where_col, where_param):
    cursor.execute(
        sql.SQL(
            """
            SELECT * FROM {}
            WHERE {} = %(where_param)s
            """,
        ).format(sql.Identifier(table), sql.Identifier(where_col)), {"where_param": where_param}
    )
    details = cursor.fetchall()
    return details


@database_common.connection_handler
def simple_insert(cursor, table, columns, values):
    cursor.execute(
        sql.SQL(
            """
            INSERT INTO {0} ({1})
            VALUES ({2})
            """
        ).format(
            sql.Identifier(table),
            sql.SQL(", ").join(map(sql.Identifier, columns)),
            sql.SQL(", ").join(map(sql.Literal, values))
        )
    )


@database_common.connection_handler
def update_table(cursor, table, columns, values, entry_id):

    sql_query = "UPDATE {0} SET "
    sql_query += get_updates(columns, values)
    sql_query += " WHERE id={1}"

    cursor.execute(
        sql.SQL(
            sql_query
        ).format(
            sql.Identifier(table),
            sql.Literal(entry_id)
        )
    )


@database_common.connection_handler
def simple_delete(cursor, table, where_col, where_param):
    cursor.execute(
        sql.SQL(
            """
            DELETE FROM {}
            WHERE {} = %(where_param)s
            """,
        ).format(sql.Identifier(table), sql.Identifier(where_col)), {"where_param": where_param}
    )


def get_updates(columns, values):
    """Return the SET parameters for the UPDATE SQL statement"""

    update_list = []
    for col, value in zip(columns, values):
        update_list.append(" {} = '{}'".format(col, value))
    update_set = ",".join(update_list)
    return update_set


@database_common.connection_handler
def get_user_id(cursor, user_name):
    cursor.execute("SELECT id FROM users WHERE user_name=%(user_name)s;", {"user_name": user_name})
    id = cursor.fetchall()
    return id


####################################################################################
# Search queries
####################################################################################


@database_common.connection_handler
def search_question_titles(cursor, search_term):
    cursor.execute(
        """
        SELECT id, title
        FROM question
        WHERE to_tsvector(title) @@ plainto_tsquery(%(search_term)s)
        """, {"search_term": search_term}
    )
    result = cursor.fetchall()
    return result


@database_common.connection_handler
def search_question_messages(cursor, search_term):
    cursor.execute(
        """
        SELECT id, title, message
        FROM question
        WHERE to_tsvector(message) @@ plainto_tsquery(%(search_term)s)
        """, {"search_term": search_term}
    )
    result = cursor.fetchall()
    return result


@database_common.connection_handler
def search_answers(cursor, search_term):
    cursor.execute(
        """
        SELECT q.id, q.title, a.message
        FROM question q 
        LEFT JOIN answer a 
        ON q.id = a.question_id
        WHERE to_tsvector(a.message) @@ plainto_tsquery(%(search_term)s)
        """, {"search_term": search_term}
    )
    result = cursor.fetchall()
    return result

