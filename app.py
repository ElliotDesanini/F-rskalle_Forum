
from flask import Flask, render_template, session, request, redirect, abort, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import mysql.connector

app = Flask(__name__)

app.secret_key = secrets.token_hex(32)

mydatabase = mysql.connector.connect(
	host="localhost",
	user="root",
	password="",
	database="fforum"
)


def reset_session():
	session.clear()


def logged_in():
	if "userid" not in session:
		return False

	with mydatabase.cursor() as cursor:
		cursor.execute(
			"SELECT id FROM users WHERE id = %s",
			(session["userid"],)
		)
		user = cursor.fetchone()

	if user is None:
		reset_session()
		return False

	return True



@app.route("/")
def index():
	if not logged_in():
		return redirect("/managment/login")

	page = request.args.get("page", 1, type=int)

	if page < 1:
		abort(400)

	offset = (page - 1) * 50

	with mydatabase.cursor() as cursor:
		cursor.execute("""SELECT topics.title, users.username, topics.createdate,
			topics.id, topics.content FROM topics
			INNER JOIN users ON users.id = topics.userid
			ORDER BY topics.createdate DESC
			LIMIT 50 OFFSET %s""", (offset,))

		topics = cursor.fetchall()

		cursor.execute("SELECT COUNT(*) FROM topics")

		total_topics = cursor.fetchone()[0]

	return render_template(
		"index.html",
		username=session["username"],
		topics=topics,
		total_topics= total_topics,
		pagenumber=page
	)


@app.route("/topic")
def topic():
	if not logged_in():
		return redirect("/managment/login")

	topicid = request.args.get("id", type=int)
	page = request.args.get("page", 1, type=int)

	if topicid is None or topicid < 1 or page < 1:
		abort(400)

	offset = (page - 1) * 50

	with mydatabase.cursor() as cursor:

		cursor.execute(
			"SELECT id FROM topics WHERE id = %s",
			(topicid,)
		)

		if cursor.fetchone() is None:
			abort(404)

		cursor.execute("""SELECT threads.title, users.username, threads.createdate,
			threads.id, threads.content
			FROM threads
			INNER JOIN users ON users.id = threads.userid
			WHERE threads.topicid = %s
			ORDER BY threads.createdate DESC
			LIMIT 50 OFFSET %s""", (topicid, offset))

		threads = cursor.fetchall()

		cursor.execute("SELECT COUNT(*) FROM threads WHERE topicid = %s",(topicid,))

		total_threads = cursor.fetchone()[0]

	return render_template("content/topic.html", username=session["username"], total_threads= total_threads, threads=threads, pagenumber=page, topicid=topicid)


@app.route("/managment/login", methods=["GET", "POST"])
def login():

	if request.method == "GET":
		return render_template("managment/login.html")

	username = request.form.get("username")
	password = request.form.get("password")

	if not username or not password:
		abort(400)

	with mydatabase.cursor() as cursor:
		cursor.execute(
			"SELECT id, username, hpassword FROM users WHERE username = %s",
			(username,)
		)

		user = cursor.fetchone()

	if user is None or not check_password_hash(user[2], password):
		abort(401)

	reset_session()

	session["userid"] = user[0]
	session["username"] = user[1]

	return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():

	if request.method == "GET":
		return render_template("managment/register.html")

	username = request.form.get("username")
	password = request.form.get("password")

	if not username or not password:
		abort(400)

	hpassword = generate_password_hash(password)

	try:
		with mydatabase.cursor() as cursor:
			cursor.execute("INSERT INTO users (username, hpassword)VALUES (%s, %s)",(username, hpassword))

			userid = cursor.lastrowid

		mydatabase.commit()

	except mysql.connector.IntegrityError:
		mydatabase.rollback()
		return "Username already exists.", 409

	except mysql.connector.Error:
		mydatabase.rollback()
		abort(500)

	reset_session()

	session["userid"] = userid
	session["username"] = username

	return redirect("/")


@app.route("/logout", methods=["POST"])
def logout():

	reset_session()

	return redirect("/managment/login")



@app.route("/user")
def user():

	if not logged_in():
		return redirect("/managment/login")

	with mydatabase.cursor() as cursor:

		cursor.execute("SELECT id, username, createdate FROM users WHERE id = %s", (session["userid"],))

		user = cursor.fetchone()

		cursor.execute("SELECT id, title, content, createdate FROM threads WHERE userid = %s ORDER BY createdate DESC", (session["userid"],))

		threads = cursor.fetchall()

		cursor.execute("""
			SELECT posts.id, posts.threadid, posts.content,
			posts.createdate, threads.title FROM posts
			INNER JOIN threads ON threads.id = posts.threadid
			WHERE posts.userid = %s
			ORDER BY posts.createdate DESC
		""", (session["userid"],))

		posts = cursor.fetchall()

	return render_template(
		"content/user.html",
		user=user,
		threads=threads,
		posts=posts
	)


@app.route("/thread")
def thread():

	if not logged_in():
		return redirect("/managment/login")

	threadid = request.args.get("id", type=int)
	replyid = request.args.get("replyid", type=int)

	if threadid is None or threadid < 1:
		abort(400)

	with mydatabase.cursor() as cursor:

		cursor.execute("""
			SELECT threads.title, threads.content, users.username,
			threads.createdate, threads.id, threads.topicid FROM threads
			INNER JOIN users ON threads.userid = users.id
			WHERE threads.id = %s
		""", (threadid,))

		thread = cursor.fetchone()

		if thread is None:
			abort(404)

		cursor.execute("""
			SELECT users.username, posts.content,
			posts.createdate, posts.id, posts.postid FROM posts
			INNER JOIN users ON users.id = posts.userid
			WHERE posts.threadid = %s
			ORDER BY posts.createdate ASC
		""", (threadid,))

		posts = cursor.fetchall()

		cursor.execute("""
		SELECT posts.id, users.username FROM posts
		INNER JOIN users ON posts.userid = users.id
		WHERE posts.id = %s
		""", (replyid,))

		replypost = cursor.fetchone()

	return render_template(
		"content/thread.html",
		username=session["username"],
		thread=thread,
		replypost=replypost,
		posts=posts
	)


@app.route("/thread_create")
def thread_create():

	if not logged_in():
		return redirect("/managment/login")

	topicid = request.args.get("id", type=int)

	if topicid is None or topicid < 1:
		abort(400)

	with mydatabase.cursor() as cursor:
		cursor.execute(
			"SELECT id, title FROM topics WHERE id = %s",
			(topicid,)
		)

		topic = cursor.fetchone()

	if topic is None:
		abort(404)

	return render_template( "create/thread_create.html", topic=topic, topicid=topicid, username = session["username"])

@app.route("/topic_create")
def topic_create():

	if not logged_in():
		return redirect("/managment/login")

	return render_template( "create/topic_create.html", username=session["username"])

@app.route("/add_thread", methods=["POST"])
def add_thread():

	if not logged_in():
		return redirect("/managment/login")

	title = request.form.get("title")
	content = request.form.get("content")
	topicid = request.form.get("topicid", type=int)

	if not title or not content or topicid is None or topicid < 1:
		abort(400)

	try:
		with mydatabase.cursor() as cursor:

			cursor.execute("SELECT id FROM topics WHERE id = %s", (topicid,))

			if cursor.fetchone() is None:
				abort(404)

			cursor.execute("INSERT INTO threads (userid, topicid, title, content) VALUES (%s, %s, %s, %s)", (session["userid"], topicid, title, content))

		mydatabase.commit()

	except mysql.connector.Error:
		mydatabase.rollback()
		abort(500)

	return redirect(f"/topic?id={topicid}")

@app.route("/add_topic", methods=["POST"])
def add_topic():

	if not logged_in():
		return redirect("/managment/login")

	title = request.form.get("title")
	content = request.form.get("content")

	if not title or not content:
		abort(400)

	try:
		with mydatabase.cursor() as cursor:

			cursor.execute("INSERT INTO topics (userid, title, content) VALUES (%s, %s, %s)", ( session["userid"], title, content))

		mydatabase.commit()

	except mysql.connector.Error:
		mydatabase.rollback()
		abort(500)

	return redirect("/")


@app.route("/add_post", methods=["POST"])
def add_post():

	if not logged_in():
		return redirect("/managment/login")

	threadid = request.form.get("threadid", type=int)
	replyid = request.form.get("replyid", type=int)
	content = request.form.get("content")

	if threadid is None or threadid < 1 or not content:
		abort(400)

	try:
		with mydatabase.cursor() as cursor:

			cursor.execute("SELECT id FROM threads WHERE id = %s",(threadid,))

			if cursor.fetchone() is None:
				abort(404)

			if replyid != None:
				cursor.execute("INSERT INTO posts (threadid, postid, userid, content) VALUES (%s, %s, %s, %s)", ( threadid, replyid, session["userid"], content ))
			else:
				cursor.execute("INSERT INTO posts (threadid, userid, content) VALUES (%s, %s, %s)", ( threadid, session["userid"], content ))

		mydatabase.commit()

	except mysql.connector.Error:
		mydatabase.rollback()
		abort(500)

	return redirect(f"/thread?id={threadid}")


@app.route("/page/<int:pagenumber>")
def page(pagenumber):

	if not logged_in():
		return redirect("/managment/login")

	if pagenumber < 1:
		abort(400)

	return redirect(url_for("index", page=pagenumber))


@app.errorhandler(400)
def bad_request(e):

	return render_template(
		"error.html",
		errorname="BAD REQUEST",
		errorcode=400,
		error_description="there was information missing or invalid information in your request"
	), 400


@app.errorhandler(401)
def unauthorized(e):

	return render_template(
		"error.html",
		errorname="UNAUTHORIZED",
		errorcode=401,
		error_description="you are not authorized to access this page"
	), 401


@app.errorhandler(403)
def forbidden(e):

	return render_template(
		"error.html",
		errorname="FORBIDDEN",
		errorcode=403,
		error_description="you do not have permission to access this page"
	), 403


@app.errorhandler(404)
def page_not_found(e):

	return render_template(
		"error.html",
		errorname="NOT FOUND",
		errorcode=404,
		error_description="the page you are looking for does not exist. it may have been deleted or moved."
	), 404


@app.errorhandler(405)
def method_not_allowed(e):

	return render_template(
		"error.html",
		errorname="METHOD NOT ALLOWED",
		errorcode=405,
		error_description="the request method is not allowed for this page"
	), 405


@app.errorhandler(429)
def too_many_requests(e):

	return render_template(
		"error.html",
		errorname="TOO MANY REQUESTS",
		errorcode=429,
		error_description="you have sent too many requests in a short period of time"
	), 429


@app.errorhandler(500)
def server_error(e):

	return render_template(
		"error.html",
		errorname="SERVER ERROR",
		errorcode=500,
		error_description="something went wrong on our end."
	), 500


@app.errorhandler(503)
def server_down(e):

	return render_template(
		"error.html",
		errorname="SERVICE UNAVAILABLE",
		errorcode=503,
		error_description="the server is currently unavailable. it may be down because of updates, maintenance or something else."
	), 503

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5002, debug=True)
