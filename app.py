from flask import Flask, render_template
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

@app.route("/wiki/<page_name>")
def route_home(page_name):
    con = sqlite3.connect("database.sqlite3")
    cur = con.cursor()
    query = cur.execute("SELECT * FROM pages WHERE name='{}'".format(page_name)).fetchall()
    con.close()
    if len(query) == 0:
        return render_template("Wikipage.html", page=Page(0, page_name, "Page not found on this wiki."))
    else:
        return render_template("Wikipage.html", page=Page(query[0][0], query[0][1], query[0][2]))

if __name__ == "__main__":
    app.run(debug=True)