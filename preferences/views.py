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


def ensure_major_schema(conn):
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(nganh_hoc)").fetchall()]
    if "chi_tieu" not in columns:
        conn.execute("ALTER TABLE nganh_hoc ADD COLUMN chi_tieu INTEGER DEFAULT 1")
        conn.execute("UPDATE nganh_hoc SET chi_tieu = 1 WHERE chi_tieu IS NULL OR chi_tieu <= 0")
        conn.commit()


def _to_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def calculate_admission(conn):
    ensure_major_schema(conn)

    majors = conn.execute(
        """
        SELECT id, ma_nganh, ten_nganh, COALESCE(chi_tieu, 1) AS chi_tieu
        FROM nganh_hoc
        ORDER BY id ASC
        """
    ).fetchall()

    candidates = conn.execute(
        """
        SELECT id, ho_ten, sbd, cccd, diem_max_xet_tuyen
        FROM thi_sinh
        """
    ).fetchall()

    raw_preferences = conn.execute(
        """
        SELECT nv.id, nv.thi_sinh_id, nv.nganh_id, nv.thu_tu, nh.ma_nganh, nh.ten_nganh
        FROM nguyen_vong nv
        JOIN nganh_hoc nh ON nv.nganh_id = nh.id
        ORDER BY nv.thi_sinh_id ASC, nv.thu_tu ASC, nv.id ASC
        """
    ).fetchall()

    candidate_by_id = {
        row["id"]: {
            "id": row["id"],
            "ho_ten": row["ho_ten"],
            "sbd": row["sbd"],
            "cccd": row["cccd"],
            "score": _to_float(row["diem_max_xet_tuyen"])
        }
        for row in candidates
    }

    preferences_by_candidate = {}
    max_order = 0
    for row in raw_preferences:
        max_order = max(max_order, row["thu_tu"])
        preferences_by_candidate.setdefault(row["thi_sinh_id"], []).append(
            {
                "nganh_id": row["nganh_id"],
                "thu_tu": row["thu_tu"],
                "ma_nganh": row["ma_nganh"],
                "ten_nganh": row["ten_nganh"]
            }
        )

    assigned = {}
    admitted_by_major = {major["id"]: [] for major in majors}

    for order in range(1, max_order + 1):
        for major in majors:
            major_id = major["id"]
            quota = max(int(major["chi_tieu"] or 1), 1)
            pool = list(admitted_by_major[major_id])

            for candidate_id, prefs in preferences_by_candidate.items():
                if candidate_id in assigned:
                    continue
                pref = next((item for item in prefs if item["thu_tu"] == order and item["nganh_id"] == major_id), None)
                if pref is None:
                    continue
                info = candidate_by_id.get(candidate_id)
                if info is None:
                    continue
                pool.append(
                    {
                        "candidate_id": candidate_id,
                        "ho_ten": info["ho_ten"],
                        "sbd": info["sbd"],
                        "cccd": info["cccd"],
                        "score": info["score"],
                        "thu_tu": order
                    }
                )

            pool.sort(key=lambda x: (-x["score"], x["thu_tu"], x["candidate_id"]))
            selected = pool[:quota]
            selected_ids = {item["candidate_id"] for item in selected}
            previous_ids = {item["candidate_id"] for item in admitted_by_major[major_id]}

            for removed_id in previous_ids - selected_ids:
                assigned.pop(removed_id, None)
            for item in selected:
                assigned[item["candidate_id"]] = {"nganh_id": major_id, "thu_tu": item["thu_tu"]}

            admitted_by_major[major_id] = selected

    cutoff_by_major = {}
    for major in majors:
        admitted = admitted_by_major[major["id"]]
        cutoff_by_major[major["id"]] = min((item["score"] for item in admitted), default=None)

    candidate_result = {}
    for candidate_id, assignment in assigned.items():
        major_id = assignment["nganh_id"]
        pref = next(
            (p for p in preferences_by_candidate.get(candidate_id, []) if p["nganh_id"] == major_id),
            None
        )
        candidate_result[candidate_id] = {
            "nganh_id": major_id,
            "thu_tu": assignment["thu_tu"],
            "ma_nganh": pref["ma_nganh"] if pref else "",
            "ten_nganh": pref["ten_nganh"] if pref else ""
        }

    return majors, admitted_by_major, cutoff_by_major, candidate_result


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


@preferences_bp.route("/admin/results")
@login_required
@role_required("admin")
def admin_admission_results():
    conn = get_db_connection()
    majors, admitted_by_major, cutoff_by_major, _ = calculate_admission(conn)
    conn.close()
    return render_template(
        "admin_admission_results.html",
        majors=majors,
        admitted_by_major=admitted_by_major,
        cutoff_by_major=cutoff_by_major
    )


@preferences_bp.route("/candidate/result")
@login_required
@role_required("candidate")
def candidate_admission_result():
    thi_sinh_id = session.get("thi_sinh_id")
    conn = get_db_connection()
    _, _, _, candidate_result = calculate_admission(conn)
    result = candidate_result.get(thi_sinh_id)
    conn.close()
    return render_template("candidate_admission_result.html", result=result)