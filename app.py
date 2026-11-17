"""
within database "fforum", there are 3 tables:
	"users" that handles values (id, username, hpassword, createdate)
	"threads" that handles values (id, userid, title, content, createdate)
	"posts" that handles values (id, threadid, postid, userid, content, createdate)
"""


from flask import Flask, render_template, session, request, redirect, abort
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import mysql.connector

app = Flask(__name__)

app.secret_key = app.secret_key = secrets.token_hex(32)

mydatabase = mysql.connector.connect(
	host="localhost",
	user="root",
	password="",
	database="fforum"
)


def reset_session():
	session.clear()
	session["page"] = 0

@app.route("/")
def index():
	if "userid" not in session:
		return render_template("managment/login.html")

	page = session.get("page", 0)

	with mydatabase.cursor() as cursor:
		cursor.execute("""
		SELECT threads.title, users.username, threads.createdate, threads.id
		FROM threads
		INNER JOIN users ON users.id = threads.userid
		ORDER BY threads.createdate DESC
		LIMIT 50 OFFSET %s
		""", (page * 50,))

		threads = cursor.fetchall()

	return render_template( "content/index.html", username=session["username"], threads=threads, pagenumber=page)


@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "GET":
		return render_template("login.html")

	username = request.form.get("username")
	password = request.form.get("password")

	if not username or not password:
		return "Username and password are required.", 400

	with mydatabase.cursor() as cursor:
		cursor.execute("SELECT id, username, hpassword FROM users WHERE username = %s", (username,))

		user = cursor.fetchone()

	if user is None or not check_password_hash(user[2], password):
		return "Incorrect username or password.", 401

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
		return "Username and password are required.", 400

	hpassword = generate_password_hash(password)

	try:
		with mydatabase.cursor() as cursor:
			cursor.execute("INSERT INTO users (username, hpassword) VALUES (%s, %s)", (username, hpassword))
			mydatabase.commit()
		userid = cursor.lastrowid

	except mysql.connector.IntegrityError:
		mydatabase.rollback()
		return "Username already exists.", 409

	reset_session()
	session["userid"] = userid
	session["username"] = username
	return redirect("/")


@app.route("/logout", methods=["POST"])
def logout():
   reset_session()
   return redirect("/login")


@app.route("/user")

@app.route("/user")
def user():
	if "userid" not in session:
		return redirect("/login")

	with mydatabase.cursor() as cursor:
		cursor.execute("SELECT id, username, createdate FROM users WHERE id = %s", (session["userid"],))

		user = cursor.fetchone()

		if user is None:
			reset_session()
			return redirect("/login")
		
		cursor.execute("SELECT id, title, content, createdate FROM threads WHERE userid = %s ORDER BY createdate DESC", (session["userid"],))

		threads = cursor.fetchall()

		cursor.execute("SELECT posts.id, posts.threadid, posts.content, posts.createdate, threads.title FROM posts INNER JOIN threads ON threads.id = posts.threadid WHERE posts.userid = %s ORDER BY posts.createdate DESC", (session["userid"],))

		posts = cursor.fetchall()

	return render_template("content/user.html", user=user, threads=threads, posts=posts)

 
@app.route("/thread")
def thread():
	if "userid" not in session:
		return redirect("/login")

	threadid = request.args.get("id", type=int)

	if threadid is None:
		return "Invalid thread ID.", 400

	with mydatabase.cursor() as cursor:
		cursor.execute("SELECT threads.title, threads.content, users.username, threads.createdate, threads.id FROM threads INNER JOIN users ON threads.userid = users.id WHERE threads.id = %s", (threadid,))

		thread = cursor.fetchone()

		if thread is None:
			abort(404)

		cursor.execute("""SELECT users.username, posts.content, posts.createdate, posts.id
			FROM posts INNER JOIN users ON users.id = posts.userid
			WHERE posts.threadid = %s ORDER BY posts.createdate ASC""", (threadid,))

		posts = cursor.fetchall()

	return render_template( "content/thread.html", username=session["username"], thread=thread, posts=posts)


@app.route("/add_thread", methods=["POST"])
def add_thread():
	if "userid" not in session:
		return redirect("/login")

	title = request.form.get("title")
	content = request.form.get("content")

	if not title or not content:
		return "Title and content are required.", 400

	with mydatabase.cursor() as cursor:
		cursor.execute(
			"INSERT INTO threads (userid, title, content) VALUES (%s, %s, %s)",
			(session["userid"], title, content)
		)
		mydatabase.commit()

	return redirect("/")


@app.route("/add_post", methods=["POST"])
def add_post():
	if "userid" not in session:
		return redirect("/login")

	threadid = request.form.get("threadid", type=int)
	content = request.form.get("content")

	if threadid is None or not content:
		return "Thread ID and content are required.", 400

	with mydatabase.cursor() as cursor:
		cursor.execute("SELECT id FROM threads WHERE id = %s",(threadid,))

		thread = cursor.fetchone()

		if thread is None:
			abort(404)

		cursor.execute("INSERT INTO posts (threadid, userid, content) VALUES (%s, %s, %s)", (threadid, session["userid"], content))
		mydatabase.commit()

	return redirect(f"/thread?id={threadid}")


@app.route("/page/<int:pagenumber>")
def page(pagenumber):
	if "userid" not in session:
		return redirect("/login")

	if pagenumber < 0:
		return redirect("/")

	session["page"] = pagenumber

	return redirect("/")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error/404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("error/500.html"), 500

@app.errorhandler(503)
def server_down(e):
    return render_template("error/503.html"), 503

@app.errorhandler(403)
def forbidden(e):
    return render_template("error/403.html"), 403

@app.errorhandler(401)
def unauthorized(e):
    return render_template("error/401.html"), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
