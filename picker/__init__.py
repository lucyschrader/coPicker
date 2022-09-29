# -*- coding: utf-8 -*-

import sys
sys.path.append("C:/Users/lucy.schrader/Documents/Scripts/coApiHarvest")

import os
import requests
import json
from flask import Flask, render_template, url_for, request, flash, g
from datetime import datetime
import time
import sqlite3
import TePapaHarvester

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

	from . import harvest, view
	app.register_blueprint(harvest.bp)
	app.register_blueprint(view.bp)

	@app.route("/", methods=["GET","POST"])
	def start():
		return render_template("base.html", records=None)

	return app