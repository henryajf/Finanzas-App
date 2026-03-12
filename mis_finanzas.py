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
# 2. SESSION STATE — dark mode + navegación
# ─────────────────────────────────────────────
if "dark"    not in st.session_state: st.session_state.dark    = False
if "screen"  not in st.session_state: st.session_state.screen  = "inicio"
if "sel_cat" not in st.session_state: st.session_state.sel_cat = None

dark = st.session_state.dark

# ─────────────────────────────────────────────
# 3. TEMA DINÁMICO
# ─────────────────────────────────────────────
if dark:
    BG       = "#0a0a0a"
    SURFACE  = "#161616"
    SURFACE2 = "#1a1a1a"
    BORDER   = "rgba(255,255,255,0.07)"
    TEXT     = "#f5f5f5"
    MUTED    = "#666666"
    SHADOW   = "0 2px 16px rgba(0,0,0,.5)"
    PLOTBG   = "rgba(0,0,0,0)"
    LEGENDC  = "#888"
else:
    BG       = "#f5f5f5"
    SURFACE  = "#ffffff"
    SURFACE2 = "#fafafa"
    BORDER   = "#ebebeb"
    TEXT     = "#1a1a1a"
    MUTED    = "#999999"
    SHADOW   = "0 2px 12px rgba(0,0,0,.06)"
    PLOTBG   = "rgba(0,0,0,0)"
    LEGENDC  = "#999"

ACCENT = "#009ee3"
GREEN  = "#00a650"
RED    = "#f23d4f"
ORANGE = "#ff9c00"

# ─────────────────────────────────────────────
# 4. CSS GLOBAL
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {{
  --bg:      {BG};
  --surface: {SURFACE};
  --border:  {BORDER};
  --text:    {TEXT};
  --muted:   {MUTED};
  --accent:  {ACCENT};
  --green:   {GREEN};
  --red:     {RED};
  --orange:  {ORANGE};
  --shadow:  {SHADOW};
  --radius:  16px;
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
.main-wrap {{
  max-width: 980px;
  margin: 0 auto;
  padding: 0 20px 32px;
}}

/* ── HEADER ── */
.app-header {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 22px 0 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 20px;
  position: relative;
  overflow: hidden;
}}

/* Bandera Argentina — decorativa, tenue */
.arg-flag {{
  position: absolute;
  right: 0; top: 0; bottom: 0;
  width: 220px;
  display: flex; flex-direction: column;
  opacity: {'0.06' if dark else '0.07'};
  pointer-events: none;
  border-radius: 0 0 0 32px;
  overflow: hidden;
}}
.flag-stripe-top    {{ flex: 1; background: #74acdf; }}
.flag-stripe-middle {{ flex: 1; background: #ffffff; position: relative; }}
.flag-stripe-bottom {{ flex: 1; background: #74acdf; }}

/* Sol de Mayo — centro de la franja blanca */
.flag-sun {{
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 28px; height: 28px;
}}
.sun-circle {{
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 12px; height: 12px;
  border-radius: 50%;
  background: #f6b40e;
}}
.sun-ray {{
  position: absolute;
  top: 50%; left: 50%;
  width: 2px; height: 14px;
  background: #f6b40e;
  border-radius: 2px;
  transform-origin: bottom center;
}}

/* Versión sutil con gradiente fade a la izquierda */
.arg-flag-fade {{
  position: absolute;
  right: 0; top: 0; bottom: 0;
  width: 220px;
  background: linear-gradient(
    to right,
    {'rgba(10,10,10,1)' if dark else 'rgba(245,245,245,1)'} 0%,
    {'rgba(10,10,10,0)' if dark else 'rgba(245,245,245,0)'} 30%
  );
  pointer-events: none;
  z-index: 1;
}}

.header-brand {{
  font-size: 22px; font-weight: 800; color: var(--text);
  letter-spacing: -.03em; position: relative; z-index: 2;
}}
.header-brand span {{ color: var(--accent); }}
.header-date {{
  font-size: 12px; color: var(--muted); font-weight: 500;
  margin-top: 2px; position: relative; z-index: 2;
}}
.dolar-chip {{
  background: {'rgba(0,158,227,.08)' if dark else '#e8f5fc'};
  border: 1px solid rgba(0,158,227,.22);
  border-radius: 12px; padding: 8px 16px; text-align: center;
}}
.dolar-label {{ font-size: 9px; color: var(--muted); letter-spacing: .08em;
  text-transform: uppercase; font-weight: 700; }}
.dolar-val {{ font-size: 18px; font-weight: 800; color: var(--accent); margin-top: 1px; }}

/* ── NAV TABS (simula bottom nav en escritorio) ── */
.nav-tabs {{
  display: flex; gap: 8px; margin-bottom: 20px;
}}
.nav-tab {{
  flex: 1; padding: 10px 0; border: 1px solid var(--border);
  border-radius: 12px; background: var(--surface);
  font-family: inherit; font-size: 13px; font-weight: 700;
  color: var(--muted); cursor: pointer; text-align: center;
  transition: all .2s; box-shadow: var(--shadow);
}}
.nav-tab.active {{
  background: var(--accent); color: #fff;
  border-color: var(--accent);
  box-shadow: 0 4px 14px rgba(0,158,227,.3);
}}

/* ── CARDS ── */
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 20px;
  margin-bottom: 14px;
}}
.card-title {{
  font-size: 11px; font-weight: 700; color: var(--muted);
  letter-spacing: .06em; text-transform: uppercase; margin-bottom: 14px;
}}

/* ── HERO CATEGORY CARD ── */
.cat-hero {{
  text-align: center;
  padding: 28px 20px 20px;
  margin-bottom: 14px;
  border-radius: var(--radius);
  border: 1.5px solid;
  box-shadow: var(--shadow);
}}
.cat-hero-icon {{
  width: 64px; height: 64px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 30px; margin: 0 auto 12px;
}}
.cat-hero-label {{
  font-size: 12px; font-weight: 700; color: var(--muted);
  letter-spacing: .05em; text-transform: uppercase; margin-bottom: 6px;
}}
.cat-hero-total {{
  font-size: 34px; font-weight: 800; color: var(--text);
  letter-spacing: -.02em; line-height: 1;
}}
.cat-hero-sub {{ font-size: 12px; color: var(--muted); margin-top: 6px; }}

/* ── MINI STATS ── */
.mini-stats {{
  display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; margin-bottom: 14px;
}}
.mini-stat {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 14px 10px; text-align: center;
  box-shadow: var(--shadow);
}}
.mini-stat-val {{ font-size: 24px; font-weight: 800; line-height: 1; }}
.mini-stat-label {{
  font-size: 10px; font-weight: 700; color: var(--muted);
  letter-spacing: .05em; text-transform: uppercase; margin-top: 5px;
}}

/* ── LISTA CATEGORÍAS ── */
.cat-list-card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); box-shadow: var(--shadow);
  overflow: hidden; margin-bottom: 14px;
}}
.cat-row {{
  display: flex; align-items: center; gap: 14px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  cursor: pointer; transition: background .15s;
}}
.cat-row:last-child {{ border-bottom: none; }}
.cat-row:hover {{ background: {'rgba(255,255,255,0.03)' if dark else '#fafafa'}; }}
.cat-icon {{
  width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 20px;
}}
.cat-name {{ flex: 1; font-size: 15px; font-weight: 600; color: var(--text); }}
.cat-amount {{ font-size: 15px; font-weight: 700; color: var(--text); white-space: nowrap; }}
.cat-arrow {{ color: var(--muted); font-size: 18px; margin-left: 4px; }}

/* ── LISTA GASTOS ── */
.gasto-row {{
  display: flex; align-items: center; gap: 12px;
  padding: 13px 20px;
  border-bottom: 1px solid var(--border);
  transition: opacity .15s;
}}
.gasto-row:last-child {{ border-bottom: none; }}
.gasto-check {{
  width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
}}
.gasto-info {{ flex: 1; min-width: 0; }}
.gasto-name {{
  font-size: 14px; font-weight: 600; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.gasto-meta {{ font-size: 11px; color: var(--muted); margin-top: 2px; }}
.gasto-right {{ text-align: right; flex-shrink: 0; }}
.gasto-monto {{ font-size: 14px; font-weight: 700; color: var(--text); }}
.pill {{
  display: inline-block; padding: 2px 9px; border-radius: 20px;
  font-size: 10px; font-weight: 700; margin-top: 3px;
}}

/* ── ALERTAS ── */
.alerta {{
  padding: 11px 16px; border-radius: 12px; font-size: 13px;
  font-weight: 500; margin-bottom: 10px;
  display: flex; align-items: center; gap: 8px;
}}
.alerta-red  {{
  background: {'rgba(242,61,79,.1)' if dark else '#fff0f1'};
  border: 1px solid rgba(242,61,79,.2); color: #c0392b;
}}
.alerta-warn {{
  background: {'rgba(255,156,0,.1)' if dark else '#fff8ee'};
  border: 1px solid rgba(255,156,0,.2); color: #b7681a;
}}

/* ── PROGRESS ── */
.progress-bar {{
  height: 5px; background: var(--border); border-radius: 4px;
  overflow: hidden; margin-top: 12px;
}}
.progress-fill {{
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, var(--accent), #00c9ff);
}}

/* ── SPLIT METRICS ── */
.split-metrics {{
  display: flex; justify-content: center; gap: 28px;
  margin-top: 16px; padding-top: 14px;
  border-top: 1px solid var(--border);
}}
.split-item {{ text-align: center; }}
.split-label {{
  font-size: 9px; font-weight: 700; color: var(--muted);
  letter-spacing: .07em; text-transform: uppercase; margin-bottom: 4px;
}}
.split-val {{ font-size: 16px; font-weight: 800; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
  background: transparent !important;
  border-bottom: 2px solid var(--border) !important;
  gap: 0 !important; padding: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
  background: transparent !important; color: var(--muted) !important;
  font-family: 'Plus Jakarta Sans',sans-serif !important;
  font-size: 13px !important; font-weight: 700 !important;
  border-bottom: 2px solid transparent !important;
  padding: 11px 18px !important; margin-bottom: -2px !important;
}}
.stTabs [aria-selected="true"] {{
  color: var(--accent) !important;
  border-bottom-color: var(--accent) !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-panel"] {{ padding: 14px 0 0 !important; }}

/* ── DATA EDITOR ── */
[data-testid="stDataEditorContainer"] {{
  background: var(--surface) !important;
  border: none !important; border-radius: 0 !important;
}}

/* ── BOTONES ── */
.stButton > button[kind="primary"] {{
  background: var(--accent) !important; color: #fff !important;
  border: none !important; border-radius: 12px !important;
  padding: 13px 24px !important;
  font-family: 'Plus Jakarta Sans',sans-serif !important;
  font-size: 14px !important; font-weight: 700 !important;
  box-shadow: 0 4px 14px rgba(0,158,227,.25) !important;
  transition: all .2s !important;
}}
.stButton > button[kind="primary"]:hover {{
  background: #0088c7 !important; transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(0,158,227,.35) !important;
}}
.stButton > button[kind="secondary"] {{
  background: var(--surface) !important; color: var(--muted) !important;
  border: 1.5px solid var(--border) !important; border-radius: 12px !important;
  font-family: 'Plus Jakarta Sans',sans-serif !important;
  font-size: 13px !important; font-weight: 600 !important;
  transition: all .2s !important;
}}
.stButton > button[kind="secondary"]:hover {{
  border-color: var(--accent) !important; color: var(--accent) !important;
}}

/* ── RESPONSIVE ── */
@media (max-width: 768px) {{
  .main-wrap {{ padding: 0 12px 24px; }}
  .cat-row {{ padding: 12px 14px; gap: 10px; }}
  .cat-icon {{ width: 38px; height: 38px; font-size: 18px; }}
  .cat-name {{ font-size: 13px; }}
  .cat-amount {{ font-size: 13px; }}
}}

hr {{ display: none !important; }}
[data-testid="stVerticalBlock"] > div {{ gap: 0 !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 5. COLORES POR CATEGORÍA
# ─────────────────────────────────────────────
CAT_COLORS = {
    "⚡":"#009ee3", "🔌":"#009ee3",
    "🏠":"#00a650", "🛒":"#00a650",
    "🚗":"#ff9c00", "🚌":"#ff9c00",
    "💳":"#a855f7", "📺":"#ec4899",
    "📈":"#0ea5e9", "🏥":"#14b8a6",
    "🎭":"#f59e0b", "👪":"#8b5cf6",
    "🍔":"#ef4444", "🏋":"#22d3ee",
}
DONUT_PALETTE = [
    "#009ee3","#00a650","#a855f7","#ec4899","#ff9c00",
    "#f59e0b","#14b8a6","#0ea5e9","#ef4444","#8b5cf6","#6b7280","#34d399",
]

def cat_color(cat):
    for emoji, color in CAT_COLORS.items():
        if emoji in str(cat):
            return color
    return "#6b7280"

# ─────────────────────────────────────────────
# 6. CONEXIÓN A GOOGLE SHEETS
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
        st.error(f"❌ No se pudo conectar con Google Sheets: {e}")
        return pd.DataFrame()

    data = [r for r in data if any(str(c).strip() for c in r)]
    if not data or len(data) < 2:
        return pd.DataFrame()

    headers = ["Categoría", "Ítem", "Monto (ARS)", "Día Pago", "Pagado"]
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
def fmt_ars(n):
    s = f"{n:,.0f}".replace(",","X").replace(".",",").replace("X",".")
    return f"$ {s}"

def fmt_k(n):
    if n >= 1_000_000: return f"$ {n/1_000_000:.1f}M"
    if n >= 1_000:     return f"$ {n/1_000:.0f}k"
    return fmt_ars(n)

def fmt_usd(n, d):
    return f"U$S {n/d:,.0f}" if d > 0 else "U$S —"

def get_estado(row):
    if row["Pagado"]:             return ("✅ Listo",    GREEN,  "rgba(0,166,80,.12)"  if dark else "#e8f8ef")
    if pd.isna(row["Día Pago"]): return ("⚪ Sin Fecha", MUTED,  "rgba(0,0,0,.05)"    if dark else "#f5f5f5")
    if row["Día Pago"] < date.today():
        return ("🔴 Vencido",  RED,    "rgba(242,61,79,.12)" if dark else "#fff0f1")
    if row["Día Pago"] <= date.today() + timedelta(days=3):
        return ("🟡 Próximo",  ORANGE, "rgba(255,156,0,.12)" if dark else "#fff8ee")
    return ("🟢 Al Día", GREEN,  "rgba(0,166,80,.12)"  if dark else "#e8f8ef")

def procesar(df_base, dolar):
    df    = df_base.copy()
    total = df["Monto (ARS)"].sum()
    df["Peso (%)"] = (df["Monto (ARS)"] / total).fillna(0) if total > 0 else 0
    df["USD"]      = (df["Monto (ARS)"] / dolar).round(2)  if dolar > 0 else 0
    df["Cat."]     = df["Categoría"].apply(lambda x: str(x).strip() or "—")
    df["Estado"]   = df.apply(lambda r: get_estado(r)[0], axis=1)
    return df.sort_values(["Pagado","Día Pago"], ascending=[True,True], na_position="last")

# ─────────────────────────────────────────────
# 8. CARGA
# ─────────────────────────────────────────────
dolar   = get_dolar()
df_base = cargar_datos()

if not df_base.empty:
    df         = procesar(df_base, dolar)
    total_ars  = df["Monto (ARS)"].sum()
    pagado_ars = df[df["Pagado"] == True]["Monto (ARS)"].sum()
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
# 9. RENDER
# ─────────────────────────────────────────────
st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

# ── HEADER ──────────────────────────────────
meses = ["enero","febrero","marzo","abril","mayo","junio",
         "julio","agosto","septiembre","octubre","noviembre","diciembre"]
hoy   = date.today()
hoy_str = f"{hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

# SVG del Sol de Mayo — 16 rayos
sun_rays = ""
for i in range(16):
    angle = i * (360/16) - 90
    rad   = math.radians(angle)
    x1 = 16 + math.cos(rad) * 7
    y1 = 16 + math.sin(rad) * 7
    x2 = 16 + math.cos(rad) * 14
    y2 = 16 + math.sin(rad) * 14
    sun_rays += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#f6b40e" stroke-width="2" stroke-linecap="round"/>'

flag_opacity = "0.10" if dark else "0.12"

st.markdown(f"""
<div class="app-header">

  <!-- Bandera decorativa -->
  <div style="position:absolute;right:0;top:0;bottom:0;width:200px;
    display:flex;flex-direction:column;opacity:{flag_opacity};
    pointer-events:none;border-radius:0 0 0 40px;overflow:hidden">
    <div style="flex:1;background:#74acdf"></div>
    <div style="flex:1;background:#ffffff;position:relative;
      display:flex;align-items:center;justify-content:center">
      <!-- Sol de Mayo SVG -->
      <svg width="32" height="32" viewBox="0 0 32 32">
        {sun_rays}
        <circle cx="16" cy="16" r="5.5" fill="#f6b40e"/>
        <circle cx="16" cy="16" r="3.5" fill="#85340a" opacity="0.4"/>
      </svg>
    </div>
    <div style="flex:1;background:#74acdf"></div>
  </div>

  <!-- Fade gradiente sobre la bandera -->
  <div style="position:absolute;right:0;top:0;bottom:0;width:200px;
    background:linear-gradient(to right,
      {'rgba(10,10,10,1)' if dark else 'rgba(245,245,245,1)'} 0%,
      {'rgba(10,10,10,0)' if dark else 'rgba(245,245,245,0)'} 45%);
    pointer-events:none;z-index:1"></div>

  <!-- Contenido del header -->
  <div style="position:relative;z-index:2">
    <div class="header-brand">Finanzas <span>AR</span></div>
    <div class="header-date">{hoy_str}</div>
  </div>

  <div style="display:flex;gap:10px;align-items:center;position:relative;z-index:2">
    <div class="dolar-chip">
      <div class="dolar-label">USD Blue</div>
      <div class="dolar-val">${dolar:,.0f}</div>
    </div>
  </div>

</div>
""", unsafe_allow_html=True)

# ── DARK MODE TOGGLE ─────────────────────────
col_dm, _ = st.columns([1, 8])
with col_dm:
    lbl = "☀️ Claro" if dark else "🌙 Oscuro"
    if st.button(lbl, type="secondary"):
        st.session_state.dark = not dark
        st.rerun()

# ── NAVEGACIÓN ──────────────────────────────
nav_col1, nav_col2, nav_col3 = st.columns(3)
with nav_col1:
    if st.button("🏠  Inicio",  type="primary" if st.session_state.screen == "inicio"  else "secondary", use_container_width=True):
        st.session_state.screen = "inicio"
        st.rerun()
with nav_col2:
    if st.button("📋  Gastos",  type="primary" if st.session_state.screen == "gastos"  else "secondary", use_container_width=True):
        st.session_state.screen = "gastos"
        st.rerun()
with nav_col3:
    cat_label = f"🔍  {st.session_state.sel_cat}" if st.session_state.sel_cat else "🔍  Detalle"
    if st.button(cat_label, type="primary" if st.session_state.screen == "detalle" else "secondary",
                 use_container_width=True, disabled=st.session_state.sel_cat is None):
        st.session_state.screen = "detalle"
        st.rerun()

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PANTALLA: INICIO
# ─────────────────────────────────────────────
if st.session_state.screen == "inicio":

    col_main, col_side = st.columns([1.6, 1], gap="medium")

    with col_main:
        # Alertas
        if not vencidos.empty:
            items = ", ".join(vencidos["Ítem"].astype(str).tolist())
            st.markdown(f'<div class="alerta alerta-red">🔴 <strong>{len(vencidos)} vencido{"s" if len(vencidos)>1 else ""}</strong> — {items}</div>', unsafe_allow_html=True)
        if not proximos.empty:
            items = ", ".join(proximos["Ítem"].astype(str).tolist())
            st.markdown(f'<div class="alerta alerta-warn">🟡 <strong>{len(proximos)} próximo{"s" if len(proximos)>1 else ""}</strong> — {items}</div>', unsafe_allow_html=True)

        # Lista de categorías con onclick
        if not por_cat.empty:
            st.markdown('<div class="cat-list-card"><div style="padding:16px 20px 8px;font-size:11px;font-weight:700;color:'+MUTED+';letter-spacing:.06em;text-transform:uppercase">Por categoría</div>', unsafe_allow_html=True)
            for _, row in por_cat.iterrows():
                cat   = str(row["Cat."]).strip()
                monto = row["Monto (ARS)"]
                color = cat_color(cat)
                pct_cat = int(monto / total_ars * 100) if total_ars > 0 else 0
                st.markdown(f"""
                <div class="cat-row" onclick="">
                  <div class="cat-icon" style="background:{color}20;color:{color}">{cat}</div>
                  <div style="flex:1">
                    <div class="cat-name">{cat}</div>
                    <div style="height:3px;background:{BORDER};border-radius:3px;margin-top:5px;width:100%">
                      <div style="height:100%;width:{pct_cat}%;background:{color};border-radius:3px"></div>
                    </div>
                  </div>
                  <span class="cat-amount">{fmt_ars(monto)}</span>
                  <span class="cat-arrow">›</span>
                </div>
                """, unsafe_allow_html=True)

            # Botones de detalle por categoría
            cats = por_cat["Cat."].tolist()
            btn_cols = st.columns(min(len(cats), 5))
            for i, cat in enumerate(cats):
                with btn_cols[i % 5]:
                    if st.button(cat, key=f"cat_{i}", use_container_width=True):
                        st.session_state.sel_cat = cat
                        st.session_state.screen  = "detalle"
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    with col_side:
        if not por_cat.empty:
            # DONUT GRANDE
            colors_donut = [cat_color(c) for c in por_cat["Cat."]]
            fig = go.Figure(go.Pie(
                labels=por_cat["Cat."],
                values=por_cat["Monto (ARS)"],
                hole=0.60,
                marker=dict(colors=colors_donut, line=dict(color=SURFACE, width=3)),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
                direction="clockwise", sort=True,
            ))
            fig.add_annotation(
                text=f"<b>{fmt_k(total_ars)}</b>",
                x=0.5, y=0.55,
                font=dict(size=14, color=TEXT, family="Plus Jakarta Sans"),
                showarrow=False,
            )
            fig.add_annotation(
                text=f"<span style='font-size:11px'>{fmt_usd(total_ars, dolar)}</span>",
                x=0.5, y=0.42,
                font=dict(size=10, color=MUTED, family="Plus Jakarta Sans"),
                showarrow=False,
            )
            fig.update_layout(
                showlegend=False, height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor=PLOTBG, plot_bgcolor=PLOTBG,
            )
            st.markdown('<div class="card" style="padding:16px">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">Distribución</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # Split metrics dentro de la card
            st.markdown(f"""
            <div class="split-metrics">
              <div class="split-item">
                <div class="split-label">Pagado</div>
                <div class="split-val" style="color:{GREEN}">{fmt_k(pagado_ars)}</div>
              </div>
              <div style="width:1px;background:{BORDER}"></div>
              <div class="split-item">
                <div class="split-label">Pendiente</div>
                <div class="split-val" style="color:{RED}">{fmt_k(pend_ars)}</div>
              </div>
              <div style="width:1px;background:{BORDER}"></div>
              <div class="split-item">
                <div class="split-label">Cubierto</div>
                <div class="split-val" style="color:{ACCENT}">{pct}%</div>
              </div>
            </div>
            <div class="progress-bar" style="margin:14px 0 4px">
              <div class="progress-fill" style="width:{pct}%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Resumen rápido
            st.markdown(f"""
            <div class="card">
              <div class="card-title">Resumen</div>
              {''.join([f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {BORDER};font-size:13px"><span style="color:{MUTED};font-weight:500">{k}</span><span style="font-weight:700;color:{vc}">{vv}</span></div>'
              for k,vv,vc in [
                ("Total ítems", len(df), TEXT),
                ("Pagados", len(df[df["Pagado"]==True]), GREEN),
                ("Pendientes", len(df[df["Pagado"]==False]), ORANGE),
                ("Vencidos", len(vencidos), RED),
                ("Mayor gasto", df.loc[df["Monto (ARS)"].idxmax(),"Ítem"] if not df.empty else "—", TEXT),
              ]])}
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PANTALLA: GASTOS
# ─────────────────────────────────────────────
elif st.session_state.screen == "gastos":

    if df.empty:
        st.markdown(f'<div class="card" style="text-align:center;padding:48px;color:{MUTED}"><div style="font-size:40px;margin-bottom:12px">📭</div><div style="font-size:15px;font-weight:600">Sin datos</div></div>', unsafe_allow_html=True)
    else:
        col_tabla, col_info = st.columns([2.4, 1], gap="medium")

        with col_tabla:
            tab_todos, tab_pend, tab_pag = st.tabs([
                f"Todos  {len(df)}",
                f"Pendientes  {len(df[df['Pagado']==False])}",
                f"Pagados  {len(df[df['Pagado']==True])}",
            ])

            COL_CONFIG = {
                "Pagado":      st.column_config.CheckboxColumn("✓", width="small"),
                "Cat.":        st.column_config.TextColumn("Cat.", width="small"),
                "Categoría":   None,
                "Ítem":        st.column_config.TextColumn("Ítem"),
                "Monto (ARS)": st.column_config.NumberColumn("Monto", format="$ %d"),
                "USD":         st.column_config.NumberColumn("USD", format="U$S %.0f", disabled=True, width="small"),
                "Peso (%)":    st.column_config.ProgressColumn("Peso", format="%.1f%%", min_value=0, max_value=1, width="small"),
                "Día Pago":    st.column_config.DateColumn("Venc.", format="DD/MM/YY", width="small"),
                "Estado":      st.column_config.TextColumn("Estado", disabled=True, width="medium"),
            }
            COL_ORDER = ("Pagado","Cat.","Ítem","Monto (ARS)","USD","Peso (%)","Día Pago","Estado")

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

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            bc1, bc2 = st.columns([3, 1])
            with bc1:
                if st.button("Guardar y Sincronizar", type="primary", use_container_width=True):
                    try:
                        df_up = df_edit[["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]].copy()
                        df_up["Día Pago"] = df_up["Día Pago"].apply(lambda x: str(x) if pd.notnull(x) else "")
                        df_up["Pagado"]   = df_up["Pagado"].apply(lambda x: "TRUE" if x else "FALSE")
                        st.cache_data.clear()
                        hoja = get_gspread().open("Gastos_Henry").sheet1
                        hoja.clear()
                        hoja.append_row(df_up.columns.tolist())
                        hoja.append_rows(df_up.values.tolist())
                        st.success("✓ Sincronizado con Google Sheets")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            with bc2:
                if st.button("🔄 Recargar", type="secondary", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()

        with col_info:
            # Mini donut filtrado
            fig2 = go.Figure(go.Pie(
                labels=por_cat["Cat."], values=por_cat["Monto (ARS)"],
                hole=0.55,
                marker=dict(colors=[cat_color(c) for c in por_cat["Cat."]], line=dict(color=SURFACE, width=2)),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>$ %{value:,.0f}<extra></extra>",
            ))
            fig2.add_annotation(
                text=f"<b>{pct}%</b>", x=0.5, y=0.5,
                font=dict(size=18, color=ACCENT, family="Plus Jakarta Sans"),
                showarrow=False,
            )
            fig2.update_layout(
                showlegend=False, height=200,
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor=PLOTBG, plot_bgcolor=PLOTBG,
            )
            st.markdown(f'<div class="card" style="padding:16px"><div class="card-title">Distribución</div>', unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PANTALLA: DETALLE CATEGORÍA
# ─────────────────────────────────────────────
elif st.session_state.screen == "detalle":
    sel = st.session_state.sel_cat

    if sel is None or df.empty:
        st.info("Seleccioná una categoría desde Inicio")
    else:
        df_cat  = df[df["Cat."] == sel].copy()
        t_cat   = df_cat["Monto (ARS)"].sum()
        p_cat   = df_cat[df_cat["Pagado"]==True]["Monto (ARS)"].sum()
        pe_cat  = t_cat - p_cat
        pct_cat = int(t_cat / total_ars * 100) if total_ars > 0 else 0
        color   = cat_color(sel)

        col_det, col_det_side = st.columns([1.8, 1], gap="medium")

        with col_det:
            # Hero card de categoría
            st.markdown(f"""
            <div class="cat-hero" style="background:linear-gradient(135deg,{color}18,{color}06);border-color:{color}33">
              <div class="cat-hero-icon" style="background:{color}20;color:{color}">{sel}</div>
              <div class="cat-hero-label">{sel}</div>
              <div class="cat-hero-total">{fmt_ars(t_cat)}</div>
              <div class="cat-hero-sub">{pct_cat}% del total · {fmt_usd(t_cat, dolar)}</div>
              <div class="progress-bar" style="margin-top:16px">
                <div class="progress-fill" style="width:{pct_cat}%;background:{color}"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Mini stats
            n_items = len(df_cat)
            n_pag   = len(df_cat[df_cat["Pagado"]==True])
            n_pend  = len(df_cat[df_cat["Pagado"]==False])
            st.markdown(f"""
            <div class="mini-stats">
              <div class="mini-stat">
                <div class="mini-stat-val" style="color:{TEXT}">{n_items}</div>
                <div class="mini-stat-label">Items</div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-val" style="color:{GREEN}">{n_pag}</div>
                <div class="mini-stat-label">Pagados</div>
              </div>
              <div class="mini-stat">
                <div class="mini-stat-val" style="color:{RED}">{n_pend}</div>
                <div class="mini-stat-label">Pendientes</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Lista detalle
            st.markdown(f'<div class="cat-list-card"><div style="padding:16px 20px 8px;font-size:11px;font-weight:700;color:{MUTED};letter-spacing:.06em;text-transform:uppercase">Detalle</div>', unsafe_allow_html=True)
            for _, row in df_cat.iterrows():
                estado_txt, estado_color, estado_bg = get_estado(row)
                opac = "0.5" if row["Pagado"] else "1"
                dia  = str(row["Día Pago"]) if pd.notnull(row["Día Pago"]) else "—"
                st.markdown(f"""
                <div class="gasto-row" style="opacity:{opac}">
                  <div class="gasto-check" style="background:{'rgba(0,166,80,.12)' if row['Pagado'] else BORDER};
                    border:1.5px solid {'#00a650' if row['Pagado'] else BORDER};
                    color:{'#00a650' if row['Pagado'] else MUTED}">
                    {'✓' if row['Pagado'] else '○'}
                  </div>
                  <div class="gasto-info">
                    <div class="gasto-name">{row['Ítem']}</div>
                    <div class="gasto-meta">{dia}</div>
                  </div>
                  <div class="gasto-right">
                    <div class="gasto-monto">{fmt_ars(row['Monto (ARS)'])}</div>
                    <span class="pill" style="background:{estado_bg};color:{estado_color}">{estado_txt}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_det_side:
            # Comparativa pagado vs pendiente
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                x=["Pagado","Pendiente"],
                y=[p_cat, pe_cat],
                marker=dict(
                    color=[f"rgba(0,166,80,.75)", f"rgba(242,61,79,.75)"],
                    line=dict(color=[GREEN, RED], width=1.5),
                ),
                hovertemplate="%{x}: $ %{y:,.0f}<extra></extra>",
            ))
            fig3.update_layout(
                height=180,
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor=PLOTBG, plot_bgcolor=PLOTBG,
                xaxis=dict(tickfont=dict(color=MUTED, size=11, family="Plus Jakarta Sans"),
                           gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)"),
                yaxis=dict(visible=False),
                bargap=0.35,
            )
            st.markdown(f'<div class="card" style="padding:16px"><div class="card-title">Pagado vs Pendiente</div>', unsafe_allow_html=True)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

            # Info adicional
            mayor_item  = df_cat.loc[df_cat["Monto (ARS)"].idxmax(), "Ítem"] if not df_cat.empty else "—"
            mayor_monto = df_cat["Monto (ARS)"].max()
            st.markdown(f"""
            <div class="card">
              <div class="card-title">Info</div>
              {''.join([f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {BORDER};font-size:13px"><span style="color:{MUTED};font-weight:500">{k}</span><span style="font-weight:700;color:{vc}">{vv}</span></div>'
              for k, vv, vc in [
                ("Total cat.",  fmt_ars(t_cat),       TEXT),
                ("% del total", f"{pct_cat}%",         ACCENT),
                ("Pagado",      fmt_ars(p_cat),        GREEN),
                ("Pendiente",   fmt_ars(pe_cat),       RED),
                ("Mayor ítem",  mayor_item,            TEXT),
                ("",            fmt_ars(mayor_monto),  MUTED),
              ]])}
            </div>
            """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
