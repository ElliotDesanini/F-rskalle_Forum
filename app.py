"""
within database "fforum", there are 3 tables:
    "users" that handles values (id, username, hpassword, createdate)
    "threads" that handles values (id, userid, title, content, createdate)
    "posts" that handles values (id, threadid, userid, content, createdate)
"""

from flask import Flask, render_template, session, request
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

def hfunction(password):
   hpassword = f"h{password}h"
   return hpassword

def reset_session():
   session.clear()

   session["page"] = 0

@app.route("/")
def index():
   if "username" not in session:
            return render_template("login.html")
   
   with mydatabase.cursor() as cursor:
     cursor.execute(f"SELECT title, content, createdate FROM threads ORDER BY createdate DESC LIMIT 50 OFFSET {session['page']*50}")
     threads = cursor.fetchall()

   return render_template("index.html", username=session["username"], threads=threads, pagenumber = session["page"])

@app.route("/login", methods=["GET","POST"])
def login():

   if request.method == "GET":
       return render_template("login.html")
   
   username_input = request.form.get("username")
   password_input = request.form.get("password")

   if not username_input or not password_input:
       return "Username and password are required.", 400
   
   reset_session()

   session["username"] = username_input
   session["password"] = password_input

   with mydatabase.cursor() as cursor:
      cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = %s AND hpassword = %s);", (session["username"], hfunction(session["password"])))
      user_exists = cursor.fetchone()

   if user_exists[0] != 1:
      with mydatabase.cursor() as cursor:
         cursor.execute("INSERT INTO users (username, hpassword) VALUES (%s, %s)",(session["username"], hfunction(session["password"])))
         mydatabase.commit()
         
   with mydatabase.cursor() as cursor:
      cursor.execute("SELECT * FROM users WHERE username = %s AND hpassword = %s", (session["username"], hfunction(session["password"])))
      user = cursor.fetchone()

      cursor.execute(f"SELECT threads.title, users.username, threads.createdate, threads.id FROM threads INNER JOIN users ON users.id = threads.userid ORDER BY threads.createdate DESC LIMIT 50 OFFSET {session['page']*50}")
      threads = cursor.fetchall()

   return render_template("index.html", user=user, threads=threads)

   
@app.route("/user")
def user():
   if "username" not in session:
      return render_template("login.html")

   with mydatabase.cursor() as cursor:
      cursor.execute("SELECT * FROM users WHERE username = %s AND hpassword = %s", (session["username"], hfunction(session["password"])))
      user = cursor.fetchone()

      cursor.execute("SELECT * FROM posts WHERE userid = %s", (user[0]))
      posts = cursor.fetchall()
   
   return render_template("user.html", user=user, posts=posts)


@app.route("/thread", methods=["GET","POST"])
def thread():
   if "username" not in session:
      return render_template("login.html")
   
   threadid = request.args.get('id')
   
   with mydatabase.cursor() as cursor:
      cursor.execute("SELECT * FROM users WHERE username = %s AND hpassword = %s", (session["username"], hfunction(session["password"])))
      user = cursor.fetchone()

      cursor.execute("SELECT users.username, posts.content, posts.createdate FROM posts, users ON users.id = posts.userid WHERE posts.threadid = %s", (threadid))
      posts = cursor.fetchall()
      
      cursor.execute(f"SELECT threads.title, threads.content, users.username, threads.createdate FROM threads INNER JOIN users ON threads.userid = users.id AND threads.id = {threadid}")
      thread = cursor.fetchone()


   return render_template("thread.html", user=user, thread=thread, posts=posts)


@app.route("/add_thread")
def add_thread():
   with mydatabase.cursor() as cursor:
      cursor.execute("SELECT * FROM users WHERE username = %s AND hpassword = %s", (session["username"], hfunction(session["password"])))
      user = cursor.fetchone()

      cursor.execute("INSERT INTO threads (userid, title, content) VALUES (%s, %s, %s)", (user[0], request.args.get("title"), request.args.get("content")))
      mydatabase.commit()

      cursor.execute(f"SELECT threads.title, users.username, threads.createdate FROM threads INNER JOIN users ON users.id = threads.userid ORDER BY threads.createdate DESC LIMIT 50 OFFSET {session['page']*50}")
      threads = cursor.fetchall()

   return render_template("index.html", user=user, threads=threads)

if __name__ == "__main__":
    app.run(debug=True, port=5000)