import os
import sqlite3
from functools import wraps
from flask import render_template, request, redirect, url_for, session
from . import search_bp


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE = os.path.join(BASE_DIR, "db", "database.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)
    return wrapper


@search_bp.route("/", methods=["GET", "POST"])
@login_required
def search_candidate():
    candidate = None
    preferences = []
    error = None

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()
        ngay_sinh = request.form.get("ngay_sinh", "").strip()

        conn = get_db_connection()

        candidate = conn.execute(
            """
            SELECT *
            FROM thi_sinh
            WHERE (cccd = ? OR sbd = ?)
              AND ngay_sinh = ?
            """,
            (keyword, keyword, ngay_sinh)
        ).fetchone()

        if candidate:
            preferences = conn.execute(
                """
                SELECT nv.thu_tu, nh.ma_nganh, nh.ten_nganh
                FROM nguyen_vong nv
                JOIN nganh_hoc nh ON nv.nganh_id = nh.id
                WHERE nv.thi_sinh_id = ?
                ORDER BY nv.thu_tu ASC
                """,
                (candidate["id"],)
            ).fetchall()
        else:
            error = "Không tìm thấy thông tin thí sinh."

        conn.close()

    return render_template(
        "search.html",
        candidate=candidate,
        preferences=preferences,
        error=error
    )