# -*- coding: utf-8 -*-

import functools
from flask import (Blueprint, g, redirect, render_template, request, url_for, jsonify, send_from_directory)
import os
from datetime import datetime
import time
import csv
from picker.db import get_db, write_new, query_db, update_item, delete_item
from picker.auth import login_required

bp = Blueprint('export', __name__, url_prefix='/export')

@bp.route("/<collection>")
@login_required
def export_collection(collection):
	current_project_id = g.user["currentProject"]
	UPLOAD_FOLDER = os.path.join(os.getcwd(), "picker\\static\\uploads\\")

	filename = "{}_pickeroutput.csv".format(collection)
	export_csv = UPLOAD_FOLDER + filename
	write_file = open(export_csv, 'w', newline='', encoding='utf-8')
	writer = csv.writer(write_file, delimiter=',')
	writer.writerow(["record_irn", "identifier", "title", "media_irn", "width", "height", "license", "record_include", "record_complete", "media_include"])

	collection_id = query_db(statement="SELECT * FROM collections WHERE facetedTitle = ?", args=[collection], one=True)["id"]

	records_media = query_db(statement="SELECT r.irn as recordIRN, r.title, r.identifier, m.irn as mediaIRN, m.width, m.height, m.license FROM records r \
		JOIN recordmedia rm \
		ON r.irn = rm.recordId \
		JOIN media m \
		ON rm.mediaId = m.irn \
		WHERE collectionId = ?", args=[collection_id], one=False)

	for row in records_media:
		record_irn = row["recordIRN"]
		identifier = row["identifier"]
		title = row["title"]
		media_irn = row["mediaIRN"]
		width = row["width"]
		height = row["height"]
		licence = row["license"]
		record_include = None
		record_complete = None
		media_include = None

		project_records_media = query_db(statement="SELECT pr.recordId as recordIRN, pr.include as recordInclude, pr.complete as recordComplete, pm.mediaId as mediaIRN, pm.include as mediaInclude from projectrecords pr \
			JOIN recordmedia rm \
			ON pr.recordId = rm.recordId \
			JOIN projectmedia pm \
			ON rm.mediaId = pm.mediaId \
			WHERE pr.projectId = ? and pr.recordId = ? and pm.mediaId = ?", args=(current_project_id, record_irn, media_irn), one=True)

		if project_records_media is not None:
			record_include = project_records_media["recordInclude"]
			record_complete = project_records_media["recordComplete"]
			media_include = project_records_media["mediaInclude"]

		writer.writerow([record_irn, identifier, title, media_irn, width, height, licence, record_include, record_complete, media_include])
			
	write_file.close()

	return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)