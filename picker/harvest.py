# -*- coding: utf-8 -*-

import os
import sys
from picker import HARVESTER_PATH
sys.path.append(HARVESTER_PATH)
import TePapaHarvester

import functools
from flask import (Blueprint, g, redirect, render_template, request, url_for, flash, session)
import datetime
import time
from picker.db import get_db, write_new, query_db, update_item, delete_item
from picker.auth import login_required, admin_required

bp = Blueprint('harvest', __name__, url_prefix='/harvest')

class DatabaseWriter():
	# Outputs query data to sqlite3 db
	# Creates a new object for each collection, irn, media irn and person
	def __init__(self, collection, harvest_mode):
		self.collection = collection
		self.harvest_mode = harvest_mode
		self.collection_databased = False
		self.errors = None

	def process_irns(self, record_data):
		all_irns = record_data.keys()
		#print(all_irns)

		for irn in all_irns:
			this_record = record_data[irn]

			if self.collection_databased == False:
				self.insert_collection(this_record)

			irn = int(irn)
			action = None
			existing_rec = query_db(statement="SELECT * FROM records WHERE irn = ?", args=[irn], one=True)

			if self.harvest_mode == "additive":
				if existing_rec == True:
					continue
				else:
					action = "write"
			elif self.harvest_mode == "reharvest":
				if existing_rec == True:
					action = "update"
				else:
					action = "write"
			elif self.harvest_mode == "new-harvest":
				action = "write"

			self.harvest_record(this_record=this_record, irn=irn, action=action)

	def insert_collection(self, this_record):
		if query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[self.collection], one=True) == None:
			coll_data = self.proc_coll(this_record)
			write_new(statement="INSERT INTO collections (title, facetedTitle, lastHarvested, objectType) VALUES (?, ?, ?, ?)", args=[coll_data["title"], coll_data["facetedTitle"], coll_data["lastHarvested"], coll_data["objectType"]])
			self.collection_databased == True
		else:
			self.collection_databased == True

	def harvest_record(self, this_record, irn, action):
		media_data = self.proc_med(this_record, irn)
		people_data = self.proc_per(this_record, irn)

		if len(media_data) > 0:
			rec = self.proc_rec(this_record)

			coll_id = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[self.collection], one=True)["id"]
			
			rec.update({"collectionId": coll_id})

			if action == "write":
				write_new(statement="INSERT INTO records (irn, recordCreated, recordModified, title, type, collectionId, identifier, dateLabel, dateValue, personLabel, qualityScore) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", args=(rec["irn"], rec["recordCreated"], rec["recordModified"], rec["title"], rec["type"], rec["collectionId"], rec["identifier"], rec["dateLabel"], rec["dateValue"], rec["personLabel"], rec["qualityScore"]))
			elif action == "update":
				update_item(statement="UPDATE records SET recordModified = ?, title = ?, identifier = ?, dateLabel = ?, dateValue = ?, personLabel = ?, qualityScore = ? WHERE irn = ?", args=(rec["recordModified"], rec["title"], rec["identifier"], rec["dateLabel"], rec["dateValue"], rec["personLabel"], rec["qualityScore"], irn))

			for media in media_data:
				if query_db(statement="SELECT * FROM media WHERE irn = ?", args=[media["irn"]], one=True) == None:
					write_new(statement="INSERT INTO media (irn, type, width, height, license) VALUES (?, ? , ?, ?, ?)", args=(media["irn"], media["type"], media["width"], media["height"], media["license"]))
				else:
					update_item(statement="UPDATE media SET width = ?, height = ?, license = ? WHERE irn = ?", args=(media["width"], media["height"], media["license"], media["irn"]))
				if query_db(statement="SELECT * FROM recordmedia WHERE recordId = ? AND mediaId = ?", args=(irn, media["irn"]), one=True) == None:
					write_new(statement="INSERT INTO recordmedia (recordId, mediaId) VALUES (?, ?)", args=(irn, media["irn"]))

			if len(people_data) > 0:
				for person in people_data:
					if person["title"] == None:
						person.update({"title": "No name"})
					if query_db(statement="SELECT * FROM people WHERE irn = ?", args=[person["irn"]], one=True) == None:
						write_new(statement="INSERT INTO people (title, irn) VALUES (?, ?)", args=(person["title"], person["irn"]))
					else:
						update_item(statement="UPDATE people SET title = ? WHERE irn = ?", args=[person["title"], person["irn"]])
					if query_db(statement="SELECT * FROM recordpeople WHERE recordId = ? AND personId = ?", args=(irn, person["irn"]), one=True) == None:
						write_new(statement="INSERT INTO recordpeople (recordId, personId) VALUES (?, ?)", args=(irn, person["irn"]))

			if "related" in this_record:
				for associated_link in this_record["related"]:
					associated_url = associated_link["associatedUrl"]
					if query_db(statement="SELECT * FROM recordloaded WHERE (recordId = ? AND url = ?)", args=(irn, associated_url)) == None:
						write_new(statement="INSERT INTO recordloaded (recordId, url) VALUES (?, ?)", args=(irn, associated_url))

	def proc_coll(self, this_record):
		coll_dict = {
			"title": None,
			"facetedTitle": None,
			"lastHarvested": None,
			"totalImages": None,
			"objectType": None,
		}

		if "collectionLabel" in this_record:
			coll_dict.update({"title": this_record["collectionLabel"]})

		if "collection" in this_record:
			coll_dict.update({"facetedTitle": this_record["collection"]})

		if "type" in this_record:
			coll_dict.update({"objectType": this_record["type"]})

		now = datetime.datetime.now()
		print(now)
		coll_dict.update({"lastHarvested": now})

		return coll_dict

	def proc_med(self, this_record, irn):
		media_list = []
		media_subset = []
		for media in this_record["media"]:
			if "media_width" in media:
				# Checking image size for Google
				if media["media_width"] >= 2500 and media["media_height"] >= 2500:
					if "downloadable" in media:
						if media["downloadable"] == True:
							media_subset.append(media)

		for media in media_subset:
			med_dict = {
				"irn": None,
				"type": None,
				"width": None,
				"height": None,
				"license": None
			}

			if "media_irn" in media:
				med_dict.update({"irn": media["media_irn"]})

			if "media_type" in media:
				med_dict.update({"type": media["media_type"]})

			if "media_width" in media:
				med_dict.update({"width": media["media_width"]})

			if "media_height" in media:
				med_dict.update({"height": media["media_height"]})

			if "rights_title" in media:
				med_dict.update({"license": media["rights_title"]})

			media_list.append(med_dict)

		return media_list

	def proc_per(self, this_record, irn):
		per_list = []

		if "production" in this_record:
			for prod in this_record["production"]:
				per_dict = {
					"title": None,
					"irn": None
				}

				if "producer_name" in prod:
					per_dict.update({"title": prod["producer_name"]})

				if "producer_id" in prod:
					per_dict.update({"irn": prod["producer_id"]})

				if per_dict["irn"] is not None:
					per_list.append(per_dict)

		if "collectors" in this_record:
			for person in this_record["collectors"]:
				per_dict = {
						"title": None,
						"irn": None
					}

				if "collectedBy" in person:
					per_dict.update({"title": person["collectedBy"]})

				if "collectorId" in person:
					per_dict.update({"irn": person["collectorId"]})

				if per_dict["irn"] is not None:
					per_list.append(per_dict)

		return per_list

	def proc_rec(self, this_record):
		record_dict = {
			"irn": None,
			"recordCreated": None,
			"recordModified": None,
			"title": None,
			"type": None,
			"collection": None,
			"identifier": None,
			"dateLabel": None,
			"dateValue": None,
			"personLabel": None,
			"qualityScore": None
			}

		if "id" in this_record:
			record_dict.update({"irn": this_record["id"]})

		if "recordCreated" in this_record:
			record_dict.update({"recordCreated": this_record["recordCreated"]})

		if "recordModified" in this_record:
			record_dict.update({"recordModified": this_record["recordModified"]})

		if "title" in this_record:
			record_dict.update({"title": this_record["title"]})

		if "type" in this_record:
			record_dict.update({"type": this_record["type"]})

		if "collection" in this_record:
			record_dict.update({"collection": this_record["collection"]})

		if "identifier" in this_record:
			record_dict.update({"identifier": this_record["identifier"]})

		this_date_label = None
		this_date = None
		this_person_label = None
		if "type" in this_record:
			if this_record["type"] == "Specimen":
				if "dateCollected" in this_record:
					this_date_label = "Date collected"
					this_date = this_record["dateCollected"]
			elif this_record["type"] == "Object":
				if "production" in this_record:
					production_data = this_record["production"]
					this_date_label = "Date created"
					if "production_date" in production_data[0]:
						this_date = production_data[0]["production_date"]

		if this_date_label == None:
			this_date_label = "Date"
		if this_date == None:
			this_date = "Unknown"
		if this_person_label == None:
			this_person_label = "Person"

		record_dict.update({"dateLabel": this_date_label, "dateValue": this_date, "personLabel": this_person_label})

		if "qualityScore" in this_record:
			record_dict.update({"qualityScore": this_record["qualityScore"]})

		return record_dict

class RecordData():
	def __init__(self, mode=None, source=None, collection=None, object_type=None):
		self.data = None

		self.mode = mode
		self.source = source
		self.collection = collection
		self.object_type = object_type

		self.harvester = TePapaHarvester.Harvester(quiet=True, sleep=0.1)

		if self.mode == "search":
			self.search_API()
		elif self.mode == "list":
			self.list_API()

	def search_API(self):
		q = "*"
		fields = None
		q_from = 0
		size = 500
		sort = [{"field": "id", "order": "asc"}]
		facets = [{}]
		filters = [{"field": "hasRepresentation.rights.allowsDownload", "keyword": "True"}, {"field": "collection", "keyword": "{}".format(self.collection)}, {"field": "type", "keyword": self.object_type}]

		if self.object_type == "Object":
			filters.append({"field": "additionalType", "keyword": "PhysicalObject"})

		self.harvester.set_params(q=q, fields=fields, filters=filters, facets=facets, q_from=q_from, size=size, sort=sort)
		
		self.harvester.count_results()
		
		self.data = self.harvester.harvest_records()

	def list_API(self):
		resource_type = "object"
		irns = []

		if self.source.endswith(".csv"):
			with open(self.source, newline="", encoding="utf-8") as f:
				reader = csv.DictReader(f, delimiter=",")
				for row in reader:
					if "irn" in row:
						if row["irn"] not in irns:
							irns.append(int(row["irn"].strip()))
#					if "media_irn" in row:
#						media_irns.append(int(row["media_irn"].strip()))

		elif self.source.endswith(".txt"):
			with open(self.source, 'r', encoding="utf-8") as f:
				lines = f.readlines()
				for line in lines:
					irns.append(int(line.strip()))

		self.data = self.harvester.harvest_from_list(resource_type=resource_type, irns=irns)

@bp.route("/<collection>", methods=("GET", "POST"))
@admin_required
def harvest(collection):
	if request.method == "POST":
		humanities = ["Art", "CollectedArchives", "History", "MuseumArchives", "PacificCultures", "Philatelic", "Photography", "RareBooks", "TaongaMāori"]
		sciences = ["Archaeozoology", "Birds", "Crustacea", "Fish", "FossilVertebrates", "Geology", "Insects", "LandMammals", "MarineInvertebrates", "MarineMammals", "Molluscs", "Plants", "ReptilesAndAmphibians"]
		
		harvest_mode = request.form["harvest"]
		
		if collection in humanities:
			object_type = "Object"
		elif collection in sciences:
			object_type = "Specimen"
		
		search = RecordData(mode="search", source=None, collection=collection, object_type=object_type)
		record_data = search.data

		DBwriter = DatabaseWriter(collection, harvest_mode)
		DBwriter.process_irns(record_data)

		return redirect(url_for("view.send_to_cards", collection=collection))

	coll_data = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[collection], one=True)

	if coll_data == None:
		return render_template("harvest/harvestform.html", collection=collection, harvest="new")
	else:
		return render_template("harvest/harvestform.html", collection=collection, harvest="redo")