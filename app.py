import streamlit as st
import pandas as pd
import io
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# DARK THEME DESIGN TOKENS
# ─────────────────────────────────────────────
BG_MAIN      = "#0D1117"   # page background
BG_CARD      = "#161B22"   # chart / card background
BG_SURFACE   = "#1C2333"   # slightly lighter surface
BORDER       = "#30363D"   # subtle border
ACCENT_BLUE  = "#58A6FF"   # bright blue for lines/accents
ACCENT_TEAL  = "#3BCEAC"   # teal for pass/positive
ACCENT_AMBER = "#F0B429"   # amber for secondary line
TEXT_PRIMARY = "#E6EDF3"   # main text
TEXT_MUTED   = "#FFFFFF"   # captions / axis labels
GRID_COLOR   = "#21262D"   # chart gridlines

# Gauge / traffic light
GREEN  = "#2EA043"         # satisfactory  0 – 1.8
YELLOW = "#F0B429"         # developing    1.8 – 2.0
RED    = "#F85149"         # poor          2.0 – 2.5

FONT_FAMILY = "Montserrat, sans-serif"


# ─────────────────────────────────────────────
# INJECT DARK CSS
# ─────────────────────────────────────────────
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

/* ── root background ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stSidebar"] {
    background-color: #0D1117 !important;
    color: #E6EDF3 !important;
    font-family: 'Montserrat', sans-serif !important;
}

/* sidebar */
[data-testid="stSidebar"] {
    background-color: #161B22 !important;
    border-right: 1px solid #30363D;
}

/* main content wrapper */
[data-testid="block-container"] { background-color: #0D1117 !important; }

/* ── typography ── */
h1, h2, h3, h4, h5, h6,
.stMarkdown p, .stCaption,
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    color: #E6EDF3 !important;
    font-family: 'Montserrat', sans-serif !important;
}

.stCaption { color: #8B949E !important; }

/* ── metric cards ── */
[data-testid="metric-container"] {
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    border-radius: 10px !important;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] { font-weight: 600 !important; }

/* ── divider ── */
hr { border-color: #30363D !important; }

/* ── tabs ── */
[data-baseweb="tab-list"] { background-color: #161B22 !important; border-bottom: 1px solid #30363D; }
[data-baseweb="tab"] { color: #8B949E !important; font-family: 'Montserrat', sans-serif !important; }
[aria-selected="true"] { color: #58A6FF !important; border-bottom: 2px solid #58A6FF !important; }

/* ── selectbox / multiselect ── */
[data-baseweb="select"] > div {
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #E6EDF3 !important;
    font-family: 'Montserrat', sans-serif !important;
}

/* ── buttons ── */
.stDownloadButton > button, .stButton > button {
    background-color: #1F6FEB !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover, .stButton > button:hover {
    background-color: #388BFD !important;
}

/* ── file uploader ── */
[data-testid="stFileUploader"] {
    background-color: #161B22 !important;
    border: 1px dashed #30363D !important;
    border-radius: 8px !important;
}

/* ── info / success / warning boxes ── */
[data-testid="stAlert"] { border-radius: 8px !important; }

/* plotly chart transparent bg */
.js-plotly-plot .plotly { background: transparent !important; }
</style>
"""


# ─────────────────────────────────────────────
# BASE PLOTLY LAYOUT (dark)
# ─────────────────────────────────────────────
def base_layout(title: str, xtitle: str = "", ytitle: str = "") -> dict:
    return dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(family=FONT_FAMILY, size=17, color=TEXT_PRIMARY),
            x=0.03,
        ),
        xaxis=dict(
            title=dict(text=f"<b>{xtitle}</b>", font=dict(family=FONT_FAMILY, size=12, color=TEXT_MUTED)),
            tickfont=dict(family=FONT_FAMILY, size=11, color=TEXT_MUTED),
            gridcolor=GRID_COLOR,
            linecolor=BORDER,
            showgrid=True,
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text=f"<b>{ytitle}</b>", font=dict(family=FONT_FAMILY, size=12, color=TEXT_MUTED)),
            tickfont=dict(family=FONT_FAMILY, size=11, color=TEXT_MUTED),
            gridcolor=GRID_COLOR,
            linecolor=BORDER,
            showgrid=True,
            zeroline=False,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=BG_CARD,
        font=dict(family=FONT_FAMILY, color=TEXT_PRIMARY),
        margin=dict(l=60, r=30, t=70, b=60),
        hoverlabel=dict(
            bgcolor=BG_SURFACE,
            font_color=TEXT_PRIMARY,
            font_family=FONT_FAMILY,
            bordercolor=BORDER,
        ),
    )


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
def sidebar_data():
    uploaded_files = st.sidebar.file_uploader(
        "Upload data", accept_multiple_files=True, label_visibility="visible"
    )
    st.session_state.uploaded_files = uploaded_files


# ─────────────────────────────────────────────
# FILE PROCESSING
# ─────────────────────────────────────────────
def process_and_rename_file(uploaded_file):
    df = pd.read_excel(uploaded_file)

    if "Planning" in df.columns and "Instruction" in df.columns:
        new_name = "principal_survey.xlsx"

    elif "Total Attempts" in df.columns and "Passing Attempts" in df.columns:
        new_name = "certification_exam_pass_rate.xlsx"

    elif "Overall Student Growth Score" in df.columns:
        new_name = "student_achievement_of_student_taught_by_beginning_teachers.xlsx"
        if "Year of Teaching" in df.columns:
            df = df.rename(columns={"Year of Teaching": "Teaching Years"})
        df["Overall Student Growth Score"] = df[
            ["Mathematics Student Growth Score", "English/ Reading Student Growth Score"]
        ].mean(axis=1)

    return new_name, df


# ─────────────────────────────────────────────
# DATA MANAGEMENT PAGE
# ─────────────────────────────────────────────
def show_old_new_file():
    uploaded_files = st.session_state.get("uploaded_files", [])
    if not uploaded_files:
        st.write("Upload your Files First")
    else:
        for uploaded_file in uploaded_files:
            new_name, _ = process_and_rename_file(uploaded_file)
            col1, col2, col3 = st.columns([4, 1, 4])
            with col1:
                st.info(f"{uploaded_file.name}")
            with col2:
                st.markdown(
                    "<h2 style='text-align:center;margin-top:-10px;color:#E6EDF3;'>→</h2>",
                    unsafe_allow_html=True,
                )
            with col3:
                st.success(f"{new_name}")


def download_new_file():
    uploaded_files = st.session_state.get("uploaded_files", [])
    if uploaded_files:
        st.subheader("Download file")
        for idx, uploaded_file in enumerate(uploaded_files):
            new_name, df = process_and_rename_file(uploaded_file)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Sheet1")
            st.download_button(
                label=f"Download {new_name}",
                data=buffer.getvalue(),
                file_name=new_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_{idx}_{uploaded_file.name}",
            )


def Data_Management():
    st.title("Data Management")
    show_old_new_file()
    download_new_file()


# ─────────────────────────────────────────────
# PRINCIPAL PERCEPTIONS TAB
# ─────────────────────────────────────────────
def principal_perceptions(df):
    if "gender_filter" not in st.session_state:
        st.session_state.gender_filter = "All"
    if "cohort_filter" not in st.session_state:
        st.session_state.cohort_filter = []

    df_original = df.copy()

    # ── Filters ──
    st.subheader("🔍 Filter Options")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        gender_selected = st.selectbox(
            "Gender",
            options=["All"] + sorted(df_original["Gender"].unique().tolist()),
            key="gender_select",
        )
        st.session_state.gender_filter = gender_selected
    with filter_col2:
        admission_cohort = st.multiselect(
            "Cohort Year",
            options=sorted(df_original["Admission Cohort"].unique().tolist()),
            default=st.session_state.cohort_filter,
            key="cohort_select",
        )
        st.session_state.cohort_filter = admission_cohort

    filtered_df = df_original.copy()
    if gender_selected != "All":
        filtered_df = filtered_df[filtered_df["Gender"] == gender_selected]
    if admission_cohort:
        filtered_df = filtered_df[filtered_df["Admission Cohort"].isin(admission_cohort)]
    df = filtered_df

    # ══════════════════════════════════════════
    # CHART 1 — Radar Chart
    # ══════════════════════════════════════════
    st.markdown("---")
    st.subheader("📊 Indicator 2: Principal Appraisal")
    st.caption(
        "Radar chart comparing average scores across six principal appraisal domains. "
        "A larger shaded area indicates stronger overall performance across all domains."
    )

    categories = [
        "Planning",
        "Instruction",
        "Learning Environment",
        "Professional Practices and Responsibilities",
        "Students with Disabilities",
        "English Language Learners",
    ]
    values = [df[c].mean() for c in categories]

    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name="Appraisal Score",
            line=dict(color=ACCENT_BLUE, width=2.5),
            fillcolor="rgba(88,166,255,0.15)",
            hovertemplate="<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>",
        )
    )
    fig_radar.update_layout(
        polar=dict(
            bgcolor=BG_SURFACE,
            radialaxis=dict(
                visible=True,
                range=[0, max(values) + 0.4],
                tickfont=dict(size=10, family=FONT_FAMILY, color=TEXT_MUTED),
                gridcolor=GRID_COLOR,
                linecolor=BORDER,
            ),
            angularaxis=dict(
                tickfont=dict(size=11, family=FONT_FAMILY, color=TEXT_PRIMARY),
                linecolor=BORDER,
            ),
        ),
        showlegend=False,
        title=dict(
            text="<b>Principal Appraisal — Domain Performance Overview</b>",
            font=dict(family=FONT_FAMILY, size=17, color=TEXT_PRIMARY),
            x=0.03,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, color=TEXT_PRIMARY),
        margin=dict(t=80, b=40),
        height=480,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # ══════════════════════════════════════════
    # CHART 2 — Bar Chart  (traffic-light colors)
    # ══════════════════════════════════════════
    st.markdown("---")
    st.subheader("📈 Average Overall Score by Certification Grade Level")
    st.caption(
        "Bars are color-coded by performance band: "
        "🟢 Satisfactory (< 1.8)  🟡 Developing (1.8 – 2.0)  🔴 Needs Improvement (≥ 2.0). "
        "Dashed lines mark the band boundaries."
    )

    grade_df = (
        df.groupby("Certification Area Grade Level")["Overall"]
        .mean()
        .reset_index()
        .sort_values("Overall")
    )
    grade_df.columns = ["Grade Level", "Average Score"]

    # ── traffic-light coloring ──
    def score_color(v):
        if v >= 2.0:
            return RED
        elif v >= 1.8:
            return YELLOW
        else:
            return GREEN

    bar_colors = [score_color(v) for v in grade_df["Average Score"]]

    fig_bar = go.Figure(
        go.Bar(
            x=grade_df["Grade Level"],
            y=grade_df["Average Score"],
            marker=dict(
                color=bar_colors,
                line=dict(color=BG_MAIN, width=1.5),
                opacity=0.9,
            ),
            text=grade_df["Average Score"].round(2),
            textposition="outside",
            textfont=dict(family=FONT_FAMILY, size=11, color=TEXT_PRIMARY),
            hovertemplate="<b>%{x}</b><br>Avg Score: %{y:.2f}<extra></extra>",
        )
    )
    layout_bar = base_layout(
        "Average Appraisal Score by Certification Grade Level",
        xtitle="Certification Grade Level",
        ytitle="Average Overall Score",
    )
    layout_bar["yaxis"]["range"] = [0, grade_df["Average Score"].max() + 0.45]

    # Band boundary lines
    fig_bar.add_hline(
        y=1.8,
        line=dict(color=YELLOW, dash="dash", width=1.8),
        annotation_text="",
        annotation_position="top left",
        annotation_font=dict(family=FONT_FAMILY, size=10, color=YELLOW),
    )
    fig_bar.add_hline(
        y=2.0,
        line=dict(color=RED, dash="dash", width=1.8),
        annotation_text="",
        annotation_position="top right",
        annotation_font=dict(family=FONT_FAMILY, size=10, color=RED),
    )
    fig_bar.update_layout(**layout_bar, height=430)
    st.plotly_chart(fig_bar, use_container_width=True)

    # ══════════════════════════════════════════
    # CHART 3 — Gauge + Donut  (side by side)
    # ══════════════════════════════════════════
    st.markdown("---")
    overall_avg = round(df["Overall"].mean(), 2)
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎯 Overall Average Score")
        st.caption(
            "Gauge bands: 🟢 Green = Satisfactory (0 – 1.8)  "
            "🟡 Yellow = Developing (1.8 – 2.0)  "
            "🔴 Red = Needs Improvement (2.0 – 2.5). "
            "The needle and blue bar show the current cohort average."
        )

        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=overall_avg,
                number=dict(
                    font=dict(family=FONT_FAMILY, size=52, color=TEXT_PRIMARY),
                    suffix="",
                ),
                title=dict(
                    text="Overall Appraisal Average",
                    font=dict(family=FONT_FAMILY, size=13, color=TEXT_MUTED),
                ),
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis": {
                        "range": [0, 2.5],
                        "tickvals": [0, 0.5, 1.0, 1.5, 1.8, 2.0, 2.5],
                        "ticktext": ["0", "0.5", "1.0", "1.5", "1.8", "2.0", "2.5"],
                        "tickfont": dict(family=FONT_FAMILY, size=10, color=TEXT_MUTED),
                        "tickcolor": BORDER,
                    },
                    "bar": {"color": ACCENT_BLUE, "thickness": 0.22},
                    "bgcolor": BG_SURFACE,
                    "borderwidth": 1,
                    "bordercolor": BORDER,
                    "steps": [
                        {"range": [0.0, 1.8], "color": "#90EE90"},   # Green — satisfactory
                        {"range": [1.8, 2.0], "color": "#FFFF00"},   # Yellow — developing
                        {"range": [2.0, 2.5], "color": "#FF6B6B"},   # Red — needs improvement
                    ],
                    "threshold": {
                        "line": {"color": BG_MAIN, "width": 3},
                        "thickness": 0.85,
                        "value": overall_avg,
                    },
                },
            )
        )

       

        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family=FONT_FAMILY, color=TEXT_PRIMARY),
            height=400,
            margin=dict(t=50, b=30, l=20, r=20),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.subheader("🥧 Score Distribution by Race / Ethnicity")
        st.caption(
            "Donut chart showing average principal appraisal scores proportionally "
            "by demographic group. Hover over each slice for exact values. "
            "The center displays the overall cohort average."
        )

        ethnicity_df = (
            df.groupby("Race/Ethnicity")["Overall"].mean().round(2).reset_index()
        )
        # Dark-friendly vivid palette
        palette = [
            ACCENT_BLUE, ACCENT_TEAL, "#F63228", ACCENT_AMBER,
            "#BC8CFF", "#FF7B72", "#56D364",
        ]

        fig_donut = go.Figure(
            go.Pie(
                labels=ethnicity_df["Race/Ethnicity"],
                values=ethnicity_df["Overall"],
                hole=0.48,
                marker=dict(
                    colors=palette[: len(ethnicity_df)],
                    line=dict(color=BG_MAIN, width=2.5),
                ),
                textinfo="label+percent",
                textfont=dict(family=FONT_FAMILY, size=11, color=TEXT_PRIMARY),
                hovertemplate=(
                    "<b>%{label}</b><br>Avg Score: %{value:.2f}<br>Share: %{percent}<extra></extra>"
                ),
            )
        )
        fig_donut.update_layout(
            title=dict(
                text="<b>Avg Appraisal Score by Race / Ethnicity</b>",
                font=dict(family=FONT_FAMILY, size=15, color=TEXT_PRIMARY),
                x=0.03,
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family=FONT_FAMILY, color=TEXT_PRIMARY),
            legend=dict(
                orientation="v",
                font=dict(family=FONT_FAMILY, size=10, color=TEXT_MUTED),
                bgcolor="rgba(0,0,0,0)",
            ),
            annotations=[
                dict(
                    text=f"<b>{overall_avg}</b><br><span style='font-size:11px'>Overall</span>",
                    x=0.5, y=0.5,
                    font=dict(size=18, family=FONT_FAMILY, color=TEXT_PRIMARY),
                    showarrow=False,
                )
            ],
            height=400,
            margin=dict(t=60, b=20, l=10, r=10),
        )
        st.plotly_chart(fig_donut, use_container_width=True)


# ─────────────────────────────────────────────
# STUDENT GROWTH TAB
# ─────────────────────────────────────────────
def student_growth_tab(df):
    st.subheader("📚 Indicator 3: Student Growth")
    st.caption(
        "Tracks average student growth scores across a teacher's years of experience. "
        "The dashed goal line at 70% is the ASEP program benchmark. "
        "An upward trend indicates improving outcomes as teachers gain experience."
    )

    avg_growth = df["Overall Student Growth Score"].mean()
    delta = avg_growth - 70
    delta_str = f"+{delta:.1f}%" if delta >= 0 else f"{delta:.1f}%"
    st.metric("Avg Student Growth Score", f"{avg_growth:.1f}%", delta=delta_str)

    growth_by_year = (
        df.groupby("Teaching Years")["Overall Student Growth Score"].mean().reset_index()
    )

    fig_line = go.Figure()
    fig_line.add_trace(
        go.Scatter(
            x=growth_by_year["Teaching Years"],
            y=growth_by_year["Overall Student Growth Score"],
            mode="lines+markers",
            name="Avg Growth Score",
            line=dict(color=ACCENT_BLUE, width=3),
            marker=dict(size=9, color=ACCENT_BLUE, line=dict(color=BG_MAIN, width=2)),
            fill="tozeroy",
            fillcolor="rgba(88,166,255,0.08)",
            hovertemplate="<b>Year %{x}</b><br>Avg Growth: %{y:.1f}%<extra></extra>",
        )
    )
    fig_line.add_hline(
        y=70,
        line=dict(color=ACCENT_TEAL, dash="dash", width=2),
        annotation_text="Program Goal (70%)",
        annotation_position="bottom right",
        annotation_font=dict(family=FONT_FAMILY, size=11, color=ACCENT_TEAL),
    )
    layout = base_layout(
        "Average Student Growth Score by Teaching Experience",
        xtitle="Years of Teaching Experience",
        ytitle="Average Student Growth Score (%)",
    )
    layout["yaxis"]["ticksuffix"] = "%"
    fig_line.update_layout(**layout, height=440)
    st.plotly_chart(fig_line, use_container_width=True)


# ─────────────────────────────────────────────
# EXAM PASS RATE TAB
# ─────────────────────────────────────────────
def exam_pass_rate_tab(df):
    st.subheader("🏆 Indicator 1: Certification Exam Pass Rates")
    st.caption(
        "Stacked bars show pass / fail counts per certification exam. "
        "The amber dotted line (right axis) overlays the pass rate % per exam — "
        "compare both volume and success rate at a glance."
    )

    pass_rate = (df["Passing Attempts"].sum() / df["Total Attempts"].sum()) * 100
    st.metric(
        "Overall Pass Rate",
        f"{pass_rate:.1f}%",
        delta=f"{pass_rate - 80:.1f}% vs 80% Target",
    )

    exam_stats = (
        df.groupby("Content Exam")["Outcome"]
        .value_counts()
        .unstack()
        .fillna(0)
        .reset_index()
    )
    outcome_cols = [c for c in exam_stats.columns if c != "Content Exam"]
    color_map = {"Pass": ACCENT_TEAL, "Fail": RED}

    fig_stacked = go.Figure()
    for outcome in outcome_cols:
        fig_stacked.add_trace(
            go.Bar(
                name=outcome,
                x=exam_stats["Content Exam"],
                y=exam_stats[outcome],
                marker_color=color_map.get(outcome, ACCENT_BLUE),
                hovertemplate=f"<b>%{{x}}</b><br>{outcome}: %{{y}}<extra></extra>",
            )
        )

    layout = base_layout(
        "Certification Exam Outcomes by Exam Type",
        xtitle="Certification Exam",
        ytitle="Number of Attempts",
    )
    layout["barmode"] = "stack"
    layout["legend"] = dict(
        title=dict(text="Outcome", font=dict(family=FONT_FAMILY, size=11, color=TEXT_MUTED)),
        font=dict(family=FONT_FAMILY, size=11, color=TEXT_PRIMARY),
        bgcolor="rgba(0,0,0,0)",
    )

    total_per_exam = exam_stats[outcome_cols].sum(axis=1)
    pass_counts = exam_stats.get("Pass", pd.Series([0] * len(exam_stats)))
    pass_pct = (pass_counts / total_per_exam * 100).round(1)

    fig_stacked.add_trace(
        go.Scatter(
            x=exam_stats["Content Exam"],
            y=pass_pct,
            mode="lines+markers+text",
            name="Pass Rate %",
            yaxis="y2",
            line=dict(color=ACCENT_AMBER, width=2.5, dash="dot"),
            marker=dict(size=7, color=ACCENT_AMBER),
            text=pass_pct.astype(str) + "%",
            textposition="top center",
            textfont=dict(family=FONT_FAMILY, size=10, color=ACCENT_AMBER),
            hovertemplate="<b>%{x}</b><br>Pass Rate: %{y}%<extra></extra>",
        )
    )
    fig_stacked.update_layout(
        **layout,
        yaxis2=dict(
            title=dict(
                text="<b>Pass Rate (%)</b>",
                font=dict(family=FONT_FAMILY, size=12, color=TEXT_MUTED),
            ),
            overlaying="y",
            side="right",
            ticksuffix="%",
            gridcolor=GRID_COLOR,
            showgrid=False,
            tickfont=dict(family=FONT_FAMILY, color=TEXT_MUTED),
            linecolor=BORDER,
        ),
        height=440,
    )
    st.plotly_chart(fig_stacked, use_container_width=True)


# ─────────────────────────────────────────────
# DASHBOARD PAGE
# ─────────────────────────────────────────────
def Dashboard():
    st.title("📊 ASEP Metrics Dashboard")
    st.caption(
        "Alternative Student Educator Preparation (ASEP) program metrics — "
        "Certification Pass Rates · Principal Appraisals · Student Growth"
    )

    if not st.session_state.get("uploaded_files"):
        st.warning("Please upload Excel files in the Data Management page first.")
        return

    data = {"principal": None, "growth": None, "pass_rate": None}
    for uploaded_file in st.session_state.uploaded_files:
        new_name, df = process_and_rename_file(uploaded_file)
        if new_name == "principal_survey.xlsx":
            data["principal"] = df
        elif new_name == "student_achievement_of_student_taught_by_beginning_teachers.xlsx":
            data["growth"] = df
        elif new_name == "certification_exam_pass_rate.xlsx":
            data["pass_rate"] = df

    tab1, tab2, tab3 = st.tabs(
        ["🏫 Principal Perceptions", "📈 Student Growth", "🎓 Exam Pass Rates"]
    )

    with tab1:
        if "gender_filter" not in st.session_state:
            st.session_state.gender_filter = "All"
        if "cohort_filter" not in st.session_state:
            st.session_state.cohort_filter = []
        if data["principal"] is not None:
            principal_perceptions(data["principal"])
        else:
            st.info("⚠️ Please upload a Principal Perceptions file first.")

    with tab2:
        if data["growth"] is not None:
            student_growth_tab(data["growth"])
        else:
            st.info("⚠️ Please upload a Student Growth file first.")

    with tab3:
        if data["pass_rate"] is not None:
            exam_pass_rate_tab(data["pass_rate"])
        else:
            st.info("⚠️ Please upload a Certification Pass Rate file first.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="ASEP Metrics Dashboard",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject dark CSS first
    st.markdown(DARK_CSS, unsafe_allow_html=True)

    sidebar_data()
    pg = st.navigation([Data_Management, Dashboard])
    pg.run()


main()