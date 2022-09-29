# -*- coding: utf-8 -*-

import os
import requests
import json
import sqlite3

working_folder = os.getcwd()
DATABASE = working_folder + "/static/database.db"
schema = working_folder + "/static/schema.sql"

conn = sqlite3.connect(DATABASE)

insert_coll = "INSERT INTO collections (title, facetedTitle) VALUES (?, ?)"
insert_record = "INSERT INTO records (irn, title, type, identifier, dateLabel, dateValue, personLabel, qualityScore, coUrl, include) VALUES (?, ?, ? , ?, ?, ?, ?, ?, ?, ?)"

def load_schema():
	with open(schema) as f:
		conn.executescript(f.read())

def write_test():
	cursor = conn.cursor()

	cursor.execute(insert_coll, ("Photography", "Photography"))
	cursor.execute(insert_coll, ("Rare Books", "RareBooks"))

	cursor.execute(insert_record, (1294830, "Female Choir uniform (Tokaikolo Christian Church Wellington)", "Object", "FE013055", "Created", "16 Apr 2004", "Designer", 6.2, "https://collections.tepapa.govt.nz/object/1294830", "false"))
	cursor.execute(insert_record, (184495, "yellowspotted gurnard, Pterygotrigla pauli Hardy, 1982", "Specimen", "P.010557", "Collected", "27 Jan 1981", "Collector", 5.3, "https://collections.tepapa.govt.nz/object/184495", "null"))

	conn.commit()
	conn.close()

def read_test():
	conn.row_factory = sqlite3.Row

	collections = conn.execute("SELECT * FROM collections").fetchall()
	records = conn.execute("SELECT * FROM records").fetchall()

	print(collections)
	print(records)
	for record in records:
		print(record["title"])

#load_schema()
#write_test()
read_test()