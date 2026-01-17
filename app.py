import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from PIL import Image
from decimal import Decimal, ROUND_HALF_UP
st.set_page_config(page_title="JNTU Dashboard", page_icon="🎓", layout="wide", initial_sidebar_state="collapsed")
chart_config = {'displayModeBar': False, 'staticPlot': False, 'scrollZoom': False, 'showAxisDragHandles': False, 'dragmode': False}
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 100% !important;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    h1, h2, h3 {font-family: 'Inter', sans-serif; margin-top: 1.5rem !important; margin-bottom: 0.5rem !important;}
    div[data-testid="stRadio"] {background-color: #f3f4f6; padding: 10px 15px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 20px;}
    div[data-testid="stRadio"] > div[role="radiogroup"] {gap: 15px; align-items: center; flex-wrap: wrap;}
    div[data-testid="stRadio"] label p {font-size: 1.0rem !important; font-weight: 600 !important; color: #374151 !important; margin: 0px;}
    div[data-testid="stRadio"] label:hover p {color: #000000 !important;}
    .metric-container {display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 10px;}
    .metric-card {background-color: #ffffff; border: 1px solid #e0e0e0; border-left: 5px solid #4B5563; padding: 15px; border-radius: 8px; color: #1F2937 !important; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;}
    .metric-card h3 {margin: 0; font-size: 1.8em; font-weight: 700; color: #111827 !important;}
    .metric-card p {margin: 5px 0 0 0; font-size: 0.9em; color: #6B7280 !important; font-weight: 600; text-transform: uppercase;}
    .info-box {background: #f9fafb; padding: 10px; border-radius: 8px; border: 1px solid #e5e7eb; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; margin-bottom: 5px;}
    .info-label {font-size: 0.75em; color: #6b7280 !important; text-transform: uppercase; font-weight: 700;}
    .info-value {font-size: 1.0em; color: #111827 !important; font-weight: 700; word-wrap: break-word;}
    .mobile-only {display: none !important;}
    .student-card {border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px; margin-bottom: 8px; background-color: white; box-shadow: 0 1px 2px rgba(0,0,0,0.05);}
    .card-row {display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;}
    .card-title {margin: 0; font-size: 0.95rem; font-weight: 700; color: #111827 !important;}
    .card-sub {margin: 0; font-size: 0.8rem; color: #6B7280 !important;}
    .card-stat {font-weight: 800; color: #4F46E5 !important; font-size: 1rem;}
    .card-tag {padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase;}
    .mobile-scroll-box {max-height: 400px; overflow-y: auto; padding: 4px; border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; margin-bottom: 20px;}
    .black-text-force {color: #000000 !important;}
    .stat-text-val {font-size: 1.8em; font-weight: 700; line-height: 1.2;}
    .stat-text-lbl {font-size: 0.9em; font-weight: 600; text-transform: uppercase; margin-top: 0px; opacity: 0.8;}
    @media only screen and (max-width: 768px) {
        .metric-container {grid-template-columns: repeat(2, 1fr);}
        .block-container {padding-left: 0.5rem !important; padding-right: 0.5rem !important;}
        .mobile-only {display: block !important;}
        div[data-testid="stDataFrame"] {display: none !important;}
        div[data-testid="stTable"] {display: none !important;}
        button[title="View fullscreen"] {display: none !important;}
        div[data-testid="stPlotlyChart"] {pointer-events: none;}
        .header-text-left, .header-text-right {text-align: center !important;}
    }
    .header-text-left {font-size: 1.8rem; font-weight: 800; margin: 0; padding: 0; text-align: right; transform: translateY(-6px);}
    .header-text-right {font-size: 1.8rem; font-weight: 800; margin: 0; padding: 0; text-align: left; transform: translateY(-6px);}
</style>
""", unsafe_allow_html=True)
def fmt_dec(value):
    try:
        if value is None or pd.isna(value): return "0.00"
        return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except:
        return "0.00"
def fmt_str_dec(value):
    try:
        if value is None or pd.isna(value) or float(value) == 0: return "-"
        return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    except:
        return "-"
def get_short_degree_class(long_class):
    if not long_class or pd.isna(long_class): return "NA"
    uc_class = str(long_class).upper()
    if "DISTINCTION" in uc_class: return "DISTINCTION"
    elif "FIRST" in uc_class: return "FIRST CLASS"
    elif "SECOND" in uc_class: return "SECOND CLASS"
    elif "PASS" in uc_class: return "PASS CLASS"
    else: return uc_class.title()
def clean_status(status):
    if not status: return "-"
    s = str(status).upper()
    if "PASS" in s or "COMPLETED" in s or "PROMOTED" in s: return "Pass"
    if "FAIL" in s: return "Fail"
    return status.title()
def fix_chart_layout(fig, height=400):
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=30, b=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), dragmode=False)
    return fig
def fix_subject_chart_layout(fig, height=400):
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=30, b=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), xaxis=dict(range=[0, 12]), dragmode=False)
    return fig
def is_pure_subject(subject_name):
    if not subject_name: return False
    u_name = subject_name.upper()
    exclude_terms = ['LAB', 'LABORATORY', 'PROJECT', 'INTERNSHIP', 'SEMINAR', 'WORKSHOP', 'MINI', 'TERM PAPER', 'COMPREHENSIVE']
    return not any(term in u_name for term in exclude_terms)
@st.cache_resource
def get_database_connection():
    try:
        return sqlite3.connect('file:Results.db?mode=ro', uri=True, check_same_thread=False)
    except sqlite3.OperationalError:
        conn = sqlite3.connect('Results.db', check_same_thread=False)
        return conn
@st.cache_data(ttl=600)
def load_all_students():
    conn = get_database_connection()
    return pd.read_sql_query("SELECT * FROM students WHERE status = 'ACTIVE'", conn)
@st.cache_data(ttl=600)
def load_all_cgpa_data():
    conn = get_database_connection()
    query = """SELECT s.hall_ticket, s.full_name, s.branch, s.student_type, s.degree_type, c.regular_cgpa, c.regular_percentage, c.regular_credits_secured, c.regular_credits_registered, c.degree_class, c.regular_degree_status, c.honors_cgpa, c.minors_cgpa, c.honors_degree_status, c.minors_degree_status FROM students s JOIN overall_cgpa c ON s.hall_ticket = c.hall_ticket WHERE s.status = 'ACTIVE' ORDER BY c.regular_cgpa DESC"""
    df = pd.read_sql_query(query, conn)
    for c in ['regular_cgpa', 'regular_percentage', 'regular_credits_secured', 'regular_credits_registered', 'honors_cgpa', 'minors_cgpa']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df
@st.cache_data(ttl=600)
def load_all_semester_results():
    conn = get_database_connection()
    query = """SELECT sr.*, s.full_name, s.branch, s.student_type FROM semester_results sr JOIN students s ON sr.hall_ticket = s.hall_ticket WHERE s.status = 'ACTIVE' ORDER BY sr.semester, sr.sgpa DESC"""
    df = pd.read_sql_query(query, conn)
    for c in ['sgpa', 'credits', 'honors_sgpa', 'minors_sgpa']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df
@st.cache_data(ttl=600)
def load_all_marks():
    conn = get_database_connection()
    query = """SELECT m.*, sr.hall_ticket, sr.semester, s.full_name FROM marks m JOIN semester_results sr ON m.result_id = sr.id JOIN students s ON sr.hall_ticket = s.hall_ticket WHERE s.status = 'ACTIVE'"""
    df = pd.read_sql_query(query, conn)
    df = df[df['grade'] != 'CMP']
    df['grade_points'] = pd.to_numeric(df['grade_points'], errors='coerce').fillna(0)
    return df
@st.cache_data(ttl=600)
def load_all_exam_history():
    conn = get_database_connection()
    query = """SELECT eh.*, s.student_type as cohort_type FROM exam_history eh JOIN students s ON eh.hall_ticket = s.hall_ticket WHERE s.status = 'ACTIVE'"""
    df = pd.read_sql_query(query, conn)
    df['grade_points'] = pd.to_numeric(df['grade_points'], errors='coerce').fillna(0)
    return df
@st.cache_data(ttl=600)
def load_student_data(hall_ticket):
    conn = get_database_connection()
    s_df = pd.read_sql_query("SELECT * FROM students WHERE hall_ticket = ?", conn, params=(hall_ticket,))
    if s_df.empty: return None
    c_df = pd.read_sql_query("SELECT * FROM overall_cgpa WHERE hall_ticket = ?", conn, params=(hall_ticket,))
    if not c_df.empty:
        for c in ['regular_cgpa', 'regular_percentage', 'regular_credits_secured', 'regular_credits_registered', 'honors_cgpa', 'minors_cgpa']:
            c_df[c] = pd.to_numeric(c_df[c], errors='coerce').fillna(0)
    sem_query = "SELECT * FROM semester_results WHERE hall_ticket = ? ORDER BY semester"
    sem_df = pd.read_sql_query(sem_query, conn, params=(hall_ticket,))
    for c in ['sgpa', 'credits', 'honors_sgpa', 'minors_sgpa']:
        sem_df[c] = pd.to_numeric(sem_df[c], errors='coerce').fillna(0)
    return {'student': s_df.iloc[0], 'cgpa': c_df.iloc[0] if not c_df.empty else None, 'semesters': sem_df}
@st.cache_data(ttl=600)
def load_student_marks(hall_ticket, semester):
    conn = get_database_connection()
    query = """SELECT m.subject_code, m.subject_name, m.credits, m.grade, m.grade_points, m.subject_type FROM marks m JOIN semester_results sr ON m.result_id = sr.id WHERE sr.hall_ticket = ? AND sr.semester = ? ORDER BY m.subject_type, m.subject_code"""
    df = pd.read_sql_query(query, conn, params=(hall_ticket, semester))
    df = df[df['grade'] != 'CMP']
    df['grade_points'] = pd.to_numeric(df['grade_points'], errors='coerce').fillna(0).astype(int)
    return df
@st.cache_data(ttl=600)
def load_student_history(hall_ticket):
    conn = get_database_connection()
    query = """SELECT semester, exam_type, subject_name, grade, grade_points, subject_type, subject_code FROM exam_history WHERE hall_ticket = ? ORDER BY id"""
    df = pd.read_sql_query(query, conn, params=(hall_ticket,))
    return df
def get_student_photo(hall_ticket):
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT photo FROM students WHERE hall_ticket = ?", (hall_ticket,))
    result = cursor.fetchone()
    if result and result[0]: return result[0]
    return None
def render_overview_subtab(students_df, cgpa_df, marks_df):
    st.subheader("Key Statistics")
    metrics_html = f"""
    <div class="metric-container">
        <div class='metric-card' style='border-left-color: #6366f1;'><h3>{len(students_df)}</h3><p>Total Students</p></div>
        <div class='metric-card' style='border-left-color: #ec4899;'><h3>{(cgpa_df['honors_cgpa'] > 0).sum()}</h3><p>Honors</p></div>
        <div class='metric-card' style='border-left-color: #10b981;'><h3>{(cgpa_df['minors_cgpa'] > 0).sum()}</h3><p>Minors</p></div>
        <div class='metric-card' style='border-left-color: #f59e0b;'><h3>{fmt_dec(cgpa_df['regular_cgpa'].max())}</h3><p>Highest CGPA</p></div>
        <div class='metric-card' style='border-left-color: #8b5cf6;'><h3>{fmt_dec(cgpa_df['regular_cgpa'].mean())}</h3><p>Average CGPA</p></div>
    </div>
    """
    st.markdown(metrics_html, unsafe_allow_html=True)
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Degree Class Distribution")
        d_counts = cgpa_df['degree_class'].value_counts()
        fig = px.pie(values=d_counts.values, names=d_counts.index, color_discrete_sequence=px.colors.sequential.RdBu, labels={'names': 'Class', 'values': 'Count'})
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=20, b=20), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch", config=chart_config)
    with c2:
        st.subheader("Overall Grade Distribution")
        reg_marks = marks_df[marks_df['subject_type']=='REGULAR']
        g_counts = reg_marks['grade'].value_counts().sort_index()
        fig = px.pie(values=g_counts.values, names=g_counts.index, color=g_counts.index, color_discrete_map={'O':'#2ecc71','A+':'#27ae60','A':'#3498db','B+':'#5dade2','B':'#f39c12','C':'#e67e22','D':'#e74c3c','F':'#c0392b','Ab':'#95a5a6'}, hole=0.4, labels={'names': 'Grade', 'values': 'Count'})
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=20, b=20), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, width="stretch", config=chart_config)
    st.markdown("---")
    st.subheader("CGPA Distribution")
    avg = cgpa_df['regular_cgpa'].mean()
    fig = px.histogram(cgpa_df, x='regular_cgpa', nbins=30, labels={'regular_cgpa': 'CGPA'}, color_discrete_sequence=['#667eea'])
    fig.add_vline(x=avg, line_dash="dash", line_color="red", annotation_text=f"Average: {fmt_dec(avg)}")
    fig.update_layout(xaxis_title="CGPA", yaxis_title="Number of Students")
    fig = fix_chart_layout(fig)
    st.plotly_chart(fig, width="stretch", config=chart_config)
def render_toppers_subtab(cgpa_df, semester_df):
    c1, c2, c3, c4 = st.columns([0.3, 0.7, 1.5, 4], vertical_alignment="center")
    with c1: st.markdown("<p class='header-text-left'>Top</p>", unsafe_allow_html=True)
    with c2: limit = st.number_input("Count", min_value=1, value=10, step=1, label_visibility="collapsed", key="topper_limit")
    with c3: st.markdown("<p class='header-text-right'>Students</p>", unsafe_allow_html=True)
    top_s = cgpa_df.nlargest(limit, 'regular_cgpa')[['hall_ticket','full_name','regular_cgpa','regular_percentage','regular_credits_secured','degree_class','honors_cgpa','minors_cgpa']].copy()
    top_s['regular_cgpa'] = top_s['regular_cgpa'].apply(fmt_dec)
    top_s['regular_percentage'] = top_s['regular_percentage'].apply(fmt_dec)
    top_s['honors_cgpa'] = top_s['honors_cgpa'].apply(fmt_str_dec)
    top_s['minors_cgpa'] = top_s['minors_cgpa'].apply(fmt_str_dec)
    top_s.columns = ['Roll Number','Name','CGPA','Percentage','Credits','Class','Honors','Minors']
    top_s.index = range(1, len(top_s)+1)
    top_s.index.name = "S.No."
    c_list, c_chart = st.columns([1, 1.3])
    with c_list:
        st.dataframe(top_s)
        html_cards = '<div class="mobile-only mobile-scroll-box">'
        for idx, row in top_s.iterrows():
            html_cards += f"""<div class="student-card"><div class="card-row"><h4 class="card-title">{row['Name']}</h4><span class="card-stat">{row['CGPA']}</span></div><div class="card-row"><p class="card-sub">{row['Roll Number']}</p><span class="card-tag" style="background:#EEF2FF; color:#4F46E5;">{row['Class']}</span></div></div>"""
        html_cards += "</div>"
        st.markdown(html_cards, unsafe_allow_html=True)
    with c_chart:
        top_s_chart = cgpa_df.nlargest(limit, 'regular_cgpa')[['full_name','regular_cgpa']].copy()
        fig = px.bar(top_s_chart, x='regular_cgpa', y='full_name', orientation='h', color='regular_cgpa', color_continuous_scale='Blues', text='regular_cgpa', labels={'full_name': 'Student Name', 'regular_cgpa': 'CGPA'})
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
        fig.update_yaxes(autorange="reversed", title="")
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch", config=chart_config)
    st.markdown("---")
    st.subheader("Semester Toppers")
    topper_data = []
    for sem in sorted(semester_df['semester'].unique()):
        s_data = semester_df[semester_df['semester'] == sem]
        if not s_data.empty:
            max_sgpa = s_data['sgpa'].max()
            top_students = s_data[s_data['sgpa'] == max_sgpa]
            count = len(top_students)
            top = top_students.iloc[0]
            display_name = top['full_name']
            if count > 1: display_name = f"{display_name} (+{count-1})"
            topper_data.append({'Semester': sem, 'Roll Number': top['hall_ticket'], 'Name': display_name, 'Sem. CGPA': max_sgpa})
    t_df = pd.DataFrame(topper_data)
    if not t_df.empty:
        t_df['Sem. CGPA'] = t_df['Sem. CGPA'].apply(fmt_dec)
        t_df.index = range(1, len(t_df)+1)
        t_df.index.name = "S.No."
        c_list, c_chart = st.columns([1, 1.3])
        with c_list:
            st.dataframe(t_df)
            html_cards = '<div class="mobile-only mobile-scroll-box">'
            for _, item in t_df.iterrows():
                html_cards += f"""<div class="student-card"><div class="card-row"><h4 class="card-title">{item['Semester']} Topper</h4><span class="card-stat">{item['Sem. CGPA']}</span></div><p class="card-sub" style="color:#111827 !important;">{item['Name']}</p><p class="card-sub">{item['Roll Number']}</p></div>"""
            html_cards += "</div>"
            st.markdown(html_cards, unsafe_allow_html=True)
        with c_chart:
            plot_data = t_df.copy()
            plot_data['Sem. CGPA'] = pd.to_numeric(plot_data['Sem. CGPA'])
            fig = px.bar(plot_data, x='Semester', y='Sem. CGPA', color='Sem. CGPA', color_continuous_scale='Reds', text='Sem. CGPA', labels={'Sem. CGPA': 'Semester CGPA'})
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
            fig.update_layout(height=400, margin=dict(l=60, r=60, t=0, b=100), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, width="stretch", config=chart_config)
    st.markdown("---")
    st.subheader("Most Consistent Performers")
    all_ranks = cgpa_df[['hall_ticket', 'regular_cgpa']].copy()
    all_ranks['Batch Rank'] = all_ranks['regular_cgpa'].rank(ascending=False, method='min').astype(int)
    var = semester_df.groupby('hall_ticket')['sgpa'].agg(['mean','std']).reset_index()
    merged = var.merge(cgpa_df[['hall_ticket','full_name']], on='hall_ticket').merge(all_ranks[['hall_ticket', 'Batch Rank']], on='hall_ticket')
    cons = merged[merged['mean'] >= 7.5].nsmallest(10, 'std')[['hall_ticket','full_name','mean','std', 'Batch Rank']]
    cons['mean'] = cons['mean'].apply(fmt_dec)
    cons['std'] = cons['std'].apply(fmt_dec)
    cons.columns = ['Roll Number','Name','Avg Sem. CGPA','Std Dev', 'Batch Rank']
    cons.index = range(1, len(cons)+1)
    cons.index.name = "S.No."
    st.dataframe(cons)
    html_cards = '<div class="mobile-only mobile-scroll-box">'
    for _, row in cons.iterrows():
        html_cards += f"""<div class="student-card"><div class="card-row"><h4 class="card-title">{row['Name']}</h4><span class="card-tag" style="background:#f3f4f6; color:#4b5563;">Rank: {row['Batch Rank']}</span></div><div class="card-row"><p class="card-sub">{row['Roll Number']}</p><span class="card-sub">Avg: <b>{row['Avg Sem. CGPA']}</b></span></div></div>"""
    html_cards += "</div>"
    st.markdown(html_cards, unsafe_allow_html=True)
def render_semesters_subtab(semester_df, marks_df):
    st.subheader("Semester-Wise Performance")
    sem_sel = st.selectbox("Select Semester", options=sorted(semester_df['semester'].unique()))
    sem_d = semester_df[semester_df['semester'] == sem_sel][['hall_ticket','full_name','sgpa','credits','status','honors_sgpa','minors_sgpa']].sort_values('sgpa', ascending=False)
    sem_d['sgpa'] = sem_d['sgpa'].apply(fmt_dec)
    sem_d['honors_sgpa'] = sem_d['honors_sgpa'].apply(fmt_str_dec)
    sem_d['minors_sgpa'] = sem_d['minors_sgpa'].apply(fmt_str_dec)
    sem_d['status'] = sem_d['status'].apply(clean_status)
    sem_d.columns = ['Roll Number','Name','Sem. CGPA','Credits','Status','Honors','Minors']
    sem_d.index = range(1, len(sem_d)+1)
    sem_d.index.name = "S.No."
    st.dataframe(sem_d)
    html_cards = '<div class="mobile-only mobile-scroll-box">'
    for _, row in sem_d.iterrows():
        status_color = "#16a34a" if row['Status'] == "Pass" else "#dc2626"
        html_cards += f"""<div class="student-card" style="border-left: 4px solid {status_color}"><div class="card-row"><h4 class="card-title">{row['Name']}</h4><span class="card-stat" style="color:{status_color} !important;">{row['Sem. CGPA']}</span></div><div class="card-row"><p class="card-sub">{row['Roll Number']}</p><span class="card-tag" style="background:{status_color}10; color:{status_color}">{row['Status']}</span></div></div>"""
    html_cards += "</div>"
    st.markdown(html_cards, unsafe_allow_html=True)
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Semester CGPA Distribution")
        fig = px.box(semester_df, x='semester', y='sgpa', color='semester', color_discrete_sequence=px.colors.qualitative.Set3, labels={'semester': 'Semester', 'sgpa': 'Semester CGPA'})
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch", config=chart_config)
    with c2:
        st.subheader("Grade Counts")
        reg_marks = marks_df[marks_df['subject_type']=='REGULAR']
        g_sem = reg_marks.groupby(['semester','grade']).size().reset_index(name='count')
        fig = px.bar(g_sem, x='semester', y='count', color='grade', labels={'semester': 'Semester', 'count': 'Grade Count', 'grade': 'Grade'})
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch", config=chart_config)
    st.markdown("---")
    valid_semester_df = semester_df[(semester_df['sgpa'] > 0) & (semester_df['sgpa'] <= 10)].copy()
    s_avg = valid_semester_df.groupby('semester').agg({'sgpa': ['mean', 'median', 'std', 'count']}).reset_index()
    s_avg.columns = ['semester', 'mean', 'median', 'std', 'count']
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Average vs Median")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=s_avg['semester'], y=s_avg['mean'], mode='lines+markers', name='Average', line=dict(color='#667eea', width=3)))
        fig.add_trace(go.Scatter(x=s_avg['semester'], y=s_avg['median'], mode='lines+markers', name='Median', line=dict(color='#f5576c', width=2, dash='dash')))
        fig.update_layout(yaxis_range=[0,10], xaxis_title="Semester", yaxis_title="CGPA")
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch", config=chart_config)
    with c2:
        st.subheader("Standard Deviation")
        fig = go.Figure(go.Bar(x=s_avg['semester'], y=s_avg['std'], marker_color='#4facfe', text=s_avg['std'].apply(fmt_dec), textposition='outside', hovertemplate='Semester: %{x}<br>Std Dev: %{y:.2f}<br>Count: ' + s_avg['count'].astype(str) + '<extra></extra>'))
        fig.update_layout(xaxis_title="Semester", yaxis_title="Standard Deviation")
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch", config=chart_config)
def render_subjects_subtab(exam_history_df):
    filtered_history = exam_history_df[exam_history_df['subject_name'].apply(is_pure_subject)].copy()
    stats = filtered_history.groupby(['subject_name', 'subject_type']).agg({'grade_points': ['mean', 'max'],'grade': ['count', lambda x: (x.isin(['F', 'Ab', 'ABSENT']) | (pd.to_numeric(x, errors='coerce').fillna(1) == 0)).sum()]}).reset_index()
    stats.columns = ['Subject', 'Type', 'Avg CGPA', 'Max CGPA', 'Total Attempts', 'Failures']
    stats['Fail Rate'] = (stats['Failures'] / stats['Total Attempts']) * 100
    valid = stats[stats['Total Attempts'] >= 5].copy()
    hard_raw = valid.sort_values('Fail Rate', ascending=False).head(10).reset_index(drop=True)
    easy_raw = valid.sort_values('Avg CGPA', ascending=False).head(10).reset_index(drop=True)
    hard_raw['Fail Rate Display'] = hard_raw['Fail Rate'].apply(lambda x: f"{fmt_dec(x)}%")
    hard_raw['Fail Rate Val'] = hard_raw['Fail Rate'].apply(lambda x: round(x, 2))
    easy_raw['Avg CGPA Display'] = easy_raw['Avg CGPA'].apply(fmt_dec)
    st.subheader("Hardest Subjects")
    c1, c2 = st.columns([1, 1.2])
    with c1: 
        disp_h = hard_raw[['Subject', 'Type', 'Fail Rate Display', 'Total Attempts']].copy()
        disp_h.columns = ['Subject', 'Type', 'Fail Rate', 'Total Attempts']
        disp_h.index = range(1, len(disp_h)+1)
        disp_h.index.name = "S.No."
        st.dataframe(disp_h)
        html_h = '<div class="mobile-only mobile-scroll-box">'
        for _, r in hard_raw.iterrows():
            html_h += f"<div class='student-card'><div class='card-row'><span class='card-title'>{r['Subject']}</span><span class='card-stat' style='color:#dc2626 !important;'>{r['Fail Rate']:.1f}% Fail</span></div></div>"
        html_h += "</div>"
        st.markdown(html_h, unsafe_allow_html=True)
    with c2:
        fig = px.bar(hard_raw, y='Subject', x='Fail Rate Val', orientation='h', color='Fail Rate Val', color_continuous_scale='Reds', text='Fail Rate Display', hover_data=['Type'], labels={'Fail Rate Val': 'Fail Rate'})
        fig.update_traces(textposition='outside', cliponaxis=False)
        fig.update_yaxes(autorange="reversed")
        fig = fix_subject_chart_layout(fig)
        fig.update_layout(xaxis_title="Failure Rate (%)", margin=dict(r=120))
        fig.update_xaxes(range=None)
        st.plotly_chart(fig, width="stretch", config=chart_config)
    st.markdown("---")
    st.subheader("Easiest Subjects")
    c1, c2 = st.columns([1, 1.2])
    with c1: 
        disp_e = easy_raw[['Subject', 'Type', 'Avg CGPA Display', 'Total Attempts']].copy()
        disp_e.columns = ['Subject', 'Type', 'Avg CGPA', 'Total Attempts']
        disp_e.index = range(1, len(disp_e)+1)
        disp_e.index.name = "S.No."
        st.dataframe(disp_e)
        html_e = '<div class="mobile-only mobile-scroll-box">'
        for _, r in easy_raw.iterrows():
            html_e += f"<div class='student-card'><div class='card-row'><span class='card-title'>{r['Subject']}</span><span class='card-stat' style='color:#16a34a !important;'>{r['Avg CGPA']:.2f} GPA</span></div></div>"
        html_e += "</div>"
        st.markdown(html_e, unsafe_allow_html=True)
    with c2:
        fig = px.bar(easy_raw, y='Subject', x='Avg CGPA', orientation='h', color='Avg CGPA', color_continuous_scale='Greens', text='Avg CGPA Display', hover_data=['Type'], labels={'Avg CGPA': 'Average CGPA'})
        fig.update_traces(textposition='outside', cliponaxis=False)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis=dict(range=[0, 10.5]), xaxis_title="Average CGPA") 
        fig = fix_subject_chart_layout(fig)
        st.plotly_chart(fig, width="stretch", config=chart_config)
def render_cohorts_subtab(cgpa_df, semester_df):
    st.subheader("Cohorts")
    t_stats = cgpa_df.groupby('student_type')['regular_cgpa'].agg(['mean','median','std','count']).reset_index()
    t_stats.columns = ['Cohort','Mean CGPA','Median CGPA','Std Dev','Count']
    disp_t = t_stats.copy()
    disp_t['Mean CGPA'] = disp_t['Mean CGPA'].apply(fmt_dec)
    disp_t['Median CGPA'] = disp_t['Median CGPA'].apply(fmt_dec)
    disp_t['Std Dev'] = disp_t['Std Dev'].apply(fmt_dec)
    st.dataframe(disp_t.set_index('Cohort'))
    fig = px.bar(t_stats, x='Cohort', y='Mean CGPA', color='Cohort', text='Mean CGPA', color_discrete_sequence=['#667eea','#f5576c'], labels={'Mean CGPA': 'Average CGPA'})
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False) 
    fig = fix_chart_layout(fig, height=350)
    fig.update_layout(margin=dict(t=50, l=60, r=60, b=60), yaxis=dict(range=[0, 11])) 
    st.plotly_chart(fig, width="stretch", config=chart_config)
    st.markdown("---")
    st.subheader("Honors & Minors")
    hon_df = cgpa_df[cgpa_df['honors_cgpa'] > 0].copy()
    min_df = cgpa_df[cgpa_df['minors_cgpa'] > 0].copy()
    st.markdown(f"""
    <div class="metric-container" style="grid-template-columns: repeat(2, 1fr); margin-bottom: 20px;">
        <div class='metric-card'><h3>{len(hon_df)}</h3><p>Honors Enrolled</p></div>
        <div class='metric-card'><h3>{fmt_dec(hon_df['honors_cgpa'].mean()) if not hon_df.empty else "0.00"}</h3><p>Honors Avg CGPA</p></div>
    </div>
    <div class="metric-container" style="grid-template-columns: repeat(2, 1fr);">
        <div class='metric-card'><h3>{len(min_df)}</h3><p>Minors Enrolled</p></div>
        <div class='metric-card'><h3>{fmt_dec(min_df['minors_cgpa'].mean()) if not min_df.empty else "0.00"}</h3><p>Minors Avg CGPA</p></div>
    </div>""", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if not hon_df.empty:
            st.markdown("**Honors vs Regular**")
            non_hon = cgpa_df[cgpa_df['honors_cgpa'] == 0]
            comp_data = pd.DataFrame({'Group': ['Honors Students', 'Regular Only'], 'Avg Regular CGPA': [hon_df['regular_cgpa'].mean(), non_hon['regular_cgpa'].mean()]})
            fig = px.bar(comp_data, x='Group', y='Avg Regular CGPA', color='Group', text='Avg Regular CGPA', color_discrete_sequence=['#ec4899', '#9ca3af'], labels={'Avg Regular CGPA': 'Average Regular CGPA'})
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
            fig.update_xaxes(title_text='')
            fig.update_layout(yaxis=dict(range=[0, 11]), margin=dict(t=50), showlegend=True)
            fig = fix_chart_layout(fig, height=350)
            st.plotly_chart(fig, width="stretch", config=chart_config)
    with c2:
        if not hon_df.empty or not min_df.empty:
            st.markdown("**CGPA Correlation**")
            fig = go.Figure()
            if not hon_df.empty:
                fig.add_trace(go.Scatter(x=hon_df['regular_cgpa'], y=hon_df['honors_cgpa'], mode='markers', name='Honors', marker=dict(color='#ec4899', size=10)))
            if not min_df.empty:
                fig.add_trace(go.Scatter(x=min_df['regular_cgpa'], y=min_df['minors_cgpa'], mode='markers', name='Minors', marker=dict(color='#10b981', size=10, symbol='square')))
            fig.update_layout(xaxis_title="Regular CGPA", yaxis_title="Track CGPA")
            fig = fix_chart_layout(fig, height=350)
            st.plotly_chart(fig, width="stretch", config=chart_config)
def render_individual_tab(students_df):
    s_map = {r['hall_ticket'][-2:]: r['hall_ticket'] for _, r in students_df.iterrows()}
    c1, c2 = st.columns([1, 3])
    with c1: sel_roll = st.selectbox("Select Roll No", options=sorted(s_map.keys()), key="ind_roll_sel")
    hall_ticket = s_map[sel_roll]
    data = load_student_data(hall_ticket)
    if not data: return
    stu, cgpa, sem = data['student'], data['cgpa'], data['semesters']
    exam_history = load_student_history(hall_ticket)
    st.markdown(f"<h1 style='text-align: left; margin-top: 0px;'>{stu['full_name']}</h1>", unsafe_allow_html=True)
    st_type = stu.get('degree_type','REGULAR') if stu.get('degree_type') in ['HONORS','MINORS'] else stu['student_type']
    st.markdown(f"""
    <div class="metric-container" style="grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px;">
        <div class='info-box'><span class='info-label'>Roll Number</span><span class='info-value'>{hall_ticket}</span></div>
        <div class='info-box'><span class='info-label'>Branch</span><span class='info-value'>{stu['branch']}</span></div>
        <div class='info-box'><span class='info-label'>Type</span><span class='info-value'>{st_type}</span></div>
        <div class='info-box'><span class='info-label'>Status</span><span class='info-value'>{clean_status(stu['status'])}</span></div>
        <div class='info-box'><span class='info-label'>DOB</span><span class='info-value'>{stu.get('dob','-')}</span></div>
        <div class='info-box'><span class='info-label'>Blood Group</span><span class='info-value'>{stu.get('blood_group','-')}</span></div>
        <div class='info-box'><span class='info-label'>Phone</span><span class='info-value'>{stu.get('phone','-')}</span></div>
        <div class='info-box'><span class='info-label'>Address</span><span class='info-value' style='font-size:0.9em;'>{stu.get('address','-')}</span></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    c_photo, c_stats = st.columns([1, 4])
    with c_photo:
        photo = get_student_photo(hall_ticket)
        img = Image.open(BytesIO(photo)) if photo else "https://via.placeholder.com/150x180.png?text=No+Photo"
        st.image(img) 
    with c_stats:
        hm_val = "NA"
        hm_label = "Honors/Minors CGPA"
        if cgpa['honors_cgpa'] > 0: 
            hm_val = fmt_dec(cgpa['honors_cgpa'])
            hm_label = "Honors CGPA"
        elif cgpa['minors_cgpa'] > 0: 
            hm_val = fmt_dec(cgpa['minors_cgpa'])
            hm_label = "Minors CGPA"
        all_c = load_all_cgpa_data()
        rank = (all_c['regular_cgpa'] > cgpa['regular_cgpa']).sum() + 1
        percentile = ((len(all_c)-rank+1)/len(all_c)*100)
        st.markdown(f"""
        <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start;">
            <div style="flex: 1 1 140px;"><div class="stat-text-val">{fmt_dec(cgpa['regular_cgpa'])}</div><div class="stat-text-lbl">Overall CGPA</div></div>
            <div style="flex: 1 1 140px;"><div class="stat-text-val">{hm_val}</div><div class="stat-text-lbl">{hm_label}</div></div>
            <div style="flex: 1 1 140px;"><div class="stat-text-val">{int(cgpa['regular_credits_secured'])}/{int(cgpa['regular_credits_registered'])}</div><div class="stat-text-lbl">Credits</div></div>
            <div style="flex: 1 1 140px;"><div class="stat-text-val">{rank}/{len(all_c)}</div><div class="stat-text-lbl">Batch Rank</div></div>
            <div style="flex: 1 1 140px;"><div class="stat-text-val">{fmt_dec(cgpa['regular_percentage'])}%</div><div class="stat-text-lbl">Percentage</div></div>
            <div style="flex: 1 1 140px;"><div class="stat-text-val">{fmt_dec(percentile)}%</div><div class="stat-text-lbl">Percentile</div></div>
            <div style="flex: 1 1 140px;"><div class="stat-text-val">{get_short_degree_class(cgpa['degree_class'])}</div><div class="stat-text-lbl">Class</div></div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")
    if not sem.empty:
        st.subheader("Performance Trend")
        fig = go.Figure()
        trend_sem = sem.copy()
        if len(trend_sem) > 1: trend_sem = trend_sem.iloc[:-1] 
        fig.add_trace(go.Scatter(x=sem['semester'], y=sem['sgpa'], mode='lines+markers', name='Regular', line=dict(color='#6366f1', width=3)))
        if sem['honors_sgpa'].sum()>0: fig.add_trace(go.Scatter(x=sem['semester'], y=sem['honors_sgpa'], mode='lines+markers', name='Honors', line=dict(color='#ec4899', dash='dash')))
        if sem['minors_sgpa'].sum()>0: fig.add_trace(go.Scatter(x=sem['semester'], y=sem['minors_sgpa'], mode='lines+markers', name='Minors', line=dict(color='#10b981', dash='dash')))
        fig.add_hline(y=sem['sgpa'].mean(), line_dash="dot", line_color='#ef4444', annotation_text=f"Average: {fmt_dec(sem['sgpa'].mean())}")
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch", config=chart_config)
        st.markdown(f"""
        <div class="metric-container">
            <div class='metric-card'><h3>{fmt_dec(sem['sgpa'].max())}</h3><p>High</p></div>
            <div class='metric-card'><h3>{fmt_dec(sem['sgpa'].min())}</h3><p>Low</p></div>
            <div class='metric-card'><h3>{fmt_dec(sem['sgpa'].mean())}</h3><p>Average</p></div>
            <div class='metric-card'><h3>{fmt_dec(sem['sgpa'].std())}</h3><p>Std Dev</p></div>
            <div class='metric-card'><h3>{trend_sem['sgpa'].iloc[-1] - trend_sem['sgpa'].iloc[0] if len(trend_sem)>1 else 0:+.2f}</h3><p>Trend*</p></div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("Backlog History")
    backlogs = exam_history[exam_history['grade'].isin(['F', 'Ab', 'ABSENT']) | (exam_history['grade_points'] == 0)].copy()
    if not backlogs.empty:
        active = []
        for code in backlogs['subject_code'].unique():
            if exam_history[exam_history['subject_code']==code]['grade_points'].max() == 0: active.append(code)
        st.markdown(f"<div style='background:#fef2f2; border:1px solid #f87171; padding:10px; border-radius:5px; color:#991b1b; margin-bottom:10px;'>Total Failed Attempts: {len(backlogs)} <br> Active Backlogs: {len(active)}</div>", unsafe_allow_html=True)
        backlogs_disp = backlogs[['semester', 'exam_type', 'subject_name', 'grade', 'subject_type', 'subject_code']].reset_index(drop=True)
        backlogs_disp.columns = ['Semester', 'Type', 'Subject', 'Grade', 'Category', 'Code']
        backlogs_disp.insert(0, 'S.No.', range(1, len(backlogs_disp) + 1))
        def highlight_active(row):
            return ['background-color: #fee2e2; color: #991b1b'] * len(row) if row['Code'] in active else [''] * len(row)
        st.dataframe(backlogs_disp.style.apply(highlight_active, axis=1), hide_index=True)
        html_bl = '<div class="mobile-only mobile-scroll-box">'
        for _, r in backlogs.iterrows():
            is_act = r['subject_code'] in active
            color = "#991b1b" if is_act else "#166534"
            status = "ACTIVE" if is_act else "CLEARED"
            html_bl += f"""<div class="student-card" style="border-left: 4px solid {color}"><div class="card-row"><span class="card-title" style="color:{color}!important">{r['subject_name']}</span><span class="card-stat" style="color:{color}!important">{r['grade']}</span></div><div class="card-row"><p class="card-sub">{r['semester']} ({r['exam_type']})</p><span class="card-tag" style="color:{color}; border:1px solid {color}">{status}</span></div></div>"""
        html_bl += "</div>"
        st.markdown(html_bl, unsafe_allow_html=True)
    else:
        st.success("No Backlogs 🎉")
    st.markdown("---")
    st.subheader("Semester-Wise Details")
    s_sel = st.selectbox("Select Semester", options=sem['semester'].tolist(), key="ind_sem_sel")
    marks = load_student_marks(hall_ticket, s_sel)
    if not marks.empty:
        s_info = sem[sem['semester']==s_sel].iloc[0]
        st.markdown(f"""
        <div class="metric-container" style="grid-template-columns: repeat(3, 1fr);">
            <div class='metric-card'><h3>{fmt_dec(s_info['sgpa'])}</h3><p>SGPA</p></div>
            <div class='metric-card'><h3>{s_info['credits']}</h3><p>Credits</p></div>
            <div class='metric-card'><h3>{clean_status(s_info['status'])}</h3><p>Status</p></div>
        </div>""", unsafe_allow_html=True)
        for m_type in ['REGULAR','HONORS','MINORS']:
            m_sub = marks[marks['subject_type']==m_type]
            if not m_sub.empty:
                st.markdown(f"**{m_type.title()} Subjects**")
                disp = m_sub[['subject_code','subject_name','credits','grade','grade_points']].copy()
                disp.index = range(1, len(disp)+1)
                disp.columns = ['Code','Subject','Cr','Gr','CGPA']
                disp.index.name = "S.No."
                st.dataframe(disp)
                html_m = '<div class="mobile-only mobile-scroll-box">'
                for _, m in m_sub.iterrows():
                    color = "#16a34a" if m['grade'] not in ['F','Ab'] else "#dc2626"
                    html_m += f"""
                    <div style="border-bottom:1px solid #e5e7eb; padding:10px; background-color: white; margin-bottom: 2px;">
                        <div style="display:flex; justify-content:space-between; align-items: center;">
                            <span class="black-text-force" style="font-weight:700; font-size:0.9rem;">{m['subject_name']}</span>
                            <span style="font-weight:800; color:{color} !important; font-size: 1rem;">{m['grade']}</span>
                        </div>
                        <div class="black-text-force" style="font-size:0.8rem; margin-top: 4px;">{m['subject_code']} | Cr: {m['credits']}</div>
                    </div>"""
                html_m += "</div>"
                st.markdown(html_m, unsafe_allow_html=True)
                if m_type == 'REGULAR':
                    gc = m_sub['grade'].value_counts()
                    fig = px.bar(x=gc.index, y=gc.values, color=gc.index, color_discrete_map={'O':'#2ecc71','A+':'#27ae60','F':'#c0392b'})
                    fig.update_layout(height=250, margin=dict(l=20,r=20,t=0,b=20), showlegend=False, xaxis_title="Grade", yaxis_title="Count")
                    st.plotly_chart(fig, width="stretch", config=chart_config)
def main():
    st.title("JNTU Dashboard")
    view = st.radio("Main Navigation", ["Dashboard", "Individual"], horizontal=True, label_visibility="collapsed", key="main_nav")
    if view == "Dashboard":
        dash_view = st.radio("Dashboard View", ["Overview", "Toppers", "Semesters", "Subjects", "Cohorts"], horizontal=True, label_visibility="collapsed", key="dash_nav")
        s_df = load_all_students()
        c_df = load_all_cgpa_data()
        sem_df = load_all_semester_results()
        m_df = load_all_marks()
        eh_df = load_all_exam_history()
        if dash_view == "Overview":
            render_overview_subtab(s_df, c_df, m_df)
        elif dash_view == "Toppers":
            render_toppers_subtab(c_df, sem_df)
        elif dash_view == "Semesters":
            render_semesters_subtab(sem_df, m_df)
        elif dash_view == "Subjects":
            render_subjects_subtab(eh_df)
        elif dash_view == "Cohorts":
            render_cohorts_subtab(c_df, sem_df)
    else:
        render_individual_tab(load_all_students())
if __name__ == "__main__":
    main()
