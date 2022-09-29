# -*- coding: utf-8 -*-

import sys
sys.path.append("C:/Users/lucy.schrader/Documents/Scripts/coApiHarvest")
import TePapaHarvester

import functools
from flask import (Blueprint, g, redirect, render_template, request, url_for, jsonify)
import os
from datetime import datetime
import time
import sqlite3
from picker.db import get_db, CollHandler, RecordHandler, MediaHandler, PeopleHandler

bp = Blueprint('view', __name__, url_prefix='/view')

@bp.route("/<collection>", methods=("GET", "POST"))
def view_collection(collection):
	collection_handler = CollHandler()
	record_handler = RecordHandler()
	media_handler = MediaHandler()
	people_handler = PeopleHandler()
	db = get_db()
	coll_data = collection_handler.get_coll(collection)
	coll_id = int(coll_data["id"])
	
	records = record_handler.query_recs("SELECT * FROM records WHERE collectionId = ?", coll_id)

	irns = []

	for record in records:
		irns.append(record["irn"])

	media = media_handler.get_med(statement="SELECT * from media WHERE recordId IN ({0})".format(", ".join("?" for _ in irns)), value=irns)

	if request.method == "POST":
		error = None
		db_id = request.form["db_id"]
		irn = request.form["irn"]
		include = request.form["include"]

		rec_data = {"db_id": db_id, "irn": irn, "include": include}

		update_rec = record_handler.update_rec(rec_data)

		if update_rec is None:
			error = "Update failed"

		if error is None:
			return render_template("view/records.html", records=records, media=media)

		flash(error)

	return render_template("view/records.html", records=records, media=media)

@bp.route("/select", methods=("GET", "POST"))
def saveSelection():
	media_handler = MediaHandler()

	if request.method == "POST":
		media_irn = request.form["irn"]
		selection = request.form["selection"]
		
		update = media_handler.update_med(media_irn, selection)
		print(update)
		
		read_media = media_handler.get_med(statement="SELECT * from media WHERE irn = ?", value=media_irn, one=True)
		resp = {"irn": read_media["irn"], "include": read_media["include"]}
		return resp