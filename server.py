from flask import Flask, render_template, request, session, redirect, url_for, flash, g
from functools import wraps
import data_manager
import os

UPLOAD_FOLDER = "./static/images/"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 4000 * 4000
app.secret_key = os.environ.get("SECRET_KEY")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not "user_name" in session:
            flash("You need to be logged in to user that feature!")
            return redirect(url_for('route_index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def route_index():
    questions = data_manager.get_latest_five_questions()
    tags = data_manager.get_tags_with_question_ids()
    order_by = request.args.get("order_by")
    order_direction = "desc" if request.args.get("order_direction") == "asc" else "asc"

    if order_by:
        questions = data_manager.order_list_of_dicts(questions, order_by, order_direction)
    return render_template("index.html",
                           questions=questions,
                           page_url="route_index",
                           order_direction=order_direction,
                           tags=tags)


@app.route("/list")
def route_all_questions():
    questions = data_manager.get_all_questions()
    tags = data_manager.get_tags_with_question_ids()
    order_by = request.args.get("order_by")
    order_direction = "desc" if request.args.get("order_direction") == "asc" else "asc"

    if order_by:
        questions = data_manager.order_list_of_dicts(questions, order_by, order_direction)
    return render_template("index.html",
                           questions=questions,
                           page_url="route_all_questions",
                           order_direction=order_direction,
                           tags=tags)


@app.route("/search")
def route_search():
    if request.args.get("search"):
        search_terms = request.args.get("search")
        question_titles = data_manager.search(search_terms, "question_titles")
        question_messages = data_manager.search(search_terms, "question_messages")
        answers = data_manager.search(search_terms, "answers")
        return render_template("search_results.html",
                               question_titles=question_titles,
                               question_messages=question_messages,
                               answers=answers,
                               search_terms=search_terms)


@app.route("/question/<question_id>/views")
def increase_view_counter(question_id):
    data_manager.view_count_increase(question_id)
    return redirect(url_for("display_a_question", question_id=question_id))


@app.route("/question/<question_id>")
def display_a_question(question_id):
    question = data_manager.get_question_details(question_id)
    unsorted_answers = data_manager.get_question_answers(question_id)
    answers = data_manager.order_list_of_dicts(unsorted_answers, "submission_time", "desc")
    question_comments = data_manager.get_question_comments(question_id)
    answer_comments = data_manager.get_answer_comments()
    tags = data_manager.get_question_tags(question_id)
    answers_with_comments = data_manager.get_answer_ids_with_comment("answer_id", answer_comments)
    users = data_manager.get_users()
    return render_template("display.html",
                           question=question,
                           answers=answers,
                           question_comments=question_comments,
                           answer_comments=answer_comments,
                           tags=tags,
                           answers_with_comments=answers_with_comments,
                           users=users)


@app.route("/add-question", methods=["GET", "POST"])
@login_required
def route_add_question():

    if request.method == "POST":
        file_url = data_manager.file_upload(request.files)
        title = request.form["title"]
        message = request.form["message"]
        data_manager.add_question(title, message, session["user_id"], file_url)
        return redirect(url_for("route_index"))

    return render_template("form.html",
                           form_url=url_for("route_add_question"),
                           add_question=True,
                           message_title="Details")


@app.route("/question/<question_id>/new-answer", methods=["GET", "POST"])
@login_required
def route_new_answer(question_id):

    if request.method == "POST":
        file_url = data_manager.file_upload(request.files)
        message = request.form["message"]
        data_manager.add_new_answer(message, question_id, session["user_id"], file_url)
        return redirect(url_for("display_a_question", question_id=question_id))

    return render_template("form.html",
                           form_url=url_for("route_new_answer", question_id=question_id),
                           message_title="Post answer",
                           add_answer=True)


@app.route("/question/<question_id>/new-comment", methods=["GET", "POST"])
@login_required
def route_new_question_comment(question_id):

    if request.method == "POST":
        message = request.form["message"]
        data_manager.add_comment("question_id", question_id, message, session["user_id"])
        return redirect(url_for("display_a_question", question_id=question_id))

    return render_template("form.html",
                           form_url=url_for("route_new_question_comment", question_id=question_id),
                           message_title="Post comment")


@app.route("/answer/<answer_id>/new-comment", methods=["GET", "POST"])
@login_required
def route_new_answer_comment(answer_id):

    if request.method == "POST":
        question_id = data_manager.get_question_id("answer", answer_id)
        message = request.form["message"]
        data_manager.add_comment("answer_id", answer_id, message, session["user_id"])
        return redirect(url_for("display_a_question", question_id=question_id))

    return render_template("form.html",
                           form_url=url_for("route_new_answer_comment", answer_id=answer_id),
                           message_title="Post comment")


@app.route("/question/<question_id>/edit", methods=["GET", "POST"])
@login_required
def route_edit_question(question_id):

    if request.method == "POST":
        file_url = data_manager.file_upload(request.files)
        title = request.form["title"]
        message = request.form["message"]
        data_manager.edit_question(title, message, question_id, file_url)
        return redirect(url_for("display_a_question", question_id=question_id))

    question = data_manager.get_question_details(question_id)
    question_title = question["title"]
    question_message = question["message"]
    return render_template("form.html",
                           form_url=url_for("route_edit_question", question_id=question_id),
                           add_question=True,
                           message_title="Details",
                           title=question_title,
                           message=question_message)


@app.route("/answer/<answer_id>/edit", methods=["GET", "POST"])
@login_required
def route_edit_answer(answer_id):

    if request.method == "POST":
        file_url = data_manager.file_upload(request.files)
        question_id = data_manager.get_question_id("answer", answer_id)
        message = request.form["message"]
        data_manager.edit_answer(message, answer_id, file_url)
        return redirect(url_for("display_a_question", question_id=question_id))

    answer = data_manager.get_answer(answer_id)
    answer_message = answer["message"]
    return render_template("form.html",
                           form_url=url_for("route_edit_answer", answer_id=answer_id),
                           message_title="Edit answer",
                           message=answer_message,
                           add_answer=True)


@app.route("/comments/<comment_id>/edit", methods=["GET", "POST"])
@login_required
def route_edit_comment(comment_id):

    if request.method == "POST":
        question_id = data_manager.get_question_id_from_comment(comment_id)
        message = request.form["message"]
        data_manager.edit_comment(message, comment_id)
        return redirect(url_for("display_a_question", question_id=question_id))

    comment = data_manager.get_comment(comment_id)
    comment_message = comment["message"]
    return render_template("form.html",
                           form_url=url_for("route_edit_comment", comment_id=comment_id),
                           message_title="Edit comment",
                           message=comment_message)


@app.route("/question/<question_id>/delete")
@login_required
def route_delete_question(question_id):
    data_manager.delete_question(question_id)
    return redirect(url_for("route_index"))


@app.route("/answer/<answer_id>/delete")
@login_required
def route_delete_answer(answer_id):
    question_id = data_manager.get_question_id("answer", answer_id)
    data_manager.delete_answer(answer_id)
    return redirect(url_for("display_a_question", question_id=question_id))


@app.route("/question/<question_id>/comments/<comment_id>/delete")
@login_required
def route_delete_comment(question_id, comment_id):
    data_manager.delete_comment(comment_id)
    return redirect(url_for("display_a_question", question_id=question_id))


@app.route("/question/<question_id>/vote-up")
@login_required
def route_question_vote_up(question_id):
    data_manager.vote("question", "up", question_id)
    return redirect(url_for("display_a_question", question_id=question_id))


@app.route("/question/<question_id>/vote-down")
@login_required
def route_question_vote_down(question_id):
    data_manager.vote("question", "down", question_id)
    return redirect(url_for("display_a_question", question_id=question_id))


@app.route("/answer/<answer_id>/vote-up")
@login_required
def route_answer_vote_up(answer_id):
    question_id = data_manager.get_question_id("answer", answer_id)
    data_manager.vote("answer", "up", answer_id)
    return redirect(url_for("display_a_question", question_id=question_id))


@app.route("/answer/<answer_id>/vote-down")
@login_required
def route_answer_vote_down(answer_id):
    question_id = data_manager.get_question_id("answer", answer_id)
    data_manager.vote("answer", "up", answer_id)
    return redirect(url_for("display_a_question", question_id=question_id))


@app.route("/question/<question_id>/new-tag", methods=["GET", "POST"])
@login_required
def tag_question(question_id):
    tags = data_manager.get_all_tags()

    if request.method == "POST":
        new_tag = request.form["new"]
        if new_tag:
            data_manager.add_new_tag(new_tag)
            tag_id = data_manager.get_tag_id(new_tag)
            data_manager.add_tag_to_question(question_id, tag_id)
        else:
            tag_id = request.form["existing"]
            data_manager.add_tag_to_question(question_id, tag_id)
        return redirect(url_for("display_a_question", question_id=question_id))

    return render_template("form.html",
                           form_url=url_for("tag_question", question_id=question_id),
                           add_tag=True,
                           tags=tags)


@app.route("/question/<question_id>/tag/<tag_id>/delete")
@login_required
def delete_tag(question_id, tag_id):
    data_manager.delete_question_tag(tag_id)
    return redirect(url_for("display_a_question", question_id=question_id))


@app.route("/registration", methods=["GET", "POST"])
def route_registration():
    if request.method == "POST":
        try:
            data_manager.add_new_user(request.form)
        except ValueError:
            flash("User name already exists")
            return redirect(url_for("route_registration"))
        except AssertionError:
            flash("Passwords don't match")
            return redirect(url_for("route_registration"))

        session["user_name"] = request.form["user_name"]
        session["user_id"] = data_manager.get_user_id(session["user_name"])
        return redirect(url_for("route_index"))

    return render_template("form.html",
                           registration=True)


@app.route("/login", methods=["POST"])
def route_login():
    if data_manager.login(request.form):
        session["user_name"] = request.form["user_name"]
        session["user_id"] = data_manager.get_user_id(session["user_name"])
        return redirect(url_for("route_index"))
    else:
        flash("You have entered an invalid user name or password. Please enter the correct details and try again.")
        return redirect(url_for("route_index"))


@app.route("/logout")
def route_logout():
    session.pop("user_name")
    session.pop("user_id")
    return redirect(url_for("route_index"))


@app.errorhandler(404)
def error_page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        debug=True,
    )
