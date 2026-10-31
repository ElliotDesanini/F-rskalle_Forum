"""
within database "fforum", there are 3 tables:
    "users" that handles values (id, username, hpassword, createdate)
    "threads" that handles values (id, userid, title, createdate)
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

session["page"] = 1,
session["postpage"] = 1

@app.route("/")
def index():
   if "username" in session:
      with mydatabase.cursor() as cursor:
        cursor.execute(f"SELECT * FROM threads ORDER BY createdate DESC LIMIT 50 OFFSET {session['page']*50}")
        threads = cursor.fetchall()
        return render_template("index.html", username=session["username"], threads=threads)
   else:
      return render_template("login.html")

@app.route("/login", methods=["GET","POST"])
def login():
   username = request.form.get("username")
   password = request.form.get("password")

   session["username"] = username

   with mydatabase.cursor() as cursor:
      cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = %s AND hpassword = %s);", (username, hfunction(password)))
      user_exists = cursor.fetchone()

      if user_exists[0] == 1:
         with mydatabase.cursor() as cursor:
            cursor.execute(f"SELECT * FROM threads ORDER BY createdate DESC LIMIT 50 OFFSET {session['page']*50}")
            threads = cursor.fetchall()
            return render_template("index.html", username=session["username"], threads=threads)
      else:
         with mydatabase.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, hpassword) VALUES (%s, %s)",(username, hfunction(password)))
            mydatabase.commit()
            
            cursor.execute(f"SELECT * FROM threads ORDER BY createdate DESC LIMIT 50 OFFSET {session['page']*50}")
            threads = cursor.fetchall()
            return render_template("index.html", username=session["username"], threads=threads)

   



if __name__ == "__main__":
    app.run(debug=True, port=5000)














import mysql.connector  # installera med "pip install mysql-connector-python" i kommandotolken
mydb = mysql.connector.connect(
  host="localhost",
  user="root",  # standardanvändarnamn för XAMPP
  password="",  # dito lösenord (en tom sträng)
  database="webbserverprogrammering"  # byt namn om din databas heter något annat
)
mycursor = mydb.cursor()
print("Uppkopplad till databasen!")

# Skriva till databasen
sql = "INSERT INTO students (fornamn, efternamn, klass) VALUES (%s, %s, %s)"
val = ("Graham", "Chapman", "TE24A")
mycursor.execute(sql, val)
mydb.commit()
print(mycursor.rowcount, "record inserted.")

# Läsa från databasen
mycursor.execute("SELECT * FROM students")
myresult = mycursor.fetchall()
for x in myresult:
  print(x)