# -*- coding: utf-8 -*-

import os
import sys
import requests
import json
from flask import Flask, render_template, url_for, request, flash
import shutil
import time
import hashlib

sys.path.append("C:/Users/lucy.schrader/Documents/Scripts/googleharvest")

import TePapaHarvester

app = Flask(__name__)

working_folder = os.getcwd()
image_folder = working_folder + "/static/thumbs/"
'''
class CoQuery():
	def __init__(self, headers=None, doc_type=None, irn=None):
		self.headers = headers
		self.doc_type = doc_type
		self.irn = irn

	def view_record(self):
		request = Request(self.doc_type, self.irn)
		response = json.loads(requests.get(request.url, headers=self.headers).text)
		print("Requesting {}".format(request.url))

		return result

class Request():
	def __init__(self, doc_type=None, irn=None):
		self.doc_type = doc_type
		self.irn = irn

		self.base_url = "https://data.tepapa.govt.nz/collection/"

		self.query_url = base_url + self.doc_type + "/" + self.irn

		return self.query_url

class Harvester():
	def __init__(self, doc_type=None, record=None, irn=irn):
		self.doc_type = doc_type
		self.record = record
		self.irn = irn
		self.record_dict = {}

	def save_data(self):
		if "title" in self.record:
			title = record["title"]
		else:
			title = "n/a"
		self.record_dict.update({"title":title})

		prod_list = []
		if "production" in self.record:
			prod_sec = self.record["production"]
            prod_sec_length = len(prod_sec)
			prod_num = 0
            for i in range(0,prod_sec_length):
                if prod_sec[prod_num]:
	                if "contributor" in prod_sec[prod_num]:
	                    prod_creator = prod_sec[prod_num]["contributor"]["title"]
	                    prod_list.append(prod_creator)
	                else: pass
	        self.record_dict.update({"creator":prod_list})
	    else:
	    	pass

	    if "isTypeOf" in self.record:
            type_of_section = self.record["isTypeOf"]
            type_of_cats = []
            for type_of in type_of_section:
                # poss run against whitelist and only select matches
                if "title" in type_of:
                    type_of_cats.append(type_of["title"])
                else: pass

            self.record_dict.update({"isTypeOf": type_of_cats})
        else: pass

        if "hasRepresentation" in self.record:
        	images = self.record["hasRepresentation"]
            image_list_length = len(images)
            image_num = 0
            images_data_dict = {}
            for i in range(0,image_list_length):
                this_data_set = {}
                if images[image_num]:
                    i_dat = images[image_num]
                    if "id" in i_dat:
                        image_irn = str(i_dat["id"])
                        this_data_set.update({"image_{}_irn".format(image_num):image_irn})
                    else: pass
                    if "thumbnailUrl" in i_dat:
                        image_thumb = i_dat["thumbnailUrl"]
                        filename = self.irn + "_" + image_irn + ".jpg"
                        this_data_set.update({"image_{}_url".format(image_num):image_thumb})
                        self.save_thumbnail(self.irn, filename, image_thumb)
                    else: pass
                    if "rights" in i_dat:
                        if "title" in i_dat["rights"]:
                            image_rights = i_dat["rights"]["title"]
                            this_data_set.update({"image_{}_rights".format(image_num):image_rights})
                        else: pass

                    images_data_dict.update({"image_{}".format(image_num): this_data_set})
                else: pass
#                print(images_data_dict)

                self.record_dict.update(images_data_dict)
                
#                print(self.fields)

		f.close()

		return self.record_dict
'''

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

		data_filename = "saved_data_{}.json".format(source_id)

		with open(data_filename, "w+", encoding="utf-8") as f:
			json.dump(saved_dataset, f)
		f.close()

		return render_template("base.html", source_id=source_id)
	return render_template("base.html")

@app.route("/<source_id>", methods=["GET","POST"])
def load(source_id):
	source_file = "saved_data_{}.json".format(source_id)
	with open(source_file, 'r', encoding="utf-8") as f:
		records = json.load(f)
		return render_template("base.html", records=records)