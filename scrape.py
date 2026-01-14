import sys
import logging
import sqlite3
import pandas as pd
import os
import numpy as np
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from decimal import Decimal, ROUND_HALF_UP
DB_NAME = "Results.db"
EXTRACTION_DIR = "Extraction_Output"
CSV_PATH = os.path.join(EXTRACTION_DIR, "Results.csv")
PHOTOS_DIR = os.path.join(EXTRACTION_DIR, "Student_Photos")
MISSING_VALUE = "?"
NOT_APPLICABLE = "NA"
REGULAR_URLS = {
    "I-I": "https://results.jntugvcev.edu.in/result/d5f9ed8d8577b506a546b6ddf43af665",
    "I-II": "https://results.jntugvcev.edu.in/result/fecae0ec437b775315c45e4af9b46570",
    "II-I": "https://results.jntugvcev.edu.in/result/eed48fa126d67b7e8f537072b0d0c30a",
    "II-II": "https://results.jntugvcev.edu.in/result/71e72cadbbcbd74e83d0c530af649893",
    "III-I": "https://results.jntugvcev.edu.in/result/6d4f5b938cc671b9289a61d17662d119",
    "III-II": "https://results.jntugvcev.edu.in/result/28ae2211c98c5e641901ac037dd3258a",
    "IV-I": "https://results.jntugvcev.edu.in/result/6f930a3de7b99f9638d144f2f1176660",
    "IV-II": "https://results.jntugvcev.edu.in/result/a066c7e8341a659820f0db71dbdd8be8"
}
SUPPLY_URLS = {
    "I-I": [
        "https://results.jntugvcev.edu.in/result/07011c639802ecbad78068c5fd24d8a1",
        "https://results.jntugvcev.edu.in/result/c15d58614c5061c434bd5619b31fec50",
        "https://results.jntugvcev.edu.in/result/d52d8dae1e7e97ab59786073159d7c78",
        "https://results.jntugvcev.edu.in/result/36012c5d376d029f487bfd3aa00674f6",
        "https://results.jntugvcev.edu.in/result/a2896bda221afa58d6a910eb70737aaf",
        "https://results.jntugvcev.edu.in/result/e8243084caf5b4c85a9f5b68be211bb0",
        "https://results.jntugvcev.edu.in/result/6f98e8069769d5b1c30ec8d9a47eb975",
        "https://results.jntugvcev.edu.in/result/b1b2ee548b574690a886412957081a6f",
        "https://results.jntugvcev.edu.in/result/f85a223372b76820fac587dda716f1d4"
    ],
    "I-II": [
        "https://results.jntugvcev.edu.in/result/cd05b97f4951a7a64434d49848f818f4",
        "https://results.jntugvcev.edu.in/result/4e020e0294a22654a4663009789afa1a",
        "https://results.jntugvcev.edu.in/result/d9aacfb99f488a6f24693cec48871bf4",
        "https://results.jntugvcev.edu.in/result/d1f6d70d3dea8c24e8f3d26a15ee7b99",
        "https://results.jntugvcev.edu.in/result/3efce86ad1920f04f2dd62a3b633bd02",
        "https://results.jntugvcev.edu.in/result/e11e0101e9c97ea9abac1690d31e249e",
        "https://results.jntugvcev.edu.in/result/93af2d252da958b8bc44d2dc2d41610f",
        "https://results.jntugvcev.edu.in/result/08ebffb5bdf5491ee492c883a7c0872d"
    ],
    "II-I": [
        "https://results.jntugvcev.edu.in/result/f779d728b42165ab8f20dfd476bf3b15",
        "https://results.jntugvcev.edu.in/result/7f70226722cd1758e1333a873d13addd",
        "https://results.jntugvcev.edu.in/result/2adef90ab7a53d0f23f1691c37dabb82",
        "https://results.jntugvcev.edu.in/result/3d99c090c47f7da32a63a01fcdbb5baa",
        "https://results.jntugvcev.edu.in/result/858ce7cd227a8485f3fb6d6a953fbee1",
        "https://results.jntugvcev.edu.in/result/7fbce2326e84f23abfc0014b0c638bbc",
        "https://results.jntugvcev.edu.in/result/f11231e293b2592afc950e159168d0a8",
        "https://results.jntugvcev.edu.in/result/041896335674e6290cdbbae97590dcb4",
        "https://results.jntugvcev.edu.in/result/f0ffbce81c725f083461b762ee050dac"
    ],
    "II-II": [
        "https://results.jntugvcev.edu.in/result/758d13d49b5ac1bf25125a53d17c778f",
        "https://results.jntugvcev.edu.in/result/f039a3b04e94670a5a5e5053ad543b8e",
        "https://results.jntugvcev.edu.in/result/b2b3035924e8c28193fe0a2725e11a84",
        "https://results.jntugvcev.edu.in/result/6d6b5727685971fca0ce157d31d2218f",
        "https://results.jntugvcev.edu.in/result/49ec61e50ef641161e492f6ecc3bd906",
        "https://results.jntugvcev.edu.in/result/73e522a7418b51c447dbf4a4c6dd3cf5",
        "https://results.jntugvcev.edu.in/result/f7a6c5ac29f6070134dafcef0bf75f37",
        "https://results.jntugvcev.edu.in/result/c76a0106af7e983fd0768bdb88b0ad19",
        "https://results.jntugvcev.edu.in/result/52dcd66d7cbcb77cabea1db702f0179f",
        "https://results.jntugvcev.edu.in/result/95d0ab46abf33bc50a0f1cb8ec40bfab"
    ],
    "III-I": [
        "https://results.jntugvcev.edu.in/result/05874597e7120a513219e6f295a39a3c",
        "https://results.jntugvcev.edu.in/result/79985c1c07bd98e097f5a17c219daf2d",
        "https://results.jntugvcev.edu.in/result/4d15df68c9adf51be92cac62f704e485",
        "https://results.jntugvcev.edu.in/result/9cd2084e37e8d5ed06bf6d4ff69106d3",
        "https://results.jntugvcev.edu.in/result/9e2542663dbc387bf1b1174653254cf0",
        "https://results.jntugvcev.edu.in/result/4dcc83bc5239290fe0382b11094d5fc4",
        "https://results.jntugvcev.edu.in/result/3244b656c4a1457e846fae7f0c895044"
    ],
    "III-II": [
        "https://results.jntugvcev.edu.in/result/5e43b06b2fd27f8e28f23ffe3fd01738",
        "https://results.jntugvcev.edu.in/result/3d09f173f0977caba757a59816a8f3e6",
        "https://results.jntugvcev.edu.in/result/c21a5e2943844e85b461d98ba3bd0486",
        "https://results.jntugvcev.edu.in/result/879d37e434589b6be0a94e2f47e346c5",
        "https://results.jntugvcev.edu.in/result/154a136f3109055ea0b817ff928fdf32"
    ],
    "IV-I": [
        "https://results.jntugvcev.edu.in/result/a0b4ae18b29d6636b857d6405d8fde60",
        "https://results.jntugvcev.edu.in/result/e0c1ec84ce8ac1a805c5d60e1a189aaa",
        "https://results.jntugvcev.edu.in/result/6a986b4dd79596e33afe1cc2e4739666"
    ],
    "IV-II": []
}
MINORS_URLS = {
    "II-II": "https://results.jntugvcev.edu.in/result/da6dd1992aadfa62a3499abebe9489b9",
    "III-I": "https://results.jntugvcev.edu.in/result/c2e03f3f8cc864fcfe4f7528b0dcfc5d",
    "III-II": "https://results.jntugvcev.edu.in/result/bcfd6dec3b4e197e88ff4930096f146e",
    "IV-I": "https://results.jntugvcev.edu.in/result/6bd4545e545dbf1ca95391e44672547c"
}
HONORS_URLS = {
    "II-II": "https://results.jntugvcev.edu.in/result/ef81aedd2b7de7c66d5ff228e84ee708",
    "III-I": "https://results.jntugvcev.edu.in/result/c801c9489a1efebb75d59bb27270c5eb",
    "III-II": "https://results.jntugvcev.edu.in/result/e61666ff5a0ef035b76052c694a45b95",
    "IV-I": "https://results.jntugvcev.edu.in/result/4475f740c545bf16e718a47a710d9cbc",
    "IV-II": "https://results.jntugvcev.edu.in/result/50cbd03c732ac77a475c1b0f4b70e1b7"
}
SEMESTER_ORDER = [
    "I-I", "I-II", "II-I", "II-II", "III-I", "III-II", "IV-I", "IV-II"
]
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("Scrape")
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            hall_ticket TEXT PRIMARY KEY,
            full_name TEXT,
            branch TEXT,
            student_type TEXT,
            degree_type TEXT DEFAULT "REGULAR",
            status TEXT DEFAULT "ACTIVE",
            blood_group TEXT,
            dob TEXT,
            phone TEXT,
            address TEXT,
            photo BLOB
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS semester_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hall_ticket TEXT NOT NULL,
            semester TEXT NOT NULL,
            credits REAL,
            sgpa REAL,
            status TEXT,
            honors_sgpa REAL DEFAULT 0,
            minors_sgpa REAL DEFAULT 0,
            FOREIGN KEY (hall_ticket) REFERENCES students (hall_ticket) ON DELETE CASCADE,
            UNIQUE(hall_ticket, semester)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id INTEGER NOT NULL,
            subject_code TEXT,
            subject_name TEXT,
            credits REAL,
            grade_points INTEGER,
            grade TEXT,
            subject_type TEXT DEFAULT "REGULAR", 
            FOREIGN KEY (result_id) REFERENCES semester_results (id) ON DELETE CASCADE,
            UNIQUE(result_id, subject_code)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exam_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hall_ticket TEXT NOT NULL,
            semester TEXT,
            exam_type TEXT,
            subject_code TEXT,
            subject_name TEXT,
            grade TEXT,
            grade_points INTEGER,
            credits REAL,
            subject_type TEXT,
            FOREIGN KEY (hall_ticket) REFERENCES students(hall_ticket) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS overall_cgpa (
            hall_ticket TEXT PRIMARY KEY,
            regular_credits_registered REAL,
            regular_credits_secured REAL,
            regular_cgpa REAL,
            regular_percentage REAL,
            regular_degree_status TEXT DEFAULT "NOT AWARDED",
            degree_class TEXT DEFAULT "NOT APPLICABLE",
            honors_credits_registered REAL DEFAULT 0,
            honors_credits_secured REAL DEFAULT 0,
            honors_cgpa REAL DEFAULT 0,
            honors_degree_status TEXT DEFAULT "NOT AWARDED",
            minors_credits_registered REAL DEFAULT 0,
            minors_credits_secured REAL DEFAULT 0,
            minors_cgpa REAL DEFAULT 0,
            minors_degree_status TEXT DEFAULT "NOT AWARDED",
            FOREIGN KEY (hall_ticket) REFERENCES students (hall_ticket) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()
    logger.info(f"Database initialized: {DB_NAME}")
def parse_div_tables(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables_data = []
    div_tables = soup.find_all("div", class_="table")
    for div_table in div_tables:
        rows_data = []
        headers = []
        all_rows = div_table.find_all("div", class_="row")
        for row in all_rows:
            cells = [cell.get_text(strip=True) for cell in row.find_all("div", class_="cell")]
            if "header" in row.get("class", []):
                headers = cells
            else:
                rows_data.append(cells)
        if headers and rows_data:
            clean_rows = []
            for r in rows_data:
                if len(r) < len(headers):
                    r += [''] * (len(headers) - len(r))
                clean_rows.append(r[:len(headers)])
            df = pd.DataFrame(clean_rows, columns=headers)
            tables_data.append(df)
    return tables_data
def save_exam_history(hall_ticket, semester, exam_type, marks_df):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    history_data = []
    for _, mark in marks_df.iterrows():
        sType = mark.get('mapped_subject_type', 'REGULAR')
        history_data.append((hall_ticket, semester, exam_type, mark['Code'], mark['Subject'], mark['G'], mark['GP'], mark['C'], sType))
    cursor.executemany('INSERT INTO exam_history (hall_ticket, semester, exam_type, subject_code, subject_name, grade, grade_points, credits, subject_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', history_data)
    conn.commit()
    conn.close()
def recalculate_semester_sgpa(hall_ticket, semester):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM semester_results WHERE hall_ticket=? AND semester=?', (hall_ticket, semester))
    res = cursor.fetchone()
    if not res: 
        conn.close()
        return
    result_id = res['id']
    cursor.execute('SELECT credits, grade_points, subject_type FROM marks WHERE result_id=?', (result_id,))
    marks = cursor.fetchall()
    reg_credits, reg_points, reg_failed = 0.0, 0.0, 0
    hon_credits, hon_points = 0.0, 0.0
    min_credits, min_points = 0.0, 0.0
    for m in marks:
        try:
            c = float(m['credits'])
            gp = int(m['grade_points'])
            sType = m['subject_type']
            if sType == "REGULAR":
                if gp == 0: reg_failed += 1
                if c > 0:
                    reg_points += (c * gp)
                    reg_credits += c
            elif sType == "HONORS":
                if c > 0:
                    hon_points += (c * gp)
                    hon_credits += c
            elif sType == "MINORS":
                if c > 0:
                    min_points += (c * gp)
                    min_credits += c
        except: continue
    new_sgpa = 0.0
    status = "PASSED"
    if reg_credits > 0:
        raw_sgpa = reg_points / reg_credits
        new_sgpa = float(Decimal(str(raw_sgpa)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    if reg_failed > 0 or (reg_credits > 0 and new_sgpa == 0):
        status = "FAILED"
    h_sgpa = 0.0
    if hon_credits > 0:
        raw_h = hon_points / hon_credits
        h_sgpa = float(Decimal(str(raw_h)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    m_sgpa = 0.0
    if min_credits > 0:
        raw_m = min_points / min_credits
        m_sgpa = float(Decimal(str(raw_m)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    cursor.execute('''
        UPDATE semester_results 
        SET sgpa=?, status=?, credits=?, honors_sgpa=?, minors_sgpa=? 
        WHERE id=?
    ''', (new_sgpa, status, reg_credits, h_sgpa, m_sgpa, result_id))
    conn.commit()
    conn.close()
    if status == "PASSED":
        logger.info(f"Cleared Semester: {hall_ticket} [{semester}] Regular SGPA: {new_sgpa} | Honors: {h_sgpa} | Minors: {m_sgpa}")
def save_to_database(student_df, marks_df, semester, student_type, is_supply=False, append_marks=False, subject_type="REGULAR"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        row = student_df.iloc[0]
        ht = row['HallTicket']
        if is_supply:
            cursor.execute('''
                SELECT m.subject_code, m.subject_type 
                FROM marks m 
                JOIN semester_results sr ON m.result_id = sr.id 
                WHERE sr.hall_ticket = ? AND sr.semester = ?
            ''', (ht, semester))
            existing_map = dict(cursor.fetchall())
            marks_df['mapped_subject_type'] = marks_df['Code'].map(existing_map).fillna(subject_type)
        else:
            marks_df['mapped_subject_type'] = subject_type
        save_exam_history(ht, semester, "SUPPLY" if is_supply else "REGULAR", marks_df)
        if not is_supply and not append_marks:
            cursor.execute('INSERT OR IGNORE INTO students (hall_ticket, full_name, branch, student_type, status) VALUES (?, ?, ?, ?, "ACTIVE")', (ht, row['Full Name'], row['Branch'], student_type))
            cursor.execute('UPDATE students SET status="ACTIVE", full_name=?, branch=? WHERE hall_ticket=?', (row['Full Name'], row['Branch'], ht))
            sgpa = row['SGPA']
            if 'FAIL' in str(row['Status']).upper(): sgpa = 0.0
            cursor.execute('''
                INSERT INTO semester_results (hall_ticket, semester, credits, sgpa, status) 
                VALUES (?, ?, ?, ?, ?) 
                ON CONFLICT(hall_ticket, semester) DO UPDATE SET status=excluded.status
            ''', (ht, semester, row['Credits'], sgpa, row['Status']))
        cursor.execute('SELECT id FROM semester_results WHERE hall_ticket=? AND semester=?', (ht, semester))
        res = cursor.fetchone()
        if not res: return
        result_id = res[0]
        if not is_supply and not append_marks:
            cursor.execute("DELETE FROM marks WHERE result_id = ? AND subject_type = ?", (result_id, subject_type))
            marks_data = []
            for _, mark in marks_df.iterrows():
                marks_data.append((result_id, mark['Code'], mark['Subject'], mark['C'], mark['GP'], mark['G'], mark['mapped_subject_type']))
            cursor.executemany('INSERT INTO marks (result_id, subject_code, subject_name, credits, grade_points, grade, subject_type) VALUES (?, ?, ?, ?, ?, ?, ?)', marks_data)
        else:
            for _, mark in marks_df.iterrows():
                sub_code = mark['Code']
                new_gp = int(mark['GP'])
                new_grade = mark['G']
                resolved_type = mark['mapped_subject_type']
                cursor.execute('SELECT grade_points FROM marks WHERE result_id=? AND subject_code=?', (result_id, sub_code))
                existing = cursor.fetchone()
                should_update = False
                if not existing:
                    should_update = True
                else:
                    current_gp = existing[0]
                    if new_gp > current_gp:
                        should_update = True
                if should_update:
                    cursor.execute('''
                        INSERT INTO marks (result_id, subject_code, subject_name, credits, grade_points, grade, subject_type) 
                        VALUES (?, ?, ?, ?, ?, ?, ?) 
                        ON CONFLICT(result_id, subject_code) DO UPDATE SET grade=excluded.grade, grade_points=excluded.grade_points, credits = CASE WHEN excluded.credits > 0 THEN excluded.credits ELSE marks.credits END
                    ''', (result_id, mark['Code'], mark['Subject'], mark['C'], new_gp, new_grade, resolved_type))
        conn.commit()
    except Exception as e:
        logger.error(f"DB Error ({ht} - {semester}): {e}")
        conn.rollback()
    finally:
        conn.close()
    recalculate_semester_sgpa(ht, semester)
def update_degree_type(hall_ticket, degree_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET degree_type = ? WHERE hall_ticket = ?", (degree_type, hall_ticket))
    conn.commit()
    conn.close()
    logger.info(f"Identified {degree_type}: {hall_ticket}")
def fetch_result(page, url, roll):
    try:
        page.goto(url, wait_until="domcontentloaded")
        page.evaluate(f"document.querySelector('input.hallticket').value = '{roll}';")
        with page.expect_response(lambda response: "helper.php" in response.url) as response_info:
            page.evaluate("document.querySelector('.getResultButton').click()")
        response = response_info.value
        if response.status != 200: return None
        raw_html = response.text()
        if "HallTicket" not in raw_html: return None
        return parse_div_tables(raw_html)
    except: return None
def process_semesters_and_tracks(all_rolls):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        for sem in SEMESTER_ORDER:
            logger.info(f"--- Processing {sem} Regular ---")
            current_target_rolls = all_rolls
            if sem in ["I-I", "I-II"]: 
                current_target_rolls = [r for r in all_rolls if r[1] == "REGULAR"]
            regular_url = REGULAR_URLS[sem]
            for roll, s_type in current_target_rolls:
                dfs = fetch_result(page, regular_url, roll)
                if dfs and len(dfs) >= 2:
                    save_to_database(dfs[0], dfs[1], sem, s_type, is_supply=False, subject_type="REGULAR")
            if sem in SUPPLY_URLS:
                supply_links = SUPPLY_URLS[sem]
                if supply_links:
                    logger.info(f"--- Processing {sem} Supplementary ({len(supply_links)} exams) ---")
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DISTINCT sr.hall_ticket 
                        FROM semester_results sr 
                        JOIN marks m ON sr.id = m.result_id 
                        WHERE sr.semester = ? AND m.grade_points = 0
                    """, (sem,))
                    backlog_students = [r[0] for r in cursor.fetchall()]
                    conn.close()
                    if backlog_students:
                        logger.info(f"Students with ANY backlogs (Reg/Hon/Min) in {sem}: {len(backlog_students)}")
                        for link_idx, url in enumerate(supply_links):
                            if not backlog_students: break
                            logger.info(f"Checking Supply Link {link_idx+1}/{len(supply_links)}...")
                            still_failing = []
                            for roll in backlog_students:
                                dfs = fetch_result(page, url, roll)
                                if dfs and len(dfs) >= 2:
                                    save_to_database(dfs[0], dfs[1], sem, "NA", is_supply=True, subject_type="REGULAR")
                                    conn = sqlite3.connect(DB_NAME)
                                    cur = conn.cursor()
                                    cur.execute("""
                                        SELECT count(*) FROM marks m 
                                        JOIN semester_results sr ON m.result_id = sr.id 
                                        WHERE sr.hall_ticket=? AND sr.semester=? AND m.grade_points=0
                                    """, (roll, sem))
                                    fails_count = cur.fetchone()[0]
                                    conn.close()
                                    if fails_count > 0:
                                        still_failing.append(roll)
                                else:
                                    still_failing.append(roll)
                            backlog_students = still_failing
            if sem == "II-II":
                logger.info("--- Identifying Minors/Honors Status (II-II) ---")
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("SELECT hall_ticket FROM students WHERE status='ACTIVE'")
                active_rolls = [r[0] for r in cursor.fetchall()]
                conn.close()
                for roll in active_rolls:
                    is_minors = False
                    if MINORS_URLS.get(sem):
                        dfs = fetch_result(page, MINORS_URLS[sem], roll)
                        if dfs and len(dfs) >= 2:
                            update_degree_type(roll, "MINORS")
                            save_to_database(dfs[0], dfs[1], sem, "NA", append_marks=True, subject_type="MINORS")
                            is_minors = True
                    if not is_minors and HONORS_URLS.get(sem):
                        dfs = fetch_result(page, HONORS_URLS[sem], roll)
                        if dfs and len(dfs) >= 2:
                            update_degree_type(roll, "HONORS")
                            save_to_database(dfs[0], dfs[1], sem, "NA", append_marks=True, subject_type="HONORS")
            elif sem in MINORS_URLS or sem in HONORS_URLS:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("SELECT hall_ticket FROM students WHERE degree_type='MINORS' AND status='ACTIVE'")
                minors_students = [r[0] for r in cursor.fetchall()]
                cursor.execute("SELECT hall_ticket FROM students WHERE degree_type='HONORS' AND status='ACTIVE'")
                honors_students = [r[0] for r in cursor.fetchall()]
                conn.close()
                if sem in MINORS_URLS:
                    logger.info(f"--- Processing {sem} Minors ({len(minors_students)} students) ---")
                    for roll in minors_students:
                        dfs = fetch_result(page, MINORS_URLS[sem], roll)
                        if dfs and len(dfs) >= 2: 
                            save_to_database(dfs[0], dfs[1], sem, "NA", append_marks=True, subject_type="MINORS")
                if sem in HONORS_URLS:
                    logger.info(f"--- Processing {sem} Honors ({len(honors_students)} students) ---")
                    for roll in honors_students:
                        dfs = fetch_result(page, HONORS_URLS[sem], roll)
                        if dfs and len(dfs) >= 2: 
                            save_to_database(dfs[0], dfs[1], sem, "NA", append_marks=True, subject_type="HONORS")
        browser.close()
def check_detained_students(roll_numbers):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for roll, s_type in roll_numbers:
        cursor.execute("SELECT count(*) FROM semester_results WHERE hall_ticket = ?", (roll,))
        count = cursor.fetchone()[0]
        if count == 0:
            logger.warning(f"No results found for {roll}. Marking as DETAINED.")
            cursor.execute("INSERT OR IGNORE INTO students (hall_ticket, full_name, branch, student_type, status) VALUES (?, ?, ?, ?, 'DETAINED')", (roll, NOT_APPLICABLE, NOT_APPLICABLE, s_type))
            cursor.execute("UPDATE students SET status='DETAINED', full_name=?, branch=?, student_type=? WHERE hall_ticket=?", (NOT_APPLICABLE, NOT_APPLICABLE, NOT_APPLICABLE, roll))
    conn.commit()
    conn.close()
def fill_lateral_gaps():
    logger.info("Filling missing semesters for Lateral Entry students...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT hall_ticket FROM students WHERE hall_ticket LIKE '22VV5A%' OR student_type='LATERAL'")
    lateral_students = [r[0] for r in cursor.fetchall()]
    for roll in lateral_students:
        for sem in ["I-I", "I-II"]:
            cursor.execute("INSERT OR IGNORE INTO semester_results (hall_ticket, semester, credits, sgpa, status) VALUES (?, ?, 0, ?, ?)", (roll, sem, NOT_APPLICABLE, NOT_APPLICABLE))
    conn.commit()
    conn.close()
def calculate_overall_cgpa():
    logger.info("Starting Overall CGPA Calculation (R20 Compliant)...")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT hall_ticket, student_type FROM students WHERE status='ACTIVE'")
    students = cursor.fetchall()
    for student in students:
        hall_ticket = student['hall_ticket']
        s_type = student['student_type']
        cursor.execute("""
            SELECT m.credits, m.grade_points, m.subject_type 
            FROM marks m 
            JOIN semester_results sr ON m.result_id = sr.id 
            WHERE sr.hall_ticket = ?
        """, (hall_ticket,))
        marks = cursor.fetchall()
        if not marks: continue
        reg_credits_registered, reg_credits_secured, reg_weighted_points = 0.0, 0.0, 0.0
        hon_credits_registered, hon_credits_secured, hon_weighted_points = 0.0, 0.0, 0.0
        min_credits_registered, min_credits_secured, min_weighted_points = 0.0, 0.0, 0.0
        for m in marks:
            try:
                c = float(m['credits'])
                gp = int(m['grade_points'])
                sType = m['subject_type']
                is_passed = (gp > 0)
                if c > 0:
                    if sType == "REGULAR":
                        reg_credits_registered += c
                        reg_weighted_points += (c * gp)
                        if is_passed: reg_credits_secured += c
                    elif sType == "HONORS":
                        hon_credits_registered += c
                        hon_weighted_points += (c * gp)
                        if is_passed: hon_credits_secured += c
                    elif sType == "MINORS":
                        min_credits_registered += c
                        min_weighted_points += (c * gp)
                        if is_passed: min_credits_secured += c
            except: continue
        final_cgpa = 0.0
        percentage_jntu = 0.0
        reg_status = "NOT AWARDED"
        if reg_credits_registered > 0:
            raw_cgpa = reg_weighted_points / reg_credits_registered
            final_cgpa = float(Decimal(str(raw_cgpa)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            percentage_jntu = (final_cgpa - 0.75) * 10
            percentage_jntu = float(Decimal(str(percentage_jntu)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            threshold = 121 if s_type == "LATERAL" else 160
            if reg_credits_secured >= threshold:
                reg_status = "AWARDED"
        degree_class = "NOT APPLICABLE"
        if reg_status == "AWARDED":
            cursor.execute("""
                SELECT COUNT(*) FROM exam_history 
                WHERE hall_ticket = ? AND exam_type = 'SUPPLY'
            """, (hall_ticket,))
            supply_count = cursor.fetchone()[0]
            if final_cgpa >= 7.75 and supply_count == 0:
                degree_class = "FIRST CLASS WITH DISTINCTION"
            elif final_cgpa >= 6.75:
                degree_class = "FIRST CLASS"
            elif final_cgpa >= 5.75:
                degree_class = "SECOND CLASS"
            elif final_cgpa >= 5.00:
                degree_class = "PASS CLASS"
        hon_cgpa = 0.0
        hon_status = "NOT AWARDED"
        if hon_credits_registered > 0:
            raw_h = hon_weighted_points / hon_credits_registered
            hon_cgpa = float(Decimal(str(raw_h)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            if hon_credits_secured >= 20: 
                hon_status = "AWARDED"
        min_cgpa = 0.0
        min_status = "NOT AWARDED"
        if min_credits_registered > 0:
            raw_m = min_weighted_points / min_credits_registered
            min_cgpa = float(Decimal(str(raw_m)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            if min_credits_secured >= 20:
                min_status = "AWARDED"
        cursor.execute('''
            INSERT INTO overall_cgpa (
                hall_ticket, 
                regular_credits_registered, regular_credits_secured, regular_cgpa, regular_percentage, regular_degree_status, degree_class,
                honors_credits_registered, honors_credits_secured, honors_cgpa, honors_degree_status,
                minors_credits_registered, minors_credits_secured, minors_cgpa, minors_degree_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
            ON CONFLICT(hall_ticket) DO UPDATE SET 
                regular_credits_registered=excluded.regular_credits_registered,
                regular_credits_secured=excluded.regular_credits_secured,
                regular_cgpa=excluded.regular_cgpa, 
                regular_percentage=excluded.regular_percentage,
                regular_degree_status=excluded.regular_degree_status,
                degree_class=excluded.degree_class,
                honors_credits_registered=excluded.honors_credits_registered,
                honors_credits_secured=excluded.honors_credits_secured,
                honors_cgpa=excluded.honors_cgpa,
                honors_degree_status=excluded.honors_degree_status,
                minors_credits_registered=excluded.minors_credits_registered,
                minors_credits_secured=excluded.minors_credits_secured,
                minors_cgpa=excluded.minors_cgpa,
                minors_degree_status=excluded.minors_degree_status
        ''', (hall_ticket, 
              reg_credits_registered, reg_credits_secured, final_cgpa, percentage_jntu, reg_status, degree_class,
              hon_credits_registered, hon_credits_secured, hon_cgpa, hon_status, 
              min_credits_registered, min_credits_secured, min_cgpa, min_status))
    conn.commit()
    conn.close()
    logger.info("Overall CGPA Calculation Complete.")
def normalize_database():
    logger.info("Normalizing database symbols (?, NA)...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fields = ['full_name', 'branch', 'blood_group', 'dob', 'phone', 'address']
    for field in fields:
        try:
            cursor.execute(f"UPDATE students SET {field} = ? WHERE {field} IS NULL OR {field} = '' OR {field} = '-'", (MISSING_VALUE,))
        except sqlite3.OperationalError: pass
    for field in fields:
        try:
            cursor.execute(f"UPDATE students SET {field} = ? WHERE status = 'DETAINED' AND hall_ticket IS NOT NULL", (NOT_APPLICABLE,))
        except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()
def merge_extraction_data():
    logger.info("--- Merging Extraction Data (CSV & Images) into DB ---")
    if not os.path.exists(CSV_PATH):
        logger.error(f"CSV file not found at: {CSV_PATH}")
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    logger.info(f"Reading CSV from {CSV_PATH}...")
    try:
        csv_df = pd.read_csv(CSV_PATH)
        csv_df = csv_df.replace({np.nan: MISSING_VALUE, '-': MISSING_VALUE, '': MISSING_VALUE})
        updates_count = 0
        for _, row in csv_df.iterrows():
            roll_no = row['Roll No']
            cursor.execute("SELECT status FROM students WHERE hall_ticket=?", (roll_no,))
            res = cursor.fetchone()
            if not res: continue
            status = res[0]
            if status == 'DETAINED': continue
            bg = row['Blood Group']
            dob = row['DOB']
            phone = row['Phone']
            addr = row['Address']
            cursor.execute("""
                UPDATE students 
                SET blood_group=?, dob=?, phone=?, address=? 
                WHERE hall_ticket=?
            """, (bg, dob, phone, addr, roll_no))
            updates_count += 1
        logger.info(f"Merged personal details for {updates_count} students.")
    except Exception as e:
        logger.error(f"Error merging CSV data: {e}")
    if os.path.exists(PHOTOS_DIR):
        logger.info(f"Processing images from {PHOTOS_DIR}...")
        images_count = 0
        for filename in os.listdir(PHOTOS_DIR):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                roll_no = os.path.splitext(filename)[0]
                file_path = os.path.join(PHOTOS_DIR, filename)
                cursor.execute("SELECT 1 FROM students WHERE hall_ticket=?", (roll_no,))
                if not cursor.fetchone(): continue
                try:
                    with open(file_path, 'rb') as f:
                        blob_data = f.read()
                    cursor.execute("UPDATE students SET photo=? WHERE hall_ticket=?", (blob_data, roll_no))
                    images_count += 1
                except Exception as e:
                    logger.error(f"Failed to process image for {roll_no}: {e}")
        logger.info(f"Imported {images_count} student photos.")
    else:
        logger.warning(f"Photos directory not found at: {PHOTOS_DIR}")
    conn.commit()
    conn.close()
    logger.info("Extraction data merge completed.")
if __name__ == "__main__":
    init_db()
    regular_rolls = [(f"21VV1A12{i:02d}","REGULAR") for i in range(1, 66)]
    lateral_rolls = [(f"22VV5A12{i:02d}","LATERAL") for i in range(66, 76)]
    all_rolls = regular_rolls + lateral_rolls
    process_semesters_and_tracks(all_rolls)
    check_detained_students(all_rolls)
    fill_lateral_gaps()
    calculate_overall_cgpa()
    merge_extraction_data()
    normalize_database()
