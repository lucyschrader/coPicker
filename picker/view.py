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
	def __init__(self, collection=None, filter_to_todo=False, filter_to_included=False, filter_to_excluded=False, sort=None, quiet=False):
		self.collection = collection
		self.filter_to_todo = filter_to_todo
		self.filter_to_included = filter_to_included
		self.filter_to_excluded = filter_to_excluded
		self.sort = sort
		self.view = session.get("view")
		self.coll_id = None
		self.coll_title = None
		self.total_records = 0
		self.total_images = 0
		self.recs_checked = 0
		self.recs_with_inclusions = 0
		self.img_included = 0
		self.img_excluded = 0
		self.records = []
		self.errors = None
		self.quiet = quiet

		self.collection_info()
		self.count_selections()

	def collection_info(self):
		coll_data = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[self.collection], one=True)
		
		self.coll_id = int(coll_data["id"])

		if self.quiet == False:
			print("Collection ID:", self.coll_id)

		self.coll_title = coll_data["title"]

		if self.sort:
			coll_records = query_db(statement="SELECT * FROM records WHERE collectionId = ? ORDER BY {} DESC".format(self.sort), args=[self.coll_id], one=False)
		else:
			coll_records = query_db(statement="SELECT * FROM records WHERE collectionId = ?", args=[self.coll_id], one=False)

		if self.quiet == False:
			print("Number of records in this collection:", len(coll_records))

		self.total_records = len(coll_records)

		self.total_images = len(query_db(statement="SELECT * FROM records r \
			JOIN recordmedia rm \
			ON r.irn = rm.recordId \
			JOIN media m \
			ON rm.mediaId = m.irn \
			WHERE collectionId = ?", args=[self.coll_id], one=False))

	def count_selections(self):
		q_statement = "SELECT r.irn as recordIRN, rm.mediaId as mediaIRN, pr.include as recordInclude, pr.complete as recordComplete, pm.include as mediaInclude, rl.url as recordLoadedUrl, pr.projectId as recordProjectId, pm.projectId as mediaProjectId FROM records r \
			JOIN recordmedia rm \
			ON r.irn = rm.recordId \
			LEFT JOIN projectrecords pr \
			ON r.irn = pr.recordId \
			LEFT JOIN projectmedia pm \
			ON rm.mediaId = pm.mediaId \
			LEFT JOIN recordloaded rl \
			ON r.irn = rl.recordId \
			WHERE (r.collectionId = ? AND (pr.projectId = ? OR pm.projectId = ?))"

		db_records = query_db(statement=q_statement, args=[self.coll_id, g.current_project["id"], g.current_project["id"]], one=False)

		if self.quiet == False:
			print("Number of rows without filters:", len(db_records))

		project_base_url = g.current_project["baseUrl"]

		included_records = []
		completed_records = []
		included_media = []
		excluded_media = []
		records_with_related_urls = []

		for row in db_records:
			if row["recordProjectId"]:
				if row["recordInclude"] == "y":
					included_records.append(row["recordIRN"])
				if row["recordComplete"] == "y":
					completed_records.append(row["recordIRN"])

			if row["mediaProjectId"]:
				if row["mediaInclude"] == "y":
					included_media.append(row["mediaIRN"])
				if row["mediaInclude"] == "n":
					excluded_media.append(row["mediaIRN"])

			if row["recordLoadedUrl"]:
				if project_base_url in row["recordLoadedUrl"]:
					records_with_related_urls.append(row["recordIRN"])
		
		self.recs_checked = len(list(set(completed_records)))
		self.recs_with_inclusions = len(list(set(included_records)))
		self.img_included = len(list(set(included_media)))
		self.img_excluded = len(list(set(excluded_media)))

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
			q_where_values.append("n")

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

		db_records = query_db(statement=q_statement, args=q_where_values, one=False)

		if self.quiet == False:
			print("Number of filtered rows:", len(db_records))

		return db_records

	def collate_records(self, db_records, start, size):
		db_records_irns = []
		for row in db_records:
			if row["recordIRN"] not in db_records_irns:
				db_records_irns.append(row["recordIRN"])
		for i in range(start, len(db_records_irns)):
			record_irn = db_records_irns[i]
			if len(self.records) < size:
				try:
					if self.view == "cards":
						if query_db(statement="SELECT * FROM bookedrecords WHERE (projectId = ? AND recordId = ?)", args=(g.current_project["id"], record_irn), one=True) is None:
								this_record = self.collate_this_record(db_records, record_irn)
						else:
							print("Already being viewed, moving on...")
							
					else:
						this_record = self.collate_this_record(db_records, record_irn)

				except IndexError:
					break
			elif db_records_irns[i] == db_records_irns[-1]:
				break
			else:
				break

		if len(self.records) == 0:
			print("No records left")

	def collate_this_record(self, db_records, record_irn):
		for row in filter(lambda row: row["recordIRN"] == record_irn, db_records):
			this_project = False
			if row["recordProjectId"] == None or g.current_project["id"]:
				this_project = True
			if row["mediaProjectId"] == None or g.current_project["id"]:
				this_project = True
			if this_project == True:
				this_record_index = next((i for i, record in enumerate(self.records) if record["irn"] == record_irn), None)
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
					if self.view == "cards":
						write_new(statement="INSERT INTO bookedrecords (projectId, userId, recordId) VALUES (?, ?, ?)", args=(g.current_project["id"], g.user["id"], record_irn))
				else:
					this_media_index = next((i for i, media in enumerate(self.records[this_record_index]["media"]) if media["irn"] == row["mediaIRN"]), None)
					if this_media_index == None:
						self.records[this_record_index]["media"].append({"irn": row["mediaIRN"], "include": row["mediaInclude"]})
					this_person_index = next((i for i, person in enumerate(self.records[this_record_index]["people"]) if person["irn"] == row["personIRN"]), None)
					if this_person_index == None:
						self.records[this_record_index]["people"].append({"irn": row["personIRN"], "title": row["personTitle"]})

@bp.route("/<collection>")
def send_to_cards(collection):
	return redirect(url_for("view.view_collection", collection=collection, view="cards"))

@bp.route("/<collection>/<view>", methods=("GET", "POST"))
@login_required
def view_collection(collection, view="cards"):
	session["view"] = view
	recordData = Records(collection=collection)

	if recordData.errors == None:
		return render_template("view/records.html", recordData=recordData, view=view)
	else:
		flash("Collection not harvested")
		return redirect(url_for("harvest.harvest"))

@bp.route("/<collection>/page", methods=("GET", "POST"))
def fill_page(collection):
	formatted_data = None
	if request.method == "POST":
		print(request.form)
		#view = request.form["view"]
		view = session.get("view")

		if view == "list":
			formatted_data = fill_list(request, collection)
		elif view == "cards":
			formatted_data = fill_cards(request, collection)

		if formatted_data is not None:
			recordData = formatted_data[0]
			htmlBlocks = formatted_data[1]
#			print("Records checked:", recordData.recs_checked)
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
	current_project_id = g.current_project["id"]

	size = int(request.form["size"])

	recordData = Records(collection=collection, filter_to_todo=True, sort=None, quiet=True)
	db_records = recordData.return_records()
	recordData.collate_records(db_records=db_records, start=0, size=size)
	records = recordData.records

	cards = []
	for record in records:
		card = render_template("view/recordcard.html", record=record)
		card += render_template("view/modal.html", record=record)
		cards.append(card)

	return (recordData, cards)

def fill_list(request, collection):
	current_project_id = g.current_project["id"]
	coll_id = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[collection], one=True)["id"]

	current_page = int(request.form["current-page"])
	size = int(request.form["size"])
	filter_todo = request.form["filter-todo"]
	filter_included = request.form["filter-included"]
	filter_excluded = request.form["filter-excluded"]
	sort_new = request.form["sort-new"]

	start = 0
	if current_page > 1:
		start = size * (current_page - 1)

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

	recordData = Records(collection=collection, filter_to_todo=f_todo, filter_to_included=f_include, filter_to_excluded=f_exclude, sort=sort, quiet=True)
	db_records = recordData.return_records()
	recordData.collate_records(db_records=db_records, start=start, size=size)
	records = recordData.records

	page_count = (len(records) / size)

	list_items = []
	list_modals = []

	for record in records:
		list_item = render_template("view/recordlistitem.html", record=record)
		list_modal = render_template("view/modal.html", record=record)
		list_items.append(list_item)
		list_modals.append(list_modal)

	return (recordData, {"items": list_items, "modals": list_modals, "page-count": page_count})

@bp.route("/select", methods=("GET", "POST"))
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

@bp.route("/<collection>/clearcollection", methods=["GET", "POST"])
def clear_this_collection(collection):
	coll_id = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[collection], one=True)["id"]
	records = query_db(statement="SELECT pr.id as projectRecordsId, pm.id as projectMediaId FROM projectrecords pr \
		JOIN records r \
		ON pr.recordId = r.irn \
		JOIN recordmedia rm \
		ON pr.recordId = rm.recordId \
		JOIN projectmedia pm \
		ON rm.mediaId = pm.mediaId \
		WHERE (r.collectionId = ? AND (pr.projectId = ? OR pm.projectId = ?))", args=[coll_id, g.current_project["id"], g.current_project["id"]], one=False)

	record_selections = []
	media_selections = []
	for row in records:
		record_selections.append(row["projectRecordsId"])
		media_selections.append(row["projectMediaId"])

	delete_item(statement="DELETE FROM projectrecords WHERE id IN ({0})".format(", ".join("?" for _ in record_selections)), args=record_selections)
	delete_item(statement="DELETE FROM projectmedia WHERE id IN ({0})".format(", ".join("?" for _ in media_selections)), args=media_selections)

	print("Deleted!")

	return redirect(url_for("view.send_to_cards", collection=collection))