"""
within database "fforum", there are 3 tables:
    "users" that handles values (id, userid, username, createdate, hashedpassword)
    "threads" that handles values (id, tableid, userid, title, createdate)
    "posts" that handles values (id, postid, threadid, userid, content, createdate)
"""

import zlib
from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)

mydatabase = mysql.connector.connect(
   host="localhost",
   user="root",
   password="",
   database="fforum"
)

mycursor = mydatabase.cursor()


zlib.crc32(bytes(input_password, "utf-8")) 





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