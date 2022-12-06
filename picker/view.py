# -*- coding: utf-8 -*-

import sys
sys.path.append("C:/Users/lucy.schrader/Documents/Scripts/coApiHarvest")
import TePapaHarvester

import functools
from flask import (Blueprint, g, redirect, render_template, request, url_for, jsonify, flash, session)
import os
from datetime import datetime
import time
from picker.db import get_db, write_new, query_db, update_item, delete_item
from picker.auth import login_required, admin_required

bp = Blueprint('view', __name__, url_prefix='/view')

class Records():
	def __init__(self, collection=None, sort=None):
		self.collection = collection
		self.record_selections = query_db(statement="SELECT * from projectrecords WHERE projectId = ?", args=[g.current_project["id"]], one=False)
		self.media_selections = query_db(statement="SELECT * from projectmedia WHERE projectId = ?", args=[g.current_project["id"]], one=False)
		self.loaded_records = query_db(statement="SELECT * FROM records r \
			JOIN recordloaded rl \
			ON r.irn = rl.recordId \
			WHERE (r.collectionId = ?, rl.url LIKE '%'||?||'%')", args=(self.coll_id, g.current_project["baseUrl"]), one=False)
		self.sort = sort
		self.coll_id = None
		self.coll_title = None
		self.total_records = 0
		self.total_images = 0
		self.recs_checked = 0
		self.recs_with_inclusions = 0
		self.img_included = 0
		self.img_excluded = 0
		self.img_loaded = len(self.loaded_records)
		self.records = None
		self.errors = None

		self.collection_info()
		self.return_records()

	def collection_info(self):
		coll_data = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[self.collection], one=True)
		if coll_data == None:
			self.errors = "Error: No collection data"
		
		self.coll_id = int(coll_data["id"])
		self.coll_title = coll_data["title"]

		count_records = query_db(statement="SELECT COUNT(*) FROM records WHERE collectionId = ?", args=[self.coll_id], one=False)
		for row in count_records:
			self.total_records = row[0]

		count_images = query_db(statement="SELECT COUNT(*) FROM records r \
			JOIN recordmedia rm \
			ON r.irn = rm.recordId \
			JOIN media m \
			ON rm.mediaId = m.irn \
			WHERE collectionId = ?", args=[self.coll_id], one=False)
		for row in count_images:
			self.total_images = row[0]

		for row in self.record_selections:
			if row["include"] == "y":
				self.recs_with_inclusions += 1
			if row["complete"] == "y":
				self.recs_checked += 1

		for row in self.media_selections:
			if row["include"] == "y":
				self.img_included += 1
			elif row["include"] == "n":
				self.img_excluded += 1

	def return_records(self):
		if self.sort:
			query_statement = "SELECT * FROM records WHERE collectionId = ? ORDER BY {} DESC".format(self.sort)
			response = query_db(statement=query_statement, args=[self.coll_id], one=False)
		else:
			response = query_db(statement="SELECT * FROM records WHERE collectionId = ?", args=[self.coll_id], one=False)

		if response is not None:
			records = [{k: record[k] for k in record.keys()} for record in response]

			for record in records:
				record.update({"media": None, "people": None, "include": None, "checkComplete": "n"})

				for row in self.record_selections:
					if row["recordId"] == record["irn"]:
						record.update({"include": row["include"]})

				m_response = query_db(statement="SELECT * from media m \
					JOIN recordmedia rm \
					ON m.irn = rm.mediaId \
					WHERE rm.recordId = ?", args=[record["irn"]], one=False)

				if m_response is not None:
					meds = [{k: med[k] for k in med.keys()} for med in m_response]
					for med in meds:
						med.update({"include": None})
						total_media = len(meds)
						checked_media = 0
						for row in self.media_selections:
							if row["mediaId"] == med["irn"]:
								med.update({"include": row["include"]})
								if row["include"] == "y":
									checked_media += 1
						if total_media == checked_media:
							record.update({"checkComplete": "y"})
					record.update({"media": meds})

				p_response = query_db(statement="SELECT p.irn, p.title from people p \
						JOIN recordpeople rp \
						ON p.irn = rp.personId \
						WHERE rp.recordId = ?", args=[record["irn"]], one=False)

				if p_response is not None:
					peeps = [{k: peep[k] for k in peep.keys()} for peep in p_response]
					record.update({"people": peeps})

			self.records = records

@bp.route("/<collection>")
def send_to_cards(collection):
	return redirect(url_for("view.view_collection", collection=collection))

@bp.route("/<collection>/cards", methods=("GET", "POST"))
@login_required
def view_collection(collection):
	recordData = Records(collection=collection)

	if recordData.errors == None:
		return render_template("view/records.html", recordData=recordData, view="cards")

	else:
		flash("Collection not harvested")
		return redirect(url_for("harvest.harvest"))

@bp.route("/<collection>/list", methods=("GET", "POST"))
@login_required
def view_collection_list(collection):
	recordData = Records(collection=collection)

	if recordData.errors == None:
		return render_template("view/records.html", recordData=recordData, view="list")

	else:
		flash("Collection not harvested")
		return redirect(url_for("harvest.harvest"))

@bp.route("/<collection>/page", methods=("GET", "POST"))
@login_required
def fill_page(collection):
	formatted_data = None
	if request.method == "POST":
		print(request.form)
		view = request.form["view"]

		if view == "list":
			formatted_data = fill_list(request)
		elif view == "cards"
			formatted_data = fill_cards(request)

		if formatted_data is not None:
			recordData = formatted_data[0]
			htmlBlocks = formatted_data[1]
			return {"recordData": recordData; "htmlBlocks": htmlBlocks}

def fill_cards(request):
	current_project_id = g.user["currentProject"]

	size = int(request.form["size"])

	recordData = Records(collection=collection, sort=None)
	records = recordData.records

	cards = []
	record_set = []
	for i in range(0, len(records)):
		if len(record_set) < size:
			try:
				this_record = records[i]
				this_record_projectcheck = query_db(statement="SELECT * from projectrecords WHERE (recordId = ? AND projectId = ?)", args=(this_record["irn"], current_project_id), one=True)
				if this_record_projectcheck == None:
					record_set.append(this_record)
				else:
					if this_record_projectcheck["complete"] == "n":
						record_set.append(this_record)

			except IndexError:
				break
		elif records[i] == records[-1]:
			break
		else:
			break

	if len(record_set) == 0:
		print("Oh no")

	for record in record_set:
		card = render_template("view/recordcard.html", record=record)
		card += render_template("view/modal.html", record=record)
		cards.append(card)

	return (recordData, cards)

def fill_list(request):
	current_project_id = g.user["currentProject"]

	current_page = int(request.form["current-page"])
	size = int(request.form["size"])
	filter_todo = request.form["filter-todo"]
	filter_included = request.form["filter-included"]
	filter_excluded = request.form["filter-excluded"]
	sort_new = request.form["sort-new"]

	f_todo = False
	if filter_todo == "true":
		f_todo = True

	f_include = False
	if filter_included == "true":
		f_include = True

	f_exclude = False
	if filter_excluded == "true":
		f_exclude = True

	sort = None
	if sort_new == "true":
		sort = "recordModified"

	recordData = Records(collection=collection, sort=sort)
	records = recordData.records

	page_count = (len(records) / size)
	start = 0
	if current_page > 1:
		start = size * current_page - 1

	list_items = []
	list_modals = []
	record_set = []
	for i in range(start, len(records)):
		if len(record_set) < size:
			try:
				this_record = records[i]
				this_record_projectcheck = query_db(statement="SELECT * from projectrecords WHERE (recordId = ? AND projectId = ?)", args=(this_record["irn"], current_project_id), one=True)

				if f_todo == True:
					if this_record_projectcheck == None:
						record_set.append(this_record)
					else:
						if this_record_projectcheck["complete"] == "n":
							record_set.append(this_record)
				
				elif f_include == True:
					if this_record_projectcheck["include"] == "y":
						record_set.append(this_record)

				elif f_exclude == True:
					if this_record_projectcheck["include"] == "n":
						record_set.append(this_record)

				else:
					record_set.append(this_record)

			except IndexError:
				break
		elif records[i] == records[-1]:
			break
		else:
			break

	if len(record_set) == 0:
		print("Oh no")

	for record in record_set:
		list_item = render_template("view/recordlistitem.html", record=record)
		list_modal = render_template("view/modal.html", record=record)
		list_items.append(list_item)
		list_modals.append(list_modal)

	return (recordData, {"items": list_items, "modals": list_modals, "page-count": page_count})

@bp.route("/select", methods=("GET", "POST"))
@login_required
def saveSelection():
	if request.method == "POST":
		current_project_id = g.user["currentProject"]
		record_irn = request.form["record_irn"]
		media_irn = request.form["media_irn"]
		selection = request.form["selection"]
		resp = {"media_irn": media_irn, "prev_include": None, "new_include": None, "prev_rec_status_include": None, "prev_rec_status_complete": None, "new_rec_status_include": None, "new_rec_status_complete": None}
		
		project_media_db = query_db(statement="SELECT * from projectmedia WHERE (mediaId = ? AND projectId = ?)", args=(media_irn, current_project_id), one=True)
		
		if project_media_db is not None:
			prev_media_status_include = project_media_db["include"]
			resp.update({"prev_include": prev_media_status_include})
			if prev_media_status_include == selection:
				pass
			else:
				update_item(statement="UPDATE projectmedia SET include = ? WHERE id = ?", args=(selection, project_media_db["id"]))
		else:
			write_new(statement="INSERT INTO projectmedia (mediaId, projectId, include) VALUES (?, ?, ?)", args=(media_irn, current_project_id, selection))

		resp.update({"new_include": selection})

		project_record_db = query_db(statement="SELECT * from projectrecords \
			JOIN records \
			ON projectrecords.recordId = records.irn \
			WHERE (recordId = ? AND projectId = ?)", args=(record_irn, current_project_id), one=True)

		record_media = query_db(statement="SELECT * from media m \
			JOIN recordmedia rm \
			ON m.irn = rm.mediaId \
			WHERE rm.recordId = ?", args=[record_irn], one=False)

		total_record_media = len(record_media)
		checked_record_media = 0
		included_record_media = 0

		new_rec_status_include = None
		new_rec_status_complete = None

		attached_media_irns = []
		for media in record_media:
			attached_media_irns.append(media["irn"])

		print("Attached media: ", attached_media_irns)

		project_all_media_db_args = []
		for i in attached_media_irns:
			project_all_media_db_args.append(i)
		project_all_media_db_args.append(current_project_id)

		project_all_media_db = query_db(statement="SELECT * from projectmedia WHERE (mediaId IN ({0}) AND projectId = ?)".format(", ".join("?" for _ in attached_media_irns)), args=project_all_media_db_args, one=False)

		for row in project_all_media_db:
			print("Media in DB: ", row["mediaId"], row["include"])

		if project_all_media_db:
			for media in record_media:
				for row in project_all_media_db:
					if media["irn"] == row["mediaId"]:
						checked_record_media += 1
						if row["include"] == "y":
							included_record_media += 1

		print("Checked media:", checked_record_media)
		print("Included media:", included_record_media)

		if included_record_media > 0:
			new_rec_status_include = "y"
		elif included_record_media == 0 and total_record_media == checked_record_media:
			new_rec_status_include = "n"

		if total_record_media == checked_record_media:
			new_rec_status_complete = "y"

		resp.update({"new_rec_status_include": new_rec_status_include, "new_rec_status_complete": new_rec_status_complete})

		if project_record_db is not None:
			prev_rec_status_include = project_record_db["include"]
			prev_rec_status_complete = project_record_db["complete"]
			resp.update({"prev_rec_status_include": prev_rec_status_include, "prev_rec_status_complete": prev_rec_status_complete})

			update_item(statement="UPDATE projectrecords SET include = ?, complete = ? WHERE id = ?", args=(new_rec_status_include, new_rec_status_complete, project_record_db["id"]))

		else:
			write_new(statement="INSERT INTO projectrecords (projectId, recordId, include, complete) VALUES (?, ?, ?, ?)", args=(current_project_id, record_irn, new_rec_status_include, new_rec_status_complete))

		print(resp)
		return resp