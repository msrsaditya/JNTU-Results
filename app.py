import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from PIL import Image
from decimal import Decimal, ROUND_HALF_UP
st.set_page_config(page_title="JNTU Dashboard", page_icon="🎓", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
    [data-testid="stSidebar"] {display: none;}
    .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 100% !important;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    h1, h2, h3 {font-family: 'Inter', sans-serif;}
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-left: 5px solid #4B5563;
        padding: 20px;
        border-radius: 8px;
        color: #1F2937;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin: 5px 0;
        text-align: center;
        height: 100%;
        transition: transform 0.2s;
    }
    .metric-card:hover {transform: translateY(-2px); box-shadow: 0 6px 8px rgba(0, 0, 0, 0.1);}
    .metric-card h3 {margin: 0; font-size: 2.2em; font-weight: 700; color: #111827;}
    .metric-card p {margin: 8px 0 0 0; font-size: 1em; color: #6B7280; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;}
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 5px;
        padding-top: 5px;
        display: flex;
        justify-content: space-evenly;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        flex-grow: 1;
        height: 50px;
        white-space: pre-wrap;
        background-color: #f3f4f6;
        border-radius: 8px;
        padding: 10px;
        color: #4b5563;
        font-weight: 600;
        font-size: 16px;
        border: 1px solid #e5e7eb;
        transition: transform 0.2s ease-in-out, background-color 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        min-width: 120px;
        margin-bottom: 5px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e0e7ff;
        color: #3730a3;
        transform: translateY(-2px); 
    }
    .stTabs [aria-selected="true"] {
        background-color: #4F46E5 !important;
        color: #FFFFFF !important;
        border: 1px solid #4F46E5;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
    }
    .info-box {
        background: #f9fafb;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        text-align: center;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 10px;
    }
    .info-label {font-size: 0.85em; color: #6b7280; text-transform: uppercase; font-weight: 600; margin-bottom: 4px;}
    .info-value {
        font-size: 1.1em; 
        color: #111827; 
        font-weight: 700; 
        word-wrap: break-word; 
        white-space: normal;
        line-height: 1.4;
    }
    div[data-testid="stNumberInput"] {margin-top: 0px; width: 100%;}
    div[data-testid="stNumberInput"] input {padding-right: 0px;}
    .header-text-left {font-size: 1.8rem; font-weight: 800; margin: 0; padding: 0; line-height: 1.2; display: block; white-space: nowrap; text-align: right; transform: translateY(-6px);}
    .header-text-right {font-size: 1.8rem; font-weight: 800; margin: 0; padding: 0; line-height: 1.2; display: block; white-space: nowrap; text-align: left; transform: translateY(-6px);}
    @media only screen and (max-width: 768px) {
        .metric-card h3 {font-size: 1.8em;}
        .metric-card p {font-size: 0.8em;}
        .header-text-left, .header-text-right {font-size: 1.4rem; text-align: left; transform: none;}
        .js-plotly-plot {margin-bottom: 10px;}
        .stTabs [data-baseweb="tab"] {font-size: 14px; padding: 5px; height: 40px;}
        .header-text-left {text-align: left; margin-bottom: 5px;}
    }
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
def fix_chart_layout(fig, height=400, top_margin=20):
    fig.update_layout(
        height=height, 
        margin=dict(l=60, r=60, t=top_margin, b=60), 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
def fix_subject_chart_layout(fig, height=400):
    fig.update_layout(
        height=height, 
        margin=dict(l=60, r=80, t=30, b=60), 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(range=[0, 12])
    )
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
    query = """
        SELECT s.hall_ticket, s.full_name, s.branch, s.student_type, s.degree_type,
               c.regular_cgpa, c.regular_percentage, c.regular_credits_secured, 
               c.regular_credits_registered, c.degree_class, c.regular_degree_status,
               c.honors_cgpa, c.minors_cgpa, c.honors_degree_status, c.minors_degree_status
        FROM students s 
        JOIN overall_cgpa c ON s.hall_ticket = c.hall_ticket 
        WHERE s.status = 'ACTIVE' 
        ORDER BY c.regular_cgpa DESC
    """
    df = pd.read_sql_query(query, conn)
    numeric = ['regular_cgpa', 'regular_percentage', 'regular_credits_secured', 
               'regular_credits_registered', 'honors_cgpa', 'minors_cgpa']
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df
@st.cache_data(ttl=600)
def load_all_semester_results():
    conn = get_database_connection()
    query = """
        SELECT sr.*, s.full_name, s.branch, s.student_type 
        FROM semester_results sr 
        JOIN students s ON sr.hall_ticket = s.hall_ticket 
        WHERE s.status = 'ACTIVE' 
        ORDER BY sr.semester, sr.sgpa DESC
    """
    df = pd.read_sql_query(query, conn)
    for c in ['sgpa', 'credits', 'honors_sgpa', 'minors_sgpa']:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    return df
@st.cache_data(ttl=600)
def load_all_marks():
    conn = get_database_connection()
    query = """
        SELECT m.*, sr.hall_ticket, sr.semester, s.full_name 
        FROM marks m 
        JOIN semester_results sr ON m.result_id = sr.id 
        JOIN students s ON sr.hall_ticket = s.hall_ticket 
        WHERE s.status = 'ACTIVE'
    """
    df = pd.read_sql_query(query, conn)
    df = df[df['grade'] != 'CMP']
    df['grade_points'] = pd.to_numeric(df['grade_points'], errors='coerce').fillna(0)
    return df
@st.cache_data(ttl=600)
def load_all_exam_history():
    conn = get_database_connection()
    query = """
        SELECT eh.*, s.student_type as cohort_type
        FROM exam_history eh
        JOIN students s ON eh.hall_ticket = s.hall_ticket
        WHERE s.status = 'ACTIVE'
    """
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
    query = """
        SELECT m.subject_code, m.subject_name, m.credits, m.grade, m.grade_points, m.subject_type 
        FROM marks m 
        JOIN semester_results sr ON m.result_id = sr.id 
        WHERE sr.hall_ticket = ? AND sr.semester = ? 
        ORDER BY m.subject_type, m.subject_code
    """
    df = pd.read_sql_query(query, conn, params=(hall_ticket, semester))
    df = df[df['grade'] != 'CMP']
    df['grade_points'] = pd.to_numeric(df['grade_points'], errors='coerce').fillna(0).astype(int)
    return df
@st.cache_data(ttl=600)
def load_student_history(hall_ticket):
    conn = get_database_connection()
    query = """
        SELECT semester, exam_type, subject_name, grade, grade_points, subject_type, subject_code
        FROM exam_history
        WHERE hall_ticket = ?
        ORDER BY id
    """
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
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(f"<div class='metric-card' style='border-left-color: #6366f1;'><h3>{len(students_df)}</h3><p>Total Students</p></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card' style='border-left-color: #ec4899;'><h3>{(cgpa_df['honors_cgpa'] > 0).sum()}</h3><p>Honors Students</p></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card' style='border-left-color: #10b981;'><h3>{(cgpa_df['minors_cgpa'] > 0).sum()}</h3><p>Minors Students</p></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card' style='border-left-color: #f59e0b;'><h3>{fmt_dec(cgpa_df['regular_cgpa'].max())}</h3><p>Highest CGPA</p></div>", unsafe_allow_html=True)
    with c5: st.markdown(f"<div class='metric-card' style='border-left-color: #8b5cf6;'><h3>{fmt_dec(cgpa_df['regular_cgpa'].mean())}</h3><p>Average CGPA</p></div>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Degree Class Distribution")
        d_counts = cgpa_df['degree_class'].value_counts()
        fig = px.pie(values=d_counts.values, names=d_counts.index, color_discrete_sequence=px.colors.sequential.RdBu)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0))
        st.plotly_chart(fig, width="stretch")
    with col2:
        st.subheader("Overall Grade Distribution")
        reg_marks = marks_df[marks_df['subject_type']=='REGULAR']
        g_counts = reg_marks['grade'].value_counts().sort_index()
        fig = px.pie(values=g_counts.values, names=g_counts.index, color=g_counts.index, 
                    color_discrete_map={'O':'#2ecc71','A+':'#27ae60','A':'#3498db','B+':'#5dade2','B':'#f39c12','C':'#e67e22','D':'#e74c3c','F':'#c0392b','Ab':'#95a5a6'}, 
                    hole=0.4)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.0))
        st.plotly_chart(fig, width="stretch")
    st.markdown("---")
    st.subheader("CGPA Distribution")
    avg = cgpa_df['regular_cgpa'].mean()
    fig = px.histogram(cgpa_df, x='regular_cgpa', nbins=30, labels={'regular_cgpa': 'CGPA'}, color_discrete_sequence=['#667eea'])
    fig.add_vline(x=avg, line_dash="dash", line_color="red", annotation_text=f"Average: {fmt_dec(avg)}")
    fig = fix_chart_layout(fig)
    st.plotly_chart(fig, width="stretch")
def render_toppers_subtab(cgpa_df, semester_df):
    c1, c2, c3, c4 = st.columns([0.3, 0.7, 1.5, 4], vertical_alignment="center", gap="small")
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
    container = st.container()
    with container:
        col_t, col_p = st.columns([1, 1.3])
        with col_t: st.dataframe(top_s)
        with col_p:
            top_s_chart = cgpa_df.nlargest(limit, 'regular_cgpa')[['full_name','regular_cgpa']].copy()
            top_s_chart.index = range(1, len(top_s_chart)+1)
            top_s_chart.columns = ['Name', 'CGPA']
            fig = px.bar(top_s_chart.reset_index(), x='CGPA', y='Name', orientation='h', color='CGPA', color_continuous_scale='Blues', text='CGPA')
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
            fig.update_layout(height=400, margin=dict(l=60, r=60, t=20, b=60), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, width="stretch")
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
            if count > 1:
                display_name = f"{display_name} (+{count-1})"
            topper_data.append({'Semester': sem, 'Roll Number': top['hall_ticket'], 'Name': display_name, 'Sem. CGPA': max_sgpa})
    t_df = pd.DataFrame(topper_data)
    if not t_df.empty:
        t_df['Sem. CGPA'] = t_df['Sem. CGPA'].apply(fmt_dec)
        t_df.index = range(1, len(t_df)+1)
        t_df.index.name = "S.No."
        container2 = st.container()
        with container2:
            c_t, c_p = st.columns([1, 1.3])
            with c_t: st.dataframe(t_df)
            with c_p:
                plot_data = t_df.copy()
                plot_data['Sem. CGPA'] = pd.to_numeric(plot_data['Sem. CGPA'])
                fig = px.bar(plot_data, x='Semester', y='Sem. CGPA', color='Sem. CGPA', color_continuous_scale='Reds', text='Sem. CGPA', hover_data=['Name'])
                fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
                fig.update_layout(height=400, margin=dict(l=60, r=60, t=0, b=100), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, width="stretch")
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
def render_semesters_subtab(semester_df, marks_df):
    st.subheader("Semester-Wise Performance")
    sem_sel = st.selectbox("Select Semester", options=sorted(semester_df['semester'].unique()), key="sem_overview_sel")
    sem_d = semester_df[semester_df['semester'] == sem_sel][['hall_ticket','full_name','sgpa','credits','status','honors_sgpa','minors_sgpa']].sort_values('sgpa', ascending=False)
    sem_d['sgpa'] = sem_d['sgpa'].apply(fmt_dec)
    sem_d['honors_sgpa'] = sem_d['honors_sgpa'].apply(fmt_str_dec)
    sem_d['minors_sgpa'] = sem_d['minors_sgpa'].apply(fmt_str_dec)
    sem_d.columns = ['Roll Number','Name','Sem. CGPA','Credits','Status','Honors','Minors']
    sem_d.index = range(1, len(sem_d)+1)
    sem_d.index.name = "S.No."
    st.dataframe(sem_d)
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Sem. CGPA Distribution")
        fig = px.box(semester_df, x='semester', y='sgpa', color='semester', color_discrete_sequence=px.colors.qualitative.Set3, labels={'semester': 'Semester', 'sgpa': 'SGPA'})
        fig.update_traces(quartilemethod="exclusive")
        fig = fix_chart_layout(fig, height=450)
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("Grade Distribution")
        reg_marks = marks_df[marks_df['subject_type']=='REGULAR']
        g_sem = reg_marks.groupby(['semester','grade']).size().reset_index(name='count')
        fig = px.bar(g_sem, x='semester', y='count', color='grade', color_discrete_map={'O':'#2ecc71','A+':'#27ae60','A':'#3498db','B+':'#5dade2','B':'#f39c12','C':'#e67e22','D':'#e74c3c','F':'#c0392b'})
        fig = fix_chart_layout(fig, height=450)
        st.plotly_chart(fig, width="stretch")
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
        fig.update_layout(yaxis_range=[0,10])
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("Standard Deviation")
        fig = go.Figure(go.Bar(x=s_avg['semester'], y=s_avg['std'], marker_color='#4facfe', text=s_avg['std'].apply(fmt_dec), textposition='outside', hovertemplate='Semester: %{x}<br>Std Dev: %{y:.2f}<br>Count: ' + s_avg['count'].astype(str) + '<extra></extra>'))
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch")
def render_subjects_subtab(exam_history_df):
    filtered_history = exam_history_df[exam_history_df['subject_name'].apply(is_pure_subject)].copy()
    stats = filtered_history.groupby(['subject_name', 'subject_type']).agg({
        'grade_points': ['mean', 'max'],
        'grade': ['count', lambda x: (x.isin(['F', 'Ab', 'ABSENT']) | (pd.to_numeric(x, errors='coerce').fillna(1) == 0)).sum()]
    }).reset_index()
    stats.columns = ['Subject', 'Type', 'Avg CGPA', 'Max CGPA', 'Total Attempts', 'Failures']
    stats = stats[stats['Max CGPA'] > 0]
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
    with c2:
        fig = px.bar(hard_raw, y='Subject', x='Fail Rate Val', orientation='h', color='Fail Rate Val', 
                     color_continuous_scale='Reds', text='Fail Rate Display', hover_data=['Type'],
                     labels={'Fail Rate Val': 'Fail Rate'})
        fig.update_traces(textposition='outside', cliponaxis=False)
        fig.update_yaxes(autorange="reversed")
        fig = fix_subject_chart_layout(fig)
        fig.update_layout(xaxis_title="Failure Rate (%)", margin=dict(r=120))
        fig.update_xaxes(range=None)
        st.plotly_chart(fig, width="stretch")
    st.markdown("---")
    st.subheader("Easiest Subjects")
    c1, c2 = st.columns([1, 1.2])
    with c1: 
        disp_e = easy_raw[['Subject', 'Type', 'Avg CGPA Display', 'Total Attempts']].copy()
        disp_e.columns = ['Subject', 'Type', 'Avg CGPA', 'Total Attempts']
        disp_e.index = range(1, len(disp_e)+1)
        disp_e.index.name = "S.No."
        st.dataframe(disp_e)
    with c2:
        fig = px.bar(easy_raw, y='Subject', x='Avg CGPA', orientation='h', color='Avg CGPA', 
                     color_continuous_scale='Greens', text='Avg CGPA Display', hover_data=['Type'])
        fig.update_traces(textposition='outside', cliponaxis=False)
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis=dict(range=[0, 10.5]), xaxis_title="Average CGPA") 
        fig = fix_subject_chart_layout(fig)
        st.plotly_chart(fig, width="stretch")
def render_cohorts_subtab(cgpa_df, semester_df):
    st.subheader("Cohorts")
    t_stats = cgpa_df.groupby('student_type')['regular_cgpa'].agg(['mean','median','std','count']).reset_index()
    t_stats.columns = ['Cohort','Mean CGPA','Median CGPA','Std Dev','Count']
    disp_t = t_stats.copy()
    disp_t['Mean CGPA'] = disp_t['Mean CGPA'].apply(fmt_dec)
    disp_t['Median CGPA'] = disp_t['Median CGPA'].apply(fmt_dec)
    disp_t['Std Dev'] = disp_t['Std Dev'].apply(fmt_dec)
    st.dataframe(disp_t.set_index('Cohort'))
    fig = px.bar(t_stats, x='Cohort', y='Mean CGPA', color='Cohort', text='Mean CGPA', color_discrete_sequence=['#667eea','#f5576c'])
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False) 
    fig = fix_chart_layout(fig, height=350)
    fig.update_layout(margin=dict(t=50, l=60, r=60, b=60), yaxis=dict(range=[0, 11])) 
    st.plotly_chart(fig, width="stretch")
    st.markdown("---")
    st.subheader("Honors & Minors")
    hon_df = cgpa_df[cgpa_df['honors_cgpa'] > 0].copy()
    min_df = cgpa_df[cgpa_df['minors_cgpa'] > 0].copy()
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Honors Enrolled", f"{len(hon_df)}", delta=f"{fmt_dec(len(hon_df)/len(cgpa_df)*100)}% of Batch")
    with m2: st.metric("Honors Avg CGPA", fmt_dec(hon_df['honors_cgpa'].mean()) if not hon_df.empty else "0.00")
    with m3: st.metric("Minors Enrolled", f"{len(min_df)}", delta=f"{fmt_dec(len(min_df)/len(cgpa_df)*100)}% of Batch")
    with m4: st.metric("Minors Avg CGPA", fmt_dec(min_df['minors_cgpa'].mean()) if not min_df.empty else "0.00")
    c1, c2 = st.columns(2)
    with c1:
        if not hon_df.empty:
            st.markdown("**Honors vs Regular**")
            non_hon = cgpa_df[cgpa_df['honors_cgpa'] == 0]
            comp_data = pd.DataFrame({
                'Group': ['Honors Students', 'Regular Only'],
                'Avg Regular CGPA': [hon_df['regular_cgpa'].mean(), non_hon['regular_cgpa'].mean()]
            })
            fig = px.bar(comp_data, x='Group', y='Avg Regular CGPA', color='Group', text='Avg Regular CGPA', color_discrete_sequence=['#ec4899', '#9ca3af'])
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
            fig.update_xaxes(title_text='')
            fig.update_layout(
                yaxis=dict(range=[0, 11]), 
                margin=dict(t=50), 
                showlegend=True
            )
            fig = fix_chart_layout(fig, height=350)
            st.plotly_chart(fig, width="stretch")
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
            st.plotly_chart(fig, width="stretch")
def render_individual_tab(students_df):
    s_map = {r['hall_ticket'][-2:]: r['hall_ticket'] for _, r in students_df.iterrows()}
    c1, c2 = st.columns([1, 3])
    with c1: 
        sel_roll = st.selectbox("Select Roll No", options=sorted(s_map.keys()), key="ind_roll_sel")
    hall_ticket = s_map[sel_roll]
    data = load_student_data(hall_ticket)
    if not data: 
        st.error("Not Found")
        return
    stu, cgpa, sem = data['student'], data['cgpa'], data['semesters']
    exam_history = load_student_history(hall_ticket)
    with c2:
        st.markdown(f"<h1 style='text-align: left; margin-top: 0px;'>{stu['full_name']}</h1>", unsafe_allow_html=True)
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1: st.markdown(f"<div class='info-box'><div class='info-label'>Roll Number</div><div class='info-value'>{hall_ticket}</div></div>", unsafe_allow_html=True)
    with r1c2: st.markdown(f"<div class='info-box'><div class='info-label'>Branch</div><div class='info-value'>{stu['branch']}</div></div>", unsafe_allow_html=True)
    with r1c3: st.markdown(f"<div class='info-box'><div class='info-label'>Type</div><div class='info-value'>{stu.get('degree_type','REGULAR') if stu.get('degree_type') in ['HONORS','MINORS'] else stu['student_type']}</div></div>", unsafe_allow_html=True)
    with r1c4: st.markdown(f"<div class='info-box'><div class='info-label'>Status</div><div class='info-value'>{stu['status']}</div></div>", unsafe_allow_html=True)
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1: st.markdown(f"<div class='info-box'><div class='info-label'>DOB</div><div class='info-value'>{stu.get('dob','-')}</div></div>", unsafe_allow_html=True)
    with r2c2: st.markdown(f"<div class='info-box'><div class='info-label'>Blood Group</div><div class='info-value'>{stu.get('blood_group','-')}</div></div>", unsafe_allow_html=True)
    with r2c3: st.markdown(f"<div class='info-box'><div class='info-label'>Phone</div><div class='info-value'>{stu.get('phone','-')}</div></div>", unsafe_allow_html=True)
    with r2c4: st.markdown(f"<div class='info-box'><div class='info-label'>Address</div><div class='info-value' style='font-size:0.9em;'>{stu.get('address','-')}</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    col_photo, col_stats = st.columns([1, 4])
    with col_photo:
        photo = get_student_photo(hall_ticket)
        img = Image.open(BytesIO(photo)) if photo else "https://via.placeholder.com/150x180.png?text=No+Photo"
        st.image(img) 
    with col_stats:
        vc1, vc2, vc3, vc4 = st.columns(4)
        with vc1:
            st.metric("Overall CGPA", fmt_dec(cgpa['regular_cgpa']))
            hm_val = "NA"
            if cgpa['honors_cgpa'] > 0:
                hm_val = fmt_dec(cgpa['honors_cgpa'])
            elif cgpa['minors_cgpa'] > 0:
                hm_val = fmt_dec(cgpa['minors_cgpa'])
            st.metric("Honors/Minors CGPA", hm_val)
        with vc2:
            st.metric("Credits", f"{int(cgpa['regular_credits_secured'])}/{int(cgpa['regular_credits_registered'])}")
            all_c = load_all_cgpa_data()
            rank = (all_c['regular_cgpa'] > cgpa['regular_cgpa']).sum() + 1
            st.metric("Batch Rank", f"{rank}/{len(all_c)}")
        with vc3:
            st.metric("Percentage", f"{fmt_dec(cgpa['regular_percentage'])}%")
            percentile = ((len(all_c)-rank+1)/len(all_c)*100)
            st.metric("Percentile", f"{fmt_dec(percentile)}%")
        with vc4:
            short_degree = get_short_degree_class(cgpa['degree_class'])
            st.metric("Degree Class", short_degree)
    st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
    if not sem.empty:
        st.subheader("Semester Performance Trend")
        fig = go.Figure()
        COLOR_REG = '#6366f1'
        COLOR_HON = '#ec4899'
        COLOR_MIN = '#10b981'
        COLOR_AVG = '#ef4444'
        trend_sem = sem.copy()
        if len(trend_sem) > 1:
             trend_sem = trend_sem.iloc[:-1] 
        fig.add_trace(go.Scatter(x=sem['semester'], y=sem['sgpa'], mode='lines+markers', name='Regular', line=dict(color=COLOR_REG, width=3)))
        if sem['honors_sgpa'].sum()>0: 
            fig.add_trace(go.Scatter(x=sem['semester'], y=sem['honors_sgpa'], mode='lines+markers', name='Honors', line=dict(color=COLOR_HON, dash='dash')))
        if sem['minors_sgpa'].sum()>0: 
            fig.add_trace(go.Scatter(x=sem['semester'], y=sem['minors_sgpa'], mode='lines+markers', name='Minors', line=dict(color=COLOR_MIN, dash='dash')))
        fig.add_hline(y=sem['sgpa'].mean(), line_dash="dot", line_color=COLOR_AVG, annotation_text=f"Average: {fmt_dec(sem['sgpa'].mean())}")
        fig = fix_chart_layout(fig)
        st.plotly_chart(fig, width="stretch")
        sc1, sc2, sc3, sc4, sc5 = st.columns(5)
        with sc1: st.metric("High", fmt_dec(sem['sgpa'].max()))
        with sc2: st.metric("Low", fmt_dec(sem['sgpa'].min()))
        with sc3: st.metric("Average", fmt_dec(sem['sgpa'].mean()))
        with sc4: st.metric("Standard Deviation", fmt_dec(sem['sgpa'].std()))
        with sc5: 
            tr = trend_sem['sgpa'].iloc[-1] - trend_sem['sgpa'].iloc[0] if len(trend_sem)>1 else 0
            st.metric("Trend*", f"{tr:+.2f}", help="Last semester excluded from trend calculation.")
    st.markdown("---")
    st.subheader("Backlog History")
    backlogs = exam_history[exam_history['grade'].isin(['F', 'Ab', 'ABSENT']) | (exam_history['grade_points'] == 0)].copy()
    if not backlogs.empty:
        active_backlog_codes = []
        for code in backlogs['subject_code'].unique():
            subj_history = exam_history[exam_history['subject_code'] == code]
            if subj_history['grade_points'].max() == 0:
                active_backlog_codes.append(code)
        num_active = len(active_backlog_codes)
        st.markdown(f"""
        <div style="background-color: #fef2f2; border: 1px solid #f87171; padding: 10px; border-radius: 5px; color: #991b1b; margin-bottom: 10px;">
            <div style="font-weight: 600;">Total Failed Attempts: {len(backlogs)}</div>
            <div style="font-weight: 600;">Active Backlogs: {num_active}</div>
        </div>
        """, unsafe_allow_html=True)
        backlogs_disp = backlogs[['semester', 'exam_type', 'subject_name', 'grade', 'subject_type', 'subject_code']].reset_index(drop=True)
        backlogs_disp.columns = ['Semester', 'Type', 'Subject', 'Grade', 'Category', 'Code']
        backlogs_disp.insert(0, 'S.No.', range(1, len(backlogs_disp) + 1))
        def highlight_active(row):
            if row['Code'] in active_backlog_codes:
                return ['background-color: #fee2e2; color: #991b1b'] * len(row)
            return [''] * len(row)
        st.dataframe(backlogs_disp.style.apply(highlight_active, axis=1), hide_index=True)
    else:
        st.success("No Backlogs 🎉")
    st.markdown("---")
    st.subheader("Semester-Wise Details")
    s_sel = st.selectbox("Select Semester", options=sem['semester'].tolist(), key="ind_sem_sel")
    marks = load_student_marks(hall_ticket, s_sel)
    if not marks.empty:
        s_info = sem[sem['semester']==s_sel].iloc[0]
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("SGPA", fmt_dec(s_info['sgpa']))
        with c2: st.metric("Credits", f"{s_info['credits']}")
        with c3: st.metric("Status", s_info['status'])
        for m_type in ['REGULAR','HONORS','MINORS']:
            m_sub = marks[marks['subject_type']==m_type]
            if not m_sub.empty:
                st.markdown(f"**{m_type.title()} Subjects**")
                disp = m_sub[['subject_code','subject_name','credits','grade','grade_points']].copy()
                disp.index = range(1, len(disp)+1)
                disp.columns = ['Code','Subject','Cr','Gr','CGPA']
                disp.index.name = "S.No."
                st.dataframe(disp)
                if m_type == 'REGULAR':
                    gc = m_sub['grade'].value_counts()
                    fig = px.bar(x=gc.index, y=gc.values, color=gc.index, color_discrete_map={'O':'#2ecc71','A+':'#27ae60','F':'#c0392b'})
                    fig.update_layout(height=250, margin=dict(l=20,r=20,t=0,b=20), showlegend=False)
                    st.plotly_chart(fig, width="stretch")
def main():
    st.title("JNTU Dashboard")
    t_dash, t_ind = st.tabs(["Dashboard", "Individual"])
    with t_dash:
        s_df = load_all_students()
        c_df = load_all_cgpa_data()
        sem_df = load_all_semester_results()
        m_df = load_all_marks()
        eh_df = load_all_exam_history()
        t1, t2, t3, t4, t5 = st.tabs(["📊 Overview", "🏆 Toppers", "📅 Semesters", "📚 Subjects", "🎯 Cohorts"])
        with t1: render_overview_subtab(s_df, c_df, m_df)
        with t2: render_toppers_subtab(c_df, sem_df)
        with t3: render_semesters_subtab(sem_df, m_df)
        with t4: render_subjects_subtab(eh_df)
        with t5: render_cohorts_subtab(c_df, sem_df)
    with t_ind:
        render_individual_tab(load_all_students())
if __name__ == "__main__":
    main()
