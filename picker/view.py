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
from picker.db import get_db, write_new, query_db, update_item, delete_item

bp = Blueprint('view', __name__, url_prefix='/view')

@bp.route("/<collection>", methods=("GET", "POST"))
def view_collection(collection):
	cards = None

	coll_data = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[collection], one=True)
	coll_id = int(coll_data["id"])
	coll_title = coll_data["title"]

	coll_size = len(query_db(statement="SELECT * FROM records WHERE collectionId = ?", args=[coll_id], one=False))
	
	if request.method == "POST":
		response = query_db(statement="SELECT * FROM records WHERE collectionId = ?", args=[coll_id], one=False)
		if response is not None:
			records = [{k: record[k] for k in record.keys()} for record in response]

			for record in records:
				record.update({"media": None, "people": None})
				m_response = query_db(statement="SELECT m.irn, m.width, m.height, m.license, m.include from media m \
						JOIN recordmedia rm \
						ON m.irn = rm.mediaId \
						WHERE rm.recordId = ?", args=[record["irn"]], one=False)

				if m_response is not None:
					meds = [{k: med[k] for k in med.keys()} for med in m_response]
					record.update({"media": meds})

				p_response = query_db(statement="SELECT p.irn, p.title from people p \
						JOIN recordpeople rp \
						ON p.irn = rp.personId \
						WHERE rp.recordId = ?", args=[record["irn"]], one=False)

				if p_response is not None:
					peeps = [{k: peep[k] for k in peep.keys()} for peep in p_response]
					record.update({"people": meds})

#		for record in records:
#			irns.append(record["irn"])
#
#		if len(irns) > 0:
#			media = query_db(statement="SELECT * from media WHERE recordId IN ({0})".format(", ".join("?" for _ in irns)), args=irns, one=False)
#
			return render_cards(records=records, request=request)

		else:
			return render_template("view/records.html", coll_title=coll_title, coll_size="No matching images.", collection=collection)

	else:
		return render_template("view/records.html", coll_title=coll_title, coll_size=coll_size, collection=collection)

def render_cards(records, request):
	print(request.form)
	start = int(request.form["start"])
	size = int(request.form["size"])

	f_todo = None
	if request.form["todo"] == 'true':
		f_todo = True
	elif request.form["todo"] == 'false':
		f_todo = False

	cards = []
	record_set = []
	for i in range(start, len(records)):
		if len(record_set) < size:
			try:
				this_record = records[i]

				if f_todo == False:
					record_set.append(this_record)
				else:
					this_record_todo = False

					for image in this_record["media"]:
						if image["include"] == None:
							this_record_todo = True

					if this_record_todo == True:
						record_set.append(records[i])

			except IndexError:
				break
		elif records[i] == records[-1]:
			break
		else:
			break

	if len(record_set) == 0:
		print("Oh no")
		return "none"

	for record in record_set:
		record_id = record["irn"]
		card = render_template("view/recordcard.html", record=record)
		cards.append(card)
	return cards

@bp.route("/select", methods=("GET", "POST"))
def saveSelection():
	if request.method == "POST":
		media_irn = request.form["irn"]
		selection = request.form["selection"]
		
		update = update_item(statement="UPDATE media SET include = ? WHERE irn = ?", args=(selection, media_irn), message="Updated image {}".format(media_irn))
		
		read_media = query_db(statement="SELECT * from media WHERE irn = ?", args=(media_irn,), one=True)

		resp = {"irn": read_media["irn"], "include": read_media["include"]}

		return resp