# -*- coding: utf-8 -*-

import functools
from flask import (Blueprint, g, redirect, render_template, request, url_for, jsonify, flash, session)
import os
import json
from datetime import datetime
import time
from picker.db import get_db, write_new, query_db, update_item, delete_item
from picker.auth import login_required, admin_required

bp = Blueprint('view', __name__, url_prefix='/view')

class Records():
	def __init__(self, collection=None, filter_to_todo=False, filter_to_included=False, filter_to_excluded=False, sort=None, mode=None):
		self.collection = collection
		self.filter_to_todo = filter_to_todo
		self.filter_to_included = filter_to_included
		self.filter_to_excluded = filter_to_excluded
		self.sort = sort
		self.mode = mode
		self.coll_id = None
		self.coll_title = None
		self.coll_records_irns = []
		self.total_records = 0
		self.total_images = 0
		self.recs_checked = 0
		self.recs_with_inclusions = 0
		self.img_included = 0
		self.img_excluded = 0
		self.records = []
		self.errors = None

		self.collection_info()
		self.count_selections()
		if mode == "fill":
			self.return_records()

	def collection_info(self):
		coll_data = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[self.collection], one=True)
		
		self.coll_id = int(coll_data["id"])
		print("Collection ID:", self.coll_id)
		self.coll_title = coll_data["title"]

		if self.sort:
			coll_records = query_db(statement="SELECT * FROM records WHERE collectionId = ? ORDER BY {} DESC".format(self.sort), args=[self.coll_id], one=False)
		else:
			coll_records = query_db(statement="SELECT * FROM records WHERE collectionId = ?", args=[self.coll_id], one=False)

		print("Number of records in this collection:", len(coll_records))

		for row in coll_records:
			self.coll_records_irns.append(row["irn"])

		self.total_records = len(coll_records)
		print("Total records:", self.total_records)

		self.total_images = len(query_db(statement="SELECT * FROM records r \
			JOIN recordmedia rm \
			ON r.irn = rm.recordId \
			JOIN media m \
			ON rm.mediaId = m.irn \
			WHERE collectionId = ?", args=[self.coll_id], one=False))

		print("Total images:", self.total_images)

	def count_selections(self):
		q_statement = "SELECT r.irn as recordIRN, m.irn as mediaIRN, pr.include as recordInclude, pr.complete as recordComplete, pm.include as mediaInclude, rl.url as recordLoadedUrl, pr.projectId as recordProjectId, pm.projectId as mediaProjectId FROM records r \
			JOIN recordmedia rm \
			ON r.irn = rm.recordId \
			JOIN media m \
			ON rm.mediaId = m.irn \
			LEFT JOIN projectrecords pr \
			ON r.irn = pr.recordId \
			LEFT JOIN projectmedia pm \
			ON rm.mediaId = pm.mediaId \
			LEFT JOIN recordloaded rl \
			ON r.irn = rl.recordId \
			WHERE r.collectionId = ?"

		db_records = query_db(statement=q_statement, args=[self.coll_id], one=False)

		print("Number of rows without filters:", len(db_records))

		project_base_url = g.current_project["baseUrl"]
		records_with_related_urls = []

		for row in db_records:
			if row["recordProjectId"] == None or g.current_project["id"]:
				if row["recordInclude"] == "y":
					self.recs_with_inclusions += 1
				if row["recordComplete"] == "y":
					self.recs_checked += 1

			if row["mediaProjectId"] == None or g.current_project["id"]:
				if row["mediaInclude"] == "y":
					self.img_included += 1
				elif row["mediaInclude"] == "n":
					self.img_excluded += 1

			if row["recordLoadedUrl"] is not None:
				if project_base_url in row["recordLoadedUrl"]:
					if row["recordIRN"] not in records_with_related_urls:
						records_with_related_urls.append(row["recordIRN"])
						self.loaded_records += 1

	def return_records(self):
		q_where = " WHERE (r.collectionId = ?"
		q_where_values = [self.coll_id]

		if self.filter_to_todo == True:
			q_where += " AND (pr.complete IS ? OR pr.complete = ?)"
			q_where_values.append(None)
			q_where_values.append("n")
		if self.filter_to_included == True:
			q_where += " AND pr.include = ?"
			q_where_values.append("y")
		if self.filter_to_excluded == True:
			q_where += " AND pr.include = ?"
			q_where_params.append("n")

		q_statement = "SELECT r.irn as recordIRN, r.recordModified, r.title as recordTitle, r.dateLabel, r.dateValue, r.personLabel, m.irn as mediaIRN, p.irn as personIRN, p.title as personTitle, pr.include as recordInclude, pr.complete as recordComplete, pr.projectId as recordProjectId, pm.include as mediaInclude, pm.projectId as mediaProjectId, rl.url as recordLoadedUrl \
			FROM records r \
			JOIN recordmedia rm \
			ON r.irn = rm.recordId \
			JOIN media m \
			ON rm.mediaId = m.irn \
			LEFT JOIN projectrecords pr \
			ON r.irn = pr.recordId \
			LEFT JOIN projectmedia pm \
			ON m.irn = pm.mediaId \
			LEFT JOIN recordpeople rp \
			ON r.irn = rp.recordId \
			LEFT JOIN people p \
			ON rp.personId = p.irn \
			LEFT JOIN recordloaded rl \
			ON r.irn = rl.recordId" + q_where + ")"

		if self.sort:
			q_statement += " ORDER BY {} DESC".format(self.sort)

		print(q_statement)
		print(q_where_values)

		db_records = query_db(statement=q_statement, args=q_where_values, one=False)
		print("Number of filtered rows:", len(db_records))
		self.collate_records(db_records)

	def collate_records(self, db_records):
		for irn in self.coll_records_irns:
			for row in db_records:
				this_project = False
				if row["recordProjectId"] == None or g.current_project["id"]:
					this_project = True
				if row["mediaProjectId"] == None or g.current_project["id"]:
					this_project = True
				if this_project == True:
					record_irn = row["recordIRN"]
					if record_irn == irn:
						this_record_index = next((i for i, record in enumerate(self.records) if record["irn"] == record_irn), None)
						print("Record index:", this_record_index)
						if this_record_index == None:
							this_record = {
								"irn": record_irn,
								"title": row["recordTitle"],
								"dateLabel": row["dateLabel"],
								"dateValue": row["dateValue"],
								"personLabel": row["personLabel"],
								"recordModified": row["recordModified"],
								"media": [{"irn": row["mediaIRN"], "include": row["mediaInclude"]}],
								"people": [{"irn": row["personIRN"], "title": row["personTitle"]}],
								"include": row["recordInclude"],
								"complete": row["recordComplete"],
								"loaded": row["recordLoadedUrl"]
								}
							self.records.append(this_record)
						else:
							this_media_index = next((i for i, media in enumerate(self.records[this_record_index]["media"]) if media["irn"] == row["mediaIRN"]), None)
							if this_media_index == None:
								self.records[this_record_index]["media"].append({"irn": row["mediaIRN"], "include": row["mediaInclude"]})
							this_person_index = next((i for i, person in enumerate(self.records[this_record_index]["people"]) if person["irn"] == row["personIRN"]), None)
							if this_person_index == None:
								self.records[this_record_index]["people"].append({"irn": row["personIRN"], "title": row["personTitle"]})
		print("All records collated")

@bp.route("/<collection>")
def send_to_cards(collection):
	return redirect(url_for("view.view_collection", collection=collection, view="cards"))

@bp.route("/<collection>/<view>", methods=("GET", "POST"))
@login_required
def view_collection(collection, view="cards"):
	recordData = Records(collection=collection, mode="count")

	if recordData.errors == None:
		return render_template("view/records.html", recordData=recordData, view=view)
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
			formatted_data = fill_list(request, collection)
		elif view == "cards":
			formatted_data = fill_cards(request, collection)

		if formatted_data is not None:
			recordData = formatted_data[0]
			htmlBlocks = formatted_data[1]
			return {
				"recordData": {
					"collection": recordData.collection,
					"coll_id": recordData.coll_id,
					"coll_title": recordData.coll_title,
					"total_records": recordData.total_records,
					"total_images": recordData.total_images,
					"recs_checked": recordData.recs_checked,
					"recs_with_inclusions": recordData.recs_with_inclusions,
					"img_included": recordData.img_included,
					"img_excluded": recordData.img_excluded,
				},
				"errors": recordData.errors,
				"htmlBlocks": htmlBlocks
			}

	return "Error"

def fill_cards(request, collection):
	current_project_id = g.user["currentProject"]

	size = int(request.form["size"])

	recordData = Records(collection=collection, filter_to_todo=True, sort=None, mode="fill")
	records = recordData.records
	print("Records for cards:", len(records))

	cards = []
	record_set = []
	for i in range(0, len(records)):
		if len(record_set) < size:
			try:
				record_set.append(records[i])
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

def fill_list(request, collection):
	current_project_id = g.user["currentProject"]
	coll_id = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[collection], one=True)["id"]

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

	recordData = Records(collection=collection, filter_to_todo=f_todo, filter_to_included=f_include, filter_to_excluded=f_exclude, sort=sort, mode="fill")
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
			this_record = records[i]
			try:
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