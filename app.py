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
    for page in Store.pages:
        if page.name == page_name:
            return render_template("Wikipage.html", page=page)
    return render_template("Wikipage.html", page=Page(0, page_name, "Page not found on this wiki."))

if __name__ == "__main__":
    app.run(debug=True)