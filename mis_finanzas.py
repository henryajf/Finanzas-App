import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.graph_objects as go
import math
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, timedelta

# ─────────────────────────────────────────────
# 1. CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Finanzas AR",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 2. SESSION STATE
# ─────────────────────────────────────────────
if "screen" not in st.session_state:
    st.session_state.screen = "inicio"

# ─────────────────────────────────────────────
# 3. TEMA — OSCURO FIJO
# ─────────────────────────────────────────────
BG      = "#0a0a0a"
SURFACE = "#131313"
SURF2   = "#1a1a1a"
BORDER  = "rgba(255,255,255,0.07)"
BORDER2 = "rgba(255,255,255,0.04)"
TEXT    = "#f0f0f0"
MUTED   = "#444444"
MUTED2  = "#777777"
SHADOW  = "0 2px 20px rgba(0,0,0,.7)"
PLOTBG  = "rgba(0,0,0,0)"
ACCENT  = "#009ee3"
GREEN   = "#00c853"
RED     = "#f23d4f"
ORANGE  = "#ff9c00"
YELLOW  = "#fbbf24"

# Colores por emoji de categoría
CAT_COLORS = {
    "⚡": "#009ee3", "🔌": "#009ee3",
    "🏠": "#00a650", "🏡": "#00a650",
    "🛒": "#22c55e", "🍔": "#ef4444",
    "🚗": "#ff9c00", "🚌": "#ff9c00",
    "💳": "#a855f7", "📺": "#ec4899",
    "📈": "#0ea5e9", "🏥": "#14b8a6",
    "🎭": "#f59e0b", "👪": "#8b5cf6",
    "🏋": "#22d3ee", "✈": "#60a5fa",
    "🔘": "#6b7280",
}

def cat_color(cat):
    for emoji, color in CAT_COLORS.items():
        if emoji in str(cat):
            return color
    return "#6b7280"

PALETTE = [
    "#009ee3","#00a650","#a855f7","#ec4899","#ff9c00",
    "#f59e0b","#14b8a6","#0ea5e9","#ef4444","#8b5cf6","#6b7280","#34d399",
]

# ─────────────────────────────────────────────
# 4. SVG ÍCONOS MINIMALISTAS POR CATEGORÍA
# ─────────────────────────────────────────────
def svg_icon(cat: str, color: str, size: int = 22) -> str:
    """Devuelve un SVG minimalista según el emoji de la categoría."""
    c = str(cat)
    s = size
    stroke = "none"
    fill   = "white"

    if "⚡" in c or "🔌" in c:
        path = f'<polygon points="{s*0.6},{s*0.05} {s*0.3},{s*0.52} {s*0.52},{s*0.52} {s*0.4},{s*0.95} {s*0.7},{s*0.45} {s*0.48},{s*0.45}" fill="white"/>'
    elif "🏠" in c or "🏡" in c:
        path = (
            f'<polygon points="{s*0.5},{s*0.1} {s*0.88},{s*0.45} {s*0.78},{s*0.45} {s*0.78},{s*0.88} {s*0.22},{s*0.88} {s*0.22},{s*0.45} {s*0.12},{s*0.45}" fill="white"/>'
            f'<rect x="{s*0.38}" y="{s*0.58}" width="{s*0.24}" height="{s*0.3}" rx="{s*0.03}" fill="{color}" opacity="0.6"/>'
        )
    elif "🛒" in c:
        path = (
            f'<path d="M{s*.1},{s*.18} L{s*.22},{s*.18} L{s*.35},{s*.65} L{s*.8},{s*.65} L{s*.9},{s*.3} L{s*.3},{s*.3}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{s*.38}" cy="{s*.8}" r="{s*.07}" fill="white"/>'
            f'<circle cx="{s*.72}" cy="{s*.8}" r="{s*.07}" fill="white"/>'
        )
    elif "💳" in c:
        path = (
            f'<rect x="{s*.1}" y="{s*.25}" width="{s*.8}" height="{s*.5}" rx="{s*.08}" fill="white" opacity="0.9"/>'
            f'<rect x="{s*.1}" y="{s*.38}" width="{s*.8}" height="{s*.12}" fill="{color}" opacity="0.5"/>'
            f'<rect x="{s*.16}" y="{s*.58}" width="{s*.2}" height="{s*.08}" rx="{s*.03}" fill="{color}" opacity="0.7"/>'
        )
    elif "📺" in c:
        path = (
            f'<rect x="{s*.1}" y="{s*.15}" width="{s*.8}" height="{s*.55}" rx="{s*.07}" fill="white" opacity="0.9"/>'
            f'<rect x="{s*.18}" y="{s*.23}" width="{s*.64}" height="{s*.39}" rx="{s*.04}" fill="{color}" opacity="0.6"/>'
            f'<polygon points="{s*.4},{s*.35} {s*.4},{s*.52} {s*.62},{s*.435}" fill="white"/>'
            f'<rect x="{s*.38}" y="{s*.74}" width="{s*.24}" height="{s*.08}" rx="{s*.03}" fill="white" opacity="0.5"/>'
        )
    elif "🚗" in c or "🚌" in c:
        path = (
            f'<rect x="{s*.08}" y="{s*.42}" width="{s*.84}" height="{s*.3}" rx="{s*.07}" fill="white" opacity="0.9"/>'
            f'<path d="M{s*.22},{s*.42} L{s*.32},{s*.22} L{s*.68},{s*.22} L{s*.78},{s*.42}" fill="white" opacity="0.9"/>'
            f'<circle cx="{s*.27}" cy="{s*.76}" r="{s*.1}" fill="{color}" opacity="0.8"/>'
            f'<circle cx="{s*.27}" cy="{s*.76}" r="{s*.05}" fill="white"/>'
            f'<circle cx="{s*.73}" cy="{s*.76}" r="{s*.1}" fill="{color}" opacity="0.8"/>'
            f'<circle cx="{s*.73}" cy="{s*.76}" r="{s*.05}" fill="white"/>'
        )
    elif "🏥" in c:
        path = (
            f'<rect x="{s*.38}" y="{s*.12}" width="{s*.24}" height="{s*.76}" rx="{s*.06}" fill="white"/>'
            f'<rect x="{s*.12}" y="{s*.38}" width="{s*.76}" height="{s*.24}" rx="{s*.06}" fill="white"/>'
        )
    elif "📈" in c:
        path = (
            f'<polyline points="{s*.1},{s*.75} {s*.32},{s*.5} {s*.52},{s*.62} {s*.72},{s*.28} {s*.9},{s*.35}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<polyline points="{s*.72},{s*.18} {s*.9},{s*.18} {s*.9},{s*.35}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    elif "🎭" in c:
        path = f'<polygon points="{s*.5},{s*.1} {s*.61},{s*.38} {s*.92},{s*.38} {s*.68},{s*.56} {s*.77},{s*.85} {s*.5},{s*.67} {s*.23},{s*.85} {s*.32},{s*.56} {s*.08},{s*.38} {s*.39},{s*.38}" fill="white"/>'
    elif "👪" in c:
        path = (
            f'<circle cx="{s*.35}" cy="{s*.28}" r="{s*.13}" fill="white"/>'
            f'<circle cx="{s*.65}" cy="{s*.28}" r="{s*.13}" fill="white"/>'
            f'<path d="M{s*.1},{s*.82} Q{s*.1},{s*.5} {s*.35},{s*.5} Q{s*.6},{s*.5} {s*.6},{s*.82}" fill="white"/>'
            f'<path d="M{s*.4},{s*.82} Q{s*.4},{s*.5} {s*.65},{s*.5} Q{s*.9},{s*.5} {s*.9},{s*.82}" fill="white"/>'
        )
    elif "🍔" in c:
        path = (
            f'<rect x="{s*.28}" y="{s*.12}" width="{s*.08}" height="{s*.76}" rx="{s*.04}" fill="white"/>'
            f'<path d="M{s*.24},{s*.12} Q{s*.2},{s*.35} {s*.36},{s*.38} Q{s*.52},{s*.35} {s*.48},{s*.12}" fill="white"/>'
            f'<rect x="{s*.62}" y="{s*.12}" width="{s*.1}" height="{s*.4}" rx="{s*.04}" fill="white"/>'
            f'<rect x="{s*.60}" y="{s*.48}" width="{s*.14}" height="{s*.4}" rx="{s*.06}" fill="white"/>'
        )
    else:
        path = (
            f'<circle cx="{s*.5}" cy="{s*.4}" r="{s*.18}" fill="white" opacity="0.9"/>'
            f'<rect x="{s*.44}" y="{s*.62}" width="{s*.12}" height="{s*.26}" rx="{s*.05}" fill="white" opacity="0.9"/>'
        )

    return f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">{path}</svg>'


# ─────────────────────────────────────────────
# 5. CSS GLOBAL
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {{
  --bg:      {BG};
  --surface: {SURFACE};
  --surf2:   {SURF2};
  --border:  {BORDER};
  --text:    {TEXT};
  --muted:   {MUTED};
  --muted2:  {MUTED2};
  --accent:  {ACCENT};
  --green:   {GREEN};
  --red:     {RED};
  --orange:  {ORANGE};
  --shadow:  {SHADOW};
  --r:       16px;
}}

html, body, [class*="css"], .stApp {{
  font-family: 'Plus Jakarta Sans','Helvetica Neue',sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}}
* {{ box-sizing: border-box; }}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {{ display: none !important; }}

.block-container {{ padding: 0 !important; max-width: 100% !important; }}

/* ── WRAPPER ── */
.wrap {{
  max-width: 1060px;
  margin: 0 auto;
  padding: 0 22px 48px;
}}

/* ── HEADER ── */
.hdr {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 22px 0 16px;
  border-bottom: 1px solid var(--border);
  position: relative; overflow: hidden;
}}
.hdr-brand {{
  font-size: 22px; font-weight: 800; color: var(--text);
  letter-spacing: -.03em; position: relative; z-index: 2;
}}
.hdr-brand span {{ color: var(--accent); }}
.hdr-date {{
  font-size: 11px; color: var(--muted2); font-weight: 500;
  margin-top: 3px; position: relative; z-index: 2;
}}
.dolar-chip {{
  background: rgba(0,158,227,.08);
  border: 1px solid rgba(0,158,227,.2);
  border-radius: 12px; padding: 8px 16px; text-align: center;
  position: relative; z-index: 2;
}}
.dolar-lbl {{ font-size: 9px; color: var(--muted2); letter-spacing: .08em;
  text-transform: uppercase; font-weight: 700; }}
.dolar-val {{ font-size: 18px; font-weight: 800; color: var(--accent); margin-top: 1px; }}

/* ── NAV — 2 botones full width siempre ── */
.nav-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 14px 0 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 22px;
}}
/* Forzar botones Streamlit a ocupar 100% dentro del grid */
.nav-grid .stButton,
.nav-grid .stButton > button {{
  width: 100% !important;
  display: block !important;
}}
.stButton > button[kind="primary"] {{
  background: {ACCENT} !important; color: #fff !important;
  border: none !important; border-radius: 12px !important;
  padding: 12px 16px !important; width: 100% !important;
  font-family: 'Plus Jakarta Sans',sans-serif !important;
  font-size: 14px !important; font-weight: 700 !important;
  box-shadow: 0 4px 14px rgba(0,158,227,.3) !important;
  transition: all .2s !important; letter-spacing: .01em !important;
}}
.stButton > button[kind="primary"]:hover {{
  background: #007fc0 !important; transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(0,158,227,.4) !important;
}}
.stButton > button[kind="secondary"] {{
  background: var(--surface) !important; color: var(--muted2) !important;
  border: 1px solid var(--border) !important; border-radius: 12px !important;
  padding: 12px 16px !important; width: 100% !important;
  font-family: 'Plus Jakarta Sans',sans-serif !important;
  font-size: 14px !important; font-weight: 700 !important;
  transition: all .2s !important;
}}
.stButton > button[kind="secondary"]:hover {{
  border-color: {ACCENT} !important; color: {ACCENT} !important;
}}

/* ── GRID MÉTRICAS ── */
.metrics {{
  display: grid; grid-template-columns: repeat(4,1fr); gap: 12px;
  margin-bottom: 20px;
}}
.mcard {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r); padding: 18px 20px;
  position: relative; overflow: hidden;
}}
.mcard::before {{
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  border-radius: var(--r) var(--r) 0 0;
}}
.mc-a::before {{ background:linear-gradient(90deg,{ACCENT},transparent); }}
.mc-g::before {{ background:linear-gradient(90deg,{GREEN},transparent); }}
.mc-r::before {{ background:linear-gradient(90deg,{RED},transparent); }}
.mc-o::before {{ background:linear-gradient(90deg,{ORANGE},transparent); }}
.mlbl {{ font-size:9px; font-weight:700; color:var(--muted);
  letter-spacing:.1em; text-transform:uppercase; margin-bottom:10px; }}
.mval {{ font-size:23px; font-weight:800; color:var(--text);
  letter-spacing:-.02em; line-height:1; }}
.msub {{ font-size:11px; color:var(--muted2); margin-top:5px; }}
.mpct {{ font-size:28px; font-weight:800; color:{ACCENT}; }}
.pbar {{ height:4px; background:rgba(255,255,255,.06);
  border-radius:4px; overflow:hidden; margin-top:10px; }}
.pfill {{ height:100%; border-radius:4px;
  background:linear-gradient(90deg,{ACCENT},#00c9ff); }}

/* ── ALERTAS ── */
.alert {{
  padding: 12px 16px; border-radius: 12px; font-size: 13px;
  font-weight: 500; margin-bottom: 10px;
  display: flex; align-items: flex-start; gap: 10px; line-height: 1.5;
}}
.alert-r {{ background:rgba(242,61,79,.08); border:1px solid rgba(242,61,79,.2); color:#ff8a94; }}
.alert-o {{ background:rgba(255,156,0,.08);  border:1px solid rgba(255,156,0,.2);  color:#ffc066; }}

/* ── CARD GENÉRICA ── */
.card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r); margin-bottom: 16px; overflow: hidden;
}}
.card-pad {{ padding: 20px; }}
.ctitle {{
  font-size: 10px; font-weight: 700; color: var(--muted);
  letter-spacing: .1em; text-transform: uppercase; margin-bottom: 14px;
}}

/* ── HEADER DE SECCIÓN (agrupado por cat) ── */
.sec-hdr {{
  display: flex; align-items: center; gap: 12px;
  padding: 11px 18px 9px;
  background: rgba(255,255,255,.018);
  border-bottom: 1px solid {BORDER2};
}}
.sec-hdr-icon {{
  width: 26px; height: 26px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}}
.sec-hdr-name {{
  flex: 1; font-size: 11px; font-weight: 700;
  color: var(--muted2); letter-spacing: .03em; text-transform: uppercase;
}}
.sec-hdr-total {{ font-size: 13px; font-weight: 800; }}
.sec-badge {{
  font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 6px;
  background: rgba(242,61,79,.14); color: {RED}; margin-left: 6px;
}}

/* ── ITEM ROW (estilo MP mejorado) ── */
.item-row {{
  display: flex; align-items: center; gap: 14px;
  padding: 13px 18px;
  border-bottom: 1px solid {BORDER2};
  transition: background .12s;
}}
.item-row:last-child {{ border-bottom: none; }}
.item-row:hover {{ background: rgba(255,255,255,.018); }}

/* Ícono circular grande estilo MP */
.item-ico {{
  width: 46px; height: 46px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  position: relative;
}}

.item-body {{ flex: 1; min-width: 0; }}
.item-name {{
  font-size: 14px; font-weight: 700; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-bottom: 5px;
}}
.item-name-paid {{
  font-size: 14px; font-weight: 600;
  color: var(--muted2); text-decoration: line-through;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  margin-bottom: 5px;
}}

/* Badge de vencimiento */
.vbadge {{
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 700; padding: 3px 9px;
  border-radius: 20px; white-space: nowrap;
}}
.vb-paid  {{ background:rgba(0,200,83,.1);   color:{GREEN};  }}
.vb-venc  {{ background:rgba(242,61,79,.14); color:{RED};    border:1px solid rgba(242,61,79,.25); }}
.vb-hoy   {{ background:rgba(242,61,79,.12); color:{RED};    }}
.vb-prox  {{ background:rgba(255,156,0,.12); color:{ORANGE}; }}
.vb-soon  {{ background:rgba(251,191,36,.1); color:{YELLOW}; }}
.vb-ok    {{ background:rgba(0,200,83,.08);  color:{GREEN};  }}
.vb-none  {{ background:rgba(255,255,255,.05); color:var(--muted2); }}

.item-right {{ text-align: right; flex-shrink: 0; min-width: 90px; }}
.item-monto {{ font-size: 15px; font-weight: 800; color: var(--text); line-height: 1; }}
.item-monto-paid {{ font-size: 15px; font-weight: 600; color: var(--muted2);
  text-decoration: line-through; line-height: 1; }}
.item-usd {{ font-size: 11px; color: var(--muted2); margin-top: 4px; }}

/* ── BARRAS PENDIENTE POR CAT ── */
.cat-bar-row {{ margin-bottom: 11px; }}
.cat-bar-top {{
  display: flex; justify-content: space-between; margin-bottom: 4px;
  font-size: 12px;
}}
.cat-bar-bg {{
  height: 5px; background: rgba(255,255,255,.06);
  border-radius: 4px; overflow: hidden;
}}
.cat-bar-fill {{ height: 100%; border-radius: 4px; }}

/* ── RES ROWS ── */
.res-row {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 9px 0; border-bottom: 1px solid {BORDER2}; font-size: 13px;
}}
.res-row:last-child {{ border-bottom: none; }}
.res-k {{ color: var(--muted2); font-weight: 500; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important; padding: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
  background: transparent !important; color: var(--muted2) !important;
  font-family: 'Plus Jakarta Sans',sans-serif !important;
  font-size: 13px !important; font-weight: 700 !important;
  border-bottom: 2px solid transparent !important;
  padding: 11px 18px !important; margin-bottom: -1px !important;
}}
.stTabs [aria-selected="true"] {{
  color: {ACCENT} !important; border-bottom-color: {ACCENT} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding: 16px 0 0 !important; }}

/* ── DATA EDITOR ── */
[data-testid="stDataEditorContainer"] {{
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important; overflow: hidden !important;
}}

/* ── RESPONSIVE ── */
@media (max-width: 860px) {{
  .metrics {{ grid-template-columns: repeat(2,1fr); }}
}}
@media (max-width: 560px) {{
  .metrics {{ grid-template-columns: 1fr 1fr; gap: 8px; }}
  .mval {{ font-size: 18px; }}
  .wrap {{ padding: 0 12px 32px; }}
  .item-ico {{ width: 40px; height: 40px; }}
  .item-name, .item-name-paid {{ font-size: 13px; }}
  .item-monto, .item-monto-paid {{ font-size: 14px; }}
}}
hr {{ display: none !important; }}
[data-testid="stVerticalBlock"] > div {{ gap: 0 !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. CONEXIÓN Y DATOS
# ─────────────────────────────────────────────
@st.cache_resource
def get_gspread():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json", scope)
    except Exception:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos():
    try:
        hoja = get_gspread().open("Gastos_Henry").sheet1
        data = hoja.get_all_values()
    except Exception as e:
        st.error(f"❌ Error conectando con Google Sheets: {e}")
        return pd.DataFrame()

    data = [r for r in data if any(str(c).strip() for c in r)]
    if not data or len(data) < 2:
        return pd.DataFrame()

    headers = ["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]
    primera = str(data[0][0]).strip().lower()
    filas   = data[1:] if primera in ["categoría","categoria","cat","category"] else data
    filas   = [r + [""] * (5 - len(r)) for r in filas if len(r) >= 2]
    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas, columns=headers)
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
    df["Día Pago"]    = pd.to_datetime(df["Día Pago"], errors="coerce").dt.date
    df["Pagado"]      = df["Pagado"].apply(
        lambda x: str(x).strip().upper() in ["TRUE","VERDADERO","✅","SI","SÍ","1"]
    )
    df = df[~((df["Monto (ARS)"] == 0) & (df["Ítem"].str.strip() == ""))]
    return df.reset_index(drop=True)

@st.cache_data(ttl=300)
def get_dolar():
    try:
        return float(requests.get("https://dolarapi.com/v1/dolares/blue", timeout=5).json()["venta"])
    except Exception:
        return 1450.0

# ─────────────────────────────────────────────
# 7. HELPERS
# ─────────────────────────────────────────────
def categorizar_inteligente(item: str) -> str:
    """Asigna una categoría automáticamente según palabras clave en el ítem."""
    i = str(item).lower()
    
    if any(x in i for x in ["mercadocredito", "mercado credito", "tarjeta", "visa", "mastercard", "amex", "crédito", "credito", "banco", "financiamiento", "financiación", "financiacion", "cuota"]): return "💳 Crédito/Financiación"
    elif any(x in i for x in ["luz", "edenor", "edesur", "agua", "aysa", "gas", "metrogas"]): return "⚡ Servicios"
    elif any(x in i for x in ["super", "coto", "carrefour", "dia", "jumbo", "disco", "mercado", "almacén", "chino"]): return "🛒 Supermercado"
    elif any(x in i for x in ["alquiler", "expensas", "abl", "limpieza"]): return "🏠 Hogar"
    elif any(x in i for x in ["nafta", "ypf", "shell", "axion", "uber", "cabify", "taxi", "peaje", "sube", "transporte", "trasporte"]): return "🚗 Transporte"
    elif any(x in i for x in ["netflix", "spotify", "prime", "hbo", "disney", "youtube", "telecentro", "fibertel", "internet", "claro", "personal", "movistar", "meli", "google", "apple one", "vpn"]): return "📺 Suscripciones"
    elif any(x in i for x in ["gym", "gimnasio", "megatlon", "sportclub", "crossfit"]): return "🏋 Fitness"
    elif any(x in i for x in ["farmacia", "osde", "swiss", "galeno", "médico", "salud", "depilife"]): return "🏥 Salud"
    elif any(x in i for x in ["mc", "burger", "pedidosya", "rappi", "helado", "pizza", "restaurante", "bar", "café"]): return "🍔 Comida/Delivery"
    elif any(x in i for x in ["ropa", "zapat", "zara", "dafiti", "peluquería", "estética"]): return "🎭 Personal/Ocio"
    elif any(x in i for x in ["vuelo", "pasaje", "hotel", "airbnb"]): return "✈ Viajes"
    else: return "🔘 Otros"

def fmt_ars(n):
    s = f"{n:,.0f}".replace(",","X").replace(".",",").replace("X",".")
    return f"$ {s}"

def fmt_k(n):
    if n >= 1_000_000: return f"$ {n/1_000_000:.1f}M"
    if n >= 1_000:     return f"$ {n/1_000:.0f}k"
    return fmt_ars(n)

def fmt_usd(n, d):
    return f"U$S {n/d:,.0f}" if d > 0 else "U$S —"

def venc_html(row):
    """Badge de vencimiento inteligente."""
    if row["Pagado"]:
        return '<span class="vbadge vb-paid">✓ Pagado</span>'
    dia = row["Día Pago"]
    if pd.isna(dia):
        return '<span class="vbadge vb-none">⚪ Sin fecha</span>'
    diff     = (dia - date.today()).days
    fmt_dia  = dia.strftime("%-d %b")
    if diff < 0:
        return f'<span class="vbadge vb-venc">🔴 Vencido · {fmt_dia}</span>'
    if diff == 0:
        return f'<span class="vbadge vb-hoy">🔴 Hoy · {fmt_dia}</span>'
    if diff <= 3:
        return f'<span class="vbadge vb-prox">🟡 {diff}d · {fmt_dia}</span>'
    if diff <= 10:
        return f'<span class="vbadge vb-soon">🟡 {diff}d · {fmt_dia}</span>'
    return f'<span class="vbadge vb-ok">🟢 {fmt_dia}</span>'

def procesar(df_base, dolar):
    df    = df_base.copy()
    # Aplicar la categorización inteligente
    df["Categoría"] = df["Ítem"].apply(categorizar_inteligente)
    total = df["Monto (ARS)"].sum()
    df["Peso (%)"] = (df["Monto (ARS)"] / total).fillna(0) if total > 0 else 0
    df["USD"]      = (df["Monto (ARS)"] / dolar).round(2)  if dolar > 0 else 0
    df["Cat."]     = df["Categoría"]
    return df.sort_values(["Pagado","Día Pago"], ascending=[True,True], na_position="last")

# ─────────────────────────────────────────────
# 8. CARGA
# ─────────────────────────────────────────────
dolar   = get_dolar()
df_base = cargar_datos()

if not df_base.empty:
    df         = procesar(df_base, dolar)
    total_ars  = df["Monto (ARS)"].sum()
    pagado_ars = df[df["Pagado"]==True]["Monto (ARS)"].sum()
    pend_ars   = total_ars - pagado_ars
    pct        = int(pagado_ars / total_ars * 100) if total_ars > 0 else 0
    vencidos   = df[(df["Pagado"]==False) & df["Día Pago"].notna() & (df["Día Pago"] < date.today())]
    proximos   = df[(df["Pagado"]==False) & df["Día Pago"].notna() &
                    (df["Día Pago"] >= date.today()) &
                    (df["Día Pago"] <= date.today() + timedelta(days=3))]
    por_cat    = (df.groupby("Cat.")["Monto (ARS)"].sum()
                  .reset_index().sort_values("Monto (ARS)", ascending=False))
else:
    df = por_cat = pd.DataFrame()
    total_ars = pagado_ars = pend_ars = pct = 0
    vencidos = proximos = pd.DataFrame()

# ─────────────────────────────────────────────
# 9. RENDER — HEADER CON BANDERA
# ─────────────────────────────────────────────
sun_rays = ""
for i in range(16):
    angle = i * (360/16) - 90
    rad   = math.radians(angle)
    x1 = 16 + math.cos(rad) * 7
    y1 = 16 + math.sin(rad) * 7
    x2 = 16 + math.cos(rad) * 14
    y2 = 16 + math.sin(rad) * 14
    sun_rays += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#d4960e" stroke-width="1.8" stroke-linecap="round"/>'

meses   = ["enero","febrero","marzo","abril","mayo","junio",
           "julio","agosto","septiembre","octubre","noviembre","diciembre"]
hoy     = date.today()
hoy_str = f"{hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

st.markdown('<div class="wrap">', unsafe_allow_html=True)

st.markdown(f"""
<div class="hdr">
  <div style="
    position:absolute; right:0; top:0; bottom:0; width:280px;
    pointer-events:none; z-index:0;
    display:flex; flex-direction:column;
    border-radius:0 0 0 50px; overflow:hidden;
    -webkit-mask-image:linear-gradient(to right,
      transparent 0%,rgba(0,0,0,.1) 20%,rgba(0,0,0,.26) 50%,rgba(0,0,0,.26) 72%,transparent 100%);
    mask-image:linear-gradient(to right,
      transparent 0%,rgba(0,0,0,.1) 20%,rgba(0,0,0,.26) 50%,rgba(0,0,0,.26) 72%,transparent 100%);
  ">
    <div style="flex:1;background:linear-gradient(135deg,#3d87c0,#74acdf)"></div>
    <div style="flex:1;background:#b0b0b0;display:flex;align-items:center;justify-content:center">
      <svg width="34" height="34" viewBox="0 0 32 32">
        {sun_rays}
        <circle cx="16" cy="16" r="5.5" fill="#d4960e"/>
        <circle cx="16" cy="16" r="3.2" fill="#9a6608" opacity="0.55"/>
      </svg>
    </div>
    <div style="flex:1;background:linear-gradient(135deg,#74acdf,#3d87c0)"></div>
  </div>

  <div style="position:relative;z-index:2">
    <div class="hdr-brand">Finanzas <span>AR</span></div>
    <div class="hdr-date">{hoy_str}</div>
  </div>
  <div style="position:relative;z-index:2">
    <div class="dolar-chip">
      <div class="dolar-lbl">USD Blue</div>
      <div class="dolar-val">${dolar:,.0f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 10. NAVEGACIÓN — 2 botones full width 50/50
# ─────────────────────────────────────────────
screen = st.session_state.screen
st.markdown('<div class="nav-grid">', unsafe_allow_html=True)
nav1, nav2 = st.columns(2)
with nav1:
    if st.button("🏠  Inicio", type="primary" if screen=="inicio" else "secondary",
                 use_container_width=True):
        st.session_state.screen = "inicio"; st.rerun()
with nav2:
    if st.button("📋  Gastos", type="primary" if screen=="gastos" else "secondary",
                 use_container_width=True):
        st.session_state.screen = "gastos"; st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════
# PANTALLA: INICIO
# ═════════════════════════════════════════════
if st.session_state.screen == "inicio":

    # ── ALERTAS ──────────────────────────────
    if not vencidos.empty:
        items_v = " · ".join(
            f"<strong>{r['Ítem']}</strong> ({fmt_ars(r['Monto (ARS)'])})"
            for _, r in vencidos.iterrows()
        )
        st.markdown(
            f'<div class="alert alert-r">🔴&nbsp; {len(vencidos)} pago{"s" if len(vencidos)>1 else ""} vencido{"s" if len(vencidos)>1 else ""} — {items_v}</div>',
            unsafe_allow_html=True,
        )
    if not proximos.empty:
        items_p = " · ".join(
            f"<strong>{r['Ítem']}</strong> ({r['Día Pago'].strftime('%-d %b')})"
            for _, r in proximos.iterrows()
        )
        st.markdown(
            f'<div class="alert alert-o">🟡&nbsp; Próximos 3 días — {items_p}</div>',
            unsafe_allow_html=True,
        )

    # ── MÉTRICAS ─────────────────────────────
    st.markdown(f"""
    <div class="metrics">
      <div class="mcard mc-a">
        <div class="mlbl">📊 Total del mes</div>
        <div class="mval">{fmt_ars(total_ars)}</div>
        <div class="msub">{fmt_usd(total_ars,dolar)}</div>
      </div>
      <div class="mcard mc-g">
        <div class="mlbl">✅ Pagado</div>
        <div class="mval" style="color:{GREEN}">{fmt_ars(pagado_ars)}</div>
        <div class="msub">{fmt_usd(pagado_ars,dolar)}</div>
      </div>
      <div class="mcard mc-r">
        <div class="mlbl">⏳ Pendiente</div>
        <div class="mval" style="color:{RED}">{fmt_ars(pend_ars)}</div>
        <div class="msub">{fmt_usd(pend_ars,dolar)}</div>
      </div>
      <div class="mcard mc-o">
        <div class="mlbl">📈 Cubierto</div>
        <div class="mpct">{pct}%</div>
        <div class="pbar"><div class="pfill" style="width:{pct}%"></div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.markdown(
            f'<div class="card card-pad" style="text-align:center;padding:48px;color:{MUTED2}">'
            f'<div style="font-size:36px;margin-bottom:10px">📭</div>'
            f'<div style="font-weight:600">Sin datos. Verificá la conexión con Google Sheets.</div></div>',
            unsafe_allow_html=True,
        )
    else:
        col_izq, col_der = st.columns([1.65, 1], gap="medium")

        # ── COL IZQUIERDA: LISTA AGRUPADA ────
        with col_izq:
            # Orden: primero categorías con pendientes
            cats_orden = (
                df.groupby("Cat.")
                .apply(lambda g: g["Pagado"].eq(False).sum())
                .sort_values(ascending=False)
                .index.tolist()
            )

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="padding:16px 18px 4px" class="ctitle">Detalle de gastos</div>', unsafe_allow_html=True)

            for cat in cats_orden:
                df_cat  = df[df["Cat."] == cat]
                t_cat    = df_cat["Monto (ARS)"].sum()
                color    = cat_color(cat)
                n_pend  = int(df_cat["Pagado"].eq(False).sum())
                badge    = f'<span class="sec-badge">{n_pend} pend.</span>' if n_pend > 0 else ""

                # Ícono SVG pequeño para el header de sección
                icon_s  = svg_icon(cat, color, size=16)

                st.markdown(f"""
                <div class="sec-hdr">
                  <div class="sec-hdr-icon" style="background:{color}25">{icon_s}</div>
                  <span class="sec-hdr-name">{cat}{badge}</span>
                  <span class="sec-hdr-total" style="color:{color}">{fmt_ars(t_cat)}</span>
                </div>
                """, unsafe_allow_html=True)

                for _, row in df_cat.iterrows():
                    paid      = row["Pagado"]
                    monto     = row["Monto (ARS)"]
                    usd_str   = fmt_usd(monto, dolar)
                    badge_venc= venc_html(row)
                    icon_lg   = svg_icon(cat, color, size=22)
                    opacity   = "0.45" if paid else "1"

                    name_cls  = "item-name-paid" if paid else "item-name"
                    monto_cls = "item-monto-paid" if paid else "item-monto"

                    st.markdown(f"""
                    <div class="item-row" style="opacity:{opacity}">
                      <div class="item-ico" style="background:{color}{'20' if not paid else '10'}">
                        {icon_lg}
                      </div>
                      <div class="item-body">
                        <div class="{name_cls}">{row['Ítem']}</div>
                        <div>{badge_venc}</div>
                      </div>
                      <div class="item-right">
                        <div class="{monto_cls}">{fmt_ars(monto)}</div>
                        <div class="item-usd">{usd_str}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ── COL DERECHA: DONUT + SIDEBAR ─────
        with col_der:

            # DONUT
            fig = go.Figure(go.Pie(
                labels=por_cat["Cat."],
                values=por_cat["Monto (ARS)"],
                hole=0.62,
                marker=dict(
                    colors=[cat_color(c) for c in por_cat["Cat."]],
                    line=dict(color=SURFACE, width=3),
                ),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
                direction="clockwise", sort=True,
            ))
            fig.add_annotation(
                text=f"<b>{fmt_k(total_ars)}</b>",
                x=0.5, y=0.56,
                font=dict(size=14, color=TEXT, family="Plus Jakarta Sans"),
                showarrow=False,
            )
            fig.add_annotation(
                text=fmt_usd(total_ars, dolar),
                x=0.5, y=0.42,
                font=dict(size=10, color=MUTED2, family="Plus Jakarta Sans"),
                showarrow=False,
            )
            fig.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v", x=1.02, y=0.5,
                    font=dict(color=MUTED2, size=10, family="Plus Jakarta Sans"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                height=270,
                margin=dict(t=8, b=8, l=8, r=95),
                paper_bgcolor=PLOTBG, plot_bgcolor=PLOTBG,
            )
            st.markdown('<div class="card card-pad"><div class="ctitle">Distribución</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""
            <div style="display:flex;border-top:1px solid {BORDER2};padding-top:14px;margin-top:4px">
              <div style="flex:1;text-align:center">
                <div style="font-size:9px;font-weight:700;color:{MUTED};letter-spacing:.08em;text-transform:uppercase">Pagado</div>
                <div style="font-size:16px;font-weight:800;color:{GREEN};margin-top:4px">{fmt_k(pagado_ars)}</div>
              </div>
              <div style="width:1px;background:{BORDER2}"></div>
              <div style="flex:1;text-align:center">
                <div style="font-size:9px;font-weight:700;color:{MUTED};letter-spacing:.08em;text-transform:uppercase">Pendiente</div>
                <div style="font-size:16px;font-weight:800;color:{RED};margin-top:4px">{fmt_k(pend_ars)}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # RESUMEN
            n_pag  = int(df["Pagado"].sum())
            n_pend = len(df) - n_pag
            n_venc = len(vencidos)
            n_prox = len(proximos)
            mayor  = df.loc[df["Monto (ARS)"].idxmax(), "Ítem"] if not df.empty else "—"
            mayor_m= df["Monto (ARS)"].max() if not df.empty else 0

            st.markdown(f"""
            <div class="card card-pad">
              <div class="ctitle">Resumen</div>
              <div class="res-row"><span class="res-k">Total ítems</span><span style="font-weight:700">{len(df)}</span></div>
              <div class="res-row"><span class="res-k">Pagados</span><span style="font-weight:700;color:{GREEN}">{n_pag}</span></div>
              <div class="res-row"><span class="res-k">Pendientes</span><span style="font-weight:700;color:{ORANGE}">{n_pend}</span></div>
              <div class="res-row"><span class="res-k">Vencidos</span><span style="font-weight:700;color:{RED}">{n_venc}</span></div>
              <div class="res-row"><span class="res-k">Próx. 3 días</span><span style="font-weight:700;color:{YELLOW}">{n_prox}</span></div>
              <div class="res-row" style="flex-direction:column;align-items:flex-start;gap:2px;border-bottom:none">
                <span class="res-k">Mayor gasto</span>
                <span style="font-weight:700;color:{TEXT}">{mayor}</span>
                <span style="font-size:11px;color:{MUTED2}">{fmt_ars(mayor_m)}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # BARRAS PENDIENTE POR CAT
            pend_cat = (
                df[df["Pagado"]==False]
                .groupby("Cat.")["Monto (ARS)"].sum()
                .sort_values(ascending=False)
            )
            if not pend_cat.empty:
                max_p = pend_cat.max()
                st.markdown('<div class="card card-pad"><div class="ctitle">Pendiente por categoría</div>', unsafe_allow_html=True)
                for cat, val in pend_cat.items():
                    pct_bar = int(val / max_p * 100) if max_p > 0 else 0
                    color   = cat_color(cat)
                    st.markdown(f"""
                    <div class="cat-bar-row">
                      <div class="cat-bar-top">
                        <span style="font-weight:600;color:{TEXT}">{cat}</span>
                        <span style="font-weight:700;color:{color}">{fmt_ars(val)}</span>
                      </div>
                      <div class="cat-bar-bg">
                        <div class="cat-bar-fill" style="width:{pct_bar}%;background:{color}"></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════
# PANTALLA: GASTOS
# ═════════════════════════════════════════════
elif st.session_state.screen == "gastos":

    if df.empty:
        st.markdown(
            f'<div class="card card-pad" style="text-align:center;padding:48px;color:{MUTED2}">'
            f'<div style="font-size:36px;margin-bottom:10px">📭</div>'
            f'<div style="font-weight:600">Sin datos en Google Sheets.</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="font-size:13px;color:{MUTED2};margin-bottom:14px;font-weight:500">'
            f'Editá, agregá o marcá pagos acá. Los cambios se reflejan en Inicio al guardar.</div>',
            unsafe_allow_html=True,
        )

        tab_todos, tab_pend, tab_pag = st.tabs([
            f"Todos  {len(df)}",
            f"Pendientes  {len(df[df['Pagado']==False])}",
            f"Pagados  {len(df[df['Pagado']==True])}",
        ])

        COL_CONFIG = {
            "Pagado":      st.column_config.CheckboxColumn("✓", width="small"),
            "Ítem":        st.column_config.TextColumn("Ítem"),
            "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$ %d"),
            "USD":         st.column_config.NumberColumn("USD", format="U$S %.0f", disabled=True, width="small"),
            "Día Pago":    st.column_config.DateColumn("Vencimiento", format="DD/MM/YY"),
        }
        COL_ORDER = ("Pagado","Ítem","Monto (ARS)","USD","Día Pago")

        def render_tabla(data, key):
            return st.data_editor(
                data, column_config=COL_CONFIG, column_order=COL_ORDER,
                num_rows="dynamic", use_container_width=True,
                hide_index=True, key=key,
            )

        with tab_todos:
            df_edit = render_tabla(df, "t_todos")
        with tab_pend:
            render_tabla(df[df["Pagado"]==False].copy(), "t_pend")
        with tab_pag:
            render_tabla(df[df["Pagado"]==True].copy(), "t_pag")

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        bc1, bc2 = st.columns([3, 1])
        with bc1:
            if st.button("💾  Guardar y Sincronizar", type="primary", use_container_width=True):
                try:
                    df_up = df_edit.copy()
                    df_up["Categoría"] = df_up["Ítem"].apply(categorizar_inteligente)
                    df_up = df_up[["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]]
                    df_up["Día Pago"] = df_up["Día Pago"].apply(lambda x: str(x) if pd.notnull(x) else "")
                    df_up["Pagado"]   = df_up["Pagado"].apply(lambda x: "TRUE" if x else "FALSE")
                    st.cache_data.clear()
                    hoja = get_gspread().open("Gastos_Henry").sheet1
                    hoja.clear()
                    hoja.append_row(df_up.columns.tolist())
                    hoja.append_rows(df_up.values.tolist())
                    st.success("✓ Cambios guardados en Google Sheets")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")
        with bc2:
            if st.button("🔄  Recargar", type="secondary", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
