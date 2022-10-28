# -*- coding: utf-8 -*-

import sys
sys.path.append("C:/Users/lucy.schrader/Documents/Scripts/coApiHarvest")
import TePapaHarvester

import functools
from flask import (Blueprint, g, redirect, render_template, request, url_for)
import os
import datetime
import time
import sqlite3
from picker.db import get_db, write_new, query_db, update_item, delete_item

bp = Blueprint('harvest', __name__, url_prefix='/harvest')

class DatabaseWriter():
	# Outputs query data to sqlite3 db
	# Creates a new object for each collection, irn, media irn and person
	def __init__(self):
		self.errors = None
		self.search_rec_statement = "SELECT * FROM records WHERE irn = ?"
		self.write_rec_statement = "INSERT INTO records (irn, title, type, collectionId, identifier, dateLabel, dateValue, personLabel, qualityScore, include) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
		self.search_coll_statement = "SELECT * FROM collections WHERE facetedTitle = ?"
		self.write_coll_statement = "INSERT INTO collections (title, facetedTitle, lastHarvested, objectType) VALUES (?, ?, ?, ?)"
		self.write_media_statement = "INSERT INTO media (irn, type, width, height, license) VALUES (?, ? , ?, ?, ?)"
		self.write_person_statement = "INSERT INTO people (title, irn) VALUES (?, ?)"

	def process_irns(self, record_data):
		all_irns = record_data.keys()
		#print(all_irns)

		for irn in all_irns:
			this_record = record_data[irn]
			irn = int(irn)
			if query_db(self.search_rec_statement, [irn], one=True):
				print("{} already in DB".format(irn))
			else:
				facetedTitle = this_record["collection"]
				
				if query_db(self.search_coll_statement, [facetedTitle], one=True) == None:
					coll_data = self.proc_coll(this_record)
					
					write_new(self.write_coll_statement, [coll_data["title"], coll_data["facetedTitle"], coll_data["lastHarvested"], coll_data["objectType"]], "{} successfully saved".format(coll_data["title"]))

				media_data = self.proc_med(this_record, irn)
				people_data = self.proc_per(this_record, irn)

				if len(media_data) > 0:
					rec = self.proc_rec(this_record)

					coll_id = query_db(self.search_coll_statement, [facetedTitle], one=True)["id"]
					
					rec.update({"collectionId": coll_id})

					write_new(self.write_rec_statement, (rec["irn"], rec["title"], rec["type"], rec["collectionId"], rec["identifier"], rec["dateLabel"], rec["dateValue"], rec["personLabel"], rec["qualityScore"], rec["include"]), "Record {} successfully updated".format(rec["irn"]))

					for media in media_data:
						if query_db("SELECT * FROM media WHERE irn = ?", [media["irn"]], one=True) == None:
							write_new(self.write_media_statement, (media["irn"], media["type"], media["width"], media["height"], media["license"]), "Image {} successfully saved".format(media["irn"]))
						write_new("INSERT INTO recordmedia (recordId, mediaId) VALUES (?, ?)", (irn, media["irn"]), "{} successfully joined".format(media["irn"]))

					if len(people_data) > 0:
						for person in people_data:
							if query_db("SELECT * FROM people WHERE irn = ?", [person["irn"]], one=True) == None:
								write_new(self.write_person_statement, (person["title"], person["irn"]), "{} successfully saved".format(person["title"]))
							write_new("INSERT INTO recordpeople (recordId, personId) VALUES (?, ?)", (irn, person["irn"]), "{} successfully joined".format(person["title"]))

#		self.count_total_images(facetedTitle)

	def count_total_images(self, facetedTitle):
		coll_data = query_db(statement=self.search_coll_statement, args=[facetedTitle], one=True)
		coll_id = int(coll_data["id"])
	
		records = query_db(statement="SELECT * FROM records WHERE collectionId = ?", args=[coll_id], one=False)

		irns = []

		for record in records:
			irns.append(record["irn"])

		query_total_images = query_db(statement="SELECT COUNT(*) FROM media WHERE recordId IN ({0})".format(", ".join("?" for _ in irns)), args=irns, one=False)
		total_images = 0
		for row in query_total_images:
			total_images = row[0]

		# Need to add counts and updates for loaded, included, and excluded images
		update_item(statement="UPDATE collections SET totalImages = ? WHERE id = ?", args=[total_images, coll_id], message="{} successfully updated".format(facetedTitle))

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
				"license": None,
				"include": "None"
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
			"title": None,
			"type": None,
			"collection": None,
			"identifier": None,
			"dateLabel": None,
			"dateValue": None,
			"personLabel": None,
			"qualityScore": None,
			"include": "None"
			}

		if "id" in this_record:
			record_dict.update({"irn": this_record["id"]})

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

@bp.route("/save", methods=("GET", "POST"))
def harvest():
	all_colls = ["Archaeozoology", "Art", "Birds", "CollectedArchives", "Crustacea", "Fish", "FossilVertebrates", "Geology", "History", "Insects", "LandMammals", "MarineInvertebrates", "MarineMammals", "Molluscs", "MuseumArchives", "PacificCultures", "Philatelic", "Photography", "Plants", "RareBooks", "ReptilesAndAmphibians", "TaongaMāori"]
	collections = query_db(statement="SELECT * FROM collections")
	if request.method == "POST":
		collection = request.form.get("collection-harvest")
		error = None

		if not collection:
			error = "Collection is required"
		else:
			search = RecordData(mode="search", source=None, collection=collection)
			record_data = search.data

			DBwriter = DatabaseWriter()
			DBwriter.process_irns(record_data)

			return redirect(url_for("view.view_collection", collection=collection))

		if error:
			flash(error)

	return render_template("harvest/save.html", all_colls=all_colls, collections=collections)

@bp.route("/<collection>", methods=("GET", "POST"))
def initial_harvest(collection):
	humanities = ["Art", "CollectedArchives", "History", "MuseumArchives", "PacificCultures", "Philatelic", "Photography", "RareBooks", "TaongaMāori"]
	sciences = ["Archaeozoology", "Birds", "Crustacea", "Fish", "FossilVertebrates", "Geology", "Insects", "LandMammals", "MarineInvertebrates", "MarineMammals", "Molluscs", "Plants", "ReptilesAndAmphibians"]
	if request.method == "POST":
		if request.form["yesbutton"] == "yes":
			if collection in humanities:
				object_type = "Object"
			elif collection in sciences:
				object_type = "Specimen"
			search = RecordData(mode="search", source=None, collection=collection, object_type=object_type)
			record_data = search.data

			DBwriter = DatabaseWriter()
			DBwriter.process_irns(record_data)

			return redirect(url_for("view.view_collection", collection=collection))
		else:
			return redirect("/")

	return render_template("harvest/initial.html", collection=collection)