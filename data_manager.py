import connection
from datetime import datetime
import os

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


####################################################################################
# Display block
####################################################################################


def get_latest_five_questions():
    questions = connection.get_questions_list(True)
    return questions


def get_all_questions():
    questions = connection.get_questions_list()
    return questions


def get_question_details(question_id):
    question_details = connection.simple_select("question", "id", question_id)
    return question_details[0]


def get_question_answers(question_id):
    answers = connection.simple_select("answer", "question_id", question_id)
    return answers


def get_answer(answer_id):
    answer = connection.simple_select("answer", "id", answer_id)
    return answer[0]


def get_question_comments(question_id):
    comments = connection.simple_select("comment", "question_id", question_id)
    comments = order_list_of_dicts(comments, "submission_time", "desc")
    return comments


def get_answer_comments():
    comments = connection.get_answer_comments()
    comments = order_list_of_dicts(comments, "submission_time", "desc")
    return comments


def get_comment(comment_id):
    comment = connection.simple_select("comment", "id", comment_id)
    return comment[0]


def get_question_tags(question_id):
    tags = connection.get_question_tags(question_id)
    return tags


def get_all_tags():
    tags = connection.get_all_tags()
    return tags


def get_tags_with_question_ids():
    tags = connection.get_tags_with_question_ids()
    return tags

####################################################################################
# Insert block
####################################################################################


def add_question(title, message, image=None):
    columns = ["submission_time", "view_number", "vote_number", "title", "message"]
    values = []

    dt = datetime.now().replace(microsecond=000000)
    values.append(str(dt))
    values.append(0)
    values.append(0)
    values.append(title)
    values.append(message)

    if image:
        columns.append("image")
        values.append(image)

    connection.simple_insert("question", columns, values)


def add_new_answer(message, question_id, image=None):
    columns = ["submission_time", "vote_number", "question_id", "message"]
    values = []

    dt = datetime.now().replace(microsecond=000000)
    values.append(str(dt))
    values.append(0)
    values.append(question_id)
    values.append(message)

    if image:
        columns.append("image")
        values.append(image)

    connection.simple_insert("answer", columns, values)


def add_comment(column, column_id, message):
    columns = [column, "message", "submission_time", "edited_count"]
    values = []

    dt = datetime.now().replace(microsecond=000000)
    values.append(column_id)
    values.append(message)
    values.append(dt)
    values.append(0)

    connection.simple_insert("comment", columns, values)


def add_new_tag(name):
    column = ["name"]
    value = [name]
    connection.simple_insert("tag", column, value)


def add_tag_to_question(question_id, tag_id):
    columns = ["question_id", "tag_id"]
    values = []
    values.append(question_id)
    values.append(tag_id)
    connection.simple_insert("question_tag", columns, values)


####################################################################################
# Edit block
####################################################################################


def edit_question(title, message, question_id, image=None):
    columns = ["title", "message"]
    values = []

    values.append(title)
    values.append(message)

    if image:
        delete_image("question", "id", question_id)
        columns.append("image")
        values.append(image)

    connection.update_table("question", columns, values, question_id)


def edit_answer(message, answer_id, image=None):
    columns = ["message"]
    values = []

    values.append(message)

    if image:
        delete_image("answer", "id", answer_id)
        columns.append("image")
        values.append(image)

    connection.update_table("answer", columns, values, answer_id)


def edit_comment(message, comment_id):
    comment = connection.simple_select("comment", "id", comment_id)[0]
    columns = ["message", "edited_count"]
    values = []
    edited = str(comment["edited_count"] + 1)

    values.append(message)
    values.append(edited)

    connection.update_table("comment", columns, values, comment_id)


def vote(table, direction, entry_id):
    record = connection.simple_select(table, "id", entry_id)[0]
    column = ["vote_number"]

    if direction == "up":
        value = [str(record["vote_number"]+1)]
    else:
        value = [str(record["vote_number"]-1)]

    connection.update_table(table, column, value, entry_id)


####################################################################################
# Delete block
####################################################################################


def delete_question(question_id):
    answer_ids = get_answer_ids(question_id)
    delete_image("question", "id", question_id)
    connection.simple_delete("comment", "question_id", question_id)
    connection.simple_delete("question_tag", "question_id", question_id)
    for answer_id in answer_ids:
        delete_answer(answer_id)
    connection.simple_delete("question", "id", question_id)
    return answer_ids


def delete_answer(answer_id):
    delete_image("answer", "id", answer_id)
    connection.simple_delete("comment", "answer_id", answer_id)
    connection.simple_delete("answer", "id", answer_id)


def delete_comment(comment_id):
    connection.simple_delete("comment", "id", comment_id)


def delete_question_tag(tag_id):
    connection.simple_delete("question_tag", "tag_id", tag_id)


####################################################################################
# Get ids block
####################################################################################


def get_answer_ids(question_id):
    query_result = connection.get_answer_ids(question_id)
    answer_ids = []
    for answer_id in query_result:
        for value in answer_id:
            answer_ids.append(answer_id[value])
    return answer_ids


def get_question_id(table, entry_id):
    query_result = connection.get_question_id(table, entry_id)
    question_id = query_result[0]["question_id"]
    return question_id


def get_question_id_from_comment(comment_id):
    comment = get_comment(comment_id)
    if comment["question_id"] is not None:
        return comment["question_id"]

    query_result = connection.get_question_id_from_answer_comment(comment_id)
    question_id = query_result[0]["question_id"]
    return question_id


def get_tag_id(attribute):
    query_result = connection.get_tag_id(attribute)
    tag_id = query_result[0]["id"]
    return tag_id


####################################################################################
# Other
####################################################################################


def view_count_increase(question_id):
    question = connection.simple_select("question", "id", question_id)[0]

    columns = ["view_number"]
    values = [str(question["view_number"] + 1)]

    connection.update_table("question", columns, values, question_id)


def order_list_of_dicts(list_of_dicts, orderby, order_direction):
    reverse = True if order_direction == "desc" else False
    strings = ["title", "message"]

    if orderby in strings:
        sorted_questions = sorted(list_of_dicts, key=lambda key: key[orderby].lower(), reverse=reverse)
    else:
        sorted_questions = sorted(list_of_dicts, key=lambda key: key[orderby], reverse=reverse)
    return sorted_questions


def get_answer_ids_with_comment(key, list_of_dict):
    ids = [elem[key] for elem in list_of_dict]
    return ids


def delete_image(table, column, record_id):
    record = connection.simple_select(table, column, record_id)[0]
    image_url = record["image"]
    if image_url:
        os.remove(os.path.join(os.path.dirname(__file__), 'static/', image_url))


def search(search_term, search_location):
    if search_location == "question_titles":
        result = connection.search_question_titles(search_term)
    elif search_location == "question_messages":
        result = connection.search_question_messages(search_term)
    else:
        result = connection.search_answers(search_term)
    return result


def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

