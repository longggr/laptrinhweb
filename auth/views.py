import sqlite3
from flask import render_template, request, redirect, url_for, session, flash
from . import auth_bp
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE = os.path.join(BASE_DIR, "db", "database.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db_connection()
        user = conn.execute(
            """
            SELECT id, username, password_hash, role, display_name, thi_sinh_id
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()
        conn.close()

        if user is None or password != user["password_hash"]:
            error = "Sai tên đăng nhập hoặc mật khẩu."
        else:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["display_name"] = user["display_name"]
            session["thi_sinh_id"] = user["thi_sinh_id"]

            return redirect(url_for("home"))

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))