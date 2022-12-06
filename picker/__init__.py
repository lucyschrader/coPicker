# -*- coding: utf-8 -*-

import os
import requests
import json
from flask import Flask, render_template, url_for, request, flash, g
from datetime import datetime
import random
import time
from picker.db import get_db, write_new, query_db, update_item, delete_item

def create_app(test_config=None):
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		SECRET_KEY='dev',
		DATABASE = os.path.join(app.instance_path, "picker.sqlite"))

	if test_config is None:
		app.config.from_pyfile("config.py", silent=True)
	else:
		app.config.from_mapping(test_config)

	try:
		os.makedirs(app.instance_path)
	except OSError:
		pass

	from . import db
	db.init_app(app)

	from . import auth, harvest, view, export
	app.register_blueprint(auth.bp)
	app.register_blueprint(harvest.bp)
	app.register_blueprint(view.bp)
	app.register_blueprint(export.bp)

	@app.route("/", methods=["GET","POST"])
	def start():
		if g.user:
			return harvest.harvest()
		else:
			cover_images = os.listdir("picker/static/images/covers/")
			cover = "/images/covers/{}".format(random.choice(cover_images))
			return render_template("start.html", cover=cover)

	@app.context_processor
	def projects_collections():
		projects_collections = {
			"db_projects": query_db(statement="SELECT * FROM projects"),
			"coll_names": ["Archaeozoology", "Art", "Birds", "CollectedArchives", "Crustacea", "Fish", "FossilVertebrates", "Geology", "History", "Insects", "LandMammals", "MarineInvertebrates", "MarineMammals", "Molluscs", "MuseumArchives", "PacificCultures", "Philatelic", "Photography", "Plants", "RareBooks", "ReptilesAndAmphibians", "TaongaMāori"],
			"db_collections": query_db(statement="SELECT * FROM collections")
		}
		return projects_collections

	return app