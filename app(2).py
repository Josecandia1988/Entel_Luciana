import io
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Gestión Comercial | Entel y Socios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ENTEL_BLUE = "#0066CC"
ENTEL_DARK = "#003B70"
CYAN = "#00AEEF"
GREEN = "#18A558"
YELLOW = "#F4B400"
RED = "#D93025"
GRAY = "#667085"

SHEETS = [
    "Movil", "VOZ", "RU", "Fibra", "Funnel", "Solicitudes",
    "Equipos", "Seguros", "Accesorios", "Rechazo", "Q Movil",
]


st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(135deg,#F4F8FF 0%,#F8F4FF 48%,#EEFBFF 100%);}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#021C3A 0%,#063B70 100%); min-width:285px;}
    [data-testid="stSidebar"] * {color: white;}
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * {color: #162033;}
    [data-testid="stSidebar"] .stRadio label {padding: .3rem 0;}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
      background:rgba(255,255,255,.07); border:1px dashed rgba(255,255,255,.55);
      border-radius:15px; padding:.75rem;}
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {color:white !important;}
    [data-testid="stSidebar"] button {background:rgba(255,255,255,.14); border-color:rgba(255,255,255,.3);}
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1650px;}
    .hero {background: linear-gradient(110deg,#003B70,#0066CC 62%,#00AEEF); color:white;
           padding:2rem 2.2rem; border-radius:24px; margin-bottom:1.25rem;
           box-shadow:0 14px 34px rgba(0,59,112,.20);}
    .hero h1 {font-size:2.65rem; margin:0 0 .35rem; line-height:1.1;}
    .hero p {margin:0; opacity:.92; font-size:1.2rem;}
    .hero-grid {display:flex; align-items:center; justify-content:space-between; gap:1.5rem;}
    .hero-status {display:flex; gap:1rem; align-items:center; min-width:310px; justify-content:flex-end;}
    .status-box {border-left:1px solid rgba(255,255,255,.35); padding-left:1rem; font-size:.92rem; line-height:1.45;}
    .status-box strong {display:block; font-size:1.02rem;}
    .live-dot {display:inline-block; width:11px; height:11px; background:#20D873; border-radius:50%;
               margin-right:.4rem; box-shadow:0 0 0 6px rgba(32,216,115,.18);}
    .scope {display:inline-block; margin-top:1rem; padding:.48rem .95rem;
            border-radius:999px; background:rgba(255,255,255,.20); font-size:1.05rem; font-weight:800;}
    .kpi {background:linear-gradient(145deg,var(--soft),#FFFFFF 68%); border-radius:21px;
          padding:1.25rem 1.2rem; min-height:178px; border:1px solid rgba(255,255,255,.9);
          border-top:7px solid var(--accent); box-shadow:0 9px 24px rgba(16,44,79,.11);
          transition:transform .18s ease,box-shadow .18s ease;}
    .kpi:hover {transform:translateY(-3px); box-shadow:0 13px 28px rgba(16,44,79,.16);}
    .kpi-title {color:#344054; font-size:.98rem; text-transform:uppercase; font-weight:900;
                letter-spacing:.035em; min-height:48px; line-height:1.25;}
    .kpi-title-row {display:flex; align-items:center; gap:.55rem;}
    .kpi-icon {font-size:1.55rem; line-height:1; color:var(--accent);}
    .kpi-value {font-size:2.25rem; line-height:1.05; font-weight:950; color:#102A43; margin:.35rem 0 .25rem;}
    .kpi-sub {color:#52647A; font-size:.96rem; font-weight:650; line-height:1.4; margin-top:.35rem;}
    .pill {display:inline-block; font-size:.93rem; font-weight:900; padding:.28rem .68rem;
           border-radius:999px; color:white; margin-top:.35rem; box-shadow:0 3px 8px rgba(0,0,0,.12);}
    .progress-track {height:8px; background:#DCE3EC; border-radius:99px; margin:.7rem 0 .15rem; overflow:visible; position:relative;}
    .progress-fill {height:8px; border-radius:99px; background:var(--bar); max-width:100%;}
    .progress-target {position:absolute; left:83.33%; top:-3px; height:14px; border-left:2px dotted #64748B;}
    .section-title {font-size:1.55rem; font-weight:950; color:#003B70; margin:1.3rem 0 .85rem;}
    .notice {background:#EAF5FF; border-left:5px solid #0066CC; color:#12395B;
             padding:.85rem 1rem; border-radius:10px; margin:.7rem 0;}
    div[data-testid="stDataFrame"] {background:white; border-radius:14px; padding:.25rem;}
    .stTabs [data-baseweb="tab-list"] {gap:.4rem;}
    .stTabs [data-baseweb="tab"] {background:white; border-radius:12px 12px 0 0; padding:.8rem 1.2rem; font-size:1.02rem; font-weight:750;}
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {font-size:1rem;}
    .brand-block {padding:.35rem 0 1rem; border-bottom:1px solid rgba(255,255,255,.22); margin-bottom:1rem;}
    .brand-title {font-size:1.65rem; font-weight:900; color:white;}
    .brand-mark {font-size:2.5rem; font-weight:950; color:white; margin-top:.35rem; letter-spacing:-.15rem;}
    .brand-mark span {color:#FF6B21;}
    @media (max-width:900px) {
      .hero h1 {font-size:2rem;} .kpi {min-height:158px;} .kpi-value {font-size:1.85rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def clean_text(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_frame(frame):
    frame = frame.copy()
    frame.columns = [clean_text(c) for c in frame.columns]
    for col in frame.columns:
        if frame[col].dtype == "object":
            frame[col] = frame[col].map(clean_text)
    return frame


@st.cache_data(show_spinner=False, max_entries=4)
def load_workbook(raw):
    book = pd.ExcelFile(io.BytesIO(raw))
    data = {}
    for sheet in SHEETS:
        if sheet not in book.sheet_names:
            data[sheet] = pd.DataFrame()
            continue
        if sheet == "Seguros":
            tmp = pd.read_excel(io.BytesIO(raw), sheet_name=sheet, header=1)
        elif sheet == "Rechazo":
            tmp = pd.read_excel(io.BytesIO(raw), sheet_name=sheet, header=3)
        else:
            tmp = pd.read_excel(io.BytesIO(raw), sheet_name=sheet)
        data[sheet] = clean_frame(tmp.dropna(how="all"))
    return data, book.sheet_names


def find_col(frame, *candidates):
    normalized = {re.sub(r"[^a-z0-9]", "", str(c).lower()): c for c in frame.columns}
    for candidate in candidates:
        key = re.sub(r"[^a-z0-9]", "", candidate.lower())
        if key in normalized:
            return normalized[key]
    return None


def number(value, default=0.0):
    parsed = pd.to_numeric(value, errors="coerce")
    return default if pd.isna(parsed) else float(parsed)


def fmt_int(value):
    return f"{number(value):,.0f}".replace(",", ".")


def fmt_money(value):
    # Equipos y accesorios vienen expresados en millones de pesos.
    return f"${number(value):,.1f} MM".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(value, digits=1):
    return f"{number(value) * 100:.{digits}f}%".replace(".", ",")


def status_color(value):
    value = number(value)
    if value >= 1:
        return GREEN
    if value >= .85:
        return YELLOW
    return RED


def metric_card(title, value, compliance=None, sub="", accent=None, soft=None):
    palette = {
        "Móvil": ("#0066CC", "#E8F2FF"), "Voz": ("#7457D9", "#F0ECFF"),
        "Solicitudes fibra": ("#F59E0B", "#FFF4D8"), "Fibra instalada": ("#00A878", "#E2F8F0"),
        "Mix Solicitudes 2 + Play Full": ("#E548A4", "#FDE9F5"),
        "Equipos": ("#EF5B2A", "#FFF0E9"), "Venta de equipos": ("#EF5B2A", "#FFF0E9"),
        "Accesorios": ("#00AEEF", "#E5F8FF"), "Seguros": ("#18A558", "#E7F7EC"),
    }
    default_accent, default_soft = palette.get(title, ("#0066CC", "#EAF4FF"))
    accent = accent or default_accent
    soft = soft or default_soft
    icons = {
        "Móvil": "▯", "Voz": "☎", "Solicitudes fibra": "⌂", "Fibra instalada": "◉",
        "Mix Solicitudes 2 + Play Full": "♧", "Equipos": "▣", "Venta de equipos": "▣",
        "Accesorios": "◉", "Seguros": "♢", "Conversión fibra": "↗",
    }
    icon = icons.get(title, "◆")
    pill = ""
    progress = '<div class="progress-track"><div class="progress-fill" style="width:0"></div></div>'
    if compliance is not None:
        pill = f'<span class="pill" style="background:{status_color(compliance)}">{fmt_pct(compliance)}</span>'
        progress_width = min(max(number(compliance) / 1.2 * 100, 0), 100)
        progress = (f'<div class="progress-track"><div class="progress-fill" '
                    f'style="width:{progress_width:.1f}%;--bar:{status_color(compliance)}"></div>'
                    f'<span class="progress-target"></span></div>')
    st.markdown(
        f'<div class="kpi" style="--accent:{accent};--soft:{soft}"><div class="kpi-title-row">'
        f'<span class="kpi-icon">{icon}</span><div class="kpi-title">{title}</div></div>'
        f'<div class="kpi-value">{value}</div>{pill}{progress}<div class="kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def cut_date_from_name(filename):
    match = re.search(r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)", filename)
    if not match:
        return "No informada"
    day, month, year = match.groups()
    return f"{day}/{month}/20{year}"


def dimension_columns(frame):
    return {
        "zone": find_col(frame, "NOMBRES ZONA"),
        "partner": find_col(frame, "SOCIO"),
        "store": find_col(frame, "NOMBRE_PDV"),
    }


def valid_partners(data):
    values = set()
    for frame in data.values():
        if frame.empty:
            continue
        col = dimension_columns(frame)["partner"]
        if col:
            values.update(clean_text(v) for v in frame[col] if clean_text(v).upper() != "TOTAL")
    return sorted(v for v in values if v)


def valid_stores(data, partner):
    values = set()
    for frame in data.values():
        if frame.empty:
            continue
        dims = dimension_columns(frame)
        if not dims["partner"] or not dims["store"]:
            continue
        mask = frame[dims["partner"]].astype(str).str.upper().eq(partner.upper())
        stores = frame.loc[mask, dims["store"]]
        values.update(clean_text(v) for v in stores if clean_text(v).upper() != "TOTAL")
    return sorted(v for v in values if v)


def scope_row(frame, level, partner=None, store=None):
    if frame.empty:
        return None
    dims = dimension_columns(frame)
    work = frame.copy()
    if level == "Entel":
        # El consolidado general es la fila cuya primera dimensión es Total.
        if dims["zone"]:
            hit = work[work[dims["zone"]].astype(str).str.upper().eq("TOTAL")]
        else:
            hit = pd.DataFrame()
    elif level == "Socio" and dims["partner"]:
        mask = work[dims["partner"]].astype(str).str.upper().eq(str(partner).upper())
        if dims["store"]:
            mask &= work[dims["store"]].astype(str).str.upper().eq("TOTAL")
        hit = work[mask]
    elif level == "Tienda" and dims["partner"] and dims["store"]:
        mask = work[dims["partner"]].astype(str).str.upper().eq(str(partner).upper())
        mask &= work[dims["store"]].astype(str).str.upper().eq(str(store).upper())
        hit = work[mask]
    else:
        hit = pd.DataFrame()
    return None if hit.empty else hit.iloc[0]


def cell(row, frame, *columns, default=0):
    if row is None:
        return default
    col = find_col(frame, *columns)
    return default if col is None else row.get(col, default)


def comparison_frame(frame, value_col, compliance_col, level, partner=None):
    if frame.empty:
        return pd.DataFrame()
    dims = dimension_columns(frame)
    value = find_col(frame, value_col)
    compliance = find_col(frame, compliance_col)
    if not value:
        return pd.DataFrame()
    if level == "Entel" and dims["partner"]:
        view = frame[frame[dims["partner"]].astype(str).str.upper().ne("TOTAL")].copy()
        if dims["store"]:
            view = view[view[dims["store"]].astype(str).str.upper().eq("TOTAL")]
        label = dims["partner"]
    elif level == "Socio" and dims["partner"] and dims["store"]:
        view = frame[frame[dims["partner"]].astype(str).str.upper().eq(str(partner).upper())].copy()
        view = view[view[dims["store"]].astype(str).str.upper().ne("TOTAL")]
        label = dims["store"]
    else:
        return pd.DataFrame()
    cols = [label, value] + ([compliance] if compliance else [])
    view = view[cols].copy()
    view[value] = pd.to_numeric(view[value], errors="coerce").fillna(0)
    if compliance:
        view[compliance] = pd.to_numeric(view[compliance], errors="coerce").fillna(0)
    return view.drop_duplicates(label).sort_values(value, ascending=False)


def bar_chart(frame, label, value, title, percent=False):
    if frame.empty:
        st.info("No hay desglose disponible para esta selección.")
        return
    plot = frame.sort_values(value).tail(15)
    fig = px.bar(plot, x=value, y=label, orientation="h", text=value, title=title)
    fig.update_traces(marker_color=ENTEL_BLUE, texttemplate="%{text:.1%}" if percent else "%{text:,.0f}", textposition="outside")
    fig.update_layout(height=max(340, len(plot) * 34), margin=dict(l=10, r=30, t=55, b=10),
                      paper_bgcolor="white", plot_bgcolor="white", showlegend=False)
    if percent:
        fig.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig, width="stretch")


def gauge(value, title):
    value = number(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value * 100, number={"suffix": "%", "font": {"size": 34}},
        title={"text": title, "font": {"size": 16}},
        gauge={"axis": {"range": [0, max(130, value * 110)]}, "bar": {"color": status_color(value)},
               "steps": [{"range": [0, 85], "color": "#FDE8E7"},
                         {"range": [85, 100], "color": "#FFF4D6"},
                         {"range": [100, 130], "color": "#E4F5EA"}]},
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=55, b=15), paper_bgcolor="white")
    st.plotly_chart(fig, width="stretch")


def display_table(frame, percent_columns=None, money_columns=None):
    if frame.empty:
        st.info("No hay datos disponibles para esta selección.")
        return
    percent_columns = percent_columns or []
    money_columns = money_columns or []
    formats = {c: "{:.1%}" for c in percent_columns if c in frame.columns}
    formats.update({c: "${:,.1f} MM" for c in money_columns if c in frame.columns})
    st.dataframe(frame.style.format(formats, na_rep="—"), width="stretch", hide_index=True)


def render_overview(data, level, partner, store):
    movil, voz, fibra, equipos = (data[x] for x in ["Movil", "VOZ", "Fibra", "Equipos"])
    accesorios, seguros, funnel = (data[x] for x in ["Accesorios", "Seguros", "Funnel"])
    rows = {name: scope_row(frame, level, partner, store) for name, frame in data.items()}

    if all(rows[x] is None for x in ["Movil", "VOZ", "Fibra", "Equipos"]):
        st.warning("El archivo no contiene información para esta tienda en los indicadores principales.")
        return
    st.markdown('<div class="section-title">Indicadores principales</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    with cols[0]:
        metric_card("Móvil", fmt_int(cell(rows["Movil"], movil, "Q mes")),
                    number(cell(rows["Movil"], movil, "%Cumpl Proy")),
                    f'Meta {fmt_int(cell(rows["Movil"], movil, "Meta mes"))}')
    with cols[1]:
        metric_card("Voz", fmt_int(cell(rows["VOZ"], voz, "Q mes")),
                    number(cell(rows["VOZ"], voz, "%Cumpl Proy")),
                    f'Meta {fmt_int(cell(rows["VOZ"], voz, "Meta mes"))}')
    with cols[2]:
        metric_card("Solicitudes fibra", fmt_int(cell(rows["Solicitudes"], data["Solicitudes"], "Q Mes")),
                    number(cell(rows["Solicitudes"], data["Solicitudes"], "%Cumpl Proy")),
                    f'Meta {fmt_int(cell(rows["Solicitudes"], data["Solicitudes"], "Meta mes"))}')
    with cols[3]:
        metric_card("Fibra instalada", fmt_int(cell(rows["Fibra"], fibra, "Q mes")),
                    number(cell(rows["Fibra"], fibra, "%Cumpl Proy")),
                    f'Meta {fmt_int(cell(rows["Fibra"], fibra, "Meta mes"))}')
    with cols[4]:
        metric_card("Mix Solicitudes 2 + Play Full", "—", sub="KPI preparado para incorporar próximamente")

    st.markdown('<div class="section-title">Resultados complementarios</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]:
        metric_card("Equipos", fmt_money(cell(rows["Equipos"], equipos, "$ mes")),
                    number(cell(rows["Equipos"], equipos, "%Cumpl Proy")),
                    f'Meta {fmt_money(cell(rows["Equipos"], equipos, "Meta mes"))}')
    with cols[1]:
        metric_card("Accesorios", fmt_money(cell(rows["Accesorios"], accesorios, "$ mes")),
                    number(cell(rows["Accesorios"], accesorios, "%Cumpl Proy")),
                    f'Meta {fmt_money(cell(rows["Accesorios"], accesorios, "Meta"))}')
    with cols[2]:
        metric_card("Seguros", fmt_int(cell(rows["Seguros"], seguros, "Q mes")),
                    number(cell(rows["Seguros"], seguros, "% Q Equipos")),
                    f'ATR {fmt_pct(cell(rows["Seguros"], seguros, "ATR"))}')
    with cols[3]:
        metric_card("Conversión fibra", fmt_pct(cell(rows["Funnel"], funnel, "%Conversion")),
                    sub=f'Factibilidad {fmt_pct(cell(rows["Funnel"], funnel, "%Fact"))}',
                    accent="#7A52C7", soft="#F1ECFF")

    st.markdown('<div class="section-title">Cumplimientos proyectados</div>', unsafe_allow_html=True)
    charts = st.columns(3)
    with charts[0]: gauge(cell(rows["Movil"], movil, "%Cumpl Proy"), "Móvil")
    with charts[1]: gauge(cell(rows["Fibra"], fibra, "%Cumpl Proy"), "Fibra")
    with charts[2]: gauge(cell(rows["Equipos"], equipos, "%Cumpl Proy"), "Equipos")


def render_mobile(data, level, partner, store):
    movil, voz, ru = data["Movil"], data["VOZ"], data["RU"]
    rm, rv, rr = (scope_row(f, level, partner, store) for f in [movil, voz, ru])
    cols = st.columns(4)
    with cols[0]: metric_card("Móvil proyectado", fmt_int(cell(rm, movil, "Q mes")), number(cell(rm, movil, "%Cumpl Proy")))
    with cols[1]: metric_card("Voz proyectada", fmt_int(cell(rv, voz, "Q mes")), number(cell(rv, voz, "%Cumpl Proy")))
    with cols[2]: metric_card("Conversión móvil", fmt_pct(cell(rr, ru, "Conversion Movil")))
    with cols[3]: metric_card("Peso portabilidad", fmt_pct(cell(rr, ru, "Peso Porta")))
    cols = st.columns(3)
    with cols[0]: metric_card("Conversión porta", fmt_pct(cell(rr, ru, "Conversion Porta")))
    with cols[1]: metric_card("Conversión 1ras líneas", fmt_pct(cell(rr, ru, "Conversion 1eras")))
    with cols[2]: metric_card("Conversión 2das líneas", fmt_pct(cell(rr, ru, "Conversion 2das")))

    comp = comparison_frame(movil, "Q mes", "%Cumpl Proy", level, partner)
    if not comp.empty:
        dims = dimension_columns(movil)
        label = dims["partner"] if level == "Entel" else dims["store"]
        bar_chart(comp, label, find_col(comp, "Q mes"), "Volumen móvil por socio/tienda")


def render_fiber(data, level, partner, store):
    fibra, solicitudes, funnel = data["Fibra"], data["Solicitudes"], data["Funnel"]
    rf, rs, rfu = (scope_row(f, level, partner, store) for f in [fibra, solicitudes, funnel])
    cols = st.columns(3)
    with cols[0]: metric_card("Instalaciones", fmt_int(cell(rf, fibra, "Q mes")), number(cell(rf, fibra, "%Cumpl Proy")), f'Meta {fmt_int(cell(rf, fibra, "Meta mes"))}')
    with cols[1]: metric_card("Solicitudes", fmt_int(cell(rs, solicitudes, "Q Mes")), number(cell(rs, solicitudes, "%Cumpl Proy")), f'Meta {fmt_int(cell(rs, solicitudes, "Meta mes"))}')
    with cols[2]: metric_card("Conversión fibra", fmt_pct(cell(rfu, funnel, "%Conversion")), sub=f'Factibilidad {fmt_pct(cell(rfu, funnel, "%Fact"))}')
    cols = st.columns(3)
    with cols[0]: metric_card("Llegadas", fmt_int(cell(rfu, funnel, "Llegadas")))
    with cols[1]: metric_card("Validaciones", fmt_int(cell(rfu, funnel, "Validaciones")), sub=f'Tasa {fmt_pct(cell(rfu, funnel, "%Valid"))}')
    with cols[2]: metric_card("Factibles", fmt_int(cell(rfu, funnel, "Factibles")))
    comp = comparison_frame(fibra, "Q mes", "%Cumpl Proy", level, partner)
    if not comp.empty:
        dims = dimension_columns(fibra)
        label = dims["partner"] if level == "Entel" else dims["store"]
        bar_chart(comp, label, find_col(comp, "Q mes"), "Instalaciones de fibra por socio/tienda")


def render_commercial(data, level, partner, store):
    equipos, accesorios, seguros = data["Equipos"], data["Accesorios"], data["Seguros"]
    re, ra, rse = (scope_row(f, level, partner, store) for f in [equipos, accesorios, seguros])
    cols = st.columns(3)
    with cols[0]: metric_card("Equipos", fmt_money(cell(re, equipos, "$ mes")), number(cell(re, equipos, "%Cumpl Proy")), f'Variación M-1 {fmt_pct(cell(re, equipos, "%Var m-1"))}')
    with cols[1]: metric_card("Accesorios", fmt_money(cell(ra, accesorios, "$ mes")), number(cell(ra, accesorios, "%Cumpl Proy")), f'Variación M-1 {fmt_pct(cell(ra, accesorios, "%Var m-1"))}')
    with cols[2]: metric_card("Seguros", fmt_int(cell(rse, seguros, "Q mes")), number(cell(rse, seguros, "% Q Equipos")), f'ATR {fmt_pct(cell(rse, seguros, "ATR"))}')
    comp = comparison_frame(equipos, "$ mes", "%Cumpl Proy", level, partner)
    if not comp.empty:
        dims = dimension_columns(equipos)
        label = dims["partner"] if level == "Entel" else dims["store"]
        bar_chart(comp, label, find_col(comp, "$ mes"), "Venta de equipos (MM$)")


def render_detail(data, level, partner, store):
    rows = []
    definitions = [
        ("Móvil", "Movil", "Q mes", "Meta mes", "%Cumpl Proy", "Q"),
        ("Voz", "VOZ", "Q mes", "Meta mes", "%Cumpl Proy", "Q"),
        ("Fibra instalada", "Fibra", "Q mes", "Meta mes", "%Cumpl Proy", "Q"),
        ("Solicitudes fibra", "Solicitudes", "Q Mes", "Meta mes", "%Cumpl Proy", "Q"),
        ("Equipos", "Equipos", "$ mes", "Meta mes", "%Cumpl Proy", "MM$"),
        ("Accesorios", "Accesorios", "$ mes", "Meta", "%Cumpl Proy", "MM$"),
        ("Seguros", "Seguros", "Q mes", "Meta Mes", "% Q Equipos", "Q"),
    ]
    for metric, sheet, real_col, meta_col, compl_col, unit in definitions:
        frame = data[sheet]
        row = scope_row(frame, level, partner, store)
        rows.append({"Indicador": metric, "Real/Proyección": number(cell(row, frame, real_col)),
                     "Meta": number(cell(row, frame, meta_col)), "Cumplimiento": number(cell(row, frame, compl_col)),
                     "Unidad": unit, "Disponible": "Sí" if row is not None else "No"})
    detail = pd.DataFrame(rows)
    display_table(detail, percent_columns=["Cumplimiento"])
    with st.expander("Ver hojas y campos encontrados en el archivo"):
        for name, frame in data.items():
            st.markdown(f"**{name}:** {len(frame):,} filas · {', '.join(map(str, frame.columns)) if not frame.empty else 'sin datos'}")


st.sidebar.markdown(
    '<div class="brand-block"><div class="brand-title">Gestión Entel</div>'
    '<div class="brand-mark">e<span>›</span></div></div>', unsafe_allow_html=True,
)
st.sidebar.markdown("#### CARGAR PRECIERRE")
uploaded = st.sidebar.file_uploader("Cargar archivo Precierre", type=["xlsx", "xlsm"])

sample_path = Path(__file__).with_name("Precierre 310826.xlsx")
if uploaded is not None:
    raw = uploaded.getvalue()
    source_name = uploaded.name
elif sample_path.exists():
    raw = sample_path.read_bytes()
    source_name = sample_path.name
else:
    st.markdown('<div class="hero"><h1>Gestión Comercial Entel</h1><p>Socios y tiendas</p></div>', unsafe_allow_html=True)
    st.info("Carga el archivo Precierre desde el panel izquierdo para comenzar.")
    st.stop()

try:
    data, workbook_sheets = load_workbook(raw)
except Exception as exc:
    st.error(f"No pude leer el archivo: {exc}")
    st.stop()

partners = valid_partners(data)
level = st.sidebar.radio("Nivel de análisis", ["Entel", "Socio", "Tienda"], horizontal=False)
partner = None
store = None
if level in ["Socio", "Tienda"]:
    partner = st.sidebar.selectbox("Socio", partners)
if level == "Tienda":
    stores = valid_stores(data, partner)
    if stores:
        store = st.sidebar.selectbox("Tienda", stores)
    else:
        st.sidebar.warning("Este socio no trae tiendas desglosadas en el archivo.")

scope_name = "Entel · Total canal" if level == "Entel" else partner
if level == "Tienda":
    scope_name = f"{partner} · {store or 'sin tiendas disponibles'}"
st.markdown(
    f'<div class="hero"><div class="hero-grid"><div><h1>Gestión Comercial Entel</h1>'
    f'<p>Precierre, desempeño y oportunidades</p><span class="scope">▣ &nbsp;{scope_name}</span></div>'
    f'<div class="hero-status"><div class="status-box"><strong>▣ &nbsp;Corte de datos</strong>'
    f'{cut_date_from_name(source_name)}</div><div class="status-box"><strong><span class="live-dot"></span>Actualizado</strong>'
    f'Archivo disponible</div></div></div></div>', unsafe_allow_html=True,
)

if level == "Tienda" and store is None:
    st.markdown('<div class="notice">El Excel no entrega filas de tienda para este socio. Selecciona el nivel Socio para revisar su consolidado.</div>', unsafe_allow_html=True)
    st.stop()

tabs = st.tabs(["▦  Resumen", "☎  Móvil y voz", "◉  Fibra", "▣  Equipos y accesorios", "☷  Detalle"])
with tabs[0]: render_overview(data, level, partner, store)
with tabs[1]: render_mobile(data, level, partner, store)
with tabs[2]: render_fiber(data, level, partner, store)
with tabs[3]: render_commercial(data, level, partner, store)
with tabs[4]: render_detail(data, level, partner, store)

st.sidebar.divider()
st.sidebar.caption(f"Archivo activo: {source_name}")
st.sidebar.caption(f"Hojas leídas: {len(workbook_sheets)}")
