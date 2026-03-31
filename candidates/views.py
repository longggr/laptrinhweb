import os
import sqlite3
from functools import wraps
from flask import (
    render_template, request, redirect,
    url_for, session, flash
)
from . import candidates_bp


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE = os.path.join(BASE_DIR, "db", "database.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_sbd(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    return f"SBD{int(digits):06d}"


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
# CANDIDATE PROFILE
# =========================
@candidates_bp.route("/profile", methods=["GET", "POST"])
@login_required
@role_required("candidate")
def profile():
    thi_sinh_id = session.get("thi_sinh_id")
    conn = get_db_connection()

    if request.method == "POST":
        ho_ten = request.form.get("ho_ten")
        ngay_sinh = request.form.get("ngay_sinh")
        gioi_tinh = request.form.get("gioi_tinh")
        dan_toc = request.form.get("dan_toc")
        noi_sinh = request.form.get("noi_sinh")
        tinh_tp = request.form.get("tinh_tp")
        quan_huyen = request.form.get("quan_huyen")

        conn.execute(
            """
            UPDATE thi_sinh
            SET ho_ten = ?, ngay_sinh = ?, gioi_tinh = ?, dan_toc = ?,
                noi_sinh = ?, tinh_tp = ?, quan_huyen = ?
            WHERE id = ?
            """,
            (ho_ten, ngay_sinh, gioi_tinh, dan_toc, noi_sinh, tinh_tp, quan_huyen, thi_sinh_id)
        )
        conn.commit()

        conn.execute(
            """
            UPDATE users
            SET display_name = ?
            WHERE thi_sinh_id = ?
            """,
            (ho_ten, thi_sinh_id)
        )
        conn.commit()

        session["display_name"] = ho_ten
        flash("Cập nhật hồ sơ thành công.", "success")

    candidate = conn.execute(
        """
        SELECT *
        FROM thi_sinh
        WHERE id = ?
        """,
        (thi_sinh_id,)
    ).fetchone()

    conn.close()
    return render_template("candidate_profile.html", candidate=candidate)


# =========================
# ADMIN CANDIDATES
# =========================
@candidates_bp.route("/admin")
@login_required
@role_required("admin")
def admin_candidates():
    conn = get_db_connection()
    candidates = conn.execute(
        """
        SELECT *
        FROM thi_sinh
        ORDER BY id ASC
        """
    ).fetchall()
    conn.close()

    return render_template("admin_candidates.html", candidates=candidates)


@candidates_bp.route("/admin/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_candidate():
    if request.method == "POST":
        cccd = request.form.get("cccd")
        sbd = normalize_sbd(request.form.get("sbd"))
        ma_ho_so = request.form.get("ma_ho_so")
        ho_ten = request.form.get("ho_ten")
        ngay_sinh = request.form.get("ngay_sinh")
        gioi_tinh = request.form.get("gioi_tinh")
        dan_toc = request.form.get("dan_toc")
        noi_sinh = request.form.get("noi_sinh")
        tinh_tp = request.form.get("tinh_tp")
        quan_huyen = request.form.get("quan_huyen")
        nam_tot_nghiep = request.form.get("nam_tot_nghiep")

        conn = get_db_connection()
        try:
            conn.execute(
                """
                INSERT INTO thi_sinh (
                    cccd, sbd, ma_ho_so, ho_ten, ngay_sinh, gioi_tinh,
                    dan_toc, noi_sinh, tinh_tp, quan_huyen, nam_tot_nghiep
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cccd, sbd, ma_ho_so, ho_ten, ngay_sinh, gioi_tinh,
                    dan_toc, noi_sinh, tinh_tp, quan_huyen, nam_tot_nghiep
                )
            )
            conn.commit()
            flash("Thêm thí sinh thành công.", "success")
            return redirect(url_for("candidates.admin_candidates"))
        except sqlite3.IntegrityError:
            flash("CCCD, SBD hoặc mã hồ sơ đã tồn tại.", "error")
        finally:
            conn.close()

    return render_template("admin_candidate_form.html", candidate=None)




@candidates_bp.route("/admin/delete/<int:id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_candidate(id):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM thi_sinh WHERE id = ?", (id,))
        conn.commit()
        flash("Xóa thí sinh thành công.", "success")
    except sqlite3.IntegrityError:
        flash("Không thể xóa thí sinh này.", "error")
    finally:
        conn.close()

    return redirect(url_for("candidates.admin_candidates"))

@candidates_bp.route("/admin/<int:id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_candidate_detail(id):
    conn = get_db_connection()

    candidate = conn.execute(
        """
        SELECT *
        FROM thi_sinh
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    if candidate is None:
        conn.close()
        return "Không tìm thấy thí sinh.", 404

    if request.method == "POST":
        cccd = request.form.get("cccd")
        sbd = normalize_sbd(request.form.get("sbd"))
        ma_ho_so = request.form.get("ma_ho_so")
        ho_ten = request.form.get("ho_ten")
        ngay_sinh = request.form.get("ngay_sinh")
        gioi_tinh = request.form.get("gioi_tinh")
        dan_toc = request.form.get("dan_toc")
        noi_sinh = request.form.get("noi_sinh")
        doi_tuong_uu_tien = request.form.get("doi_tuong_uu_tien")
        khu_vuc_uu_tien = request.form.get("khu_vuc_uu_tien")
        diem_cong_xet_tuyen = request.form.get("diem_cong_xet_tuyen")
        tinh_tp = request.form.get("tinh_tp")
        quan_huyen = request.form.get("quan_huyen")
        nam_tot_nghiep = request.form.get("nam_tot_nghiep")
        hoc_luc = request.form.get("hoc_luc")
        hanh_kiem = request.form.get("hanh_kiem")
        diem_tb_lop_12 = request.form.get("diem_tb_lop_12")
        ma_tinh_lop_12 = request.form.get("ma_tinh_lop_12")
        ma_truong_lop_12 = request.form.get("ma_truong_lop_12")
        diem_toan = request.form.get("diem_toan")
        diem_van = request.form.get("diem_van")
        diem_ly = request.form.get("diem_ly")
        diem_ngoai_ngu = request.form.get("diem_ngoai_ngu")
        ma_mon_ngoai_ngu = request.form.get("ma_mon_ngoai_ngu")
        diem_xet_tot_nghiep = request.form.get("diem_xet_tot_nghiep")
        diem_thpt = request.form.get("diem_thpt")
        diem_dgnl_dgtd = request.form.get("diem_dgnl_dgtd")
        diem_ccqt_thpt = request.form.get("diem_ccqt_thpt")
        diem_sat_act = request.form.get("diem_sat_act")
        diem_pt_khac = request.form.get("diem_pt_khac")
        diem_max_xet_tuyen = request.form.get("diem_max_xet_tuyen")

        try:
            conn.execute(
                """
                UPDATE thi_sinh
                SET
                    cccd = ?, sbd = ?, ma_ho_so = ?, ho_ten = ?, ngay_sinh = ?,
                    gioi_tinh = ?, dan_toc = ?, noi_sinh = ?, doi_tuong_uu_tien = ?,
                    khu_vuc_uu_tien = ?, diem_cong_xet_tuyen = ?, tinh_tp = ?,
                    quan_huyen = ?, nam_tot_nghiep = ?, hoc_luc = ?, hanh_kiem = ?,
                    diem_tb_lop_12 = ?, ma_tinh_lop_12 = ?, ma_truong_lop_12 = ?,
                    diem_toan = ?, diem_van = ?, diem_ly = ?, diem_ngoai_ngu = ?,
                    ma_mon_ngoai_ngu = ?, diem_xet_tot_nghiep = ?, diem_thpt = ?,
                    diem_dgnl_dgtd = ?, diem_ccqt_thpt = ?, diem_sat_act = ?,
                    diem_pt_khac = ?, diem_max_xet_tuyen = ?
                WHERE id = ?
                """,
                (
                    cccd, sbd, ma_ho_so, ho_ten, ngay_sinh,
                    gioi_tinh, dan_toc, noi_sinh, doi_tuong_uu_tien,
                    khu_vuc_uu_tien, diem_cong_xet_tuyen, tinh_tp,
                    quan_huyen, nam_tot_nghiep, hoc_luc, hanh_kiem,
                    diem_tb_lop_12, ma_tinh_lop_12, ma_truong_lop_12,
                    diem_toan, diem_van, diem_ly, diem_ngoai_ngu,
                    ma_mon_ngoai_ngu, diem_xet_tot_nghiep, diem_thpt,
                    diem_dgnl_dgtd, diem_ccqt_thpt, diem_sat_act,
                    diem_pt_khac, diem_max_xet_tuyen, id
                )
            )
            conn.commit()

            conn.execute(
                """
                UPDATE users
                SET display_name = ?
                WHERE thi_sinh_id = ?
                """,
                (ho_ten, id)
            )
            conn.commit()

            flash("Cập nhật thông tin thí sinh thành công.", "success")
        except sqlite3.IntegrityError:
            flash("CCCD, SBD hoặc mã hồ sơ đã tồn tại.", "error")

        candidate = conn.execute(
            "SELECT * FROM thi_sinh WHERE id = ?",
            (id,)
        ).fetchone()

    conn.close()
    return render_template("admin_candidate_detail.html", candidate=candidate)