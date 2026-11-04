"""
within database "fforum", there are 3 tables:
    "users" that handles values (id, username, hpassword, createdate)
    "threads" that handles values (id, userid, title, content, createdate)
    "posts" that handles values (id, threadid, userid, content, createdate)
"""

from flask import Flask, render_template, session
import mysql.connector

app = Flask(__name__)

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

   session["page"] = 1

reset_session()

@app.route("/")
def index():
   if "username" not in session:
            return render_template("login.html")
   
   with mydatabase.cursor() as cursor:
     cursor.execute(f"SELECT * FROM threads ORDER BY createdate DESC LIMIT 50 OFFSET {session['page']*50}")
     threads = cursor.fetchall()

   return render_template("index.html", username=session["username"], threads=threads)

@app.route("/login", methods=["GET","POST"])
def login():
   reset_session()

   session["username"] = request.form.get("username")
   session["password"] = request.form.get("password")

   with mydatabase.cursor() as cursor:
      cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = %s AND hpassword = %s);", (session["username"], hfunction(session["password"])))
      user_exists = cursor.fetchone()

   if user_exists[0] != 1:
      with mydatabase.cursor() as cursor:
         cursor.execute("INSERT INTO users (username, hpassword) VALUES (%s, %s)",(session["username"], hfunction(session["password"])))
         mydatabase.commit()
         
   with mydatabase.cursor() as cursor:
      cursor.execute(f"SELECT threads.title, users.username, threads.createdate FROM threads INNER JOIN users ON users.id = threads.userid ORDER BY threads.createdate DESC LIMIT 50 OFFSET {session['page']*50}")
      threads = {"title": cursor.fetchall()[0], "user": cursor.fetchall()[1], "createdate": cursor.fetchall()[2]}

   return render_template("index.html", username=session["username"], threads=threads)

   
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


@app.route("/thread")
def thread():
   if "username" not in session:
      return render_template("login.html")
   
   threadid = request.args.get('id')
   
   with mydatabase.cursor() as cursor:
      cursor.execute("SELECT users.username, posts.content, posts.createdate FROM posts, users ON users.id = posts.userid WHERE posts.threadid = %s", (threadid))
      posts = {"user": cursor.fetchall()[0], "content": cursor.fetchall()[1], "createdate": cursor.fetchall()[2]}

      
      cursor.execute(f"SELECT threads.title, threads.content, users.username, threads.createdate ")
      thread = {"title": cursor.fetchall()[0], "content": cursor.fetchall()[1], "user": cursor.fetchall()[2], "createdate": cursor.fetchall()[3]}


   return render_template("thread.html", thread=thread, posts=posts)


if __name__ == "__main__":
    app.run(debug=True, port=5000)