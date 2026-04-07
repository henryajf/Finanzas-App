import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.graph_objects as go
import io
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, timedelta

st.set_page_config(page_title="Finanzas AR", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")

for k, v in [("screen", "inicio"), ("show_add", False), ("show_add_ingreso", False), ("periodo_sel", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── COLORES ──
BG      = "#000000"
SURFACE = "#1C1C1E"
SURF2   = "#2C2C2E"
SURF3   = "#3A3A3C"
TEXT    = "#FFFFFF"
TEXT2   = "rgba(235,235,245,0.6)"
TEXT3   = "rgba(235,235,245,0.3)"
SEP     = "rgba(84,84,88,0.65)"
ACCENT  = "#0A84FF"
GREEN   = "#32D74B"
RED     = "#FF453A"
ORANGE  = "#FF9F0A"
YELLOW  = "#FFD60A"
PURPLE  = "#BF5AF2"
PLOTBG  = "rgba(0,0,0,0)"

CAT_COLORS = {
    "Servicios": "#FF9F0A", "Hogar": "#32D74B", "Supermercado": "#30D158",
    "Comida": "#FF453A", "Transporte": "#0A84FF", "Suscripciones": "#BF5AF2",
    "Fitness": "#FF6B35", "Salud": "#32D74B", "Credito": "#FF9F0A",
    "Personal": "#5AC8FA", "Viajes": "#0A84FF", "Otros": "#636366",
}

def cat_color(cat):
    c = str(cat)
    for k, v in CAT_COLORS.items():
        if k.lower() in c.lower(): return v
    return "#636366"

def cat_icon_svg(cat, color, size=34):
    c = str(cat).lower(); s = size; r = s * 0.22
    if "servicio" in c or "luz" in c or "gas" in c:
        ico = f'<polygon points="{s*.6},{s*.08} {s*.32},{s*.52} {s*.52},{s*.52} {s*.4},{s*.92} {s*.68},{s*.45} {s*.48},{s*.45}" fill="white"/>'
    elif "hogar" in c or "alquiler" in c:
        ico = f'<polygon points="{s*.5},{s*.15} {s*.85},{s*.48} {s*.77},{s*.48} {s*.77},{s*.82} {s*.23},{s*.82} {s*.23},{s*.48} {s*.15},{s*.48}" fill="white"/><rect x="{s*.4}" y="{s*.58}" width="{s*.2}" height="{s*.24}" rx="{s*.04}" fill="{color}" opacity="0.8"/>'
    elif "super" in c or "mercado" in c:
        ico = f'<path d="M{s*.12},{s*.2} L{s*.24},{s*.2} L{s*.38},{s*.62} L{s*.78},{s*.62} L{s*.88},{s*.32} L{s*.32},{s*.32}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="{s*.38}" cy="{s*.76}" r="{s*.07}" fill="white"/><circle cx="{s*.7}" cy="{s*.76}" r="{s*.07}" fill="white"/>'
    elif "credito" in c or "tarjeta" in c or "financ" in c:
        ico = f'<rect x="{s*.1}" y="{s*.28}" width="{s*.8}" height="{s*.44}" rx="{s*.07}" fill="white" opacity="0.9"/><rect x="{s*.1}" y="{s*.4}" width="{s*.8}" height="{s*.11}" fill="{color}"/><rect x="{s*.16}" y="{s*.56}" width="{s*.18}" height="{s*.08}" rx="{s*.03}" fill="{color}" opacity="0.7"/>'
    elif "suscripcion" in c:
        ico = f'<rect x="{s*.12}" y="{s*.18}" width="{s*.76}" height="{s*.5}" rx="{s*.07}" fill="white" opacity="0.9"/><rect x="{s*.2}" y="{s*.26}" width="{s*.6}" height="{s*.34}" rx="{s*.04}" fill="{color}"/><polygon points="{s*.38},{s*.36} {s*.38},{s*.5} {s*.58},{s*.43}" fill="white"/>'
    elif "transporte" in c or "nafta" in c:
        ico = f'<rect x="{s*.1}" y="{s*.44}" width="{s*.8}" height="{s*.28}" rx="{s*.07}" fill="white" opacity="0.9"/><path d="M{s*.24},{s*.44} L{s*.34},{s*.24} L{s*.66},{s*.24} L{s*.76},{s*.44}" fill="white" opacity="0.9"/><circle cx="{s*.28}" cy="{s*.76}" r="{s*.09}" fill="{color}"/><circle cx="{s*.28}" cy="{s*.76}" r="{s*.045}" fill="white"/><circle cx="{s*.72}" cy="{s*.76}" r="{s*.09}" fill="{color}"/><circle cx="{s*.72}" cy="{s*.76}" r="{s*.045}" fill="white"/>'
    elif "salud" in c or "farmac" in c:
        ico = f'<rect x="{s*.4}" y="{s*.12}" width="{s*.2}" height="{s*.76}" rx="{s*.06}" fill="white"/><rect x="{s*.12}" y="{s*.4}" width="{s*.76}" height="{s*.2}" rx="{s*.06}" fill="white"/>'
    elif "fitness" in c or "gym" in c:
        ico = f'<rect x="{s*.06}" y="{s*.38}" width="{s*.14}" height="{s*.24}" rx="{s*.05}" fill="white"/><rect x="{s*.8}" y="{s*.38}" width="{s*.14}" height="{s*.24}" rx="{s*.05}" fill="white"/><rect x="{s*.18}" y="{s*.44}" width="{s*.64}" height="{s*.12}" rx="{s*.04}" fill="white"/>'
    elif "comida" in c or "delivery" in c:
        ico = f'<rect x="{s*.15}" y="{s*.3}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/><rect x="{s*.15}" y="{s*.46}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/><rect x="{s*.15}" y="{s*.62}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/>'
    elif "personal" in c or "ocio" in c:
        ico = f'<circle cx="{s*.5}" cy="{s*.35}" r="{s*.17}" fill="white"/><path d="M{s*.2},{s*.85} Q{s*.2},{s*.6} {s*.5},{s*.6} Q{s*.8},{s*.6} {s*.8},{s*.85}" fill="white"/>'
    elif "viaje" in c:
        ico = f'<path d="M{s*.5},{s*.1} L{s*.88},{s*.58} L{s*.7},{s*.53} L{s*.64},{s*.82} L{s*.5},{s*.72} L{s*.36},{s*.82} L{s*.3},{s*.53} L{s*.12},{s*.58} Z" fill="white" opacity="0.9"/>'
    else:
        ico = f'<circle cx="{s*.5}" cy="{s*.38}" r="{s*.16}" fill="white" opacity="0.9"/><path d="M{s*.24},{s*.82} Q{s*.24},{s*.6} {s*.5},{s*.6} Q{s*.76},{s*.6} {s*.76},{s*.82}" fill="white" opacity="0.9"/>'
    return f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg"><rect width="{s}" height="{s}" rx="{r}" fill="{color}"/>{ico}</svg>'

st.markdown(f"""
<style>
:root{{
  --bg:{BG};--surface:{SURFACE};--surf2:{SURF2};--surf3:{SURF3};
  --text:{TEXT};--text2:{TEXT2};--text3:{TEXT3};--sep:{SEP};
  --accent:{ACCENT};--green:{GREEN};--red:{RED};--orange:{ORANGE};
}}
html, body, .stApp {{
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",Arial,sans-serif !important;
  background:{BG} !important;color:{TEXT} !important;
  /* ANTI SCROLL HORIZONTAL */
  overflow-x: clip !important; 
  width: 100vw !important;
  max-width: 100% !important;
}}
*{{box-sizing:border-box;-webkit-font-smoothing:antialiased;}}

/* Ocultar elementos nativos de Streamlit */
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="collapsedControl"] {{display:none !important;}}
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {{display:none !important;height:0 !important;overflow:hidden !important;}}
.stBottomContainer, .stChatFloatingInputContainer {{display:none !important;}}
.block-container {{padding:0 !important;max-width:100% !important; overflow-x: clip !important;}}
.wrap {{max-width:900px;margin:0 auto;padding:0 16px 80px;}}

/* ── HEADER ── */
.ios-hdr {{
  position:sticky;top:0;z-index:100;
  background:rgba(0,0,0,0.85);
  backdrop-filter:saturate(180%) blur(20px);
  -webkit-backdrop-filter:saturate(180%) blur(20px);
  border-bottom:0.5px solid rgba(255,255,255,0.1);
  padding:14px 16px 10px;
  margin:0 -16px 18px;
}}
.ios-hdr-top{{display:flex;justify-content:space-between;align-items:center;}}
.ios-title{{font-size:28px;font-weight:700;letter-spacing:-.02em;color:{TEXT};}}
.ios-title span{{color:{ACCENT};}}
.ios-date{{font-size:12px;color:{TEXT2};margin-top:2px;}}
.dolar-block{{text-align:right;}}
.dolar-lbl{{font-size:9px;color:{TEXT2};letter-spacing:.06em;text-transform:uppercase;font-weight:600;}}
.dolar-val{{font-size:20px;font-weight:700;color:{ACCENT};letter-spacing:-.01em;}}
.dolar-trend{{font-size:11px;margin-top:1px;}}

/* ── PERIODO BAR ── */
.periodo-bar{{
  display:flex;align-items:center;gap:6px;
  padding:8px 0 0;margin-top:8px;
  border-top:0.5px solid rgba(255,255,255,0.07);
  overflow-x:auto;scrollbar-width:none;
}}
.periodo-bar::-webkit-scrollbar{{display:none;}}
.periodo-chip{{
  flex-shrink:0;padding:4px 12px;border-radius:20px;
  font-size:12px;font-weight:600;cursor:pointer;
  border:none;font-family:-apple-system,sans-serif;
  transition:all .15s;
}}
.periodo-chip-active{{background:{ACCENT};color:#fff;}}
.periodo-chip-inactive{{background:{SURF2};color:{TEXT2};}}

/* ── BOTONES ── */
.stButton>button[kind="primary"]{{
  background:{ACCENT} !important;color:#fff !important;border:none !important;
  border-radius:10px !important;padding:10px 18px !important;
  font-family:-apple-system,sans-serif !important;
  font-size:14px !important;font-weight:600 !important;
  box-shadow:none !important;
}}
.stButton>button[kind="secondary"]{{
  background:{SURF2} !important;color:{TEXT2} !important;border:none !important;
  border-radius:10px !important;padding:10px 18px !important;
  font-family:-apple-system,sans-serif !important;
  font-size:14px !important;font-weight:600 !important;
  box-shadow:none !important;
}}

/* ── TARJETAS ── */
.kpi-grid-main{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px;}}
.kpi-grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;}}
@media(max-width:700px){{.kpi-grid-main{{grid-template-columns:repeat(2,1fr);}}}}
.kpi-card{{background:{SURFACE};border-radius:12px;padding:14px 15px;}}
.kpi-lbl{{font-size:11px;font-weight:500;color:{TEXT2};margin-bottom:5px;letter-spacing:.01em;}}
.kpi-val{{font-size:19px;font-weight:700;letter-spacing:-.02em;line-height:1.1;}}
.kpi-sub{{font-size:11px;color:{TEXT2};margin-top:4px;}}
.kpi-bar{{height:3px;background:rgba(255,255,255,.1);border-radius:3px;overflow:hidden;margin-top:8px;}}
.kpi-bar-fill{{height:100%;border-radius:3px;}}

/* ── ALERTAS ── */
.alert{{padding:11px 13px;border-radius:10px;font-size:13px;margin-bottom:8px;line-height:1.5;}}
.alert-r{{background:rgba(255,69,58,.12);color:#FF6B63;}}
.alert-o{{background:rgba(255,159,10,.12);color:#FFB340;}}
.alert-g{{background:rgba(50,215,75,.1);color:#3EDD60;}}
.alert-b{{background:rgba(10,132,255,.1);color:#5BA4FF;}}

/* ── GRUPOS / FILAS ── */
.grp{{background:{SURFACE};border-radius:12px;overflow:hidden;margin-bottom:8px;}}
.grp-hdr{{display:flex;align-items:center;gap:9px;padding:9px 13px;border-bottom:0.5px solid {SEP};}}
.grp-hdr-lbl{{flex:1;font-size:12px;font-weight:600;color:{TEXT2};letter-spacing:.03em;text-transform:uppercase;}}
.grp-hdr-amt{{font-size:13px;font-weight:600;}}
.pend-badge{{font-size:10px;font-weight:700;padding:2px 6px;border-radius:20px;background:rgba(255,69,58,.18);color:{RED};margin-left:3px;}}
.row{{display:flex;align-items:center;gap:11px;padding:10px 13px;position:relative;}}
.row::after{{content:'';position:absolute;bottom:0;left:57px;right:0;height:0.5px;background:{SEP};}}
.row:last-child::after{{display:none;}}
.row-body{{flex:1;min-width:0;}}
.row-name{{font-size:15px;font-weight:400;color:{TEXT};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.row-name-paid{{font-size:15px;font-weight:400;color:{TEXT2};text-decoration:line-through;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.row-sub{{font-size:12px;color:{TEXT2};margin-top:2px;}}
.row-right{{text-align:right;flex-shrink:0;}}
.row-amt{{font-size:15px;font-weight:600;color:{TEXT};}}
.row-amt-paid{{font-size:15px;font-weight:400;color:{TEXT2};text-decoration:line-through;}}
.row-usd{{font-size:11px;color:{TEXT2};margin-top:2px;}}

/* ── BADGES ── */
.badge{{display:inline-flex;align-items:center;font-size:11px;font-weight:600;padding:2px 7px;border-radius:20px;white-space:nowrap;}}
.badge-paid{{background:rgba(50,215,75,.15);color:{GREEN};}}
.badge-venc{{background:rgba(255,69,58,.18);color:{RED};}}
.badge-hoy{{background:rgba(255,69,58,.18);color:{RED};}}
.badge-prox{{background:rgba(255,159,10,.15);color:{ORANGE};}}
.badge-soon{{background:rgba(255,214,10,.12);color:{YELLOW};}}
.badge-ok{{background:rgba(50,215,75,.1);color:{GREEN};}}
.badge-none{{background:rgba(99,99,102,.3);color:{TEXT2};}}
.badge-henry{{background:rgba(10,132,255,.15);color:{ACCENT};}}
.badge-jaike{{background:rgba(191,90,242,.15);color:{PURPLE};}}

/* ── SECCION ── */
.sec-lbl{{font-size:12px;font-weight:400;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;padding:0 4px;margin:16px 0 6px;}}

/* ── ADD PANELS ── */
.add-panel{{background:{SURFACE};border-radius:12px;padding:14px;margin-bottom:10px;}}
.add-panel-green{{background:{SURFACE};border-radius:12px;padding:14px;margin-bottom:10px;border-left:3px solid {GREEN};}}
.stTextInput>div>div>input,.stNumberInput>div>div>input{{
  background:{SURF2} !important;border:none !important;border-radius:9px !important;
  color:{TEXT} !important;font-size:15px !important;
  font-family:-apple-system,sans-serif !important;
}}
.toast-ok{{display:inline-flex;align-items:center;gap:7px;padding:9px 13px;border-radius:9px;font-size:13px;font-weight:500;margin-bottom:8px;background:rgba(50,215,75,.12);color:{GREEN};}}
.toast-err{{display:inline-flex;align-items:center;gap:7px;padding:9px 13px;border-radius:9px;font-size:13px;font-weight:500;margin-bottom:8px;background:rgba(255,69,58,.12);color:{RED};}}

/* ── TENDENCIAS ── */
.hist-row{{display:flex;align-items:center;padding:10px 14px;border-bottom:0.5px solid {SEP};gap:10px;}}
.hist-row:last-child{{border-bottom:none;}}
.hist-row-mes{{font-size:14px;font-weight:500;color:{TEXT};min-width:100px;}}
.hist-pill-active{{font-size:10px;font-weight:700;padding:2px 6px;border-radius:20px;background:rgba(10,132,255,.2);color:{ACCENT};margin-left:5px;}}
.hist-bars{{flex:1;display:flex;flex-direction:column;gap:3px;}}
.hist-bar-row{{display:flex;align-items:center;gap:6px;}}
.hist-bar-bg{{flex:1;height:4px;background:rgba(255,255,255,.08);border-radius:4px;overflow:hidden;}}
.hist-bar-fill{{height:100%;border-radius:4px;}}
.hist-bar-lbl{{font-size:11px;color:{TEXT2};min-width:30px;text-align:right;}}
.ing-row{{display:flex;align-items:center;gap:11px;padding:10px 13px;position:relative;}}
.ing-row::after{{content:'';position:absolute;bottom:0;left:57px;right:0;height:0.5px;background:{SEP};}}
.ing-row:last-child::after{{display:none;}}

/* ── BOTTOM TAB BAR (MINIMALISTA) ── */
.btab-bar{{
  position:fixed !important;bottom:0 !important;left:0 !important;right:0 !important;
  z-index:2147483647 !important;display:flex !important;align-items:stretch;
  background:rgba(0,0,0,0.3) !important;
  backdrop-filter:saturate(180%) blur(10px);
  -webkit-backdrop-filter:saturate(180%) blur(10px);
  border-top:none !important;
  padding-bottom:env(safe-area-inset-bottom,0px) !important;
  height:calc(42px + env(safe-area-inset-bottom,0px)) !important;
  transform:translateZ(0);will-change:transform;isolation:isolate;
}}
.btab{{
  flex:1;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:2px;
  background:transparent;border:none;cursor:pointer;
  padding:0;
  color:rgba(255,255,255,0.15);
  font-size:8px;
  font-weight:400;
  font-family:-apple-system,sans-serif;
  -webkit-tap-highlight-color:transparent;
}}
.btab-active{{color:rgba(10,132,255,0.6) !important;}}
.btab-ico{{width:15px;height:15px;fill:currentColor;}}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{{background:transparent !important;border-bottom:0.5px solid {SEP} !important;gap:0 !important;padding:0 !important;}}
.stTabs [data-baseweb="tab"]{{background:transparent !important;color:{TEXT2} !important;font-size:13px !important;font-weight:500 !important;border-bottom:2px solid transparent !important;padding:9px 14px !important;margin-bottom:-1px !important;}}
.stTabs [aria-selected="true"]{{color:{ACCENT} !important;border-bottom-color:{ACCENT} !important;}}
.stTabs [data-baseweb="tab-highlight"]{{display:none !important;}}
.stTabs [data-baseweb="tab-panel"]{{padding:10px 0 0 !important;}}
[data-testid="stDataEditorContainer"]{{background:{SURFACE} !important;border:none !important;border-radius:12px !important;overflow:hidden !important;}}

@media(max-width:700px){{.ios-title{{font-size:22px;}}.wrap{{padding:0 12px 80px;}}}}
hr{{display:none !important;}}
[data-testid="stVerticalBlock"]>div{{gap:0 !important;}}
</style>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
# CONEXION Y CARGA DE DATOS
# ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_gspread():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json", scope)
    except Exception:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos_maestro():
    try:
        hoja = get_gspread().open("Gastos_Henry").sheet1
        data = hoja.get_all_values()
    except Exception as e:
        st.error(f"Error conectando con Google Sheets: {e}")
        return pd.DataFrame()

    data = [r for r in data if any(str(c).strip() for c in r)]
    if not data or len(data) < 2:
        return pd.DataFrame()

    headers_new = ["Categoria","Item","Monto (ARS)","Dia Pago","Pagado","Periodo","Tasa USD"]
    headers_legacy = ["Categoria","Item","Monto (ARS)","Dia Pago","Pagado"]
    primera = [str(c).strip().lower() for c in data[0]]
    tiene_periodo = "periodo" in primera

    if tiene_periodo:
        filas = data[1:]
        filas = [r + [""] * (7 - len(r)) for r in filas if len(r) >= 2]
        if not filas: return pd.DataFrame()
        df = pd.DataFrame(filas, columns=headers_new)
    else:
        filas = data[1:] if primera[0] in ["categoria","cat","category"] else data
        filas = [r + [""] * (5 - len(r)) for r in filas if len(r) >= 2]
        if not filas: return pd.DataFrame()
        df = pd.DataFrame(filas, columns=headers_legacy)
        df["Periodo"] = date.today().strftime("%Y-%m")
        df["Tasa USD"] = 0.0

    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
    df["Tasa USD"]    = pd.to_numeric(df["Tasa USD"],    errors="coerce").fillna(0)
    df["Dia Pago"]    = pd.to_datetime(df["Dia Pago"],   errors="coerce").dt.date
    df["Pagado"]      = df["Pagado"].apply(lambda x: str(x).strip().upper() in ["TRUE","VERDADERO","SI","1"])
    df = df[~((df["Monto (ARS)"] == 0) & (df["Item"].str.strip() == ""))]
    return df.reset_index(drop=True)

@st.cache_data(ttl=600)
def cargar_ingresos():
    try:
        sh = get_gspread().open("Gastos_Henry")
        ws = next((h for h in sh.worksheets() if h.title.strip().lower() == "ingresos"), None)
        if not ws:
            ws = sh.add_worksheet(title="Ingresos", rows=200, cols=8)
            ws.append_row(["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha"])
            return pd.DataFrame()
        data = ws.get_all_values()
        if not data or len(data) < 2: return pd.DataFrame()
        headers = ["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha"]
        filas = data[1:]
        filas = [r + [""] * (8 - len(r)) for r in filas if len(r) >= 2]
        if not filas: return pd.DataFrame()
        df = pd.DataFrame(filas, columns=headers)
        for col in ["Monto ARS","Monto USD","Monto Original","Tasa USD/ARS"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df["Fecha"]   = pd.to_datetime(df["Fecha"],  errors="coerce").dt.date
        df = df[df["Monto ARS"] > 0]
        df["Periodo"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.strftime("%Y-%m")
        return df.reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_dolar():
    try:
        return float(requests.get("https://dolarapi.com/v1/dolares/blue", timeout=5).json()["venta"])
    except Exception:
        return 1450.0

@st.cache_data(ttl=3600)
def get_dolar_tendencia():
    try:
        venta = get_dolar()
        hist = requests.get("https://api.argentinadatos.com/v1/cotizaciones/dolares/blue", timeout=5).json()
        if isinstance(hist, list) and len(hist) >= 2:
            ayer = float(hist[-2].get("venta", venta))
            diff = venta - ayer
            pct = round((diff / ayer) * 100, 2) if ayer > 0 else 0.0
            return venta, ayer, diff, pct
        return venta, venta, 0.0, 0.0
    except Exception:
        return get_dolar(), 0, 0.0, 0.0

def guardar_hoja_maestro(df_guardar, dolar_actual=None):
    df_up = df_guardar.copy()
    df_up["Categoria"] = df_up["Item"].apply(categorizar)
    if "Periodo" not in df_up.columns:
        df_up["Periodo"] = date.today().strftime("%Y-%m")
    if "Tasa USD" not in df_up.columns:
        df_up["Tasa USD"] = dolar_actual or 0.0
    else:
        if dolar_actual:
            df_up["Tasa USD"] = df_up["Tasa USD"].apply(lambda x: dolar_actual if (x == 0 or pd.isna(x)) else x)
    df_up = df_up[["Categoria","Item","Monto (ARS)","Dia Pago","Pagado","Periodo","Tasa USD"]]
    df_up["Dia Pago"] = df_up["Dia Pago"].apply(lambda x: str(x) if pd.notnull(x) else "")
    df_up["Pagado"]   = df_up["Pagado"].apply(lambda x: "TRUE" if x else "FALSE")
    hoja = get_gspread().open("Gastos_Henry").sheet1
    hoja.clear()
    hoja.append_row(df_up.columns.tolist())
    hoja.append_rows(df_up.values.tolist())
    st.cache_data.clear()

def guardar_ingreso(desc, persona, moneda, monto_orig, monto_ars, monto_usd, tasa, fecha):
    sh = get_gspread().open("Gastos_Henry")
    ws = next((h for h in sh.worksheets() if h.title.strip().lower() == "ingresos"), None)
    if not ws:
        ws = sh.add_worksheet(title="Ingresos", rows=200, cols=8)
        ws.append_row(["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha"])
    ws.append_row([desc, persona, moneda, monto_orig, monto_ars, monto_usd, tasa, str(fecha)])
    st.cache_data.clear()

def marcar_pagado_maestro(idx, df_full, dolar_actual):
    df_act = df_full.copy()
    if idx < len(df_act):
        df_act.at[idx, "Pagado"] = True
        guardar_hoja_maestro(df_act, dolar_actual)

def categorizar(item):
    i = str(item).lower()
    if any(x in i for x in ["mercadocredito","tarjeta","visa","mastercard","amex","credito","banco","financiamiento","cuota"]): return "Credito/Financiacion"
    elif any(x in i for x in ["luz","edenor","edesur","agua","aysa","gas","metrogas"]): return "Servicios"
    elif any(x in i for x in ["super","coto","carrefour","dia","jumbo","disco","mercado","almacen","chino"]): return "Supermercado"
    elif any(x in i for x in ["alquiler","expensas","abl","limpieza"]): return "Hogar"
    elif any(x in i for x in ["nafta","ypf","shell","axion","uber","cabify","taxi","peaje","sube","transporte"]): return "Transporte"
    elif any(x in i for x in ["netflix","spotify","prime","hbo","disney","youtube","telecentro","fibertel","internet","claro","personal","movistar","meli","google","apple","vpn"]): return "Suscripciones"
    elif any(x in i for x in ["gym","gimnasio","megatlon","sportclub","crossfit"]): return "Fitness"
    elif any(x in i for x in ["farmacia","osde","swiss","galeno","medico","salud","depilife"]): return "Salud"
    elif any(x in i for x in ["mc","burger","pedidosya","rappi","helado","pizza","restaurante","bar","cafe"]): return "Comida/Delivery"
    elif any(x in i for x in ["ropa","zapat","zara","dafiti","peluqueria","estetica"]): return "Personal/Ocio"
    elif any(x in i for x in ["vuelo","pasaje","hotel","airbnb"]): return "Viajes"
    else: return "Otros"

def fmt_ars(n):
    s = f"{n:,.0f}".replace(",","X").replace(".",",").replace("X",".")
    return f"$ {s}"

def fmt_usd_from_ars(n, d):
    return f"U$S {n/d:,.0f}" if d > 0 else "U$S -"

def fmt_usd(n):
    return f"U$S {n:,.2f}"

def badge_venc(row):
    if row["Pagado"]: return f'<span class="badge badge-paid">Pagado</span>'
    dia = row["Dia Pago"]
    if pd.isna(dia) or dia is None: return f'<span class="badge badge-none">Sin fecha</span>'
    diff = (dia - date.today()).days
    fd = dia.strftime("%-d %b")
    if diff < 0:  return f'<span class="badge badge-venc">Vencido {fd}</span>'
    if diff == 0: return f'<span class="badge badge-hoy">Hoy</span>'
    if diff <= 3:  return f'<span class="badge badge-prox">{diff}d — {fd}</span>'
    if diff <= 10: return f'<span class="badge badge-soon">{diff}d — {fd}</span>'
    return f'<span class="badge badge-ok">{fd}</span>'

def badge_persona(persona):
    p = str(persona).upper()
    if p == "HENRY": return f'<span class="badge badge-henry">Henry</span>'
    if p == "JAIKE": return f'<span class="badge badge-jaike">Jaike</span>'
    return f'<span class="badge badge-none">{persona}</span>'

def procesar(df_base, dolar_live):
    df = df_base.copy()
    df["Categoria"] = df["Item"].apply(categorizar)
    total = df["Monto (ARS)"].sum()
    def calc_usd(row):
        tasa = row.get("Tasa USD", 0)
        t = tasa if tasa and tasa > 0 else dolar_live
        return round(row["Monto (ARS)"] / t, 2) if t > 0 else 0
    df["USD"] = df.apply(calc_usd, axis=1)
    df["Cat"] = df["Categoria"]
    return df.sort_values(["Pagado","Dia Pago"], ascending=[True,True], na_position="last")

def exportar_excel(df, df_ing=None):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_exp = df[["Cat","Item","Monto (ARS)","USD","Dia Pago","Pagado","Periodo"]].copy()
        df_exp.columns = ["Categoria","Item","Monto ARS","USD","Vencimiento","Pagado","Periodo"]
        df_exp.to_excel(writer, index=False, sheet_name="Gastos")
        resumen = df.groupby(["Periodo","Cat"])["Monto (ARS)"].sum().reset_index()
        resumen.to_excel(writer, index=False, sheet_name="Resumen")
        if df_ing is not None and not df_ing.empty:
            df_ing.to_excel(writer, index=False, sheet_name="Ingresos")
    return output.getvalue()

def calcular_mes_anterior(periodo_str):
    y, m = map(int, periodo_str.split('-'))
    if m == 1:
        return f"{y-1}-12"
    else:
        return f"{y}-{m-1:02d}"

# ── CARGA INICIAL ──
MESES = ["enero","febrero","marzo","abril","mayo","junio",
         "julio","agosto","septiembre","octubre","noviembre","diciembre"]
hoy          = date.today()
hoy_str      = f"{hoy.day} de {MESES[hoy.month-1]} de {hoy.year}"
periodo_actual = hoy.strftime("%Y-%m")

dolar = get_dolar()
dolar_val, dolar_ayer, dolar_diff, dolar_pct = get_dolar_tendencia()

df_maestro   = cargar_datos_maestro()
df_ing_todo  = cargar_ingresos()

# Periodos disponibles
if not df_maestro.empty:
    periodos_disponibles = sorted(df_maestro["Periodo"].dropna().unique(), reverse=True)
    if periodo_actual not in periodos_disponibles:
        periodos_disponibles = [periodo_actual] + list(periodos_disponibles)
else:
    periodos_disponibles = [periodo_actual]

if st.session_state.periodo_sel is None or st.session_state.periodo_sel not in periodos_disponibles:
    st.session_state.periodo_sel = periodo_actual

periodo_viendo = st.session_state.periodo_sel

def label_periodo(p):
    try:
        y, m = p.split("-")
        return f"{MESES[int(m)-1].capitalize()} {y}"
    except Exception:
        return p


# ══════════════════════════════════════════════════════════════════
# ── NAVEGACIÓN OCULTA (EN SIDEBAR) PARA EVITAR ESPACIOS EN MÓVIL ──
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    for p in periodos_disponibles[:8]:
        if st.button(label_periodo(p), key=f"nav_periodo_{p}", type="secondary"):
            st.session_state.periodo_sel = p
            st.rerun()
    for screen in ["inicio", "ingresos", "gastos", "tendencias"]:
        if st.button(screen, key=f"nav_{screen}", type="secondary"):
            st.session_state.screen = screen
            st.rerun()

nav_offset = len(periodos_disponibles[:8])
_sc = st.session_state.screen


# Filtrar al periodo seleccionado
if not df_maestro.empty:
    df_base_periodo = df_maestro[df_maestro["Periodo"] == periodo_viendo].copy()
    df = procesar(df_base_periodo, dolar)
    total_ars   = df["Monto (ARS)"].sum()
    pagado_ars  = df[df["Pagado"] == True]["Monto (ARS)"].sum()
    pend_ars    = total_ars - pagado_ars
    pct_pag     = int(pagado_ars / total_ars * 100) if total_ars > 0 else 0
    por_cat     = df.groupby("Cat")["Monto (ARS)"].sum().reset_index().sort_values("Monto (ARS)", ascending=False)
    es_mes_actual = (periodo_viendo == periodo_actual)
    vencidos = df[(df["Pagado"]==False) & df["Dia Pago"].notna() & (df["Dia Pago"] < hoy)] if es_mes_actual else pd.DataFrame()
    proximos = df[(df["Pagado"]==False) & df["Dia Pago"].notna() & (df["Dia Pago"] >= hoy) & (df["Dia Pago"] <= hoy + timedelta(days=3))] if es_mes_actual else pd.DataFrame()
else:
    df_base_periodo = pd.DataFrame()
    df = por_cat = pd.DataFrame()
    total_ars = pagado_ars = pend_ars = pct_pag = 0
    vencidos = proximos = pd.DataFrame()
    es_mes_actual = True

# Ingresos del periodo seleccionado
if not df_ing_todo.empty:
    df_ing_periodo = df_ing_todo[df_ing_todo["Periodo"] == periodo_viendo]
else:
    df_ing_periodo = pd.DataFrame()

total_ing_ars  = df_ing_periodo["Monto ARS"].sum() if not df_ing_periodo.empty else 0
total_ing_usd  = df_ing_periodo["Monto USD"].sum() if not df_ing_periodo.empty else 0
ing_henry      = df_ing_periodo[df_ing_periodo["Persona"].str.upper()=="HENRY"]["Monto ARS"].sum() if not df_ing_periodo.empty else 0
ing_jaike      = df_ing_periodo[df_ing_periodo["Persona"].str.upper()=="JAIKE"]["Monto ARS"].sum() if not df_ing_periodo.empty else 0
balance_ars    = total_ing_ars - total_ars
balance_pct    = int(total_ing_ars / total_ars * 100) if total_ars > 0 else 0


# ── PWA & BOTTOM TAB BAR ──
st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#000000">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-title" content="Finanzas AR">
<link rel="apple-touch-icon" href="https://fav.farm/💳">
<script>
function haptic(ms){try{navigator.vibrate&&navigator.vibrate(ms||50);}catch(e){}}
document.addEventListener('DOMContentLoaded',function(){
  function patchInputs(){
    document.querySelectorAll('input[type="number"]').forEach(function(el){if(!el.getAttribute('inputmode')){el.setAttribute('inputmode','decimal');}});
    document.querySelectorAll('input[type="text"]').forEach(function(el){if(!el.getAttribute('inputmode')){el.setAttribute('inputmode','text');}});
  }
  function killBottom(){
    var sel=['[data-testid="stBottom"]','[data-testid="stBottomBlockContainer"]','.stBottomContainer','.stChatFloatingInputContainer'];
    sel.forEach(function(s){document.querySelectorAll(s).forEach(function(el){el.style.cssText='display:none!important;height:0!important;overflow:hidden!important;';});});
  }
  patchInputs(); killBottom();
  var obs=new MutationObserver(function(){patchInputs();killBottom();});
  obs.observe(document.body,{childList:true,subtree:true});
});
</script>
""", unsafe_allow_html=True)

# JS chips → botones
st.markdown(f"""
<script>
(function(){{
  function attachChips(){{
    var chips=document.querySelectorAll('.periodo-chip');
    if(!chips.length){{setTimeout(attachChips,200);return;}}
    chips.forEach(function(chip,idx){{
      chip.onclick=function(){{haptic(10);var btns=document.querySelectorAll('[data-testid=stBaseButton-secondary]');if(btns[idx])btns[idx].click();}};
    }});
  }}
  attachChips();
}})();
</script>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="btab-bar">
  <button class="btab {'btab-active' if _sc=='inicio' else ''}"
    onclick="(function(){{haptic(8);var b=document.querySelectorAll('[data-testid=stBaseButton-secondary]');b[{nav_offset}]&&b[{nav_offset}].click();}})()">
    <svg class="btab-ico" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
    <span>Inicio</span>
  </button>
  <button class="btab {'btab-active' if _sc=='ingresos' else ''}"
    onclick="(function(){{haptic(8);var b=document.querySelectorAll('[data-testid=stBaseButton-secondary]');b[{nav_offset+1}]&&b[{nav_offset+1}].click();}})()">
    <svg class="btab-ico" viewBox="0 0 24 24"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>
    <span>Ingresos</span>
  </button>
  <button class="btab {'btab-active' if _sc=='gastos' else ''}"
    onclick="(function(){{haptic(8);var b=document.querySelectorAll('[data-testid=stBaseButton-secondary]');b[{nav_offset+2}]&&b[{nav_offset+2}].click();}})()">
    <svg class="btab-ico" viewBox="0 0 24 24"><path d="M20 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/></svg>
    <span>Gastos</span>
  </button>
  <button class="btab {'btab-active' if _sc=='tendencias' else ''}"
    onclick="(function(){{haptic(8);var b=document.querySelectorAll('[data-testid=stBaseButton-secondary]');b[{nav_offset+3}]&&b[{nav_offset+3}].click();}})()">
    <svg class="btab-ico" viewBox="0 0 24 24"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>
    <span>Tendencias</span>
  </button>
</div>
""", unsafe_allow_html=True)


st.markdown('<div class="wrap">', unsafe_allow_html=True)

# ── HEADER ──
if dolar_diff > 0:
    trend_html = f'<span style="color:{RED};font-size:11px;font-weight:700">▲ {dolar_pct:+.1f}%</span>'
elif dolar_diff < 0:
    trend_html = f'<span style="color:{GREEN};font-size:11px;font-weight:700">▼ {dolar_pct:.1f}%</span>'
else:
    trend_html = f'<span style="color:{TEXT2};font-size:11px">—</span>'

chips_html = ""
for p in periodos_disponibles[:8]:
    activo = "active" if p == periodo_viendo else "inactive"
    chips_html += f'<span class="periodo-chip periodo-chip-{activo}" data-periodo="{p}">{label_periodo(p)}</span>'

st.markdown(f"""
<div class="ios-hdr">
  <div class="ios-hdr-top">
    <div>
      <div class="ios-title">Finanzas <span>AR</span></div>
      <div class="ios-date">{hoy_str}</div>
    </div>
    <div class="dolar-block">
      <div class="dolar-lbl">USD Blue</div>
      <div class="dolar-val">$ {dolar:,.0f}</div>
      <div class="dolar-trend">{trend_html}</div>
    </div>
  </div>
  <div class="periodo-bar" id="periodoBar">{chips_html}</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PANTALLA: INICIO
# ══════════════════════════════════════════════════════════════════
if st.session_state.screen == "inicio":

    bc = GREEN if balance_ars >= 0 else RED
    bs = "+" if balance_ars >= 0 else ""

    if not es_mes_actual:
        st.markdown(f'<div class="alert alert-b">📅 Historial — <strong>{label_periodo(periodo_viendo)}</strong> (solo lectura)</div>', unsafe_allow_html=True)

    # Alertas de vencimiento
    if es_mes_actual:
        if not vencidos.empty:
            items_v = " · ".join(r["Item"] for _, r in vencidos.iterrows())
            st.markdown(f'<div class="alert alert-r"><strong>{len(vencidos)} vencido{"s" if len(vencidos)>1 else ""}</strong> — {items_v}</div>', unsafe_allow_html=True)
        if not proximos.empty:
            st.markdown(f'<div class="alert alert-o">Vencen en 3 días: {" · ".join(r["Item"] for _, r in proximos.iterrows())}</div>', unsafe_allow_html=True)

    # ── EL NUEVO DASHBOARD OPTIMIZADO DE 4 TARJETAS ──
    st.markdown(f"""<div class="kpi-grid-main">
      <div class="kpi-card"><div class="kpi-lbl">Ingresos</div>
        <div class="kpi-val" style="color:{GREEN}">{fmt_ars(total_ing_ars)}</div>
        <div class="kpi-sub">{fmt_usd(total_ing_usd)}</div></div>
      <div class="kpi-card"><div class="kpi-lbl">Gastos ({pct_pag}% pagado)</div>
        <div class="kpi-val">{fmt_ars(total_ars)}</div>
        <div class="kpi-sub">{fmt_usd_from_ars(total_ars, dolar)}</div>
        <div class="kpi-bar"><div class="kpi-bar-fill" style="width:{pct_pag}%;background:{ACCENT}"></div></div></div>
      <div class="kpi-card"><div class="kpi-lbl">Balance</div>
        <div class="kpi-val" style="color:{bc}">{bs}{fmt_ars(balance_ars)}</div>
        <div class="kpi-sub">{"Superávit" if balance_ars >= 0 else "Déficit"}</div></div>
      <div class="kpi-card"><div class="kpi-lbl">Pendiente de pago</div>
        <div class="kpi-val" style="color:{RED}">{fmt_ars(pend_ars)}</div>
        <div class="kpi-sub">{fmt_usd_from_ars(pend_ars, dolar)}</div></div>
    </div>""", unsafe_allow_html=True)

    # KPIs Henry / Jaike
    if total_ing_ars > 0:
        ph = int(ing_henry / total_ing_ars * 100) if total_ing_ars > 0 else 0
        pj = int(ing_jaike / total_ing_ars * 100) if total_ing_ars > 0 else 0
        st.markdown(f"""<div class="kpi-grid-2" style="margin-bottom:16px">
          <div class="kpi-card" style="border-left:3px solid {ACCENT}">
            <div class="kpi-lbl" style="color:{ACCENT}">Henry</div>
            <div class="kpi-val" style="color:{ACCENT}">{fmt_ars(ing_henry)}</div>
            <div class="kpi-sub">{fmt_usd_from_ars(ing_henry, dolar)} · {ph}%</div></div>
          <div class="kpi-card" style="border-left:3px solid {PURPLE}">
            <div class="kpi-lbl" style="color:{PURPLE}">Jaike</div>
            <div class="kpi-val" style="color:{PURPLE}">{fmt_ars(ing_jaike)}</div>
            <div class="kpi-sub">{fmt_usd_from_ars(ing_jaike, dolar)} · {pj}%</div></div>
        </div>""", unsafe_allow_html=True)

    # Botones agregar (solo mes actual)
    if es_mes_actual:
        ba1, ba2 = st.columns(2)
        with ba1:
            lbl_g = "Cancelar" if st.session_state.show_add else "＋ Gasto"
            if st.button(lbl_g, type="secondary" if st.session_state.show_add else "primary", use_container_width=True, key="btn_add_g"):
                st.session_state.show_add = not st.session_state.show_add
                st.session_state.show_add_ingreso = False
                st.rerun()
        with ba2:
            lbl_i = "Cancelar" if st.session_state.show_add_ingreso else "＋ Ingreso"
            if st.button(lbl_i, type="secondary" if st.session_state.show_add_ingreso else "primary", use_container_width=True, key="btn_add_i"):
                st.session_state.show_add_ingreso = not st.session_state.show_add_ingreso
                st.session_state.show_add = False
                st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── LÓGICA DE CLONACIÓN INTELIGENTE ──
        if not df_maestro.empty:
            periodo_ant = calcular_mes_anterior(periodo_actual)
            df_ant = df_maestro[df_maestro["Periodo"] == periodo_ant]
            
            if not df_ant.empty:
                cats_fijas = ["Servicios", "Suscripciones", "Hogar", "Salud", "Fitness", "Credito/Financiacion"]
                items_actuales = df_base_periodo["Item"].str.lower().str.strip().tolist() if not df_base_periodo.empty else []
                
                df_clonables = df_ant[df_ant["Categoria"].isin(cats_fijas)]
                df_clonables = df_clonables[~df_clonables["Item"].str.lower().str.strip().isin(items_actuales)]
                
                if not df_clonables.empty:
                    with st.expander(f"🔄 Clonar {len(df_clonables)} gastos fijos de {label_periodo(periodo_ant)}"):
                        st.markdown('<div style="font-size:13px;color:var(--text2);margin-bottom:10px">Se detectaron gastos fijos del mes pasado que aún no están en este mes. Copialos en estado "Pendiente" con un clic.</div>', unsafe_allow_html=True)
                        for _, r in df_clonables.iterrows():
                            st.markdown(f'<div style="font-size:14px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.1)">{r["Item"]} <span style="float:right;color:var(--text2)">{fmt_ars(r["Monto (ARS)"])}</span></div>', unsafe_allow_html=True)
                        
                        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                        if st.button("Clonar ítems ahora", type="primary", use_container_width=True):
                            nuevos_registros = []
                            y_act, m_act = map(int, periodo_actual.split('-'))
                            
                            for _, r in df_clonables.iterrows():
                                nueva_fecha = None
                                if pd.notnull(r["Dia Pago"]) and str(r["Dia Pago"]).strip() != "":
                                    try:
                                        old_d = pd.to_datetime(r["Dia Pago"])
                                        dia_seguro = min(old_d.day, 28)
                                        nueva_fecha = date(y_act, m_act, dia_seguro)
                                    except:
                                        pass

                                nuevos_registros.append({
                                    "Categoria": r["Categoria"],
                                    "Item": r["Item"],
                                    "Monto (ARS)": r["Monto (ARS)"],
                                    "Dia Pago": nueva_fecha,
                                    "Pagado": False,
                                    "Periodo": periodo_actual,
                                    "Tasa USD": dolar
                                })
                            
                            if nuevos_registros:
                                df_nuevos = pd.DataFrame(nuevos_registros)
                                guardar_hoja_maestro(pd.concat([df_maestro, df_nuevos], ignore_index=True), dolar)
                                st.rerun()

        # Panel agregar gasto
        if st.session_state.show_add:
            st.markdown('<div class="add-panel">', unsafe_allow_html=True)
            a1, a2, a3, a4 = st.columns([2, 1.2, 1.2, 0.8])
            with a1: new_item  = st.text_input("Descripción", placeholder="Ej: Netflix", key="new_item")
            with a2: new_monto = st.number_input("Monto ARS", min_value=0, step=100, key="new_monto")
            with a3: new_fecha = st.date_input("Vencimiento", value=None, key="new_fecha")
            with a4:
                st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
                if st.button("Agregar", type="primary", use_container_width=True):
                    if not new_item.strip():
                        st.markdown('<div class="toast-err">Ingresa una descripción</div>', unsafe_allow_html=True)
                    elif new_monto <= 0:
                        st.markdown('<div class="toast-err">El monto debe ser mayor a 0</div>', unsafe_allow_html=True)
                    else:
                        nueva = pd.DataFrame([{"Categoria": categorizar(new_item), "Item": new_item.strip(),
                                                "Monto (ARS)": float(new_monto), "Dia Pago": new_fecha,
                                                "Pagado": False, "Periodo": periodo_actual, "Tasa USD": dolar}])
                        try:
                            guardar_hoja_maestro(pd.concat([df_maestro, nueva], ignore_index=True), dolar)
                            st.session_state.show_add = False
                            st.rerun()
                        except Exception as e:
                            st.markdown(f'<div class="toast-err">Error: {e}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Panel agregar ingreso
        if st.session_state.show_add_ingreso:
            st.markdown('<div class="add-panel-green">', unsafe_allow_html=True)
            i1, i2, i3 = st.columns([2, 1, 1])
            with i1: ing_desc    = st.text_input("Descripción", placeholder="Ej: Sueldo Henry", key="ing_desc")
            with i2: ing_persona = st.selectbox("Persona", ["Henry","Jaike"], key="ing_persona")
            with i3: ing_moneda  = st.selectbox("Moneda", ["ARS","USD"], key="ing_moneda")
            i4, i5, i6 = st.columns([1.5, 1.5, 1])
            moneda_sel = st.session_state.get("ing_moneda","ARS")
            with i4: ing_monto = st.number_input(f"Monto {moneda_sel}", min_value=0.0, step=100.0, key="ing_monto")
            with i5:
                if moneda_sel == "ARS":
                    equiv = ing_monto / dolar if dolar > 0 else 0
                    st.markdown(f'<div style="padding:7px 0"><div style="font-size:11px;color:{TEXT2};font-weight:600;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Equiv. USD</div><div style="font-size:18px;font-weight:700;color:{GREEN}">U$S {equiv:,.2f}</div></div>', unsafe_allow_html=True)
                    monto_ars_f = ing_monto; monto_usd_f = equiv
                else:
                    equiv = ing_monto * dolar
                    st.markdown(f'<div style="padding:7px 0"><div style="font-size:11px;color:{TEXT2};font-weight:600;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Equiv. ARS</div><div style="font-size:18px;font-weight:700;color:{GREEN}">{fmt_ars(equiv)}</div></div>', unsafe_allow_html=True)
                    monto_ars_f = equiv; monto_usd_f = ing_monto
            with i6: ing_fecha = st.date_input("Fecha", value=hoy, key="ing_fecha")
            st.markdown(f'<div style="font-size:12px;color:{TEXT2};margin:6px 0 8px">Tasa: <strong style="color:{TEXT}">$ {dolar:,.0f} ARS/USD</strong></div>', unsafe_allow_html=True)
            if st.button("Guardar ingreso", type="primary", use_container_width=True):
                if not ing_desc.strip():
                    st.markdown('<div class="toast-err">Ingresa una descripción</div>', unsafe_allow_html=True)
                elif ing_monto <= 0:
                    st.markdown('<div class="toast-err">El monto debe ser mayor a 0</div>', unsafe_allow_html=True)
                else:
                    try:
                        guardar_ingreso(ing_desc.strip(), ing_persona, moneda_sel, ing_monto, round(monto_ars_f,2), round(monto_usd_f,4), dolar, ing_fecha)
                        st.session_state.show_add_ingreso = False
                        st.rerun()
                    except Exception as e:
                        st.markdown(f'<div class="toast-err">Error: {e}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # Lista de gastos por categoría
    if df.empty:
        st.markdown(f'<div class="grp" style="padding:28px;text-align:center;color:{TEXT2}">Sin datos para {label_periodo(periodo_viendo)}.</div>', unsafe_allow_html=True)
    else:
        busq = st.text_input("", placeholder="Buscar gasto...", label_visibility="collapsed", key="busqueda_input")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        df_vista = df.copy()
        if busq.strip():
            df_vista = df_vista[df_vista["Item"].str.contains(busq.strip(), case=False, na=False)]

        cats_orden = df_vista.groupby("Cat").apply(lambda g: g["Pagado"].eq(False).sum()).sort_values(ascending=False).index.tolist()
        st.markdown(f'<div class="sec-lbl">Gastos — {label_periodo(periodo_viendo)}</div>', unsafe_allow_html=True)

        for cat in cats_orden:
            df_cat = df_vista[df_vista["Cat"] == cat]
            t_cat  = df_cat["Monto (ARS)"].sum()
            color  = cat_color(cat)
            n_pend = int(df_cat["Pagado"].eq(False).sum())
            badge  = f'<span class="pend-badge">{n_pend}</span>' if n_pend > 0 else ""
            ico_hdr = cat_icon_svg(cat, color, size=22)
            st.markdown(f'<div class="grp"><div class="grp-hdr"><div style="width:22px;height:22px;border-radius:5px;overflow:hidden;flex-shrink:0">{ico_hdr}</div><span class="grp-hdr-lbl">{cat}{badge}</span><span class="grp-hdr-amt" style="color:{color}">{fmt_ars(t_cat)}</span></div>', unsafe_allow_html=True)
            for idx, row in df_cat.iterrows():
                paid  = row["Pagado"]
                nc    = "row-name-paid" if paid else "row-name"
                ac    = "row-amt-paid"  if paid else "row-amt"
                op    = "0.5" if paid else "1"
                ico   = cat_icon_svg(cat, color, size=34)
                tasa_r = row.get("Tasa USD", 0)
                usd_v  = row["Monto (ARS)"] / tasa_r if tasa_r > 0 else row["Monto (ARS)"] / dolar
                st.markdown(f'<div class="row" style="opacity:{op}"><div style="width:34px;height:34px;flex-shrink:0;border-radius:8px;overflow:hidden">{ico}</div><div class="row-body"><div class="{nc}">{row["Item"]}</div><div class="row-sub">{badge_venc(row)}</div></div><div class="row-right"><div class="{ac}">{fmt_ars(row["Monto (ARS)"])}</div><div class="row-usd">U$S {usd_v:,.0f}</div></div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Marcar pagado
        if es_mes_actual:
            pend_items = df_vista[df_vista["Pagado"] == False]
            if not pend_items.empty:
                with st.expander(f"Marcar como pagado ({len(pend_items)} pendientes)"):
                    for idx, row in pend_items.iterrows():
                        cn, cb = st.columns([3,1])
                        with cn:
                            st.markdown(f'<div style="font-size:14px;padding:5px 0">{row["Item"]} — {fmt_ars(row["Monto (ARS)"])}</div>', unsafe_allow_html=True)
                        with cb:
                            if st.button("✓ Pagado", key=f"pay_{idx}", use_container_width=True):
                                try:
                                    marcar_pagado_maestro(idx, df_maestro, dolar)
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))

        # Top 5
        st.markdown(f'<div class="sec-lbl">Top 5 gastos</div><div class="grp">', unsafe_allow_html=True)
        for _, row in df.nlargest(5,"Monto (ARS)").iterrows():
            color  = cat_color(row["Cat"])
            pct_t  = int(row["Monto (ARS)"] / total_ars * 100) if total_ars > 0 else 0
            ico    = cat_icon_svg(row["Cat"], color, size=34)
            tasa_r = row.get("Tasa USD", 0)
            usd_v  = row["Monto (ARS)"] / tasa_r if tasa_r > 0 else row["Monto (ARS)"] / dolar
            st.markdown(f'<div class="row"><div style="width:34px;height:34px;flex-shrink:0;border-radius:8px;overflow:hidden">{ico}</div><div class="row-body"><div class="row-name">{row["Item"]}</div><div class="row-sub">{row["Cat"]} · {pct_t}% del total</div></div><div class="row-right"><div class="row-amt">{fmt_ars(row["Monto (ARS)"])}</div><div class="row-usd">U$S {usd_v:,.0f}</div></div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Distribución por categoría (lista simple, sin gráfico)
        st.markdown(f'<div class="sec-lbl">Por categoría</div><div class="grp" style="padding:14px 16px">', unsafe_allow_html=True)
        max_cat = por_cat["Monto (ARS)"].max() if not por_cat.empty else 1
        for _, r in por_cat.iterrows():
            pct_c = int(r["Monto (ARS)"] / total_ars * 100) if total_ars > 0 else 0
            bar_w = int(r["Monto (ARS)"] / max_cat * 100)
            color = cat_color(r["Cat"])
            st.markdown(f"""
            <div style="margin-bottom:10px">
              <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                <span style="font-size:13px;color:{TEXT}">{r['Cat']}</span>
                <div style="text-align:right">
                  <span style="font-size:13px;font-weight:600;color:{color}">{fmt_ars(r['Monto (ARS)'])}</span>
                  <span style="font-size:11px;color:{TEXT2};margin-left:6px">{pct_c}%</span>
                </div>
              </div>
              <div style="height:3px;background:rgba(255,255,255,.08);border-radius:3px;overflow:hidden">
                <div style="width:{bar_w}%;height:100%;background:{color};border-radius:3px"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Resumen
        n_pag2 = int(df["Pagado"].sum()); n_pend2 = len(df) - n_pag2
        mayor  = df.loc[df["Monto (ARS)"].idxmax(),"Item"] if not df.empty else "-"
        mayor_m = df["Monto (ARS)"].max() if not df.empty else 0
        st.markdown(f"""<div class="grp" style="padding:14px 16px">
          <div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px">Resumen</div>
          <div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:0.5px solid {SEP};font-size:14px"><span style="color:{TEXT2}">Total ítems</span><span style="font-weight:600">{len(df)}</span></div>
          <div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:0.5px solid {SEP};font-size:14px"><span style="color:{TEXT2}">Pagados</span><span style="color:{GREEN};font-weight:600">{n_pag2}</span></div>
          <div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:0.5px solid {SEP};font-size:14px"><span style="color:{TEXT2}">Pendientes</span><span style="color:{ORANGE};font-weight:600">{n_pend2}</span></div>
          <div style="display:flex;justify-content:space-between;padding:9px 0;border-bottom:0.5px solid {SEP};font-size:14px"><span style="color:{TEXT2}">Vencidos</span><span style="color:{RED};font-weight:600">{len(vencidos)}</span></div>
          <div style="padding:9px 0;font-size:14px"><span style="color:{TEXT2}">Mayor gasto</span><br><span style="font-weight:600;color:{TEXT}">{mayor}</span><br><span style="font-size:12px;color:{TEXT2}">{fmt_ars(mayor_m)}</span></div>
        </div>""", unsafe_allow_html=True)

        _, ce, _ = st.columns([1,1,1])
        with ce:
            st.download_button("Exportar Excel", data=exportar_excel(df, df_ing_todo),
                               file_name=f"gastos_{periodo_viendo}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# PANTALLA: INGRESOS
# ══════════════════════════════════════════════════════════════════
elif st.session_state.screen == "ingresos":
    bc2 = GREEN if balance_ars >= 0 else RED
    bs2 = "+" if balance_ars >= 0 else ""

    if not es_mes_actual:
        st.markdown(f'<div class="alert alert-b">📅 Ingresos de <strong>{label_periodo(periodo_viendo)}</strong></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sec-lbl">Ingresos — {label_periodo(periodo_viendo)}</div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="kpi-grid">
      <div class="kpi-card"><div class="kpi-lbl">Total</div>
        <div class="kpi-val" style="color:{GREEN}">{fmt_ars(total_ing_ars)}</div>
        <div class="kpi-sub">{fmt_usd(total_ing_usd)}</div></div>
      <div class="kpi-card" style="border-left:3px solid {ACCENT}"><div class="kpi-lbl" style="color:{ACCENT}">Henry</div>
        <div class="kpi-val" style="color:{ACCENT}">{fmt_ars(ing_henry)}</div>
        <div class="kpi-sub">{fmt_usd_from_ars(ing_henry, dolar)}</div></div>
      <div class="kpi-card" style="border-left:3px solid {PURPLE}"><div class="kpi-lbl" style="color:{PURPLE}">Jaike</div>
        <div class="kpi-val" style="color:{PURPLE}">{fmt_ars(ing_jaike)}</div>
        <div class="kpi-sub">{fmt_usd_from_ars(ing_jaike, dolar)}</div></div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="kpi-card" style="margin-bottom:12px"><div class="kpi-lbl">Balance vs gastos</div><div class="kpi-val" style="color:{bc2}">{bs2}{fmt_ars(balance_ars)}</div><div class="kpi-sub">{"Superávit" if balance_ars>=0 else "Déficit"} · Gastos: {fmt_ars(total_ars)}</div></div>', unsafe_allow_html=True)

    # Botón agregar ingreso
    if es_mes_actual:
        lbl_i2 = "Cancelar" if st.session_state.show_add_ingreso else "＋ Agregar ingreso"
        if st.button(lbl_i2, type="secondary" if st.session_state.show_add_ingreso else "primary", use_container_width=True, key="btn_ing2"):
            st.session_state.show_add_ingreso = not st.session_state.show_add_ingreso
            st.rerun()
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.session_state.show_add_ingreso:
            st.markdown('<div class="add-panel-green">', unsafe_allow_html=True)
            i1, i2, i3 = st.columns([2,1,1])
            with i1: ing_desc2    = st.text_input("Descripción", placeholder="Ej: Sueldo Henry", key="ing_desc2")
            with i2: ing_persona2 = st.selectbox("Persona", ["Henry","Jaike"], key="ing_persona2")
            with i3: ing_moneda2  = st.selectbox("Moneda", ["ARS","USD"], key="ing_moneda2")
            i4, i5, i6 = st.columns([1.5, 1.5, 1])
            moneda_sel2 = st.session_state.get("ing_moneda2","ARS")
            with i4: ing_monto2 = st.number_input(f"Monto {moneda_sel2}", min_value=0.0, step=100.0, key="ing_monto2")
            with i5:
                if moneda_sel2 == "ARS":
                    equiv2 = ing_monto2 / dolar if dolar > 0 else 0
                    st.markdown(f'<div style="padding:7px 0"><div style="font-size:11px;color:{TEXT2};font-weight:600;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Equiv. USD</div><div style="font-size:18px;font-weight:700;color:{GREEN}">U$S {equiv2:,.2f}</div></div>', unsafe_allow_html=True)
                    mars2 = ing_monto2; musd2 = equiv2
                else:
                    equiv2 = ing_monto2 * dolar
                    st.markdown(f'<div style="padding:7px 0"><div style="font-size:11px;color:{TEXT2};font-weight:600;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Equiv. ARS</div><div style="font-size:18px;font-weight:700;color:{GREEN}">{fmt_ars(equiv2)}</div></div>', unsafe_allow_html=True)
                    mars2 = equiv2; musd2 = ing_monto2
            with i6: ing_fecha2 = st.date_input("Fecha", value=hoy, key="ing_fecha2")
            st.markdown(f'<div style="font-size:12px;color:{TEXT2};margin:6px 0 8px">Tasa: <strong style="color:{TEXT}">$ {dolar:,.0f} ARS/USD</strong></div>', unsafe_allow_html=True)
            if st.button("Guardar", type="primary", use_container_width=True, key="guardar_ing2"):
                if not ing_desc2.strip():
                    st.markdown('<div class="toast-err">Ingresa una descripción</div>', unsafe_allow_html=True)
                elif ing_monto2 <= 0:
                    st.markdown('<div class="toast-err">El monto debe ser mayor a 0</div>', unsafe_allow_html=True)
                else:
                    try:
                        guardar_ingreso(ing_desc2.strip(), ing_persona2, moneda_sel2, ing_monto2, round(mars2,2), round(musd2,4), dolar, ing_fecha2)
                        st.session_state.show_add_ingreso = False
                        st.rerun()
                    except Exception as e:
                        st.markdown(f'<div class="toast-err">Error: {e}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # Detalle de ingresos del periodo
    if df_ing_periodo.empty:
        st.markdown(f'<div class="grp" style="padding:28px;text-align:center;color:{TEXT2}">Sin ingresos en {label_periodo(periodo_viendo)}.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sec-lbl">Detalle — {label_periodo(periodo_viendo)}</div><div class="grp">', unsafe_allow_html=True)
        for _, row in df_ing_periodo.sort_values("Fecha", ascending=False).iterrows():
            persona  = str(row.get("Persona",""))
            desc     = str(row.get("Descripcion",""))
            monto_ar = float(row.get("Monto ARS",0))
            monto_ud = float(row.get("Monto USD",0))
            tasa_r   = float(row.get("Tasa USD/ARS",0))
            fecha_r  = row.get("Fecha","")
            fecha_s  = fecha_r.strftime("%-d %b %Y") if hasattr(fecha_r,"strftime") else str(fecha_r)
            ico_c    = ACCENT if persona.upper() == "HENRY" else PURPLE
            st.markdown(f"""<div class="ing-row">
              <div style="width:34px;height:34px;border-radius:8px;background:{ico_c};display:flex;align-items:center;justify-content:center;flex-shrink:0">
                <svg width="18" height="18" viewBox="0 0 18 18"><rect x="2" y="5" width="14" height="9" rx="2" fill="white" opacity="0.9"/><rect x="2" y="7" width="14" height="2" fill="{ico_c}"/><circle cx="5" cy="11" r="1.2" fill="{ico_c}" opacity="0.7"/></svg>
              </div>
              <div class="row-body"><div class="row-name">{desc}</div>
              <div class="row-sub">{badge_persona(persona)} &nbsp;{fecha_s} · Tasa $ {tasa_r:,.0f}</div></div>
              <div class="row-right">
                <div class="row-amt" style="color:{GREEN}">{fmt_ars(monto_ar)}</div>
                <div class="row-usd">U$S {monto_ud:,.2f}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PANTALLA: GASTOS (editor)
# ══════════════════════════════════════════════════════════════════
elif st.session_state.screen == "gastos":
    if df.empty:
        st.markdown(f'<div class="grp" style="padding:28px;text-align:center;color:{TEXT2}">Sin datos para {label_periodo(periodo_viendo)}.</div>', unsafe_allow_html=True)
    else:
        if not es_mes_actual:
            st.markdown(f'<div class="alert alert-o">📅 Editando <strong>{label_periodo(periodo_viendo)}</strong>. Guardar reescribirá la hoja maestra.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="font-size:13px;color:{TEXT2};margin-bottom:12px">Editá, agregá o marcá pagos. Guardá para sincronizar.</div>', unsafe_allow_html=True)

        tab_todos, tab_pend, tab_pag = st.tabs([
            f"Todos  {len(df)}",
            f"Pendientes  {len(df[df['Pagado']==False])}",
            f"Pagados  {len(df[df['Pagado']==True])}"
        ])
        COL_CONFIG = {
            "Pagado":     st.column_config.CheckboxColumn("Pagado", width="small"),
            "Item":       st.column_config.TextColumn("Ítem"),
            "Monto (ARS)":st.column_config.NumberColumn("ARS", format="$ %d"),
            "USD":        st.column_config.NumberColumn("USD", format="U$S %.0f", disabled=True, width="small"),
            "Dia Pago":   st.column_config.DateColumn("Vencimiento", format="DD/MM/YY"),
            "Periodo":    st.column_config.TextColumn("Periodo", disabled=True, width="small"),
            "Tasa USD":   st.column_config.NumberColumn("Tasa $", disabled=True, width="small"),
        }
        COL_ORDER = ("Pagado","Item","Monto (ARS)","USD","Dia Pago","Periodo","Tasa USD")

        def render_tabla(data, key):
            return st.data_editor(data, column_config=COL_CONFIG, column_order=COL_ORDER,
                                   num_rows="dynamic", use_container_width=True, hide_index=True, key=key)

        with tab_todos: df_edit = render_tabla(df, "t_todos")
        with tab_pend:  render_tabla(df[df["Pagado"]==False].copy(), "t_pend")
        with tab_pag:   render_tabla(df[df["Pagado"]==True].copy(), "t_pag")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        bc1, bc2, bc3 = st.columns([2.5, 0.8, 0.8])
        with bc1:
            if st.button("Guardar y Sincronizar", type="primary", use_container_width=True):
                try:
                    df_otros    = df_maestro[df_maestro["Periodo"] != periodo_viendo].copy()
                    df_combinado = pd.concat([df_otros, df_edit], ignore_index=True)
                    guardar_hoja_maestro(df_combinado, dolar)
                    st.markdown('<div class="toast-ok">Cambios guardados</div>', unsafe_allow_html=True)
                    st.rerun()
                except Exception as e:
                    st.markdown(f'<div class="toast-err">Error: {e}</div>', unsafe_allow_html=True)
        with bc2:
            if st.button("Recargar", type="secondary", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with bc3:
            if not df.empty:
                st.download_button("Excel", data=exportar_excel(df, df_ing_todo),
                                    file_name=f"gastos_{periodo_viendo}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# PANTALLA: TENDENCIAS — análisis histórico completo con ingresos
# ══════════════════════════════════════════════════════════════════
elif st.session_state.screen == "tendencias":
    st.markdown('<div class="sec-lbl">Análisis histórico</div>', unsafe_allow_html=True)

    if df_maestro.empty or df_maestro["Periodo"].nunique() < 2:
        st.markdown(f'<div class="grp" style="padding:28px;text-align:center;color:{TEXT2}">Necesitás al menos 2 meses de datos.<br><br>Seguí registrando y volvé en el mes que viene.</div>', unsafe_allow_html=True)
    else:
        # Construir tabla maestra histórica por periodo
        gasto_m = df_maestro.groupby("Periodo")["Monto (ARS)"].sum().reset_index()
        gasto_m.columns = ["Periodo","Gastos"]
        gasto_m["Label"] = gasto_m["Periodo"].apply(label_periodo)

        # ─ INGRESOS HISTÓRICOS ─
        ing_m = pd.DataFrame()
        if not df_ing_todo.empty and "Periodo" in df_ing_todo.columns:
            ing_henry_m  = df_ing_todo[df_ing_todo["Persona"].str.upper()=="HENRY"].groupby("Periodo")["Monto ARS"].sum().reset_index()
            ing_henry_m.columns  = ["Periodo","Henry"]
            ing_jaike_m  = df_ing_todo[df_ing_todo["Persona"].str.upper()=="JAIKE"].groupby("Periodo")["Monto ARS"].sum().reset_index()
            ing_jaike_m.columns  = ["Periodo","Jaike"]
            ing_total_m  = df_ing_todo.groupby("Periodo")["Monto ARS"].sum().reset_index()
            ing_total_m.columns  = ["Periodo","Ingresos"]
            ing_m = ing_total_m.merge(ing_henry_m, on="Periodo", how="left").merge(ing_jaike_m, on="Periodo", how="left").fillna(0)

        # Tabla combinada por periodo
        hist = gasto_m.merge(ing_m, on="Periodo", how="left").fillna(0).sort_values("Periodo", ascending=False)
        hist["Balance"] = hist.get("Ingresos", pd.Series(0, index=hist.index)) - hist["Gastos"]
        hist["Label"]   = hist["Periodo"].apply(label_periodo)

        tiene_ingresos = "Ingresos" in hist.columns and hist["Ingresos"].sum() > 0

        # KPIs acumulados
        total_g = hist["Gastos"].sum()
        total_i = hist["Ingresos"].sum() if tiene_ingresos else 0
        bal_tot = total_i - total_g
        prom_g  = hist["Gastos"].mean()
        n_meses = len(hist)
        bc_t    = GREEN if bal_tot >= 0 else RED
        bs_t    = "+" if bal_tot >= 0 else ""

        st.markdown(f"""<div class="kpi-grid">
          <div class="kpi-card"><div class="kpi-lbl">Gastos acumulados</div>
            <div class="kpi-val" style="color:{RED}">{fmt_ars(total_g)}</div>
            <div class="kpi-sub">{n_meses} meses · prom. {fmt_ars(prom_g)}/mes</div></div>
          <div class="kpi-card"><div class="kpi-lbl">Ingresos acumulados</div>
            <div class="kpi-val" style="color:{GREEN}">{fmt_ars(total_i) if tiene_ingresos else "—"}</div>
            <div class="kpi-sub">{fmt_usd_from_ars(total_i, dolar) if tiene_ingresos else "Sin datos"}</div></div>
          <div class="kpi-card"><div class="kpi-lbl">Balance acumulado</div>
            <div class="kpi-val" style="color:{bc_t}">{bs_t}{fmt_ars(bal_tot) if tiene_ingresos else "—"}</div>
            <div class="kpi-sub">{"Superávit total" if bal_tot >= 0 else "Déficit total"}</div></div>
        </div>""", unsafe_allow_html=True)

        # Meses extremos
        mes_max = hist.loc[hist["Gastos"].idxmax()]
        mes_min = hist.loc[hist["Gastos"].idxmin()]
        st.markdown(f"""<div class="kpi-grid-2" style="margin-bottom:14px">
          <div class="kpi-card"><div class="kpi-lbl">Mes más caro</div>
            <div class="kpi-val" style="color:{RED};font-size:17px">{mes_max['Label']}</div>
            <div class="kpi-sub">{fmt_ars(mes_max['Gastos'])}</div></div>
          <div class="kpi-card"><div class="kpi-lbl">Mes más barato</div>
            <div class="kpi-val" style="color:{GREEN};font-size:17px">{mes_min['Label']}</div>
            <div class="kpi-sub">{fmt_ars(mes_min['Gastos'])}</div></div>
        </div>""", unsafe_allow_html=True)

        # ── TABLA HISTÓRICA POR MES (minimalista) ──
        st.markdown('<div class="sec-lbl">Balance real por mes</div><div class="grp">', unsafe_allow_html=True)

        max_g = hist["Gastos"].max() if not hist.empty else 1
        max_i = hist["Ingresos"].max() if tiene_ingresos else 1

        for _, row in hist.iterrows():
            g      = row["Gastos"]
            i      = row.get("Ingresos",0)
            henry  = row.get("Henry",0)
            jaike  = row.get("Jaike",0)
            bal    = row.get("Balance",0)
            bc_r   = GREEN if bal >= 0 else RED
            bs_r   = "+" if bal >= 0 else ""
            bar_g  = int(g / max_g * 100) if max_g > 0 else 0
            bar_i  = int(i / max_i * 100) if max_i > 0 else 0
            activo = f'<span class="hist-pill-active">actual</span>' if row["Periodo"] == periodo_viendo else ""

            aportes_html = ""
            if tiene_ingresos and (henry > 0 or jaike > 0):
                aportes_html = f'<span style="font-size:11px;color:{TEXT2}">Henry: <strong style="color:{ACCENT}">{fmt_ars(henry)}</strong></span>'
                if jaike > 0:
                    aportes_html += f' &nbsp;·&nbsp; <span style="font-size:11px;color:{TEXT2}">Jaike: <strong style="color:{PURPLE}">{fmt_ars(jaike)}</strong></span>'

            st.markdown(f"""<div class="hist-row">
              <div style="min-width:110px">
                <div class="hist-row-mes">{row['Label']}{activo}</div>
                {f'<div style="font-size:11px;color:{bc_r};font-weight:600;margin-top:2px">{bs_r}{fmt_ars(bal)}</div>' if tiene_ingresos else ''}
                <div style="margin-top:3px">{aportes_html}</div>
              </div>
              <div class="hist-bars">
                <div class="hist-bar-row">
                  <span style="font-size:10px;color:{TEXT3};width:14px">G</span>
                  <div class="hist-bar-bg"><div class="hist-bar-fill" style="width:{bar_g}%;background:{RED}"></div></div>
                  <span class="hist-bar-lbl">{fmt_ars(g)}</span>
                </div>
                {f'<div class="hist-bar-row"><span style="font-size:10px;color:{TEXT3};width:14px">I</span><div class="hist-bar-bg"><div class="hist-bar-fill" style="width:{bar_i}%;background:{GREEN}"></div></div><span class="hist-bar-lbl">{fmt_ars(i)}</span></div>' if tiene_ingresos else ''}
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── APORTES COMBINADOS HENRY VS JAIKE ──
        if tiene_ingresos and "Henry" in hist.columns:
            hist_rev = hist.sort_values("Periodo")
            has_both = hist_rev["Henry"].sum() > 0 and hist_rev["Jaike"].sum() > 0

            if has_both:
                st.markdown('<div class="sec-lbl">Aportes combinados Henry vs Jaike</div>', unsafe_allow_html=True)
                fig_stack = go.Figure()
                fig_stack.add_trace(go.Bar(
                    name="Henry", x=hist_rev["Label"], y=hist_rev["Henry"],
                    marker_color=ACCENT, opacity=0.85,
                    hovertemplate="<b>Henry</b> %{x}<br>%{y:,.0f}<extra></extra>"
                ))
                fig_stack.add_trace(go.Bar(
                    name="Jaike", x=hist_rev["Label"], y=hist_rev["Jaike"],
                    marker_color=PURPLE, opacity=0.85,
                    hovertemplate="<b>Jaike</b> %{x}<br>%{y:,.0f}<extra></extra>"
                ))
                fig_stack.update_layout(
                    barmode="stack", height=240,
                    margin=dict(t=8,b=8,l=8,r=8),
                    paper_bgcolor=PLOTBG, plot_bgcolor=PLOTBG,
                    legend=dict(font=dict(color=TEXT2,size=12),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.12),
                    xaxis=dict(tickfont=dict(color=TEXT2,size=11),showgrid=False,tickangle=-20),
                    yaxis=dict(showgrid=False,showticklabels=False),
                    bargap=0.3
                )
                st.markdown(f'<div class="grp" style="padding:14px 16px"><div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Aporte por persona / mes</div>', unsafe_allow_html=True)
                st.plotly_chart(fig_stack, use_container_width=True, config={"displayModeBar": False})
                st.markdown("</div>", unsafe_allow_html=True)

        # ── RANKING ACUMULADO DE CATEGORÍAS ──
        cat_acum = df_maestro.copy()
        cat_acum["Cat"] = cat_acum["Item"].apply(categorizar)
        cat_rank = cat_acum.groupby("Cat")["Monto (ARS)"].sum().sort_values(ascending=False).reset_index()
        cat_rank["Pct"] = (cat_rank["Monto (ARS)"] / cat_rank["Monto (ARS)"].sum() * 100).round(1)

        st.markdown('<div class="sec-lbl">Ranking acumulado de categorías</div><div class="grp" style="padding:14px 16px">', unsafe_allow_html=True)
        max_v = cat_rank["Monto (ARS)"].max()
        for i, (_, row) in enumerate(cat_rank.iterrows()):
            color = cat_color(row["Cat"])
            bar_w = int(row["Monto (ARS)"] / max_v * 100) if max_v > 0 else 0
            st.markdown(f"""<div style="margin-bottom:11px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                <div style="display:flex;align-items:center;gap:7px">
                  <span style="font-size:11px;font-weight:700;color:{TEXT3};width:18px">#{i+1}</span>
                  <span style="font-size:14px;color:{TEXT}">{row['Cat']}</span>
                </div>
                <div>
                  <span style="font-size:14px;font-weight:600;color:{color}">{fmt_ars(row['Monto (ARS)'])}</span>
                  <span style="font-size:11px;color:{TEXT2};margin-left:5px">{row['Pct']}%</span>
                </div>
              </div>
              <div style="height:3px;background:rgba(255,255,255,.08);border-radius:3px;overflow:hidden">
                <div style="width:{bar_w}%;height:100%;background:{color};border-radius:3px"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
