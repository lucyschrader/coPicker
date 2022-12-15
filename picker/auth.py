# -*- coding: utf-8 -*-

import functools
from flask import (Blueprint, g, redirect, render_template, request, session, url_for, flash)
from werkzeug.security import check_password_hash, generate_password_hash
from picker.db import get_db, write_new, query_db, update_item, delete_item

bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(view):
	@functools.wraps(view)
	def wrapped_view(**kwargs):
		if g.user is None:
			return redirect(url_for("auth.login"))

		return view(**kwargs)

	return wrapped_view

def admin_required(view):
	@functools.wraps(view)
	def admin_view(**kwargs):
		user_id = session.get("user_id")
		db_user = query_db(statement="SELECT * FROM users WHERE id = ?", args=[user_id], one=True)
		if db_user["role"] != "admin":
			return redirect(url_for("start"))

		return view(**kwargs)

	return admin_view

@bp.route("/register", methods=("GET", "POST"))
@admin_required
def register():
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		error = None

		if not username:
			error = "Add a username"
		elif not password:
			error = "Add a password"

		if error is None:
			new_user = write_new(statement="INSERT INTO users (username, password) VALUES (?, ?)", args=(username, generate_password_hash(password)))

			if new_user == False:
				error = f"User {username} is already registered"
				return redirect(url_for("auth.login"))

			else:
				return redirect(url_for("auth.login"))

		flash(error)

	return render_template("auth/register.html")

@bp.route("/login", methods=("GET", "POST"))
def login():
	if request.method == "POST":
		username = request.form["login-username"]
		password = request.form["login-password"]
		project_id = request.form["login-project"]
		error = None

		user = query_db(statement="SELECT * FROM users WHERE username = ?", args=[username], one=True)

		if user is None:
			error = "Incorrect username"
		elif not check_password_hash(user["password"], password):
			error = "Incorrect password"

		if error is None:
			session.clear()
			session["user_id"] = user["id"]
			update_item(statement="UPDATE users SET currentProject = ? WHERE id = ?", args=(project_id, user["id"]))

			return redirect(url_for("start"))

		flash(error)

	return render_template("auth/login.html")

@bp.route("/projectselection", methods=("GET", "POST"))
def set_current_project():
	old_proj_id = None

	user_id = session.get("user_id")
	old_proj_id = query_db(statement="SELECT * FROM users WHERE id = ?", args=[user_id], one=True)["currentProject"]

	if request.method == "POST":
		project_id = request.form["projectId"]
		project_req = query_db(statement="SELECT * FROM projects WHERE id = ?", args=[project_id], one=True)
		project_title = project_req["title"]
		project_faceted_title = project_req["facetedTitle"]
		update_item(statement="UPDATE users SET currentProject = ? WHERE id = ?", args=(project_id, user_id))

		g.current_project = query_db(statement="SELECT * FROM projects WHERE id = ?", args=[g.user["currentProject"]], one=True)

		return {'old-proj-id': old_proj_id, 'new-proj-id': project_id, 'new-proj-title': project_title}

@bp.before_app_request
def load_logged_in_user():
	user_id = session.get("user_id")

	if user_id is None:
		g.user = None
		g.current_project = None
	else:
		g.user = query_db(statement="SELECT * FROM users WHERE id = ?", args=[user_id], one=True)
		g.current_project = query_db(statement="SELECT * FROM projects WHERE id = ?", args=[g.user["currentProject"]], one=True)

@bp.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("start"))

@bp.route("/clearbooking")
def clear_booked_records():
	print("Clearing records!")
	booked_records = query_db(statement="SELECT * FROM bookedrecords WHERE (projectId = ? AND userId = ?)", args=(g.current_project["id"], g.user["id"]), one=False)
	if booked_records:
		delete_item(statement="DELETE FROM bookedrecords WHERE (projectId = ? AND userId = ?)", args=(g.current_project["id"], g.user["id"]))
	return {"message": "Success"}