# This file generates a new database for Bevan's Wiki. It overrides any existing database.

import sqlite3
import os

# Delete old database
os.remove("database.sqlite3")

# Create new database and connect to it
con = sqlite3.connect("database.sqlite3")
cur = con.cursor()

cur.execute('''CREATE TABLE "logs" (
	"log_id"	INTEGER NOT NULL UNIQUE,
	"executor_id"	TEXT NOT NULL,
	"action"	TEXT NOT NULL,
	"target_id"	INTEGER NOT NULL,
	"message"	TEXT NOT NULL,
	"timestamp"	INTEGER NOT NULL,
	PRIMARY KEY("log_id" AUTOINCREMENT)
);''')

cur.execute('''CREATE TABLE "pages" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL UNIQUE,
	"content"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')

cur.execute('''CREATE TABLE "users" (
	"id"	INTEGER NOT NULL UNIQUE,
	"username"	TEXT NOT NULL UNIQUE,
	"password"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);''')

cur.execute('''INSERT INTO pages (name, content) VALUES ("Main Page", "Welcome to your new wiki!")''')

print("New database created.")