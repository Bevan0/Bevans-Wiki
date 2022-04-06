from flask import Flask, render_template, redirect, request
import flask_login

import sqlite3
from werkzeug import security
import re
import time
import datetime

app = Flask(__name__)
app.secret_key = b'>\xec\xf1\xb2rB\xf6\x03\xbc\xee|\x0e2\xa2y\xd82\x9b\xc6\x84m\xbd\x84\x0b'
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class Page:
    id: int
    name: str
    content: str
    edit_protection_lvl: int = 0  # 0 = everyone, 1 = everyone with lvl 1 protection, 2 = everyone with lvl 2 protection, etc
    meta_protection_lvl: int = 0  # 0 = everyone, 1 = everyone with lvl 1 protection, 2 = everyone with lvl 2 protection, etc

    def __init__(self, id, name, content, exists=True, edit_protection_lvl=0, meta_protection_lvl=0):
        self.id = id
        self.name = name
        self.content = content
        self.exists = exists
        self.edit_protection_lvl = edit_protection_lvl
        self.meta_protection_lvl = meta_protection_lvl

class User:
    id: int
    username: str
    authenticated: bool = False
    active: bool = True
    anonymous: bool = False
    max_edit_protection_lvl: int = 0  # Page edit and creation protection levels
    max_meta_protection_lvl: int = 0  # Delete and move protection levels

    def __init__(self, id, username, edit_protection_lvl, meta_protection_lvl):
        self.id = id
        self.username = username
        self.max_edit_protection_lvl = edit_protection_lvl
        self.max_meta_protection_lvl = meta_protection_lvl
    
    def is_authenticated(self):
        return self.authenticated
    
    def is_active(self):
        return self.active
    
    def is_anonymous(self):
        return self.anonymous
    
    def get_id(self):
        return self.id

    def can_edit(self, protection_required):
        return self.max_edit_protection_lvl >= protection_required
    
    def can_meta(self, protection_required):
        return self.max_meta_protection_lvl >= protection_required

def get_datetime():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@login_manager.user_loader
def load_user(user_id):
    con = sqlite3.connect("database.sqlite3")
    cur = con.cursor()
    query = cur.execute("SELECT * FROM users WHERE id=?", (user_id, )).fetchone()
    con.close()
    if query == None: return None
    else: return User(query[0], query[1], query[3], query[4])

@app.route("/")
def route_home():
    return redirect("/wiki/Main Page")

@app.route("/wiki/<page_name>")
def route_page(page_name):
    if request.args.get("search") != None:
        return redirect("/wiki/{}".format(request.args.get("search")))
    con = sqlite3.connect("database.sqlite3")
    cur = con.cursor()
    query = cur.execute("SELECT * FROM pages WHERE name='{}'".format(page_name)).fetchall()
    con.close()
    if len(query) == 0:
        return render_template("Wikipage.html", page=Page(0, page_name, "Page not found on this wiki.", exists=False))
    else:
        return render_template("Wikipage.html", page=Page(query[0][0], query[0][1], query[0][2]))

@app.route("/edit/<page_name>")
@flask_login.login_required
def route_edit(page_name):
    if request.args.get("content") == None:
        con = sqlite3.connect("database.sqlite3")
        cur = con.cursor()
        query = cur.execute("SELECT * FROM pages WHERE name='{}'".format(page_name)).fetchall()
        con.close()
        if len(query) == 0:
            return redirect("/wiki/{}".format(page_name))
        else:
            return render_template("Editpage.html", page=Page(query[0][0], query[0][1], query[0][2]))
    else:
        con = sqlite3.connect("database.sqlite3")
        cur = con.cursor()
        if not flask_login.current_user.can_edit(cur.execute("SELECT edit_prot FROM pages WHERE name=?", (request.args.get("name"), )).fetchone()[0]):
            return "You don't have permission to edit this page (your edit level: {}, required level: {})".format(flask_login.current_user.max_edit_protection_level, cur.execute("SELECT edit_prot FROM pages WHERE name=?", (request.args.get("name"), )).fetchone()[0])
        cur.execute("UPDATE pages SET content=? WHERE name=?", (request.args.get("content"), page_name))
        cur.execute("INSERT INTO logs (executor_id, action, target_id, message, timestamp) VALUES (?, ?, ?, ?, ?)", (flask_login.current_user.id, "PAGE:EDIT", cur.execute("SELECT * FROM pages WHERE name=?", (page_name, )).fetchone()[0], "{} edited page {} at {}".format(flask_login.current_user.username, page_name, get_datetime()), time.time()))
        con.commit()
        con.close()
        return redirect("/wiki/{}".format(page_name))

@app.route("/create")
@flask_login.login_required
def create_page():
    if request.args.get("name") == None:
        if request.args.get("default") == None:
            return render_template("Createpage.html", default="")
        else:
            return render_template("Createpage.html", default=request.args.get("default"))
    else:
        con = sqlite3.connect("database.sqlite3")
        cur = con.cursor()
        if cur.execute("SELECT * FROM pages WHERE name=?", (request.args.get("name"), )).fetchone() != None:
            return "Page you are trying to create exists"
        else:
            cur.execute("INSERT INTO pages (name, content) VALUES (?, 'Page is currently being created. Edit this to finish the page creation process.')", (request.args.get("name"), ))
            cur.execute("INSERT INTO logs (executor_id, action, target_id, message, timestamp) VALUES (?, ?, ?, ?, ?)", (flask_login.current_user.id, "PAGE:CREATE", cur.execute("SELECT * FROM pages WHERE name=?", (request.args.get("name"), )).fetchone()[0], "{} created page {} at {}".format(flask_login.current_user.username, request.args.get("name"), get_datetime()), time.time()))
        con.commit()
        con.close()
        return redirect("/edit/{}".format(request.args.get("name")))

@app.route("/delete")
@flask_login.login_required
def delete_page():
    if request.args.get("name") == None:
        if request.args.get("default") != None:
            return render_template("Deletepage.html", default=request.args.get("default"))
        else:
            return render_template("Deletepage.html", default="")
    else:
        con = sqlite3.connect("database.sqlite3")
        cur = con.cursor()
        if cur.execute("SELECT * FROM pages WHERE name=?", (request.args.get("name"), )).fetchone() == None:
            return "Page you are trying to delete doesn't exist"
        elif not flask_login.current_user.can_meta(cur.execute("SELECT meta_prot FROM pages WHERE name=?", (request.args.get("name"), )).fetchone()[0]):
            return "You don't have permission to delete this page (your meta level: {}, required level: {})".format(flask_login.current_user.max_meta_protection_level, cur.execute("SELECT meta_prot FROM pages WHERE name=?", (request.args.get("name"), )).fetchone()[0])
        else:
            cur.execute("INSERT INTO logs (executor_id, action, target_id, message, timestamp) VALUES (?, ?, ?, ?, ?)", (flask_login.current_user.id, "PAGE:DELETE", cur.execute("SELECT * FROM pages WHERE name=?", (request.args.get("name"), )).fetchone()[0], "{} deleted page {} at {}".format(flask_login.current_user.username, request.args.get("name"), get_datetime()), time.time()))
            cur.execute("DELETE FROM pages WHERE name=?", (request.args.get("name"), ))
        con.commit()
        con.close()
        return redirect("/wiki/Main Page")

@app.route("/move")
@flask_login.login_required
def move_page():
    if (request.args.get("name") == None or request.args.get("dest") == None):
        if request.args.get("name") != None:
            return render_template("Movepage.html", default=request.args.get("name"))
        else:
            return render_template("Movepage.html", default="")
    else:
        con = sqlite3.connect("database.sqlite3")
        cur = con.cursor()
        if cur.execute("SELECT * FROM pages WHERE name=?", (request.args.get("name"), )).fetchone() == None:
            return "Page you are trying to move doesn't exist"
        elif cur.execute("SELECT * FROM pages WHERE name=?", (request.args.get("dest"), )).fetchone() != None:
            return "Page destination already exists"
        elif not flask_login.current_user.can_meta(cur.execute("SELECT meta_prot FROM pages WHERE name=?", (request.args.get("name"), )).fetchone()[0]):
            return "You don't have permission to move this page (your meta level: {}, required level: {})".format(flask_login.current_user.max_meta_protection_level, cur.execute("SELECT meta_prot FROM pages WHERE name=?", (request.args.get("name"), )).fetchone()[0])
        else:
            cur.execute("UPDATE pages SET name=? WHERE name=?", (request.args.get("dest"), request.args.get("name")))
            cur.execute("INSERT INTO logs (executor_id, action, target_id, message, timestamp) VALUES (?, ?, ?, ?, ?)", (flask_login.current_user.id, "PAGE:MOVE", cur.execute("SELECT id FROM pages WHERE name=?", (request.args.get("dest"), )).fetchone()[0], "{} moved page {} to {} at {}".format(flask_login.current_user.username, request.args.get("name"), request.args.get("dest"), get_datetime()), time.time()))
        con.commit()
        con.close()
        return redirect("/wiki/{}".format(request.args.get("dest")))

@app.route("/log/<page_name>")
def route_log(page_name):
    logs = []
    con = sqlite3.connect("database.sqlite3")
    cur = con.cursor()
    q1 = cur.execute("SELECT * FROM pages WHERE name=?", (page_name, )).fetchone()[0]
    query = cur.execute("SELECT * FROM logs WHERE target_id=?", (q1, )).fetchall()
    con.close()
    for log in query:
        if not log[2][:5] == "PAGE:":
            continue
        logs.append(log[4])
    return render_template("Logs.html", page_name=page_name, logs=logs)

@app.route("/log")
def route_all_logs():
    logs = []
    con = sqlite3.connect("database.sqlite3")
    cur = con.cursor()
    query = cur.execute("SELECT * FROM logs").fetchall()
    con.close()
    for log in query:
        logs.append(log[4])
    return render_template("Logs.html", page_name="everything", logs=logs)

@app.route("/login", methods=["GET", "POST"])
def route_login():
    if request.method == "GET":
        return render_template("Login.html")
    else:
        if request.form.get("username") == None or request.form.get("password") == None:
            return "Bad request"
        username = request.form.get("username")
        password = request.form.get("password")
        con = sqlite3.connect("database.sqlite3")
        cur = con.cursor()
        query = cur.execute("SELECT * FROM users WHERE username=?", (username, )).fetchone()
        con.close()
        if query == None:
            return "User does not exist"
        print(query[2])
        if not security.check_password_hash(query[2], password):
            return "Wrong password"
        flask_login.login_user(User(query[0], query[1]))
        return redirect("/wiki/Main Page")

@app.route("/logout")
@flask_login.login_required
def route_logout():
    flask_login.logout_user()
    return redirect("/wiki/Main Page")

@app.route("/register", methods=["GET", "POST"])
def route_register_account():
    if request.method == "GET":
        return render_template("Register.html")
    else:
        if request.form.get("username") == None or request.form.get("password") == None:
            return "Bad request"
        username = request.form.get("username")
        if not re.compile("^[0-9, A-z]*$").match(username):
            return "Username can only contain letters and numbers"
        password = request.form.get("password")
        if len(password) < 8:
            return "Passwords must be 8 characters or longer"
        con = sqlite3.connect("database.sqlite3")
        cur = con.cursor()
        if len(cur.execute("SELECT username FROM users WHERE username=?", (username, )).fetchall()) != 0:
            return "Username taken"
        hashed_password = security.generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        cur.execute("INSERT INTO logs (executor_id, action, target_id, message, timestamp) VALUES (?, ?, ?, ?, ?)", (0, "ACCOUNT:CREATE", cur.execute("SELECT id FROM users WHERE username=?", (request.form.get("username"), )).fetchone()[0], "User {} was created at {}".format(request.form.get("username"), get_datetime()), time.time()))
        con.commit()
        con.close()
        return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)