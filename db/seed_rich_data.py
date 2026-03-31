import os
import random
import sqlite3
from datetime import date, timedelta


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE = os.path.join(BASE_DIR, "db", "database.db")


FIRST_NAMES = [
    "An", "Binh", "Chi", "Dung", "Giang", "Hanh", "Hoa", "Huy", "Khanh", "Lam",
    "Linh", "Long", "Minh", "Nam", "Ngoc", "Phuong", "Quan", "Son", "Thao", "Trang",
    "Tuan", "Van", "Viet", "Yen",
]

LAST_NAMES = [
    "Nguyen", "Tran", "Le", "Pham", "Hoang", "Phan", "Vu", "Dang", "Bui", "Do",
]

PROVINCES = [
    "Ha Noi", "Hai Phong", "Da Nang", "Hue", "Quang Ninh", "Nghe An",
    "Thanh Hoa", "Nam Dinh", "Thai Binh", "Can Tho", "An Giang", "Dong Nai",
]

MAJOR_SEEDS = [
    ("KTPM", "Ky thuat phan mem", "Dao tao lap trinh va he thong"),
    ("HTTT", "He thong thong tin", "Phan tich va thiet ke he thong"),
    ("CNTT", "Cong nghe thong tin", "Nen tang cong nghe tong hop"),
    ("KHMT", "Khoa hoc may tinh", "Thuat toan va AI"),
    ("ATTT", "An toan thong tin", "Bao mat he thong va du lieu"),
    ("TTNT", "Tri tue nhan tao", "Hoc may va AI ung dung"),
    ("DTVT", "Dien tu vien thong", "Mang truyen dan va nhung"),
    ("QTKD", "Quan tri kinh doanh", "Quan tri doanh nghiep"),
    ("MARK", "Marketing", "Truyen thong va marketing so"),
    ("TCNH", "Tai chinh ngan hang", "Tai chinh doanh nghiep"),
]


def ensure_major_schema(conn):
    cols = [row[1] for row in conn.execute("PRAGMA table_info(nganh_hoc)").fetchall()]
    if "chi_tieu" not in cols:
        conn.execute("ALTER TABLE nganh_hoc ADD COLUMN chi_tieu INTEGER DEFAULT 1")
        conn.execute("UPDATE nganh_hoc SET chi_tieu = 1 WHERE chi_tieu IS NULL OR chi_tieu <= 0")
        conn.commit()


def random_birth():
    start = date(2005, 1, 1)
    end = date(2008, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def next_numeric_seed(values, default_seed):
    max_value = default_seed
    for value in values:
        digits = "".join(ch for ch in str(value or "") if ch.isdigit())
        if digits:
            max_value = max(max_value, int(digits))
    return max_value + 1


def normalize_sbd(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    return f"SBD{int(digits):06d}"


def main():
    random.seed(20260331)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    ensure_major_schema(conn)

    existing_codes = {
        row["ma_nganh"] for row in cur.execute("SELECT ma_nganh FROM nganh_hoc").fetchall()
    }
    for ma_nganh, ten_nganh, mo_ta in MAJOR_SEEDS:
        if ma_nganh in existing_codes:
            continue
        cur.execute(
            """
            INSERT INTO nganh_hoc (ma_nganh, ten_nganh, mo_ta, chi_tieu)
            VALUES (?, ?, ?, ?)
            """,
            (ma_nganh, ten_nganh, mo_ta, random.randint(25, 80)),
        )

    cur.execute(
        "UPDATE nganh_hoc SET chi_tieu = ? WHERE chi_tieu IS NULL OR chi_tieu <= 0",
        (random.randint(20, 60),),
    )
    conn.commit()

    majors = cur.execute(
        "SELECT id, ma_nganh FROM nganh_hoc ORDER BY id ASC"
    ).fetchall()
    if not majors:
        raise RuntimeError("Khong co nganh hoc de tao du lieu nguyen vong.")

    existing_candidates = cur.execute(
        "SELECT cccd, sbd, ma_ho_so FROM thi_sinh"
    ).fetchall()
    cccd_seed = next_numeric_seed([r["cccd"] for r in existing_candidates], 100000000000)
    sbd_seed = next_numeric_seed([r["sbd"] for r in existing_candidates], 100000)
    hs_seed = next_numeric_seed([r["ma_ho_so"] for r in existing_candidates], 200000)

    new_candidates = 180
    for i in range(new_candidates):
        last = random.choice(LAST_NAMES)
        first = random.choice(FIRST_NAMES)
        ho_ten = f"{last} {first} {random.choice(FIRST_NAMES)}"
        province = random.choice(PROVINCES)
        diem_thpt = round(random.uniform(16.0, 29.0), 2)
        diem_dgnl = round(random.uniform(450.0, 980.0), 1)
        diem_ccqt = round(random.uniform(12.0, 29.0), 2)
        diem_sat = random.randint(900, 1580)
        diem_khac = round(random.uniform(10.0, 28.0), 2)
        diem_max = round(max(diem_thpt, diem_ccqt, diem_khac), 2)

        cccd = str(cccd_seed + i)
        sbd = normalize_sbd(sbd_seed + i)
        ma_ho_so = f"HS{hs_seed + i}"

        cur.execute(
            """
            INSERT INTO thi_sinh (
                cccd, sbd, ma_ho_so, ho_ten, ngay_sinh, gioi_tinh, dan_toc, noi_sinh,
                doi_tuong_uu_tien, khu_vuc_uu_tien, diem_cong_xet_tuyen, tinh_tp, quan_huyen,
                nam_tot_nghiep, hoc_luc, hanh_kiem, diem_tb_lop_12, ma_tinh_lop_12, ma_truong_lop_12,
                diem_toan, diem_van, diem_ly, diem_ngoai_ngu, ma_mon_ngoai_ngu, diem_xet_tot_nghiep,
                diem_thpt, diem_dgnl_dgtd, diem_ccqt_thpt, diem_sat_act, diem_pt_khac, diem_max_xet_tuyen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cccd, sbd, ma_ho_so, ho_ten, random_birth(), random.choice(["Nam", "Nu"]),
                "Kinh", province, "", random.choice(["KV1", "KV2", "KV2-NT", "KV3"]),
                round(random.uniform(0.0, 1.5), 2), province, "Quan/Huyen",
                2026, random.choice(["Gioi", "Kha", "Trung binh"]),
                random.choice(["Tot", "Kha"]), round(random.uniform(6.5, 9.8), 2),
                "01", "THPT01", round(random.uniform(4.0, 10.0), 2),
                round(random.uniform(4.0, 10.0), 2), round(random.uniform(4.0, 10.0), 2),
                round(random.uniform(4.0, 10.0), 2), "EN", round(random.uniform(5.0, 10.0), 2),
                diem_thpt, diem_dgnl, diem_ccqt, diem_sat, diem_khac, diem_max
            ),
        )
        thi_sinh_id = cur.lastrowid

        pref_count = random.randint(3, min(7, len(majors)))
        selected_majors = random.sample(majors, pref_count)
        for order, major in enumerate(selected_majors, start=1):
            cur.execute(
                """
                INSERT INTO nguyen_vong (thi_sinh_id, nganh_id, thu_tu)
                VALUES (?, ?, ?)
                """,
                (thi_sinh_id, major["id"], order),
            )

    conn.commit()

    major_count = cur.execute("SELECT COUNT(*) FROM nganh_hoc").fetchone()[0]
    candidate_count = cur.execute("SELECT COUNT(*) FROM thi_sinh").fetchone()[0]
    pref_count = cur.execute("SELECT COUNT(*) FROM nguyen_vong").fetchone()[0]

    print(f"Da bo sung du lieu thanh cong.")
    print(f"Tong nganh hoc: {major_count}")
    print(f"Tong thi sinh: {candidate_count}")
    print(f"Tong nguyen vong: {pref_count}")

    conn.close()


if __name__ == "__main__":
    main()
