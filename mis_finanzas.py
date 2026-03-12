import streamlit as st
import pandas as pd  # <--- Corregido: antes decía 'import pd as pd'
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

/* ── NAV — LADO A LADO EN MÓVIL ── */
[data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 8px !important;
}}
[data-testid="column"] {{
    width: 100% !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
}}

.nav-grid {{
  padding: 14px 0 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 22px;
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

/* ── ITEM ROW ── */
.item-row {{
  display: flex; align-items: center; gap: 14px;
  padding: 13px 18px;
  border-bottom: 1px solid {BORDER2};
  transition: background .12s;
}}
.item-row:last-child {{ border-bottom: none; }}
.item-row:hover {{ background: rgba(255,255,255,.018); }}

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

.vbadge {{
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; font-weight: 700; padding: 3px 9px;
  border-radius: 20px; white-space: nowrap;
}}
.vb-paid  {{ background:rgba(0,200,83,.1);   color:{GREEN};  }}
.vb-venc  {{ background:rgba(242,61,79,.14); color:{RED};    border:1px solid rgba(242,61,79,.25); }}

.item-right {{ text-align: right; flex-shrink: 0; min-width: 90px; }}
.item-monto {{ font-size: 15px; font-weight: 800; color: var(--text); line-height: 1; }}

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
  .stButton > button {{ font-size: 13px !important; padding: 10px 8px !important; }}
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

    if not data or len(data) < 2:
        return pd.DataFrame()

    df = pd.DataFrame(data[1:], columns=["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"])
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
    df["Día Pago"]    = pd.to_datetime(df["Día Pago"], errors="coerce").dt.date
    df["Pagado"]      = df["Pagado"].apply(
        lambda x: str(x).strip().upper() in ["TRUE","VERDADERO","✅","SI","SÍ","1"]
    )
    return df

@st.cache_data(ttl=300)
def get_dolar():
    try:
        return float(requests.get("https://dolarapi.com/v1/dolares/blue", timeout=5).json()["venta"])
    except Exception:
        return 1450.0

# ─────────────────────────────────────────────
# 7. HELPERS
# ─────────────────────────────────────────────
def fmt_ars(n):
    s = f"{n:,.0f}".replace(",","X").replace(".",",").replace("X",".")
    return f"$ {s}"

def venc_html(row):
    if row["Pagado"]:
        return '<span class="vbadge vb-paid">✓ Pagado</span>'
    dia = row["Día Pago"]
    if pd.isna(dia):
        return '<span class="vbadge vb-none">⚪ Sin fecha</span>'
    diff = (dia - date.today()).days
    if diff < 0:
        return f'<span class="vbadge vb-venc">🔴 Vencido</span>'
    return f'<span class="vbadge vb-none">🟢 {dia.strftime("%d/%m")}</span>'

# ─────────────────────────────────────────────
# 8. RENDER
# ─────────────────────────────────────────────
dolar = get_dolar()
df = cargar_datos()

st.markdown('<div class="wrap">', unsafe_allow_html=True)

# HEADER
st.markdown(f"""
<div class="hdr">
  <div>
    <div class="hdr-brand">Finanzas <span>AR</span></div>
    <div class="hdr-date">{date.today().strftime('%d/%m/%Y')}</div>
  </div>
  <div class="dolar-chip">
    <div class="dolar-lbl">USD Blue</div>
    <div class="dolar-val">${dolar:,.0f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# NAVEGACIÓN
st.markdown('<div class="nav-grid">', unsafe_allow_html=True)
nav1, nav2 = st.columns(2)
with nav1:
    if st.button("🏠 Inicio", type="primary" if st.session_state.screen=="inicio" else "secondary", use_container_width=True):
        st.session_state.screen = "inicio"; st.rerun()
with nav2:
    if st.button("📋 Gastos", type="primary" if st.session_state.screen=="gastos" else "secondary", use_container_width=True):
        st.session_state.screen = "gastos"; st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.screen == "inicio":
    if not df.empty:
        total = df["Monto (ARS)"].sum()
        pagado = df[df["Pagado"]]["Monto (ARS)"].sum()
        pend = total - pagado
        pct = int(pagado/total*100) if total > 0 else 0

        st.markdown(f"""
        <div class="metrics">
          <div class="mcard mc-a"><div class="mlbl">Total</div><div class="mval">{fmt_ars(total)}</div></div>
          <div class="mcard mc-g"><div class="mlbl">Pagado</div><div class="mval" style="color:{GREEN}">{fmt_ars(pagado)}</div></div>
          <div class="mcard mc-r"><div class="mlbl">Pendiente</div><div class="mval" style="color:{RED}">{fmt_ars(pend)}</div></div>
          <div class="mcard mc-o"><div class="mlbl">Progreso</div><div class="mpct">{pct}%</div></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        for _, row in df.iterrows():
            color = cat_color(row["Categoría"])
            icon = svg_icon(row["Categoría"], color)
            badge = venc_html(row)
            st.markdown(f"""
            <div class="item-row">
                <div class="item-ico" style="background:{color}20">{icon}</div>
                <div class="item-body">
                    <div class="item-name">{row['Ítem']}</div>
                    {badge}
                </div>
                <div class="item-right">
                    <div class="item-monto">{fmt_ars(row['Monto (ARS)'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.screen == "gastos":
    st.markdown('<div class="card card-pad">', unsafe_allow_html=True)
    df_edit = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
        try:
            hoja = get_gspread().open("Gastos_Henry").sheet1
            hoja.clear()
            hoja.append_row(df_edit.columns.tolist())
            hoja.append_rows(df_edit.astype(str).values.tolist())
            st.success("Guardado correctamente")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
