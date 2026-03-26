import os
import sqlite3
from functools import wraps
from flask import (
    render_template, request, redirect,
    url_for, session, flash
)
from . import preferences_bp


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


def role_required(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                return "Bạn không có quyền truy cập.", 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =========================
# CANDIDATE
# =========================
@preferences_bp.route("/candidate")
@login_required
@role_required("candidate")
def candidate_preferences():
    thi_sinh_id = session.get("thi_sinh_id")

    conn = get_db_connection()

    preferences = conn.execute(
        """
        SELECT nv.id, nv.thu_tu, nh.ma_nganh, nh.ten_nganh
        FROM nguyen_vong nv
        JOIN nganh_hoc nh ON nv.nganh_id = nh.id
        WHERE nv.thi_sinh_id = ?
        ORDER BY nv.thu_tu ASC
        """,
        (thi_sinh_id,)
    ).fetchall()

    majors = conn.execute(
        """
        SELECT id, ma_nganh, ten_nganh
        FROM nganh_hoc
        ORDER BY ten_nganh ASC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "candidate_preferences.html",
        preferences=preferences,
        majors=majors
    )


@preferences_bp.route("/candidate/add", methods=["POST"])
@login_required
@role_required("candidate")
def add_candidate_preference():
    thi_sinh_id = session.get("thi_sinh_id")
    nganh_id = request.form.get("nganh_id")
    thu_tu = request.form.get("thu_tu")

    conn = get_db_connection()

    try:
        conn.execute(
            """
            INSERT INTO nguyen_vong (thi_sinh_id, nganh_id, thu_tu)
            VALUES (?, ?, ?)
            """,
            (thi_sinh_id, nganh_id, thu_tu)
        )
        conn.commit()
        flash("Đăng ký nguyện vọng thành công.", "success")
    except sqlite3.IntegrityError:
        flash("Ngành hoặc thứ tự nguyện vọng đã tồn tại.", "error")
    finally:
        conn.close()

    return redirect(url_for("preferences.candidate_preferences"))


@preferences_bp.route("/candidate/delete/<int:id>", methods=["POST"])
@login_required
@role_required("candidate")
def delete_candidate_preference(id):
    thi_sinh_id = session.get("thi_sinh_id")
    conn = get_db_connection()

    conn.execute(
        """
        DELETE FROM nguyen_vong
        WHERE id = ? AND thi_sinh_id = ?
        """,
        (id, thi_sinh_id)
    )
    conn.commit()
    conn.close()

    flash("Xóa nguyện vọng thành công.", "success")
    return redirect(url_for("preferences.candidate_preferences"))


# =========================
# ADMIN - VIEW ONLY
# =========================
@preferences_bp.route("/admin")
@login_required
@role_required("admin")
def admin_preferences():
    keyword = request.args.get("keyword", "").strip()

    conn = get_db_connection()

    if keyword:
        preferences = conn.execute(
            """
            SELECT
                nv.id,
                nv.thu_tu,
                ts.ho_ten,
                ts.sbd,
                ts.cccd,
                nh.ma_nganh,
                nh.ten_nganh
            FROM nguyen_vong nv
            JOIN thi_sinh ts ON nv.thi_sinh_id = ts.id
            JOIN nganh_hoc nh ON nv.nganh_id = nh.id
            WHERE ts.ho_ten LIKE ?
               OR ts.sbd LIKE ?
               OR ts.cccd LIKE ?
               OR nh.ma_nganh LIKE ?
               OR nh.ten_nganh LIKE ?
            ORDER BY ts.ho_ten ASC, nv.thu_tu ASC
            """,
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%"
            )
        ).fetchall()
    else:
        preferences = conn.execute(
            """
            SELECT
                nv.id,
                nv.thu_tu,
                ts.ho_ten,
                ts.sbd,
                ts.cccd,
                nh.ma_nganh,
                nh.ten_nganh
            FROM nguyen_vong nv
            JOIN thi_sinh ts ON nv.thi_sinh_id = ts.id
            JOIN nganh_hoc nh ON nv.nganh_id = nh.id
            ORDER BY ts.ho_ten ASC, nv.thu_tu ASC
            """
        ).fetchall()

    conn.close()
    return render_template("admin_preferences.html", preferences=preferences, keyword=keyword)