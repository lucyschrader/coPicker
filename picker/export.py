# -*- coding: utf-8 -*-

import sys
sys.path.append("C:/Users/lucy.schrader/Documents/Scripts/coApiHarvest")
import TePapaHarvester

import functools
from flask import (Blueprint, g, redirect, render_template, request, url_for, jsonify)
import os
from datetime import datetime
import time
import csv
import sqlite3
from picker.db import get_db, write_new, query_db, update_item, delete_item

bp = Blueprint('export', __name__, url_prefix='/export')

@bp.route("/<collection>")
def export_collection(collection):
	export_csv = "{}_pickeroutput.csv".format(collection)
	write_file = open(export_csv, 'w', newline='', encoding='utf-8')
	writer = csv.writer(write_file, delimiter=',')
	writer.writerow(["irn", "media_irn"])

	coll_data = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[collection], one=True)
	coll_id = int(coll_data["id"])

	records = query_db(statement="SELECT * FROM records WHERE collectionId = ?", args=[coll_id], one=False)
	if records is not None:
		for record in records:
			media = query_db(statement="SELECT m.irn, m.include from media m \
					JOIN recordmedia rm \
					ON m.irn = rm.mediaId \
					WHERE rm.recordId = ?", args=[record["irn"]], one=False)

			for med in media:
				if med["include"] == "y":
					writer.writerow([record["irn"], med["irn"]])

	write_file.close()

	return redirect(url_for("view.view_collection", collection=collection))