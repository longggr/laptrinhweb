import os
import sqlite3
from functools import wraps
from flask import render_template, request, redirect, url_for, session, flash
from . import majors_bp


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE = os.path.join(BASE_DIR, "db", "database.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_major_schema(conn):
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(nganh_hoc)").fetchall()]
    if "chi_tieu" not in columns:
        conn.execute("ALTER TABLE nganh_hoc ADD COLUMN chi_tieu INTEGER DEFAULT 1")
        conn.execute("UPDATE nganh_hoc SET chi_tieu = 1 WHERE chi_tieu IS NULL OR chi_tieu <= 0")
        conn.commit()


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


@majors_bp.route("/admin")
@login_required
@role_required("admin")
def admin_majors():
    conn = get_db_connection()
    ensure_major_schema(conn)
    majors = conn.execute(
        """
        SELECT id, ma_nganh, ten_nganh, mo_ta, chi_tieu
        FROM nganh_hoc
        ORDER BY id ASC
        """
    ).fetchall()
    conn.close()

    return render_template("admin_majors.html", majors=majors)


@majors_bp.route("/admin/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_major():
    if request.method == "POST":
        ma_nganh = request.form.get("ma_nganh", "").strip()
        ten_nganh = request.form.get("ten_nganh", "").strip()
        mo_ta = request.form.get("mo_ta", "").strip()
        chi_tieu = request.form.get("chi_tieu", "1").strip()

        conn = get_db_connection()
        ensure_major_schema(conn)
        try:
            conn.execute(
                """
                INSERT INTO nganh_hoc (ma_nganh, ten_nganh, mo_ta, chi_tieu)
                VALUES (?, ?, ?, ?)
                """,
                (ma_nganh, ten_nganh, mo_ta, max(int(chi_tieu or 1), 1))
            )
            conn.commit()
            flash("Thêm ngành học thành công.", "success")
            return redirect(url_for("majors.admin_majors"))
        except (sqlite3.IntegrityError, ValueError):
            flash("Mã ngành đã tồn tại hoặc chỉ tiêu không hợp lệ.", "error")
        finally:
            conn.close()

    return render_template("admin_major_form.html", major=None)


@majors_bp.route("/admin/edit/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_major(id):
    conn = get_db_connection()
    ensure_major_schema(conn)

    major = conn.execute(
        """
        SELECT id, ma_nganh, ten_nganh, mo_ta, chi_tieu
        FROM nganh_hoc
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    if major is None:
        conn.close()
        return "Không tìm thấy ngành học.", 404

    if request.method == "POST":
        ma_nganh = request.form.get("ma_nganh", "").strip()
        ten_nganh = request.form.get("ten_nganh", "").strip()
        mo_ta = request.form.get("mo_ta", "").strip()
        chi_tieu = request.form.get("chi_tieu", "1").strip()

        try:
            conn.execute(
                """
                UPDATE nganh_hoc
                SET ma_nganh = ?, ten_nganh = ?, mo_ta = ?, chi_tieu = ?
                WHERE id = ?
                """,
                (ma_nganh, ten_nganh, mo_ta, max(int(chi_tieu or 1), 1), id)
            )
            conn.commit()
            flash("Cập nhật ngành học thành công.", "success")
            conn.close()
            return redirect(url_for("majors.admin_majors"))
        except (sqlite3.IntegrityError, ValueError):
            flash("Mã ngành đã tồn tại hoặc chỉ tiêu không hợp lệ.", "error")

    conn.close()
    return render_template("admin_major_form.html", major=major)


@majors_bp.route("/admin/delete/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_major(id):
    conn = get_db_connection()

    try:
        conn.execute("DELETE FROM nganh_hoc WHERE id = ?", (id,))
        conn.commit()
        flash("Xóa ngành học thành công.", "success")
    except sqlite3.IntegrityError:
        flash("Không thể xóa ngành học này vì đang có nguyện vọng sử dụng.", "error")
    finally:
        conn.close()

    return redirect(url_for("majors.admin_majors"))