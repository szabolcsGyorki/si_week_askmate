import connection
from datetime import datetime
import os
import password_crypting
from werkzeug.utils import secure_filename

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


def add_question(title, message, user_id, image=None):
    dt = datetime.now().replace(microsecond=000000)
    columns = ["submission_time", "view_number", "vote_number", "title", "message", "user_id"]
    values = [str(dt), 0, 0, title, message, user_id]

    if image:
        columns.append("image")
        values.append(image)
    connection.simple_insert("question", columns, values)


def add_new_answer(message, question_id, user_id, image=None):
    dt = datetime.now().replace(microsecond=000000)
    columns = ["submission_time", "vote_number", "question_id", "message", "user_id"]
    values = [str(dt), 0, question_id, message, user_id]

    if image:
        columns.append("image")
        values.append(image)
    connection.simple_insert("answer", columns, values)


def add_comment(column, column_id, message, user_id):
    dt = datetime.now().replace(microsecond=000000)
    columns = [column, "message", "submission_time", "edited_count", "user_id"]
    values = [column_id, message, dt, 0, user_id]
    connection.simple_insert("comment", columns, values)


def add_new_tag(name):
    column = ["name"]
    value = [name]
    connection.simple_insert("tag", column, value)


def add_tag_to_question(question_id, tag_id):
    columns = ["question_id", "tag_id"]
    values = [question_id, tag_id]
    connection.simple_insert("question_tag", columns, values)


def add_new_user(user):
    name = user["user_name"]
    if user_name_exists(name):
        raise ValueError

    password = user["password"]
    confirm_password = user["confirm_password"]
    if not passwords_match(password, confirm_password):
        raise AssertionError

    password = password_crypting.hash_password(password)
    date = datetime.now().replace(microsecond=000000)
    columns = ["user_name", "password", "registration_date"]
    values = [name, password, date]
    connection.simple_insert("users", columns, values)


####################################################################################
# Edit block
####################################################################################


def edit_question(title, message, question_id, image=None):
    columns = ["title", "message"]
    values = [title, message]

    if image:
        delete_image("question", "id", question_id)
        columns.append("image")
        values.append(image)
    connection.update_table("question", columns, values, question_id)


def edit_answer(message, answer_id, image=None):
    columns = ["message"]
    values = [message]

    if image:
        delete_image("answer", "id", answer_id)
        columns.append("image")
        values.append(image)
    connection.update_table("answer", columns, values, answer_id)


def edit_comment(message, comment_id):
    comment = connection.simple_select("comment", "id", comment_id)[0]
    columns = ["message", "edited_count"]
    edited = str(comment["edited_count"] + 1)
    values = [message, edited]
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


def get_answer_ids_with_comment(key, list_of_dict):
    ids = [elem[key] for elem in list_of_dict]
    return ids


def get_user_id(user_name):
    user_id = connection.get_user_id(user_name)[0]["id"]
    return user_id


def get_users():
    return connection.get_users()


####################################################################################
# Login/registration functions
####################################################################################


def user_name_exists(name):
    user_names = connection.get_user_name(name)
    return bool(user_names)


def passwords_match(password, confirm_password):
    return password == confirm_password


def login(user):
    name = user["user_name"]
    typed_password = user["password"]
    if user_name_exists(name):
        user_password = connection.get_user_password(name)[0]["password"]
        return password_crypting.verify_password(typed_password, user_password)
    return False


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


def file_upload(file_to_upload):
    upload_folder = "./static/images/"

    if file_to_upload:
        file = file_to_upload['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(os.path.dirname(__file__), upload_folder, filename))
            return os.path.join('images/', filename)
