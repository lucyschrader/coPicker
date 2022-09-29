# -*- coding: utf-8 -*-

import sys
sys.path.append("C:/Users/lucy.schrader/Documents/Scripts/coApiHarvest")
import TePapaHarvester

import functools
from flask import (Blueprint, g, redirect, render_template, request, url_for)
import os
from datetime import datetime
import time
import sqlite3
from picker.db import get_db, CollHandler, RecordHandler, MediaHandler, PeopleHandler

bp = Blueprint('harvest', __name__, url_prefix='/harvest')

class DatabaseWriter():
	# Outputs query data to sqlite3 db
	# Creates a new object for each collection, irn, media irn and person
	def __init__(self):
		self.CollHandler = CollHandler()
		self.RecordHandler = RecordHandler()
		self.MediaHandler = MediaHandler()
		self.PeopleHandler = PeopleHandler()

	def process_irns(self, record_data):
		all_irns = record_data.keys()
		#print(all_irns)

		for irn in all_irns:
			this_record = record_data[irn]
			if self.RecordHandler.get_rec(irn):
				print("{} already in DB".format(irn))
			else:
				collection_data = self.proc_coll(this_record)
				self.CollHandler.write_new(collection_data)

				media_data = self.proc_med(this_record, irn)
				people_data = self.proc_per(this_record, irn)
				if len(media_data) > 0:

					for media in media_data:
						self.MediaHandler.write_new(media)

					for person in people_data:
						self.PeopleHandler.write_new(person)

					this_record_proc = self.proc_rec(this_record)

					read_coll = self.CollHandler.get_coll(this_record["collection"])
					coll_id = read_coll["id"]
					this_record_proc.update({"collectionId": coll_id})

					self.RecordHandler.write_new(this_record_proc)

	def proc_coll(self, this_record):
		coll_dict = {
			"title": None,
			"facetedTitle": None
		}

		if "collectionLabel" in this_record:
			coll_dict.update({"title": this_record["collectionLabel"]})

		if "collection" in this_record:
			coll_dict.update({"facetedTitle": this_record["collection"]})

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
				"media_irn": None,
				"recordId": irn,
				"type_val": None,
				"width": None,
				"height": None,
				"license": None,
				"include": "None"
			}

			if "media_irn" in media:
				med_dict.update({"media_irn": media["media_irn"]})

			if "media_type" in media:
				med_dict.update({"type_val": media["media_type"]})

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
					"recordId": irn,
					"title": None,
					"irn": None
				}

				if "producer_name" in prod:
					per_dict.update({"title": prod["producer_name"]})

				if "producer_id" in prod:
					per_dict.update({"irn": prod["producer_id"]})

				per_list.append(per_dict)

		if "collectors" in this_record:
			for person in this_record["collectors"]:
				per_dict = {
						"recordId": irn,
						"title": None,
						"irn": None
					}

				if "collectedBy" in person:
					per_dict.update({"title": person["collectedBy"]})

				if "collectorId" in person:
					per_dict.update({"irn": person["collectorId"]})

				per_list.append(per_dict)

		return per_list

	def proc_rec(self, this_record):
		record_dict = {
			"irn": None,
			"title": None,
			"type_val": None,
			"collection": None,
			"identifier": None,
			"dateLabel": None,
			"dateValue": None,
			"personLabel": None,
			"people": None,
			"qualityScore": None,
			"media": None,
			"include": "None"
			}

		if "id" in this_record:
			record_dict.update({"irn": this_record["id"]})

		if "title" in this_record:
			record_dict.update({"title": this_record["title"]})

		if "type" in this_record:
			record_dict.update({"type_val": this_record["type"]})

		if "collection" in this_record:
			record_dict.update({"collection": this_record["collection"]})

		if "identifier" in this_record:
			record_dict.update({"identifier": this_record["identifier"]})

		this_date_label = None
		this_date = None
		this_person_label = None
		this_person_ids = []
		if "type" in this_record:
			if this_record["type"] == "Specimen":
				if "dateCollected" in this_record:
					this_date_label = "Date collected"
					this_date = this_record["dateCollected"]
					this_person_label = "Collector"
					this_person_ids = this_record["collectorId"]
			elif this_record["type"] == "Object":
				if "production" in this_record:
					production_data = this_record["production"]
					this_date_label = "Date created"
					if "production_date" in production_data[0]:
						this_date = production_data[0]["production_date"]
					if "producer_name" in production_data[0]:
						this_person_label = "Creator"
					for prod in production_data:
						if "producer_id" in prod:
							this_person_ids.append(prod["producer_id"])

		if this_date_label == None:
			this_date_label = "Date"
		if this_date == None:
			this_date = "Unknown"
		if this_person_label == None:
			this_person_label = "Person"
		if len(this_person_ids) == 0:
			this_person_ids = "Unknown"

		record_dict.update({"dateLabel": this_date_label, "dateValue": this_date, "personLabel": this_person_label, "people": this_person_ids})

		if "qualityScore" in this_record:
			record_dict.update({"qualityScore": this_record["qualityScore"]})

		return record_dict

class RecordData():
	def __init__(self, mode=None, source=None, collection=None):
		self.data = None

		self.mode = mode
		self.source = source
		self.collection = collection

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
		filters = [{"field": "hasRepresentation.rights.allowsDownload", "keyword": "True"}, {"field": "collection", "keyword": "{}".format(self.collection)}, {"field": "type", "keyword": "Object"}, {"field": "additionalType", "keyword": "PhysicalObject"}]

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
	collections = [{"facetedTitle": "Photography", "date": "9/27/2022"}, {"facetedTitle": "RareBooks", "date": "16/05/2021"}, {"facetedTitle": "Philatelic", "date": "01/01/1970"}, {"facetedTitle": "Birds", "date": "19/01/1983"}]
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

	return render_template("harvest/save.html", collections=collections)