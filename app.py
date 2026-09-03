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
    .stApp {background: #F5F8FC;}
    [data-testid="stSidebar"] {background: linear-gradient(180deg,#003B70,#0066CC);}
    [data-testid="stSidebar"] * {color: white;}
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * {color: #162033;}
    [data-testid="stSidebar"] .stRadio label {padding: .3rem 0;}
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1500px;}
    .hero {background: linear-gradient(110deg,#003B70,#0066CC 62%,#00AEEF); color:white;
           padding:1.5rem 1.8rem; border-radius:20px; margin-bottom:1rem;
           box-shadow:0 10px 28px rgba(0,59,112,.16);}
    .hero h1 {font-size:2rem; margin:0 0 .25rem;}
    .hero p {margin:0; opacity:.9; font-size:1rem;}
    .scope {display:inline-block; margin-top:.8rem; padding:.35rem .75rem;
            border-radius:999px; background:rgba(255,255,255,.18); font-weight:700;}
    .kpi {background:white; border-radius:16px; padding:1rem 1.05rem; min-height:142px;
          border:1px solid #E5EAF1; box-shadow:0 5px 18px rgba(16,44,79,.06);}
    .kpi-title {color:#667085; font-size:.82rem; text-transform:uppercase; font-weight:800;
                letter-spacing:.04em; min-height:38px;}
    .kpi-value {font-size:1.75rem; font-weight:900; color:#162033; margin:.2rem 0;}
    .kpi-sub {color:#667085; font-size:.82rem; line-height:1.35;}
    .pill {display:inline-block; font-size:.78rem; font-weight:800; padding:.18rem .5rem;
           border-radius:999px; color:white; margin-top:.35rem;}
    .section-title {font-size:1.18rem; font-weight:900; color:#003B70; margin:1rem 0 .7rem;}
    .notice {background:#EAF5FF; border-left:5px solid #0066CC; color:#12395B;
             padding:.85rem 1rem; border-radius:10px; margin:.7rem 0;}
    div[data-testid="stDataFrame"] {background:white; border-radius:14px; padding:.25rem;}
    .stTabs [data-baseweb="tab-list"] {gap:.4rem;}
    .stTabs [data-baseweb="tab"] {background:white; border-radius:10px 10px 0 0; padding:.65rem 1rem;}
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


def metric_card(title, value, compliance=None, sub=""):
    pill = ""
    if compliance is not None:
        pill = f'<span class="pill" style="background:{status_color(compliance)}">{fmt_pct(compliance)}</span>'
    st.markdown(
        f'<div class="kpi"><div class="kpi-title">{title}</div>'
        f'<div class="kpi-value">{value}</div>{pill}<div class="kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


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
    st.markdown('<div class="section-title">Resultado general</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    with cols[0]:
        metric_card("Móvil", fmt_int(cell(rows["Movil"], movil, "Q mes")),
                    number(cell(rows["Movil"], movil, "%Cumpl Proy")),
                    f'Meta {fmt_int(cell(rows["Movil"], movil, "Meta mes"))}')
    with cols[1]:
        metric_card("Voz", fmt_int(cell(rows["VOZ"], voz, "Q mes")),
                    number(cell(rows["VOZ"], voz, "%Cumpl Proy")),
                    f'Meta {fmt_int(cell(rows["VOZ"], voz, "Meta mes"))}')
    with cols[2]:
        metric_card("Fibra instalada", fmt_int(cell(rows["Fibra"], fibra, "Q mes")),
                    number(cell(rows["Fibra"], fibra, "%Cumpl Proy")),
                    f'Meta {fmt_int(cell(rows["Fibra"], fibra, "Meta mes"))}')
    with cols[3]:
        metric_card("Venta de equipos", fmt_money(cell(rows["Equipos"], equipos, "$ mes")),
                    number(cell(rows["Equipos"], equipos, "%Cumpl Proy")),
                    f'Meta {fmt_money(cell(rows["Equipos"], equipos, "Meta mes"))}')

    cols = st.columns(4)
    with cols[0]:
        metric_card("Solicitudes fibra", fmt_int(cell(rows["Solicitudes"], data["Solicitudes"], "Q Mes")),
                    number(cell(rows["Solicitudes"], data["Solicitudes"], "%Cumpl Proy")),
                    f'Meta {fmt_int(cell(rows["Solicitudes"], data["Solicitudes"], "Meta mes"))}')
    with cols[1]:
        metric_card("Tasa de instalación", fmt_pct(cell(rows["Funnel"], funnel, "%Tasa instalacion")),
                    sub=f'Conversión {fmt_pct(cell(rows["Funnel"], funnel, "%Conversion"))}')
    with cols[2]:
        metric_card("Seguros", fmt_int(cell(rows["Seguros"], seguros, "Q mes")),
                    number(cell(rows["Seguros"], seguros, "% Q Equipos")),
                    f'ATR {fmt_pct(cell(rows["Seguros"], seguros, "ATR"))}')
    with cols[3]:
        metric_card("Accesorios", fmt_money(cell(rows["Accesorios"], accesorios, "$ mes")),
                    number(cell(rows["Accesorios"], accesorios, "%Cumpl Proy")),
                    f'Meta {fmt_money(cell(rows["Accesorios"], accesorios, "Meta"))}')

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
    cols = st.columns(4)
    with cols[0]: metric_card("Instalaciones", fmt_int(cell(rf, fibra, "Q mes")), number(cell(rf, fibra, "%Cumpl Proy")), f'Meta {fmt_int(cell(rf, fibra, "Meta mes"))}')
    with cols[1]: metric_card("Solicitudes", fmt_int(cell(rs, solicitudes, "Q Mes")), number(cell(rs, solicitudes, "%Cumpl Proy")), f'Meta {fmt_int(cell(rs, solicitudes, "Meta mes"))}')
    with cols[2]: metric_card("Tasa instalación", fmt_pct(cell(rfu, funnel, "%Tasa instalacion")))
    with cols[3]: metric_card("Conversión fibra", fmt_pct(cell(rfu, funnel, "%Conversion")), sub=f'Factibilidad {fmt_pct(cell(rfu, funnel, "%Fact"))}')
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


st.sidebar.markdown("## 📊 Gestión Entel")
st.sidebar.caption("Dashboard de socios y tiendas")
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
    f'<div class="hero"><h1>Gestión Comercial Entel</h1><p>Precierre, desempeño y oportunidades</p>'
    f'<span class="scope">{scope_name}</span></div>', unsafe_allow_html=True,
)
st.caption(f"Fuente activa: {source_name}")

if level == "Tienda" and store is None:
    st.markdown('<div class="notice">El Excel no entrega filas de tienda para este socio. Selecciona el nivel Socio para revisar su consolidado.</div>', unsafe_allow_html=True)
    st.stop()

tabs = st.tabs(["Resumen", "Móvil y voz", "Fibra", "Equipos y accesorios", "Detalle"])
with tabs[0]: render_overview(data, level, partner, store)
with tabs[1]: render_mobile(data, level, partner, store)
with tabs[2]: render_fiber(data, level, partner, store)
with tabs[3]: render_commercial(data, level, partner, store)
with tabs[4]: render_detail(data, level, partner, store)

st.sidebar.divider()
st.sidebar.caption(f"Archivo activo: {source_name}")
st.sidebar.caption(f"Hojas leídas: {len(workbook_sheets)}")
