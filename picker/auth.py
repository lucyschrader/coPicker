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

@bp.route("/register", methods=("GET", "POST"))
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
		username = request.form["username"]
		password = request.form["password"]
		error = None

		user = query_db(statement="SELECT * FROM users WHERE username = ?", args=[username], one=True)

		if user is None:
			error = "Incorrect username"
		elif not check_password_hash(user["password"], password):
			error = "Incorrect password"

		if error is None:
			session.clear()
			session["user_id"] = user["id"]
			return redirect(url_for("index"))

		flash(error)

	return render_template("auth/login.html")

@bp.before_app_request
def load_logged_in_user():
	user_id = session.get("user_id")

	if user_id is None:
		g.user = None
	else:
		g.user = query_db(statement="SELECT * FROM users WHERE id = ?", args=[user_id], one=True)

@bp.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("index"))