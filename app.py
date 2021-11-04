from flask import Flask, render_template, redirect, request
import sqlite3

app = Flask(__name__)

class Store:
    pages = []

class Page:
    id: int
    name: str
    content: str

    def __init__(self, id, name, content):
        self.id = id
        self.name = name
        self.content = content

@app.before_first_request
def setup():
    con = sqlite3.connect("database.sqlite3")
    cur = con.cursor()
    for page in cur.execute("SELECT * FROM pages").fetchall():
        Store.pages.append(Page(page[0], page[1], page[2]))
    con.close()

@app.route("/")
def route_home():
    return redirect("/wiki/Main Page")

@app.route("/wiki/<page_name>")
def route_page(page_name):
    con = sqlite3.connect("database.sqlite3")
    cur = con.cursor()
    query = cur.execute("SELECT * FROM pages WHERE name='{}'".format(page_name)).fetchall()
    con.close()
    if len(query) == 0:
        return render_template("Wikipage.html", page=Page(0, page_name, "Page not found on this wiki."))
    else:
        return render_template("Wikipage.html", page=Page(query[0][0], query[0][1], query[0][2]))

@app.route("/edit/<page_name>")
def route_edit(page_name):
    if request.args.get("content") == None:
        print("len 0")
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
        cur.execute("UPDATE pages SET content=? WHERE name=?", (request.args.get("content"), page_name))
        con.commit()
        con.close()
        return redirect("/wiki/{}".format(page_name))

@app.route("/create")
def create_page():
    if request.args.get("name") == None:
        return render_template("Createpage.html")
    else:
        con = sqlite3.connect("database.sqlite3")
        cur = con.cursor()
        if cur.execute("SELECT * FROM pages WHERE name=?", (request.args.get("name"), )).fetchone() != None:
            return "Page you are trying to create exists"
        else:
            cur.execute("INSERT INTO pages (name, content) VALUES (?, 'Page is currently being created. Edit this to finish the page creation process.')", (request.args.get("name"), ))
        con.commit()
        con.close()
        return redirect("/edit/{}".format(request.args.get("name")))

@app.route("/delete")
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
        else:
            cur.execute("DELETE FROM pages WHERE name=?", (request.args.get("name"), ))
        con.commit()
        con.close()
        return redirect("/wiki/Main Page")

if __name__ == "__main__":
    app.run(debug=True)