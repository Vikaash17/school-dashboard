import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from numpy.polynomial import Polynomial

st.set_page_config(page_title="School Data Dashboard", layout="wide",
                   initial_sidebar_state="expanded")

# My color scheme - tried a few, settled on this
C1, C2, C3, C4, C5 = "#1a3a5c", "#2d7a9e", "#e8c34a", "#3a8c5a", "#c0392b"
PALETTE = ["#1a3a5c", "#2d7a9e", "#3a8c5a", "#e8c34a", "#c0392b",
           "#8e44ad", "#d35400", "#16a085", "#2c3e50", "#7f8c8d",
           "#2980b9", "#27ae60"]

# Some CSS tweaks - metric cards look better with subtle bg, hiding streamlit chrome
st.markdown(f"""
<style>
    .block-container {{ padding-top: 1.5rem; }}
    h1 {{ font-weight: 600; font-size: 1.6rem; margin-bottom: 0; }}
    h2 {{ font-size: 1.1rem; font-weight: 600; margin: 1rem 0 0.5rem 0; }}
    div[data-testid="stMetric"] {{
        background: rgba(128,128,128,0.06); border-radius: 8px;
        padding: 0.6rem 0.8rem;
    }}
    div[data-testid="stMetric"] label {{ font-size: 0.75rem; font-weight: 500; }}
    div[data-testid="stMetric"] div {{ font-size: 1.3rem; font-weight: 700; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 0.8rem; padding: 0.4rem 1rem; }}
    hr {{ margin: 0.5rem 0; }}
    .dec {{ display: inline-block; width: 4px; height: 1.1rem;
           background: {C3}; margin-right: 6px; vertical-align: -2px; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stAppDeployButton {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────
DATA_PATH = Path(__file__).parent / "Synthetic21_School_Data_2025_2036.xlsx"

@st.cache_data
def load_data():
    return pd.read_excel(DATA_PATH, sheet_name="Sheet1")

df = load_data()

classes = sorted(df["CLASS"].unique())
years = sorted(df["YEAR"].unique())
sections = sorted(df["SECTION"].dropna().unique())
grades_list = ["A1","A2","B1","B2","C1","C2","D","E"]
yr_min, yr_max = int(years[0]), int(years[-1])

# Reset button logic - need to do this before widgets so session_state works
if "reset" not in st.session_state:
    st.session_state.reset = False

if st.session_state.reset:
    st.session_state.yrs = (yr_min, yr_max)
    st.session_state.cls = classes
    st.session_state.sec = sections
    st.session_state.stat = ["ACTIVE","GRADUATED","DROPOUT"]
    st.session_state.gr = []
    st.session_state.pct = (0, 100)
    st.session_state.att = (0, 100)
    st.session_state.ps = False
    st.session_state.reset = False
    st.rerun()

with st.sidebar:
    st.markdown("###  Filters")

    sel_years = st.slider("Year range", yr_min, yr_max,
                          (yr_min, yr_max), key="yrs")

    sel_classes = st.multiselect("Class", classes, default=classes,
                                  key="cls")

    sel_sections = st.multiselect("Section", sections, default=sections,
                                   key="sec")

    show_status = st.multiselect("Status", df["STATUS"].unique(),
                                 default=["ACTIVE", "GRADUATED", "DROPOUT"],
                                 key="stat")

    sel_grades = st.multiselect("Grade", grades_list, default=[], key="gr")

    pct_range = st.slider("Percentage range", 0, 100, (0, 100), key="pct")

    att_range = st.slider("Attendance range", 0, 100, (0, 100), key="att")

    pass_only = st.checkbox("Show only passing students (>=33%)", key="ps")

    if st.button("Reset all filters"):
        st.session_state.reset = True
        st.rerun()

# fdf = filtered with status, fd = filtered without status
# Need fd for enrollment/dropout counts (all statuses matter there)
mask = (df["YEAR"].between(sel_years[0], sel_years[1])
        & df["CLASS"].isin(sel_classes)
        & df["SECTION"].isin(sel_sections)
        & df["STATUS"].isin(show_status)
        & df["PERCENTAGE"].between(pct_range[0], pct_range[1])
        & df["ATTENDANCE_PERCENT"].between(att_range[0], att_range[1]))

if sel_grades:
    mask = mask & df["GRADE"].isin(sel_grades)
if pass_only:
    mask = mask & (df["PERCENTAGE"] >= 33)

fdf = df[mask].copy()

fd = df[(df["YEAR"].between(sel_years[0], sel_years[1]))
        & df["CLASS"].isin(sel_classes)
        & df["SECTION"].isin(sel_sections)
        & df["PERCENTAGE"].between(pct_range[0], pct_range[1])
        & df["ATTENDANCE_PERCENT"].between(att_range[0], att_range[1])]

if sel_grades:
    fd = fd[fd["GRADE"].isin(sel_grades)]
if pass_only:
    fd = fd[fd["PERCENTAGE"] >= 33]

subjects = ["HINDI_TOTAL", "ENGLISH_TOTAL", "SCIENCE_TOTAL",
            "SOCIAL_SCIENCE_TOTAL", "SANSKRIT_URDU_TOTAL", "MATHS_TOTAL"]
subj_lbl = ["Hindi", "English", "Science", "S.Science", "Sanskrit/Urdu", "Maths"]

# Custom plotly theme - keeps all charts looking consistent
tmpl = go.layout.Template()
tmpl.layout = go.Layout(
    font=dict(family="Inter, sans-serif", size=11),
    title=dict(font=dict(size=12), x=0.02),
    xaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False, tickfont=dict(size=10)),
    yaxis=dict(gridcolor="rgba(128,128,128,0.15)", zeroline=False, tickfont=dict(size=10)),
    hoverlabel=dict(font=dict(size=10)),
    legend=dict(font=dict(size=9)),
)

st.markdown(f'<h1><span class="dec"></span>School Performance Dashboard</h1>',
            unsafe_allow_html=True)
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#st.markdown("*For government officials and education administrators*")

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview  &  Trends", "Enrollment  &  Classes",
    "Performance  Analysis", "Student  Flow"])

with tab1:
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Records", f"{len(fdf):,}")
    k2.metric("Active", f"{(fdf['STATUS']=='ACTIVE').sum():,}")
    k3.metric("Dropouts", f"{(fdf['STATUS']=='DROPOUT').sum():,}")
    k4.metric("Graduates", f"{(fdf['STATUS']=='GRADUATED').sum():,}")
    k5.metric("Avg %", f"{fdf['PERCENTAGE'].mean():.1f}%")
    k6.metric("Pass Rate", f"{(fdf['PERCENTAGE']>=33).mean()*100:.1f}%")
    st.divider()
    st.markdown("<h2> Key Trends</h2>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        tr = fd.groupby("YEAR").size().reset_index(name="v")
        fig = px.line(tr, x="YEAR", y="v", markers=True,
                      color_discrete_sequence=[C1])
        fig.update_layout(title="Total Enrollment", template=tmpl,
                          height=260, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c2:
        pt = fdf.groupby("YEAR")["PERCENTAGE"].mean().reset_index()
        fig = px.line(pt, x="YEAR", y="PERCENTAGE", markers=True,
                      color_discrete_sequence=[C2])
        fig.update_layout(title="Avg Percentage", template=tmpl,
                          height=260, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c3:
        dr = fd.groupby("YEAR")["STATUS"].apply(
            lambda x: (x == "DROPOUT").mean() * 100).reset_index()
        dr.columns = ["YEAR", "v"]
        fig = px.line(dr, x="YEAR", y="v", markers=True,
                      color_discrete_sequence=[C5])
        fig.update_layout(title="Dropout Rate %", template=tmpl,
                          height=260, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

    c4, c5, c6 = st.columns(3)
    with c4:
        pr = fdf.groupby("YEAR")["PERCENTAGE"].apply(
            lambda x: (x >= 33).mean() * 100).reset_index()
        pr.columns = ["YEAR", "v"]
        fig = px.line(pr, x="YEAR", y="v", markers=True,
                      color_discrete_sequence=[C3])
        fig.update_layout(title="Pass Rate %", template=tmpl,
                          height=260, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c5:
        at = fdf.groupby("YEAR")["ATTENDANCE_PERCENT"].mean().reset_index()
        fig = px.line(at, x="YEAR", y="ATTENDANCE_PERCENT", markers=True,
                      color_discrete_sequence=["#8e44ad"])
        fig.update_layout(title="Avg Attendance %", template=tmpl,
                          height=260, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c6:
        nt = fd[fd["STATUS"] == "NEW"].groupby("YEAR").size().reset_index(name="v")
        fig = px.bar(nt, x="YEAR", y="v",
                     color_discrete_sequence=[C2])
        fig.update_layout(title="New Admissions", template=tmpl,
                          height=260, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

    st.divider()
    st.markdown("<h2> Forecast (Next 3 Years)</h2>", unsafe_allow_html=True)

    # Simple poly fit - decent enough for trends, don't overthink it
    def forecast(vals):
        x = list(range(len(vals)))
        c = Polynomial.fit(x, vals, 2).convert().coef
        p = Polynomial(c)
        return p(list(range(len(vals), len(vals) + 3)))

    c7, c8 = st.columns(2)
    with c7:
        enr = fd.groupby("YEAR").size().reset_index(name="v")
        fv = forecast(enr["v"].values)
        fy = list(range(int(years[-1]) + 1, int(years[-1]) + 4))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=enr["YEAR"], y=enr["v"],
                                 mode="lines+markers", name="Historical",
                                 line=dict(color=C1, width=2)))
        fig.add_trace(go.Scatter(x=fy, y=fv, mode="lines+markers+text",
                                 name="Forecast", line=dict(dash="dash", color=C5, width=2),
                                 text=[f"{v:.0f}" for v in fv], textposition="top center"))
        fig.update_layout(title="Enrollment Forecast", template=tmpl,
                          height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c8:
        dp = fd.groupby("YEAR")["STATUS"].apply(
            lambda x: (x == "DROPOUT").mean() * 100).reset_index()
        dp.columns = ["YEAR", "v"]
        fv2 = forecast(dp["v"].values)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dp["YEAR"], y=dp["v"],
                                 mode="lines+markers", name="Historical",
                                 line=dict(color=C1, width=2)))
        fig.add_trace(go.Scatter(x=fy, y=fv2, mode="lines+markers+text",
                                 name="Forecast", line=dict(dash="dash", color=C4, width=2),
                                 text=[f"{v:.1f}%" for v in fv2], textposition="bottom center"))
        fig.update_layout(title="Dropout Rate Forecast", template=tmpl,
                          height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h2>Enrollment Heatmap</h2>", unsafe_allow_html=True)
        ht = fd.pivot_table(index="CLASS", columns="YEAR",
                            values="STUDENT_ID", aggfunc="count", fill_value=0)
        fig = px.imshow(ht.values, x=ht.columns.astype(str), y=ht.index.astype(str),
                        text_auto=True, aspect="auto", color_continuous_scale="Blues",
                        labels={"x": "", "y": "", "color": ""})
        fig.update_layout(template=tmpl, height=360,
                          margin=dict(l=0, r=0, t=0, b=0))
        fig.update_xaxes(tickangle=0)
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c2:
        st.markdown("<h2>Class Strength</h2>", unsafe_allow_html=True)
        ly = fd["YEAR"].max()
        lyd = fd[fd["YEAR"] == ly].groupby("CLASS").size().reset_index(name="v")
        fig = px.bar(lyd, x="CLASS", y="v", text_auto=True,
                     color="v", color_continuous_scale="Blues",
                     labels={"v": "Students"})
        fig.update_layout(title=f"Student count ({ly})", template=tmpl,
                          height=360, margin=dict(l=0, r=0, t=30, b=0))
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    st.divider()

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<h2>Section Performance</h2>", unsafe_allow_html=True)
        sp = fdf.groupby(["YEAR", "SECTION"])["PERCENTAGE"].mean().reset_index()
        fig = px.line(sp, x="YEAR", y="PERCENTAGE", color="SECTION", markers=True,
                      color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=300,
                          margin=dict(l=0, r=0, t=0, b=0))
        fig.update_xaxes(tickangle=0)
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c4:
        st.markdown("<h2>Class-wise Avg %</h2>", unsafe_allow_html=True)
        cp = fdf.groupby(["YEAR", "CLASS"])["PERCENTAGE"].mean().reset_index()
        fig = px.line(cp, x="YEAR", y="PERCENTAGE", color="CLASS", markers=True,
                      color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=300,
                          margin=dict(l=0, r=0, t=0, b=0))
        fig.update_xaxes(tickangle=0)
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    st.divider()

    st.markdown("<h2>Pass / Fail Breakdown</h2>", unsafe_allow_html=True)
    c5, c6 = st.columns(2)
    with c5:
        cp2 = fdf.groupby(["YEAR", "CLASS"])["PERCENTAGE"].apply(
            lambda x: (x >= 33).mean() * 100).reset_index()
        cp2.columns = ["YEAR", "CLASS", "v"]
        fig = px.line(cp2, x="YEAR", y="v", color="CLASS", markers=True,
                      title="Pass Rate by Class", labels={"v": "%"},
                      color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=300,
                          margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c6:
        cf = fdf.groupby(["YEAR", "CLASS"]).apply(
            lambda x: (x["PERCENTAGE"] < 33).sum()).reset_index()
        cf.columns = ["YEAR", "CLASS", "v"]
        fig = px.bar(cf, x="YEAR", y="v", color="CLASS", barmode="group",
                     title="Failures by Class", labels={"v": "Count"},
                     color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=300,
                          margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h2>Subject Averages</h2>", unsafe_allow_html=True)
        sj = fdf.groupby("YEAR")[subjects].mean().round(1).reset_index()
        sjl = sj.melt(id_vars="YEAR", var_name="s", value_name="m")
        sjl["s"] = sjl["s"].map(dict(zip(subjects, subj_lbl)))
        fig = px.line(sjl, x="YEAR", y="m", color="s", markers=True,
                      color_discrete_sequence=PALETTE,
                      labels={"m": "Avg Marks", "s": ""})
        fig.update_layout(template=tmpl, height=340,
                          margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c2:
        st.markdown("<h2>Grade Distribution</h2>", unsafe_allow_html=True)
        gc = fdf.groupby(["YEAR", "GRADE"]).size().reset_index(name="Count")
        fig = px.bar(gc, x="YEAR", y="Count", color="GRADE", barmode="stack",
                     color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=340,
                          margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    st.divider()

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<h2>Marks Spread by Subject</h2>", unsafe_allow_html=True)
        sm = fdf[subjects].melt(var_name="s", value_name="m")
        sm["s"] = sm["s"].map(dict(zip(subjects, subj_lbl)))
        fig = px.box(sm, x="s", y="m", color="s", notched=True,
                     color_discrete_sequence=PALETTE, labels={"m": "", "s": ""})
        fig.update_layout(template=tmpl, height=340,
                          margin=dict(l=0, r=0, t=0, b=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c4:
        st.markdown("<h2>Overall Grades</h2>", unsafe_allow_html=True)
        gp = fdf["GRADE"].value_counts().reset_index()
        gp.columns = ["GRADE", "Count"]
        fig = px.pie(gp, values="Count", names="GRADE",
                     color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=340,
                          margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    st.divider()

    st.markdown("<h2>Attendance vs Performance</h2>", unsafe_allow_html=True)
    c5, c6 = st.columns([2, 1])
    with c5:
        sc = fdf[fdf["STATUS"] == "ACTIVE"].copy()
        if len(sc) > 1500:
            sc = sc.sample(1500, random_state=42)
        fig = px.scatter(sc, x="ATTENDANCE_PERCENT", y="PERCENTAGE",
                         color="CLASS", size="OVERALL_TOTAL",
                         hover_data=["STUDENT_ID", "GRADE"],
                         trendline="lowess",
                         color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=360,
                          margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c6:
        corr = sc["ATTENDANCE_PERCENT"].corr(sc["PERCENTAGE"])
        st.metric("Correlation", f"{corr:.2f}")

with tab4:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h2>Status Breakdown</h2>", unsafe_allow_html=True)
        sc2 = fdf["STATUS"].value_counts().reset_index()
        sc2.columns = ["STATUS", "Count"]
        fig = px.pie(sc2, values="Count", names="STATUS", hole=0.4,
                     color="STATUS",
                     color_discrete_map={"ACTIVE": C4, "DROPOUT": C5,
                                         "GRADUATED": C2, "NEW": C3,
                                         "TRANSFER": "#8e44ad"})
        fig.update_layout(template=tmpl, height=340,
                          margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c2:
        st.markdown("<h2>Dropouts & Graduates</h2>", unsafe_allow_html=True)
        tg = fd.groupby("YEAR").agg(
            Dropouts=("STATUS", lambda x: (x=="DROPOUT").sum()),
            Graduates=("STATUS", lambda x: (x=="GRADUATED").sum())).reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tg["YEAR"], y=tg["Dropouts"],
                                 mode="lines+markers", name="Dropouts",
                                 line=dict(color=C5, width=2)))
        fig.add_trace(go.Scatter(x=tg["YEAR"], y=tg["Graduates"],
                                 mode="lines+markers", name="Graduates",
                                 line=dict(color=C2, width=2)))
        fig.update_layout(template=tmpl, height=340,
                          margin=dict(l=0, r=0, t=0, b=0),
                          legend=dict(orientation="h", y=1.05, x=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    st.divider()

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<h2>Dropouts by Class</h2>", unsafe_allow_html=True)
        dc = fd[fd["STATUS"]=="DROPOUT"].groupby(["YEAR", "CLASS"]).size().reset_index(name="v")
        fig = px.bar(dc, x="YEAR", y="v", color="CLASS", barmode="group",
                     title="Which classes lose students?",
                     labels={"v": "Dropouts"},
                     color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=300,
                          margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    with c4:
        st.markdown("<h2>Transfers by Class</h2>", unsafe_allow_html=True)
        tc = fd[fd["STATUS"]=="TRANSFER"].groupby(["YEAR", "CLASS"]).size().reset_index(name="v")
        fig = px.bar(tc, x="YEAR", y="v", color="CLASS", barmode="group",
                     title="Incoming transfers",
                     labels={"v": "Transfers"},
                     color_discrete_sequence=PALETTE)
        fig.update_layout(template=tmpl, height=300,
                          margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))
    st.divider()

    st.markdown("<h2> Cohort Flow</h2>", unsafe_allow_html=True)
    st.markdown("Pick a starting class & year to follow students over time.")
    cx1, cx2 = st.columns([1, 3])
    with cx1:
        cc = st.selectbox("Starting class", classes, index=0)
        cy = st.selectbox("Starting year", years, index=0)
    with cx2:
        ids = fd[(fd["CLASS"]==cc) & (fd["YEAR"]==cy)]["STUDENT_ID"].unique()
        cd = fd[fd["STUDENT_ID"].isin(ids)]
        fl = cd.groupby(["YEAR", "STATUS"]).size().reset_index(name="Count")
        fig = px.area(fl, x="YEAR", y="Count", color="STATUS",
                      title=f"Class {cc} starting {cy}",
                      color_discrete_map={"ACTIVE": C4, "DROPOUT": C5,
                                          "GRADUATED": C2, "NEW": C3,
                                          "TRANSFER": "#8e44ad"})
        fig.update_layout(template=tmpl, height=340,
                          margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False))

st.divider()
st.markdown(f"<p style='opacity:0.6;font-size:0.75rem;'>"
            f"Years {years[0]}–{years[-1]} &nbsp;|&nbsp; "
            f"{len(df):,} records &nbsp;|&nbsp; "
            f"Synthetic21_School_Data_2025_2036.xlsx</p>",
            unsafe_allow_html=True)
