# -*- coding: utf-8 -*-

import os
import sys
import requests
import json
from flask import Flask, render_template, url_for, request, flash
import shutil
import time
import hashlib

sys.path.append("C:/Users/lucy.schrader/Documents/Scripts/coApiHarvest")

import TePapaHarvester

#TODO figure out what's wrong with pip so I can actually
#install tinydb

from tinydb import TinyDB, Query
db = TinyDB('harvestDB.json')

app = Flask(__name__)

working_folder = os.getcwd()
image_folder = working_folder + "/static/thumbs/"

@app.route("/", methods=["GET","POST"])
def start():
	# Link to available saved files
	return render_template("base.html")

@app.route("/save", methods=["GET","POST"])
def save():
	if request.method == "POST":
		irns = request.form["irn_list"]
		irns = irns.splitlines()
		doc_type = "object"
		saved_dataset = []
		for irn in irns:
			print(irn)
			record_query = TePapaHarvester.CoApi(doc_type=doc_type, irn=irn)
			record = record_query.view_record()
			record_data = TePapaHarvester.ApiRecord(record=record, irn=irn, get_thumbs=True, image_folder=image_folder)
			saved_data = record_data.add_data()
			saved_dataset.append(saved_data)
			time.sleep(1)
		
		hashing_string = "".join(irns)
		source_id = str(hash(hashing_string))

'''
		data_filename = "saved_data_{}.json".format(source_id)

		with open(data_filename, "w+", encoding="utf-8") as f:
			json.dump(saved_dataset, f)
		f.close()
'''

		db.insert({source_id:saved_dataset})

		return render_template("base.html", source_id=source_id)
	else:
		return render_template("base.html")

@app.route("/<source_id>", methods=["GET","POST"])
def load(source_id):
	db_query = Query()
	errors = None
	try:
		records = db.search(db_query.source_id == source_id)
	except:
		errors = "Set with that ID not found"
#	source_file = "saved_data_{}.json".format(source_id)
#	with open(source_file, 'r', encoding="utf-8") as f:
#		records = json.load(f)
	return render_template("base.html", records=records, errors=errors)