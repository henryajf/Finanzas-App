import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.graph_objects as go
import io
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, timedelta

st.set_page_config(page_title="Finanzas AR", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")

for k, v in [("screen", "inicio"), ("show_add", False), ("show_add_ingreso", False),
             ("periodo_sel", None), ("tend_mes_exp", None), ("show_horas", False),
             ("theme", "dark")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════
# TEMA — minimalista, dos paletas (oscuro por defecto + claro)
# ══════════════════════════════════════════════════════════════════
THEME = st.session_state.theme

def rgba(h, a):
    h = str(h).lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{a})"

if THEME == "dark":
    BG      = "#0B0C0E"
    SURFACE = "#141619"
    SURF2   = "#1A1D21"
    SURF3   = "#20242A"
    GLASS_BORDER   = "#25292F"
    GLASS_BORDER_2 = "#343A42"
    TEXT    = "#ECEEF1"
    TEXT2   = "#98A0AC"
    TEXT3   = "#69707C"
    SEP     = "#20242A"
    ACCENT  = "#8B93F8"
    ACCENT2 = "#A9B0FB"
    GREEN   = "#4ADE80"
    RED     = "#F98A9C"
    ORANGE  = "#FBBF24"
    YELLOW  = "#FDE047"
    GOLD    = "#E0A64B"
    A_RED   = "#FCA5B4"
    A_ORANGE= "#FCD34D"
    A_GREEN = "#6EE7A8"
    A_BLUE  = "#AEB4FB"
    GRID    = "#25292F"
else:
    BG      = "#FBFBFC"
    SURFACE = "#FFFFFF"
    SURF2   = "#F5F6F8"
    SURF3   = "#EFF0F3"
    GLASS_BORDER   = "#EAEBEE"
    GLASS_BORDER_2 = "#DBDDE2"
    TEXT    = "#16181D"
    TEXT2   = "#68707B"
    TEXT3   = "#9AA0A9"
    SEP     = "#EFF0F3"
    ACCENT  = "#5B63D6"
    ACCENT2 = "#8188E4"
    GREEN   = "#1E9D57"
    RED     = "#D9455F"
    ORANGE  = "#B0790C"
    YELLOW  = "#CA9A04"
    GOLD    = "#A9781F"
    A_RED   = "#B42B41"
    A_ORANGE= "#8A5A08"
    A_GREEN = "#0F7A44"
    A_BLUE  = "#3E45B8"
    GRID    = "#EDEEF0"

PLOTBG = "rgba(0,0,0,0)"
BLUR   = "none"

# ── COLORES DE CATEGORÍA (tonos medios, legibles en ambos temas) ──
CAT_COLORS = {
    "Servicios": "#C08552", "Hogar": "#5B9279", "Supermercado": "#6B9E78",
    "Comida": "#C96A5E", "Transporte": "#4E8A98", "Suscripciones": "#B9975B",
    "Fitness": "#C0705A", "Salud": "#6FA694", "Credito": "#A9855E",
    "Impuestos": "#7C8CA8", "Personal": "#7FB0A5", "Viajes": "#5691A0",
    "Otros": "#8A8A8A",
}

def cat_color(cat):
    c = str(cat)
    for k, v in CAT_COLORS.items():
        if k.lower() in c.lower(): return v
    return "#8A8A8A"

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
    elif "impuesto" in c:
        ico = f'<rect x="{s*.24}" y="{s*.12}" width="{s*.52}" height="{s*.76}" rx="{s*.06}" fill="white" opacity="0.95"/><rect x="{s*.33}" y="{s*.28}" width="{s*.34}" height="{s*.06}" rx="{s*.02}" fill="{color}"/><rect x="{s*.33}" y="{s*.42}" width="{s*.34}" height="{s*.06}" rx="{s*.02}" fill="{color}"/><rect x="{s*.33}" y="{s*.56}" width="{s*.22}" height="{s*.06}" rx="{s*.02}" fill="{color}"/>'
    elif "personal" in c or "ocio" in c:
        ico = f'<circle cx="{s*.5}" cy="{s*.35}" r="{s*.17}" fill="white"/><path d="M{s*.2},{s*.85} Q{s*.2},{s*.6} {s*.5},{s*.6} Q{s*.8},{s*.6} {s*.8},{s*.85}" fill="white"/>'
    elif "viaje" in c:
        ico = f'<path d="M{s*.5},{s*.1} L{s*.88},{s*.58} L{s*.7},{s*.53} L{s*.64},{s*.82} L{s*.5},{s*.72} L{s*.36},{s*.82} L{s*.3},{s*.53} L{s*.12},{s*.58} Z" fill="white" opacity="0.9"/>'
    else:
        ico = f'<circle cx="{s*.5}" cy="{s*.38}" r="{s*.16}" fill="white" opacity="0.9"/><path d="M{s*.24},{s*.82} Q{s*.24},{s*.6} {s*.5},{s*.6} Q{s*.76},{s*.6} {s*.76},{s*.82}" fill="white" opacity="0.9"/>'
    return f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg"><rect width="{s}" height="{s}" rx="{r}" fill="{color}"/>{ico}</svg>'

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap');
:root{{
  --bg:{BG};--surface:{SURFACE};--surf2:{SURF2};--surf3:{SURF3};
  --text:{TEXT};--text2:{TEXT2};--text3:{TEXT3};--sep:{SEP};
  --accent:{ACCENT};--green:{GREEN};--red:{RED};--orange:{ORANGE};
  --glass-b:{GLASS_BORDER};--glass-b2:{GLASS_BORDER_2};
  --font-ui: 'Plus Jakarta Sans', -apple-system, sans-serif;
  --font-num: 'Outfit', 'Plus Jakarta Sans', sans-serif;
  --r-card:14px;--r-input:10px;--r-pill:99px;
  --sh-card:none;
  --sh-hero:none;
}}
html, body, .stApp {{
  font-family:var(--font-ui) !important;
  font-variant-numeric:tabular-nums;
  background:{BG} !important;
  background-attachment:fixed !important;
  color:{TEXT} !important;
  overflow-x: clip !important;
  width: 100vw !important;
  max-width: 100% !important;
}}
*{{box-sizing:border-box;-webkit-font-smoothing:antialiased;font-family:inherit;}}

#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="collapsedControl"] {{display:none !important;}}
.block-container, [data-testid="stMainBlockContainer"] {{
  padding:0.6rem 16px 48px !important; max-width:832px !important; margin:0 auto !important;
  overflow-x: clip !important;
}}
[data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], [data-testid="stMain"],
section.main, section.main > div:first-child {{margin-top:0 !important;background:{BG} !important;}}
.wrap {{display:contents;}}

/* ── HEADER ── */
.ios-hdr {{
  position:relative;
  background:transparent;
  border-bottom:1px solid {SEP};
  box-shadow:none;
  padding:8px 0 14px;
  margin:0 0 4px;
}}
.ios-hdr-top{{display:flex;justify-content:space-between;align-items:flex-start;}}
.ios-title{{font-size:19px;font-weight:700;letter-spacing:-.02em;color:{TEXT};}}
.ios-title span{{color:{ACCENT};}}
.ios-date{{font-size:11px;color:{TEXT3};margin-top:3px;letter-spacing:.01em;}}
.dolar-block{{text-align:right;background:transparent;border:none;border-radius:0;padding:2px 0;}}
.dolar-lbl{{font-size:9px;color:{TEXT3};letter-spacing:.10em;text-transform:uppercase;font-weight:600;}}
.dolar-val{{font-family:var(--font-num);font-size:17px;font-weight:600;color:{TEXT};letter-spacing:-.01em;margin-top:1px;}}
.dolar-trend{{font-size:10px;margin-top:1px;}}

/* ── BARRA DE NAVEGACIÓN: ver bloque <style> inyectado antes de las columnas ── */

/* ── SELECTBOX / INPUTS NATIVOS ── */
div[data-baseweb="select"] > div {{
    background: {SURFACE} !important;
    border-radius: var(--r-input) !important;
    border: 1px solid {GLASS_BORDER} !important;
    color: {TEXT} !important;
}}
div[data-baseweb="select"] * {{ color: {TEXT} !important; }}
div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {{
    background: {SURFACE} !important;
    border: 1px solid {GLASS_BORDER} !important;
    color: {TEXT} !important;
}}
div[data-baseweb="menu"] li:hover {{ background: {SURF2} !important; }}
[data-testid="stDateInput"] input {{
    background: {SURFACE} !important;
    border: 1px solid {GLASS_BORDER} !important;
    color: {TEXT} !important;
    border-radius: var(--r-input) !important;
}}
[data-testid="stCheckbox"] label, [data-testid="stCheckbox"] p {{ color: {TEXT2} !important; }}

/* ── EXPANDER ── */
[data-testid="stExpander"] {{
    border: 1px solid {GLASS_BORDER} !important;
    border-radius: var(--r-card) !important;
    background: {SURFACE} !important;
    overflow: hidden !important;
}}
[data-testid="stExpander"] summary {{
    background: {SURFACE} !important;
    color: {TEXT} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}}
[data-testid="stExpander"] summary:hover {{ color: {ACCENT} !important; }}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{ background: {SURFACE} !important; }}

/* ── CARDS ── */
.card{{background:{SURFACE};border-radius:var(--r-card);padding:22px;margin-bottom:10px;border:1px solid {GLASS_BORDER};}}
.card-ing,.card-gastos,.card-balance-pos,.card-balance-neg{{
  background:{SURFACE};border-radius:var(--r-card);padding:22px;margin-bottom:10px;border:1px solid {GLASS_BORDER};
}}

.c-lbl{{font-size:10px;font-weight:600;color:{TEXT3};text-transform:uppercase;letter-spacing:.09em;margin-bottom:7px;}}
.c-val{{font-family:var(--font-num);font-size:25px;font-weight:600;letter-spacing:-.015em;line-height:1.1;color:{TEXT};}}
.c-sub{{font-size:12px;color:{TEXT2};margin-top:4px;}}


/* ── BOTONES ── */
.stButton>button[kind="primary"]{{
  background:{ACCENT} !important;
  color:#FFFFFF !important;
  border:none !important;
  border-radius:var(--r-input) !important;
  padding:10px 18px !important;
  font-family:var(--font-ui) !important;
  font-size:13px !important;
  font-weight:600 !important;
  letter-spacing:-.005em !important;
  box-shadow:none !important;
  transition:filter 0.12s ease !important;
}}
.stButton>button[kind="primary"]:hover{{ filter:brightness(1.08) !important; }}
.stButton>button[kind="primary"]:active{{ transform:scale(0.99) !important; }}
.stButton>button[kind="secondary"]{{
  background:transparent !important;
  color:{TEXT2} !important;
  border:1px solid {GLASS_BORDER} !important;
  border-radius:var(--r-input) !important;
  padding:10px 18px !important;
  font-family:var(--font-ui) !important;
  font-size:13px !important;
  font-weight:500 !important;
  box-shadow:none !important;
  transition:border-color 0.12s ease, color 0.12s ease !important;
}}
.stButton>button[kind="secondary"]:hover{{
  border-color:{GLASS_BORDER_2} !important;
  color:{TEXT} !important;
}}
[data-testid="stDownloadButton"] button{{
  background:transparent !important;color:{TEXT2} !important;border:1px solid {GLASS_BORDER} !important;
  border-radius:var(--r-input) !important;font-size:13px !important;font-weight:500 !important;box-shadow:none !important;
}}

/* ── BARRAS DE ESTADO ── */
.bar-section{{margin-top:14px;}}
.bar-row-hdr{{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;}}
.bar-lbl{{font-size:12px;font-weight:500;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;}}
.bar-amt{{font-family:var(--font-num);font-size:14px;font-weight:600;}}
.bar-usd{{font-size:11px;color:{TEXT3};margin-top:1px;text-align:right;}}
.bar-bg{{height:4px;background:{SURF3};border-radius:4px;overflow:hidden;margin-bottom:3px;}}
.bar-fill{{height:100%;border-radius:4px;transition:width 0.7s cubic-bezier(.22,1,.36,1);animation:barGrow 0.7s cubic-bezier(.22,1,.36,1);}}
@keyframes barGrow{{from{{width:0 !important;}}}}
.bar-meta{{display:flex;justify-content:space-between;}}
.bar-pct{{font-size:11px;color:{TEXT3};}}
.bar-n{{font-size:11px;font-weight:600;padding:1px 8px;border-radius:var(--r-pill);}}
.bar-n-pag{{background:{rgba(GREEN,0.12)};color:{GREEN};}}
.bar-n-pend{{background:{rgba(RED,0.12)};color:{RED};}}
.sep{{height:1px;background:{SEP};margin:16px 0;}}

/* ── PERSONAS ── */
.persona-row{{display:flex;align-items:center;gap:11px;}}
.persona-row+.persona-row{{margin-top:12px;}}
.av{{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;border:1px solid {GLASS_BORDER};}}
.av-h{{background:{rgba(ACCENT,0.14)};color:{ACCENT};}}
.av-j{{background:{rgba(GOLD,0.14)};color:{GOLD};}}
.persona-body{{flex:1;}}
.persona-name{{font-size:13px;font-weight:500;color:{TEXT};}}
.persona-sub{{font-size:11px;color:{TEXT3};}}
.persona-amt{{font-family:var(--font-num);font-size:15px;font-weight:600;text-align:right;}}
.persona-amt-sub{{font-size:11px;color:{TEXT3};text-align:right;}}

/* ── BALANCE TAG ── */
.balance-tag-pos{{display:inline-block;font-size:10px;font-weight:600;padding:3px 10px;border-radius:var(--r-pill);background:{rgba(GREEN,0.12)};color:{GREEN};border:1px solid {rgba(GREEN,0.22)};margin-bottom:6px;}}
.balance-tag-neg{{display:inline-block;font-size:10px;font-weight:600;padding:3px 10px;border-radius:var(--r-pill);background:{rgba(RED,0.12)};color:{RED};border:1px solid {rgba(RED,0.22)};margin-bottom:6px;}}

/* ── SECCION LABEL ── */
.sec-lbl{{font-size:10px;font-weight:600;color:{TEXT3};text-transform:uppercase;letter-spacing:.10em;padding:0 2px;margin:26px 0 10px;}}

/* ── ALERTAS ── */
.alert{{padding:12px 15px;border-radius:var(--r-input);font-size:12.5px;margin-bottom:8px;line-height:1.5;border:1px solid transparent;}}
.alert-r{{background:{rgba(RED,0.09)};color:{A_RED};border-color:{rgba(RED,0.20)};}}
.alert-o{{background:{rgba(ORANGE,0.10)};color:{A_ORANGE};border-color:{rgba(ORANGE,0.22)};}}
.alert-g{{background:{rgba(GREEN,0.10)};color:{A_GREEN};border-color:{rgba(GREEN,0.20)};}}
.alert-b{{background:{rgba(ACCENT,0.10)};color:{A_BLUE};border-color:{rgba(ACCENT,0.20)};}}

/* ── GRUPOS / FILAS ── */
.grp{{background:{SURFACE};border-radius:var(--r-card);overflow:hidden;margin-bottom:10px;border:1px solid {GLASS_BORDER};}}
.grp-hdr{{display:flex;align-items:center;gap:10px;padding:13px 18px;border-bottom:1px solid {SEP};}}
.grp-hdr-lbl{{flex:1;font-size:11px;font-weight:600;color:{TEXT2};letter-spacing:.06em;text-transform:uppercase;}}
.grp-hdr-amt{{font-family:var(--font-num);font-size:13px;font-weight:600;}}
.pend-badge{{font-size:10px;font-weight:600;padding:1px 7px;border-radius:var(--r-pill);background:{rgba(RED,0.12)};color:{RED};border:1px solid {rgba(RED,0.22)};margin-left:6px;}}
.row{{display:flex;align-items:center;gap:12px;padding:13px 18px;position:relative;transition:background 0.15s ease;}}
.row:hover{{background:{SURF2};}}
.row::after{{content:'';position:absolute;bottom:0;left:60px;right:0;height:1px;background:{SEP};}}
.row:last-child::after{{display:none;}}
.row-body{{flex:1;min-width:0;}}
.row-name{{font-size:14.5px;font-weight:400;color:{TEXT};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.row-name-paid{{font-size:14.5px;font-weight:400;color:{TEXT3};text-decoration:line-through;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.row-sub{{font-size:12px;color:{TEXT3};margin-top:2px;}}
.row-right{{text-align:right;flex-shrink:0;}}
.row-amt{{font-family:var(--font-num);font-size:14.5px;font-weight:600;color:{TEXT};}}
.row-amt-paid{{font-family:var(--font-num);font-size:14.5px;font-weight:400;color:{TEXT3};text-decoration:line-through;}}
.row-usd{{font-size:11px;color:{TEXT3};margin-top:2px;}}

/* ── BADGES ── */
.badge{{display:inline-flex;align-items:center;font-size:10.5px;font-weight:600;padding:2px 9px;border-radius:var(--r-pill);white-space:nowrap;letter-spacing:.01em;}}
.badge-paid{{background:{rgba(GREEN,0.12)};color:{GREEN};border:1px solid {rgba(GREEN,0.22)};}}
.badge-venc{{background:{rgba(RED,0.12)};color:{RED};border:1px solid {rgba(RED,0.22)};}}
.badge-hoy{{background:{rgba(RED,0.12)};color:{RED};border:1px solid {rgba(RED,0.22)};}}
.badge-prox{{background:{rgba(ORANGE,0.12)};color:{A_ORANGE};border:1px solid {rgba(ORANGE,0.24)};}}
.badge-soon{{background:{rgba(YELLOW,0.14)};color:{A_ORANGE};border:1px solid {rgba(YELLOW,0.26)};}}
.badge-ok{{background:{rgba(GREEN,0.10)};color:{GREEN};border:1px solid {rgba(GREEN,0.20)};}}
.badge-none{{background:{SURF2};color:{TEXT3};border:1px solid {GLASS_BORDER};}}
.badge-henry{{background:{rgba(ACCENT,0.14)};color:{ACCENT};border:1px solid {rgba(ACCENT,0.24)};}}
.badge-jaike{{background:{rgba(GOLD,0.14)};color:{GOLD};border:1px solid {rgba(GOLD,0.24)};}}

/* ── ADD PANELS ── */
.add-panel,.add-panel-green{{background:{SURFACE};border-radius:var(--r-card);padding:22px;margin-bottom:12px;border:1px solid {GLASS_BORDER};}}
.stTextInput>div>div>input,.stNumberInput>div>div>input{{
  background:{SURFACE} !important;border:1px solid {GLASS_BORDER} !important;border-radius:var(--r-input) !important;
  color:{TEXT} !important;font-size:14px !important;
  font-family:var(--font-ui) !important;
  transition:border-color 0.12s ease, box-shadow 0.12s ease !important;
}}
.stTextInput>div>div:focus-within input,.stNumberInput>div>div:focus-within input{{
  border-color:{ACCENT} !important;
  box-shadow:0 0 0 3px {rgba(ACCENT,0.14)} !important;
}}
.stTextInput label,.stNumberInput label,.stDateInput label,.stSelectbox label{{
  color:{TEXT3} !important;font-size:11px !important;font-weight:600 !important;
  text-transform:uppercase !important;letter-spacing:.05em !important;
}}
.toast-ok{{display:inline-flex;align-items:center;gap:7px;padding:10px 14px;border-radius:var(--r-input);font-size:13px;font-weight:500;margin-bottom:8px;background:{rgba(GREEN,0.10)};color:{GREEN};border:1px solid {rgba(GREEN,0.20)};}}
.toast-err{{display:inline-flex;align-items:center;gap:7px;padding:10px 14px;border-radius:var(--r-input);font-size:13px;font-weight:500;margin-bottom:8px;background:{rgba(RED,0.10)};color:{RED};border:1px solid {rgba(RED,0.20)};}}

/* ── KPI GRID ── */
.kpi-grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;}}
.kpi-grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:10px;}}
@media(max-width:700px){{
  .kpi-grid-3{{grid-template-columns:1fr 1fr;}}
}}
.kpi-card{{background:{SURFACE};border-radius:var(--r-card);padding:16px;border:1px solid {GLASS_BORDER};}}
.kpi-lbl{{font-size:10px;font-weight:600;color:{TEXT3};margin-bottom:6px;letter-spacing:.06em;text-transform:uppercase;}}
.kpi-val{{font-family:var(--font-num);font-size:19px;font-weight:600;letter-spacing:-.02em;line-height:1.1;color:{TEXT};}}
.kpi-sub{{font-size:11px;color:{TEXT3};margin-top:5px;}}

/* ── TENDENCIAS - CARD MES ── */
.mes-card-header {{
  display: flex;
  align-items: center;
  padding: 15px 18px;
  gap: 12px;
  background: {SURFACE};
  border-radius: var(--r-card);
  border: 1px solid {GLASS_BORDER};
}}
.mes-dot {{width:8px;height:8px;border-radius:50%;flex-shrink:0;}}
.mes-title {{flex:1;}}
.mes-nombre {{font-size:15px;font-weight:600;color:{TEXT};}}
.mes-subtitle {{font-size:11px;color:{TEXT3};margin-top:3px;}}
.mes-balance-pos {{font-family:var(--font-num);font-size:13px;font-weight:600;padding:3px 11px;border-radius:var(--r-pill);background:{rgba(GREEN,0.12)};color:{GREEN};border:1px solid {rgba(GREEN,0.22)};}}
.mes-balance-neg {{font-family:var(--font-num);font-size:13px;font-weight:600;padding:3px 11px;border-radius:var(--r-pill);background:{rgba(RED,0.12)};color:{RED};border:1px solid {rgba(RED,0.22)};}}
.mes-body-grid {{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:12px 0;}}
@media(max-width:600px){{.mes-body-grid{{grid-template-columns:1fr 1fr;}}}}
.mes-mini-kpi {{background:{SURF2};border-radius:var(--r-input);padding:11px 13px;border:1px solid {GLASS_BORDER};}}
.mes-mini-lbl {{font-size:9px;color:{TEXT3};font-weight:600;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px;}}
.mes-mini-val {{font-family:var(--font-num);font-size:16px;font-weight:600;line-height:1.1;}}
.mes-mini-sub {{font-size:10px;color:{TEXT3};margin-top:2px;}}
.cat-bar-row {{display:flex;align-items:center;gap:10px;padding:7px 0;border-bottom:1px solid {SEP};}}
.cat-bar-row:last-child {{border-bottom:none;}}
.cat-bar-name {{font-size:12.5px;color:{TEXT2};width:130px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.cat-bar-track {{flex:1;height:4px;background:{SURF3};border-radius:4px;overflow:hidden;}}
.cat-bar-fill {{height:100%;border-radius:4px;transition:width 0.7s cubic-bezier(.22,1,.36,1);animation:barGrow 0.7s cubic-bezier(.22,1,.36,1);}}
.cat-bar-amt {{font-family:var(--font-num);font-size:12px;font-weight:600;min-width:80px;text-align:right;}}
.aporte-row {{display:flex;align-items:center;gap:10px;padding:8px 0;}}
.aporte-av {{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0;border:1px solid {GLASS_BORDER};}}
.aporte-body {{flex:1;}}
.aporte-name {{font-size:12.5px;font-weight:500;color:{TEXT};}}
.aporte-pct {{font-size:11px;color:{TEXT3};}}
.aporte-amt {{font-family:var(--font-num);font-size:13px;font-weight:600;text-align:right;}}
.var-badge-pos {{display:inline-flex;align-items:center;gap:3px;font-size:10.5px;font-weight:600;padding:2px 9px;border-radius:var(--r-pill);background:{rgba(GREEN,0.10)};color:{GREEN};border:1px solid {rgba(GREEN,0.20)};}}
.var-badge-neg {{display:inline-flex;align-items:center;gap:3px;font-size:10.5px;font-weight:600;padding:2px 9px;border-radius:var(--r-pill);background:{rgba(RED,0.10)};color:{RED};border:1px solid {rgba(RED,0.20)};}}
.var-badge-neu {{display:inline-flex;align-items:center;gap:3px;font-size:10.5px;font-weight:600;padding:2px 9px;border-radius:var(--r-pill);background:{SURF2};color:{TEXT3};}}
.hist-row{{display:flex;align-items:center;padding:13px 18px;border-bottom:1px solid {SEP};gap:10px;transition:background 0.15s ease;}}
.hist-row:hover{{background:{SURF2};}}
.hist-row:last-child{{border-bottom:none;}}
.ing-row{{display:flex;align-items:center;gap:12px;padding:13px 18px;position:relative;transition:background 0.15s ease;}}
.ing-row:hover{{background:{SURF2};}}
.ing-row::after{{content:'';position:absolute;bottom:0;left:60px;right:0;height:1px;background:{SEP};}}
.ing-row:last-child::after{{display:none;}}
[data-testid="stDataFrameContainer"],[data-testid="stDataEditorContainer"]{{background:{SURFACE} !important;border:1px solid {GLASS_BORDER} !important;border-radius:var(--r-card) !important;overflow:hidden !important;}}
[data-testid="stTextInputRootElement"] input::placeholder{{color:{TEXT3} !important;}}
@media(max-width:700px){{
  .ios-title{{font-size:18px;}}
  .c-val{{font-size:21px;}}
}}
hr{{display:none !important;}}
[data-testid="stVerticalBlock"]>div{{gap:0 !important;}}
</style>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# CONEXION Y LIMPIEZA
# ──────────────────────────────────────────────────────────────────
def clean_currency(val):
    if pd.isna(val) or val == "": return 0.0
    if isinstance(val, (int, float)): return float(val)
    v = str(val).upper().replace("$", "").replace("ARS", "").replace("U$S", "").replace("USD", "").strip()
    v = v.replace(" ", "").replace("\xa0", "")
    if "," in v and "." in v: v = v.replace(".", "").replace(",", ".")
    elif "," in v: v = v.replace(",", ".")
    elif "." in v:
        parts = v.split(".")
        if len(parts) > 1 and len(parts[-1]) == 3: v = v.replace(".", "")
    try: return float(v)
    except: return 0.0

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
    if not data or len(data) < 2: return pd.DataFrame()
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
    df["Monto (ARS)"] = df["Monto (ARS)"].apply(clean_currency)
    df["Tasa USD"]    = df["Tasa USD"].apply(clean_currency)
    df["Dia Pago"]    = pd.to_datetime(df["Dia Pago"], errors="coerce").dt.date
    df["Pagado"]      = df["Pagado"].apply(lambda x: str(x).strip().upper() in ["TRUE","VERDADERO","SI","1"])
    df = df[~((df["Monto (ARS)"] == 0) & (df["Item"].str.strip() == ""))]
    return df.reset_index(drop=True)

@st.cache_data(ttl=600)
def cargar_ingresos():
    try:
        sh = get_gspread().open("Gastos_Henry")
        ws = next((h for h in sh.worksheets() if h.title.strip().lower() == "ingresos"), None)
        if not ws:
            ws = sh.add_worksheet(title="Ingresos", rows=200, cols=9)
            ws.append_row(["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha","Horas"])
            return pd.DataFrame()
        data = ws.get_all_values()
        if not data or len(data) < 2: return pd.DataFrame()
        headers = ["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha","Horas"]
        filas, sheet_rows = [], []
        for i, r in enumerate(data[1:]):
            if len(r) >= 2:
                filas.append(r + [""] * (9 - len(r)))
                sheet_rows.append(i + 2)
        if not filas: return pd.DataFrame()
        df = pd.DataFrame(filas, columns=headers)
        df["SheetRow"] = sheet_rows
        for col in ["Monto ARS","Monto USD","Monto Original","Tasa USD/ARS","Horas"]:
            df[col] = df[col].apply(clean_currency)
        df["Fecha"]   = pd.to_datetime(df["Fecha"], errors="coerce").dt.date
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

def guardar_ingreso(desc, persona, moneda, monto_orig, monto_ars, monto_usd, tasa, fecha, horas=0):
    sh = get_gspread().open("Gastos_Henry")
    ws = next((h for h in sh.worksheets() if h.title.strip().lower() == "ingresos"), None)
    if not ws:
        ws = sh.add_worksheet(title="Ingresos", rows=200, cols=9)
        ws.append_row(["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha","Horas"])
    ws.append_row([desc, persona, moneda, monto_orig, monto_ars, monto_usd, tasa, str(fecha), horas if horas and horas > 0 else ""])
    st.cache_data.clear()

def actualizar_horas_ingreso(sheet_row, horas):
    sh = get_gspread().open("Gastos_Henry")
    ws = next((h for h in sh.worksheets() if h.title.strip().lower() == "ingresos"), None)
    if not ws: return
    header = ws.row_values(1)
    if len(header) < 9 or header[8].strip().lower() != "horas":
        ws.update_cell(1, 9, "Horas")
    ws.update_cell(sheet_row, 9, horas)
    st.cache_data.clear()

def marcar_pagado_maestro(item_nombre, periodo_item, df_full, dolar_actual, nuevo_monto=None):
    df_act = df_full.copy()
    mask = (df_act["Item"] == item_nombre) & (df_act["Periodo"] == periodo_item)
    if mask.any():
        df_act.loc[mask, "Pagado"] = True
        if nuevo_monto is not None and nuevo_monto > 0:
            df_act.loc[mask, "Monto (ARS)"] = float(nuevo_monto)
        guardar_hoja_maestro(df_act, dolar_actual)

def categorizar(item):
    i = str(item).lower()
    if any(x in i for x in ["mercadocredito","credipersonal","credi personal","tarjeta","visa","mastercard","amex","credito","banco","financiamiento","cuota"]): return "Credito/Financiacion"
    elif any(x in i for x in ["abl","agip"]): return "Hogar"
    elif (any(x in i for x in ["afip","monotributo","impuesto","iibb","ingresos brutos","rentas","arba","ganancias","bienes personales","autonomo","f931","sellos","patente","inmobiliario","tasa municipal","dgr"])
          or "arca" in i.split() or "vep" in i.split()): return "Impuestos"
    elif any(x in i for x in ["luz","edenor","edesur","agua","aysa","gas","metrogas","bbva seguro de hogar","bbva seguros de hogar","personal"]): return "Servicios"
    elif any(x in i for x in ["super","coto","carrefour","dia","jumbo","disco","mercado","almacen","chino"]): return "Supermercado"
    elif any(x in i for x in ["alquiler","expensas","abl","limpieza"]): return "Hogar"
    elif any(x in i for x in ["nafta","ypf","shell","axion","uber","cabify","taxi","peaje","sube","transporte"]): return "Transporte"
    elif any(x in i for x in ["netflix","spotify","prime","hbo","disney","youtube","telecentro","fibertel","internet","claro","movistar","meli","google","apple","vpn"]): return "Suscripciones"
    elif any(x in i for x in ["gym","gimnasio","megatlon","sportclub","crossfit"]): return "Fitness"
    elif any(x in i for x in ["farmacia","osde","swiss","galeno","medico","salud","depilife","peluqueria","barberia","barber","corte de cabello","corte de pelo","corte pelo","cabello","estetica","manicura","cosmetica","perfumeria"]): return "Salud/Cuidado Personal"
    elif any(x in i for x in ["mc","burger","pedidosya","rappi","helado","pizza","restaurante","bar","cafe"]): return "Comida/Delivery"
    elif any(x in i for x in ["ropa","zapat","zara","dafiti"]): return "Personal/Ocio"
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
    if m == 1: return f"{y-1}-12"
    else: return f"{y}-{m-1:02d}"

def calcular_mes_siguiente(periodo_str):
    y, m = map(int, periodo_str.split('-'))
    if m == 12: return f"{y+1}-01"
    else: return f"{y}-{m+1:02d}"


# ── CARGA INICIAL ──
MESES = ["enero","febrero","marzo","abril","mayo","junio",
         "julio","agosto","septiembre","octubre","noviembre","diciembre"]
hoy            = date.today()
hoy_str        = f"{hoy.day} de {MESES[hoy.month-1]} de {hoy.year}"
periodo_actual = hoy.strftime("%Y-%m")

dolar = get_dolar()
dolar_val, dolar_ayer, dolar_diff, dolar_pct = get_dolar_tendencia()

df_maestro   = cargar_datos_maestro()
df_ing_todo  = cargar_ingresos()

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

# ── FILTRADO DE DATOS ──
if not df_maestro.empty:
    df_base_periodo = df_maestro[df_maestro["Periodo"] == periodo_viendo].copy()
    df = procesar(df_base_periodo, dolar)
    total_ars    = df["Monto (ARS)"].sum()
    pagado_ars   = df[df["Pagado"] == True]["Monto (ARS)"].sum()
    pend_ars     = total_ars - pagado_ars
    pct_pag      = int(pagado_ars / total_ars * 100) if total_ars > 0 else 0
    pct_pend     = 100 - pct_pag
    n_pagados    = int(df["Pagado"].sum())
    n_pendientes = len(df) - n_pagados
    por_cat      = df.groupby("Cat")["Monto (ARS)"].sum().reset_index().sort_values("Monto (ARS)", ascending=False)
    es_mes_actual = (periodo_viendo == periodo_actual)
    vencidos = df[(df["Pagado"]==False) & df["Dia Pago"].notna() & (df["Dia Pago"] < hoy)] if es_mes_actual else pd.DataFrame()
    proximos = df[(df["Pagado"]==False) & df["Dia Pago"].notna() & (df["Dia Pago"] >= hoy) & (df["Dia Pago"] <= hoy + timedelta(days=3))] if es_mes_actual else pd.DataFrame()
else:
    df_base_periodo = pd.DataFrame()
    df = por_cat = pd.DataFrame()
    total_ars = pagado_ars = pend_ars = pct_pag = pct_pend = 0
    n_pagados = n_pendientes = 0
    vencidos = proximos = pd.DataFrame()
    es_mes_actual = True

# Montos del mes anterior por ítem (referencia para gastos duplicados en $0)
ref_montos = {}
if not df_maestro.empty:
    _dfp = df_maestro[df_maestro["Periodo"] == calcular_mes_anterior(periodo_viendo)]
    for _, _r in _dfp.iterrows():
        _k = str(_r["Item"]).strip().lower()
        if _k:
            ref_montos[_k] = float(_r["Monto (ARS)"])

def ref_monto(item):
    return ref_montos.get(str(item).strip().lower(), 0.0)

if not df_ing_todo.empty:
    df_ing_periodo = df_ing_todo[df_ing_todo["Periodo"] == periodo_viendo]
else:
    df_ing_periodo = pd.DataFrame()

total_ing_ars = df_ing_periodo["Monto ARS"].sum() if not df_ing_periodo.empty else 0
total_ing_usd = df_ing_periodo["Monto USD"].sum() if not df_ing_periodo.empty else 0
ing_henry     = df_ing_periodo[df_ing_periodo["Persona"].str.upper()=="HENRY"]["Monto ARS"].sum() if not df_ing_periodo.empty else 0
ing_jaike     = df_ing_periodo[df_ing_periodo["Persona"].str.upper()=="JAIKE"]["Monto ARS"].sum() if not df_ing_periodo.empty else 0
balance_ars   = total_ing_ars - total_ars
pct_henry = int(ing_henry / total_ing_ars * 100) if total_ing_ars > 0 else 0
pct_jaike = int(ing_jaike / total_ing_ars * 100) if total_ing_ars > 0 else 0

# ── PWA META TAGS ──
st.markdown(f"""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="{BG}">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-title" content="Finanzas AR">
<script>
document.addEventListener('DOMContentLoaded',function(){{
  function patchInputs(){{
    document.querySelectorAll('input[type="number"]').forEach(function(el){{
      if(!el.getAttribute('inputmode')){{el.setAttribute('inputmode','decimal');}}
    }});
  }}
  patchInputs();
  var obs=new MutationObserver(function(){{patchInputs();}});
  obs.observe(document.body,{{childList:true,subtree:true}});
}});
</script>
""", unsafe_allow_html=True)

_sc = st.session_state.screen
_nav_items = [
    ("inicio",     "Inicio"),
    ("ingresos",   "Ingresos"),
    ("gastos",     "Gastos"),
    ("tendencias", "Tendencias"),
]

# ── CONTENIDO PRINCIPAL ──
st.markdown('<div class="wrap">', unsafe_allow_html=True)

# ── HEADER ──
if dolar_diff > 0:
    trend_html = f'<span style="color:{RED};font-size:11px;font-weight:600">&#9650; {dolar_pct:+.1f}%</span>'
elif dolar_diff < 0:
    trend_html = f'<span style="color:{GREEN};font-size:11px;font-weight:600">&#9660; {dolar_pct:.1f}%</span>'
else:
    trend_html = f'<span style="color:{TEXT3};font-size:11px">&mdash;</span>'

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
</div>
""", unsafe_allow_html=True)

# ── NAV + TOGGLE DE TEMA (compacto, siempre en una fila, también en mobile) ──
st.markdown(f"""<style>
.st-key-navbar {{ border-bottom:1px solid {SEP}; padding-bottom:10px; margin-bottom:6px; }}
.st-key-navbar div[data-testid="stHorizontalBlock"] {{
  flex-direction:row !important; flex-wrap:nowrap !important; gap:4px !important;
}}
.st-key-navbar div[data-testid="stColumn"],
.st-key-navbar div[data-testid="column"] {{
  flex:1 1 0 !important; flex-basis:0 !important;
  min-width:0 !important; width:auto !important;
}}
.st-key-navbar div[data-testid="stColumn"]:last-child,
.st-key-navbar div[data-testid="column"]:last-child {{ flex:0 0 40px !important; }}
.st-key-navbar div[data-testid="stColumn"] > div,
.st-key-navbar div[data-testid="column"] > div,
.st-key-navbar .stButton {{ width:100% !important; min-width:0 !important; }}
.st-key-navbar .stButton button {{
  width:100% !important; background:{SURF2} !important;
  border:1px solid transparent !important; color:{TEXT2} !important;
  border-radius:8px !important; padding:7px 3px !important;
  font-weight:500 !important; min-height:0 !important;
  line-height:1.15 !important; box-shadow:none !important; letter-spacing:-.015em !important;
  overflow:hidden !important; white-space:nowrap !important;
}}
.st-key-navbar .stButton button p,
.st-key-navbar .stButton button div {{
  font-size:11px !important; font-weight:inherit !important; color:inherit !important;
  overflow:hidden !important; white-space:nowrap !important; text-overflow:clip !important;
}}
.st-key-navbar .stButton button:hover {{ color:{TEXT} !important; background:{SURF3} !important; }}
.st-key-pill_{_sc} .stButton button {{
  background:{rgba(ACCENT,0.16)} !important;
  color:{ACCENT} !important;
}}
.st-key-pill_{_sc} .stButton button p {{ color:{ACCENT} !important; font-weight:600 !important; }}
.st-key-theme_toggle .stButton button {{ color:{TEXT3} !important; }}
.st-key-theme_toggle .stButton button p {{ font-size:14px !important; }}
@media(max-width:460px){{
  .st-key-navbar .stButton button {{ padding:7px 1px !important; }}
  .st-key-navbar .stButton button p,
  .st-key-navbar .stButton button div {{ font-size:9.5px !important; }}
  .st-key-navbar div[data-testid="stColumn"]:last-child,
  .st-key-navbar div[data-testid="column"]:last-child {{ flex:0 0 32px !important; }}
}}
</style>""", unsafe_allow_html=True)
with st.container(key="navbar"):
    _pcols = st.columns([1, 1, 1, 1, 0.5])
    for i, (key, lbl) in enumerate(_nav_items):
        with _pcols[i]:
            if st.button(lbl, key=f"pill_{key}", use_container_width=True):
                st.session_state.screen = key
                st.rerun()
    with _pcols[4]:
        _ico_tema = "☀" if THEME == "dark" else "☾"
        if st.button(_ico_tema, key="theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if THEME == "dark" else "dark"
            st.rerun()

opciones_periodos = periodos_disponibles[:8]
idx_per = opciones_periodos.index(periodo_viendo) if periodo_viendo in opciones_periodos else 0
nuevo_periodo = st.selectbox("Período", opciones_periodos, index=idx_per,
                              format_func=label_periodo, label_visibility="collapsed")
if nuevo_periodo != st.session_state.periodo_sel:
    st.session_state.periodo_sel = nuevo_periodo
    st.rerun()

st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PANTALLA: INICIO
# ══════════════════════════════════════════════════════════════════
if st.session_state.screen == "inicio":

    if not es_mes_actual:
        st.markdown(f'<div class="alert alert-b">Historial &mdash; <strong>{label_periodo(periodo_viendo)}</strong> (solo lectura)</div>', unsafe_allow_html=True)

    if es_mes_actual:
        if not vencidos.empty:
            items_v = " · ".join(r["Item"] for _, r in vencidos.iterrows())
            st.markdown(f'<div class="alert alert-r"><strong>{len(vencidos)} vencido{"s" if len(vencidos)>1 else ""}</strong> &mdash; {items_v}</div>', unsafe_allow_html=True)
        if not proximos.empty:
            st.markdown(f'<div class="alert alert-o">Vencen en 3 días: {" · ".join(r["Item"] for _, r in proximos.iterrows())}</div>', unsafe_allow_html=True)

    if es_mes_actual:
        ba1, ba2 = st.columns(2)
        with ba1:
            lbl_g = "Cancelar" if st.session_state.show_add else "＋ Gasto"
            if st.button(lbl_g, type="secondary" if st.session_state.show_add else "primary",
                         use_container_width=True, key="btn_add_g"):
                st.session_state.show_add = not st.session_state.show_add
                st.session_state.show_add_ingreso = False
                st.rerun()
        with ba2:
            lbl_i = "Cancelar" if st.session_state.show_add_ingreso else "＋ Ingreso"
            if st.button(lbl_i, type="secondary" if st.session_state.show_add_ingreso else "primary",
                         use_container_width=True, key="btn_add_i"):
                st.session_state.show_add_ingreso = not st.session_state.show_add_ingreso
                st.session_state.show_add = False
                st.rerun()
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    ing_usd_str = fmt_usd(total_ing_usd) if total_ing_usd > 0 else fmt_usd_from_ars(total_ing_ars, dolar)

    st.markdown(f'<div class="sec-lbl">Ingresos &mdash; {label_periodo(periodo_viendo)}</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="card-ing">
  <div class="c-lbl">Total ingresado</div>
  <div class="c-val" style="color:{GREEN}">{fmt_ars(total_ing_ars) if total_ing_ars > 0 else "Sin datos"}</div>
  <div class="c-sub">{ing_usd_str} &middot; tasa $ {dolar:,.0f}</div>
  <div class="sep"></div>
  <div class="persona-row">
    <div class="av av-h">H</div>
    <div class="persona-body"><div class="persona-name">Henry</div><div class="persona-sub">{pct_henry}% del total</div></div>
    <div><div class="persona-amt" style="color:{ACCENT}">{fmt_ars(ing_henry)}</div><div class="persona-amt-sub">{fmt_usd_from_ars(ing_henry, dolar)}</div></div>
  </div>
  <div style="margin:6px 0 0 41px"><div class="bar-bg"><div class="bar-fill" style="width:{pct_henry}%;background:{ACCENT};"></div></div></div>
  <div class="persona-row" style="margin-top:12px">
    <div class="av av-j">J</div>
    <div class="persona-body"><div class="persona-name">Jaike</div><div class="persona-sub">{pct_jaike}% del total</div></div>
    <div><div class="persona-amt" style="color:{GOLD}">{fmt_ars(ing_jaike)}</div><div class="persona-amt-sub">{fmt_usd_from_ars(ing_jaike, dolar)}</div></div>
  </div>
  <div style="margin:6px 0 0 41px"><div class="bar-bg"><div class="bar-fill" style="width:{pct_jaike}%;background:{GOLD};"></div></div></div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f'<div class="sec-lbl">Gastos &mdash; {label_periodo(periodo_viendo)}</div>', unsafe_allow_html=True)
    st.markdown(f"""
<div class="card-gastos">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div><div class="c-lbl">Total del mes</div><div class="c-val">{fmt_ars(total_ars) if total_ars > 0 else "Sin datos"}</div><div class="c-sub">{fmt_usd_from_ars(total_ars, dolar)}</div></div>
    <div style="text-align:right;padding-top:2px"><div class="c-lbl">Ítems</div><div style="font-family:var(--font-num);font-size:19px;font-weight:600;color:{TEXT}">{len(df)}</div><div class="c-sub">{n_pagados} pag &middot; {n_pendientes} pend</div></div>
  </div>
  <div class="sep"></div>
  <div class="bar-section">
    <div class="bar-row-hdr">
      <div><span class="bar-lbl">Pagados</span><span style="font-size:10px;font-weight:600;padding:1px 7px;border-radius:20px;background:{rgba(GREEN,0.12)};color:{GREEN};margin-left:7px">{n_pagados}</span></div>
      <div style="text-align:right"><div class="bar-amt" style="color:{GREEN}">{fmt_ars(pagado_ars)}</div><div class="bar-usd">{fmt_usd_from_ars(pagado_ars, dolar)}</div></div>
    </div>
    <div class="bar-bg"><div class="bar-fill" style="width:{pct_pag}%;background:{GREEN};"></div></div>
    <div class="bar-meta"><span class="bar-pct">{pct_pag}% del total</span></div>
  </div>
  <div style="height:14px;"></div>
  <div class="bar-section">
    <div class="bar-row-hdr">
      <div><span class="bar-lbl">Pendientes</span><span style="font-size:10px;font-weight:600;padding:1px 7px;border-radius:20px;background:{rgba(RED,0.12)};color:{RED};margin-left:7px">{n_pendientes}</span></div>
      <div style="text-align:right"><div class="bar-amt" style="color:{RED}">{fmt_ars(pend_ars)}</div><div class="bar-usd">{fmt_usd_from_ars(pend_ars, dolar)}</div></div>
    </div>
    <div class="bar-bg"><div class="bar-fill" style="width:{pct_pend}%;background:{RED};"></div></div>
    <div class="bar-meta"><span class="bar-pct">{pct_pend}% del total</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

    if es_mes_actual:
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
                    st.markdown(f'<div style="padding:7px 0"><div style="font-size:11px;color:{TEXT3};font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">Equiv. USD</div><div style="font-family:var(--font-num);font-size:18px;font-weight:600;color:{GREEN}">U$S {equiv:,.2f}</div></div>', unsafe_allow_html=True)
                    monto_ars_f = ing_monto; monto_usd_f = equiv
                else:
                    equiv = ing_monto * dolar
                    st.markdown(f'<div style="padding:7px 0"><div style="font-size:11px;color:{TEXT3};font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">Equiv. ARS</div><div style="font-family:var(--font-num);font-size:18px;font-weight:600;color:{GREEN}">{fmt_ars(equiv)}</div></div>', unsafe_allow_html=True)
                    monto_ars_f = equiv; monto_usd_f = ing_monto
            with i6: ing_fecha = st.date_input("Fecha", value=hoy, key="ing_fecha")
            st.markdown(f'<div style="font-size:12px;color:{TEXT3};margin:6px 0 2px">Tasa: <strong style="color:{TEXT}">$ {dolar:,.0f} ARS/USD</strong></div>', unsafe_allow_html=True)
            ing_horas = st.number_input("Horas trabajadas (opcional)", min_value=0.0, step=0.5, key="ing_horas", help="Si este pago corresponde a horas trabajadas, cargalas acá y calculo el $/hora automáticamente.")
            if ing_horas > 0 and ing_monto > 0:
                ph_prev = monto_ars_f / ing_horas
                phu_prev = monto_usd_f / ing_horas
                st.markdown(f'<div style="font-size:12px;color:{TEXT3};margin:2px 0 8px">$/hora: <strong style="color:{GREEN}">{fmt_ars(ph_prev)}</strong> &middot; U$S {phu_prev:,.2f}/hs</div>', unsafe_allow_html=True)
            if st.button("Guardar ingreso", type="primary", use_container_width=True):
                if not ing_desc.strip():
                    st.markdown('<div class="toast-err">Ingresa una descripción</div>', unsafe_allow_html=True)
                elif ing_monto <= 0:
                    st.markdown('<div class="toast-err">El monto debe ser mayor a 0</div>', unsafe_allow_html=True)
                else:
                    try:
                        guardar_ingreso(ing_desc.strip(), ing_persona, moneda_sel, ing_monto,
                                        round(monto_ars_f,2), round(monto_usd_f,4), dolar, ing_fecha, ing_horas)
                        st.session_state.show_add_ingreso = False
                        st.rerun()
                    except Exception as e:
                        st.markdown(f'<div class="toast-err">Error: {e}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    if df.empty:
        st.markdown(f'<div class="grp" style="padding:28px;text-align:center;color:{TEXT3}">Sin datos para {label_periodo(periodo_viendo)}.</div>', unsafe_allow_html=True)
    else:
        busq = st.text_input("", placeholder="Buscar gasto...", label_visibility="collapsed", key="busqueda_input")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        df_vista = df.copy()
        if busq.strip():
            df_vista = df_vista[df_vista["Item"].str.contains(busq.strip(), case=False, na=False)]
        cats_orden = df_vista.groupby("Cat").apply(lambda g: g["Pagado"].eq(False).sum()).sort_values(ascending=False).index.tolist()
        st.markdown(f'<div class="sec-lbl">Gastos por categoría</div>', unsafe_allow_html=True)
        for cat in cats_orden:
            df_cat = df_vista[df_vista["Cat"] == cat]
            t_cat  = df_cat["Monto (ARS)"].sum()
            color  = cat_color(cat)
            n_pend = int(df_cat["Pagado"].eq(False).sum())
            badge  = f'<span class="pend-badge">{n_pend}</span>' if n_pend > 0 else ""
            ico_hdr = cat_icon_svg(cat, color, size=20)
            st.markdown(f'<div class="grp"><div class="grp-hdr"><div style="width:20px;height:20px;border-radius:5px;overflow:hidden;flex-shrink:0">{ico_hdr}</div><span class="grp-hdr-lbl">{cat}{badge}</span><span class="grp-hdr-amt" style="color:{color}">{fmt_ars(t_cat)}</span></div>', unsafe_allow_html=True)
            for idx, row in df_cat.iterrows():
                paid = row["Pagado"]
                nc   = "row-name-paid" if paid else "row-name"
                ac   = "row-amt-paid"  if paid else "row-amt"
                op   = "0.5" if paid else "1"
                ico  = cat_icon_svg(cat, color, size=32)
                tasa_r = row.get("Tasa USD", 0)
                if row["Monto (ARS)"] <= 0 and not paid:
                    rref = ref_monto(row["Item"])
                    amt_html = f'<div class="{ac}" style="color:{ORANGE}">A definir</div>'
                    usd_html = f'<div class="row-usd">mes ant. {fmt_ars(rref)}</div>' if rref > 0 else '<div class="row-usd">&mdash;</div>'
                else:
                    usd_v  = row["Monto (ARS)"] / tasa_r if tasa_r > 0 else row["Monto (ARS)"] / dolar
                    amt_html = f'<div class="{ac}">{fmt_ars(row["Monto (ARS)"])}</div>'
                    usd_html = f'<div class="row-usd">U$S {usd_v:,.0f}</div>'
                st.markdown(f'<div class="row" style="opacity:{op}"><div style="width:32px;height:32px;flex-shrink:0;border-radius:8px;overflow:hidden">{ico}</div><div class="row-body"><div class="{nc}">{row["Item"]}</div><div class="row-sub">{badge_venc(row)}</div></div><div class="row-right">{amt_html}{usd_html}</div></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if es_mes_actual:
            pend_items = df_vista[df_vista["Pagado"] == False]
            if not pend_items.empty:
                with st.expander(f"Marcar como pagado ({len(pend_items)} pendientes)"):
                    for _i, (_, row) in enumerate(pend_items.iterrows()):
                        _key_monto = f"monto_pay_{_i}_{row['Item']}_{row['Periodo']}"
                        _key_btn   = f"pay_{_i}_{row['Item']}_{row['Periodo']}"
                        _rref      = ref_monto(row["Item"])
                        cn, cm, cb = st.columns([2.5, 1.5, 1])
                        with cn:
                            _sub = f'<div style="font-size:11px;color:{TEXT3};margin-top:1px">mes pasado: {fmt_ars(_rref)}</div>' if _rref > 0 else ''
                            st.markdown(f'<div style="font-size:14px;padding:8px 0 0">{row["Item"]}{_sub}</div>', unsafe_allow_html=True)
                        with cm:
                            st.number_input(
                                "Monto ARS", min_value=0, step=100,
                                value=int(row["Monto (ARS)"]) if row["Monto (ARS)"] > 0 else 0,
                                key=_key_monto, label_visibility="collapsed"
                            )
                        with cb:
                            if st.button("✓ Pagado", key=_key_btn, use_container_width=True):
                                try:
                                    monto_guardado = st.session_state.get(_key_monto, row["Monto (ARS)"])
                                    marcar_pagado_maestro(row["Item"], row["Periodo"], df_maestro, dolar, nuevo_monto=monto_guardado)
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))

        st.markdown(f'<div class="sec-lbl">Top 5 gastos</div><div class="grp">', unsafe_allow_html=True)
        for _, row in df.nlargest(5,"Monto (ARS)").iterrows():
            color  = cat_color(row["Cat"])
            pct_t  = int(row["Monto (ARS)"] / total_ars * 100) if total_ars > 0 else 0
            ico    = cat_icon_svg(row["Cat"], color, size=32)
            tasa_r = row.get("Tasa USD", 0)
            usd_v  = row["Monto (ARS)"] / tasa_r if tasa_r > 0 else row["Monto (ARS)"] / dolar
            st.markdown(f'<div class="row"><div style="width:32px;height:32px;flex-shrink:0;border-radius:8px;overflow:hidden">{ico}</div><div class="row-body"><div class="row-name">{row["Item"]}</div><div class="row-sub">{row["Cat"]} &middot; {pct_t}% del total</div></div><div class="row-right"><div class="row-amt">{fmt_ars(row["Monto (ARS)"])}</div><div class="row-usd">U$S {usd_v:,.0f}</div></div></div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── DUPLICAR TODO EL MES VISTO → MES SIGUIENTE (al final de la pantalla) ──
    if not df_base_periodo.empty:
        periodo_sig = calcular_mes_siguiente(periodo_viendo)
        df_fuente = df_maestro[df_maestro["Periodo"] == periodo_viendo].copy()
        items_destino = set(
            df_maestro[df_maestro["Periodo"] == periodo_sig]["Item"].astype(str).str.strip().str.lower()
        )
        pendientes_clonar = [r for _, r in df_fuente.iterrows()
                             if str(r["Item"]).strip().lower() not in items_destino]
        ya_existen = len(df_fuente) - len(pendientes_clonar)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        with st.expander(f"Duplicar los {len(df_fuente)} ítems de {label_periodo(periodo_viendo)}  →  {label_periodo(periodo_sig)}"):
            msg = (f'Se agregarán <strong style="color:{TEXT}">{len(pendientes_clonar)} ítems</strong> a '
                   f'<strong style="color:{TEXT}">{label_periodo(periodo_sig)}</strong> con <strong style="color:{TEXT}">monto $0</strong>, '
                   f'para que cargues lo que se paga ese mes. El monto de {label_periodo(periodo_viendo)} queda como referencia.')
            if ya_existen:
                msg += f' <span style="color:{TEXT3}">({ya_existen} ya están en {label_periodo(periodo_sig)} y se omiten para no duplicar).</span>'
            st.markdown(f'<div style="font-size:13px;color:{TEXT2};margin-bottom:10px;line-height:1.5">{msg}</div>', unsafe_allow_html=True)
            for _, r in df_fuente.iterrows():
                existe  = str(r["Item"]).strip().lower() in items_destino
                color_c = cat_color(categorizar(r["Item"]))
                st.markdown(
                    f'<div style="font-size:14px;padding:7px 0;border-bottom:1px solid {SEP};'
                    f'display:flex;justify-content:space-between;align-items:center;opacity:{"0.4" if existe else "1"}">'
                    f'<span style="color:{TEXT}">{r["Item"]}{" &middot; ya existe" if existe else ""}</span>'
                    f'<span style="color:{TEXT3};font-weight:500;font-size:12px">ref. {fmt_ars(r["Monto (ARS)"])}</span></div>',
                    unsafe_allow_html=True
                )
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if st.button(f"Duplicar {len(pendientes_clonar)} ítems a {label_periodo(periodo_sig)}",
                         type="primary", use_container_width=True,
                         disabled=(len(pendientes_clonar) == 0)):
                nuevos_registros = []
                y_sig, m_sig = map(int, periodo_sig.split('-'))
                for r in pendientes_clonar:
                    nueva_fecha = None
                    if pd.notnull(r["Dia Pago"]) and str(r["Dia Pago"]).strip() != "":
                        try:
                            old_d = pd.to_datetime(r["Dia Pago"])
                            nueva_fecha = date(y_sig, m_sig, min(old_d.day, 28))
                        except Exception:
                            pass
                    nuevos_registros.append({
                        "Categoria": categorizar(r["Item"]),
                        "Item": r["Item"],
                        "Monto (ARS)": 0.0,
                        "Dia Pago": nueva_fecha,
                        "Pagado": False,
                        "Periodo": periodo_sig,
                        "Tasa USD": dolar
                    })
                if nuevos_registros:
                    df_nuevos = pd.DataFrame(nuevos_registros)
                    guardar_hoja_maestro(pd.concat([df_maestro, df_nuevos], ignore_index=True), dolar)
                    st.session_state.periodo_sel = periodo_sig
                    st.rerun()

    # ── PONER PENDIENTES EN $0 (corrección para meses ya duplicados con monto) ──
    if not df_base_periodo.empty and periodo_viendo >= periodo_actual:
        pend_con_monto = df_base_periodo[(df_base_periodo["Pagado"] == False) & (df_base_periodo["Monto (ARS)"] > 0)]
        if not pend_con_monto.empty:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            with st.expander(f"Poner en $0 los {len(pend_con_monto)} ítems pendientes de {label_periodo(periodo_viendo)}"):
                st.markdown(
                    f'<div style="font-size:13px;color:{TEXT2};margin-bottom:10px;line-height:1.5">'
                    f'Deja en <strong style="color:{TEXT}">$0</strong> los gastos pendientes de {label_periodo(periodo_viendo)} '
                    f'para que cargues el monto real de este mes. Los ya pagados no se tocan; '
                    f'el monto de {label_periodo(calcular_mes_anterior(periodo_viendo))} sigue de referencia.</div>',
                    unsafe_allow_html=True
                )
                for _, r in pend_con_monto.iterrows():
                    st.markdown(
                        f'<div style="font-size:14px;padding:7px 0;border-bottom:1px solid {SEP};'
                        f'display:flex;justify-content:space-between;align-items:center">'
                        f'<span style="color:{TEXT}">{r["Item"]}</span>'
                        f'<span style="color:{TEXT3};font-size:12px">{fmt_ars(r["Monto (ARS)"])} &rarr; $0</span></div>',
                        unsafe_allow_html=True
                    )
                st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
                if st.button(f"Poner en $0 ({len(pend_con_monto)} ítems)", type="primary",
                             use_container_width=True, key="reset_cero"):
                    df_act = df_maestro.copy()
                    mask = ((df_act["Periodo"] == periodo_viendo)
                            & (df_act["Pagado"] == False)
                            & (df_act["Monto (ARS)"] > 0))
                    df_act.loc[mask, "Monto (ARS)"] = 0.0
                    guardar_hoja_maestro(df_act, dolar)
                    st.rerun()


# ══════════════════════════════════════════════════════════════════
# PANTALLA: INGRESOS
# ══════════════════════════════════════════════════════════════════
elif st.session_state.screen == "ingresos":

    if not es_mes_actual:
        st.markdown(f'<div class="alert alert-b">Ingresos de <strong>{label_periodo(periodo_viendo)}</strong></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sec-lbl">Ingresos &mdash; {label_periodo(periodo_viendo)}</div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="card-ing">
      <div class="c-lbl">Total ingresado</div>
      <div class="c-val" style="color:{GREEN}">{fmt_ars(total_ing_ars) if total_ing_ars > 0 else "Sin datos"}</div>
      <div class="c-sub">{fmt_usd(total_ing_usd)}</div>
      <div class="sep"></div>
      <div class="persona-row">
        <div class="av av-h">H</div>
        <div class="persona-body"><div class="persona-name">Henry</div><div class="persona-sub">{pct_henry if total_ing_ars > 0 else 0}%</div></div>
        <div><div class="persona-amt" style="color:{ACCENT}">{fmt_ars(ing_henry)}</div><div class="persona-amt-sub">{fmt_usd_from_ars(ing_henry, dolar)}</div></div>
      </div>
      <div style="margin:6px 0 12px 41px"><div class="bar-bg"><div class="bar-fill" style="width:{pct_henry if total_ing_ars > 0 else 0}%;background:{ACCENT}"></div></div></div>
      <div class="persona-row">
        <div class="av av-j">J</div>
        <div class="persona-body"><div class="persona-name">Jaike</div><div class="persona-sub">{pct_jaike if total_ing_ars > 0 else 0}%</div></div>
        <div><div class="persona-amt" style="color:{GOLD}">{fmt_ars(ing_jaike)}</div><div class="persona-amt-sub">{fmt_usd_from_ars(ing_jaike, dolar)}</div></div>
      </div>
      <div style="margin:6px 0 0 41px"><div class="bar-bg"><div class="bar-fill" style="width:{pct_jaike if total_ing_ars > 0 else 0}%;background:{GOLD}"></div></div></div>
    </div>""", unsafe_allow_html=True)

    if es_mes_actual:
        lbl_i2 = "Cancelar" if st.session_state.show_add_ingreso else "＋ Agregar ingreso"
        if st.button(lbl_i2, type="secondary" if st.session_state.show_add_ingreso else "primary",
                     use_container_width=True, key="btn_ing2"):
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
                    st.markdown(f'<div style="padding:7px 0"><div style="font-size:11px;color:{TEXT3};font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">Equiv. USD</div><div style="font-family:var(--font-num);font-size:18px;font-weight:600;color:{GREEN}">U$S {equiv2:,.2f}</div></div>', unsafe_allow_html=True)
                    mars2 = ing_monto2; musd2 = equiv2
                else:
                    equiv2 = ing_monto2 * dolar
                    st.markdown(f'<div style="padding:7px 0"><div style="font-size:11px;color:{TEXT3};font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px">Equiv. ARS</div><div style="font-family:var(--font-num);font-size:18px;font-weight:600;color:{GREEN}">{fmt_ars(equiv2)}</div></div>', unsafe_allow_html=True)
                    mars2 = equiv2; musd2 = ing_monto2
            with i6: ing_fecha2 = st.date_input("Fecha", value=hoy, key="ing_fecha2")
            st.markdown(f'<div style="font-size:12px;color:{TEXT3};margin:6px 0 2px">Tasa: <strong style="color:{TEXT}">$ {dolar:,.0f} ARS/USD</strong></div>', unsafe_allow_html=True)
            ing_horas2 = st.number_input("Horas trabajadas (opcional)", min_value=0.0, step=0.5, key="ing_horas2", help="Si este pago corresponde a horas trabajadas, cargalas acá y calculo el $/hora automáticamente.")
            if ing_horas2 > 0 and ing_monto2 > 0:
                ph_prev2 = mars2 / ing_horas2
                phu_prev2 = musd2 / ing_horas2
                st.markdown(f'<div style="font-size:12px;color:{TEXT3};margin:2px 0 8px">$/hora: <strong style="color:{GREEN}">{fmt_ars(ph_prev2)}</strong> &middot; U$S {phu_prev2:,.2f}/hs</div>', unsafe_allow_html=True)
            if st.button("Guardar", type="primary", use_container_width=True, key="guardar_ing2"):
                if not ing_desc2.strip():
                    st.markdown('<div class="toast-err">Ingresa una descripción</div>', unsafe_allow_html=True)
                elif ing_monto2 <= 0:
                    st.markdown('<div class="toast-err">El monto debe ser mayor a 0</div>', unsafe_allow_html=True)
                else:
                    try:
                        guardar_ingreso(ing_desc2.strip(), ing_persona2, moneda_sel2, ing_monto2,
                                        round(mars2,2), round(musd2,4), dolar, ing_fecha2, ing_horas2)
                        st.session_state.show_add_ingreso = False
                        st.rerun()
                    except Exception as e:
                        st.markdown(f'<div class="toast-err">Error: {e}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    if df_ing_periodo.empty:
        st.markdown(f'<div class="grp" style="padding:28px;text-align:center;color:{TEXT3}">Sin ingresos en {label_periodo(periodo_viendo)}.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sec-lbl">Detalle &mdash; {label_periodo(periodo_viendo)}</div><div class="grp">', unsafe_allow_html=True)
        for _, row in df_ing_periodo.sort_values("Fecha", ascending=False).iterrows():
            persona  = str(row.get("Persona",""))
            desc     = str(row.get("Descripcion",""))
            monto_ar = float(row.get("Monto ARS",0))
            monto_ud = float(row.get("Monto USD",0))
            tasa_r   = float(row.get("Tasa USD/ARS",0))
            fecha_r  = row.get("Fecha","")
            fecha_s  = fecha_r.strftime("%-d %b %Y") if hasattr(fecha_r,"strftime") else str(fecha_r)
            ico_c    = ACCENT if persona.upper() == "HENRY" else GOLD
            st.markdown(f"""<div class="ing-row">
              <div style="width:32px;height:32px;border-radius:8px;background:{ico_c};display:flex;align-items:center;justify-content:center;flex-shrink:0">
                <svg width="17" height="17" viewBox="0 0 18 18"><rect x="2" y="5" width="14" height="9" rx="2" fill="white" opacity="0.9"/><rect x="2" y="7" width="14" height="2" fill="{ico_c}"/><circle cx="5" cy="11" r="1.2" fill="{ico_c}" opacity="0.7"/></svg>
              </div>
              <div class="row-body"><div class="row-name">{desc}</div>
              <div class="row-sub">{badge_persona(persona)} &nbsp;{fecha_s} &middot; Tasa $ {tasa_r:,.0f}</div></div>
              <div class="row-right">
                <div class="row-amt" style="color:{GREEN}">{fmt_ars(monto_ar)}</div>
                <div class="row-usd">U$S {monto_ud:,.2f}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── HORAS TRABAJADAS (discreto) ──
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    with st.expander("Horas trabajadas", expanded=False):
        st.markdown(f'<div style="font-size:11.5px;color:{TEXT3};margin-bottom:10px;line-height:1.5">Sumale las horas a cada ingreso ya cargado y calculo solo cuánto te pagaron por hora, en ARS y USD.</div>', unsafe_allow_html=True)

        ver_todo = st.checkbox("Ver historial completo (todos los períodos)", key="horas_ver_todo")
        df_horas_base = df_ing_todo if ver_todo else df_ing_periodo
        etiqueta_scope = "en todo el historial" if ver_todo else f"en {label_periodo(periodo_viendo)}"

        if df_horas_base.empty:
            st.markdown(f'<div style="text-align:center;padding:16px;color:{TEXT3};font-size:12.5px">Sin ingresos cargados {etiqueta_scope}.</div>', unsafe_allow_html=True)
        else:
            con_horas = df_horas_base[df_horas_base["Horas"] > 0]
            if not con_horas.empty:
                prom_ars = (con_horas["Monto ARS"] / con_horas["Horas"]).mean()
                prom_usd = (con_horas["Monto USD"] / con_horas["Horas"]).mean()
                st.markdown(f"""<div class="kpi-card" style="margin-bottom:10px">
                  <div class="kpi-lbl">Promedio $/hora {etiqueta_scope}</div>
                  <div class="kpi-val" style="color:{GREEN}">{fmt_ars(prom_ars)}</div>
                  <div class="kpi-sub">U$S {prom_usd:,.2f} / hs &middot; {con_horas['Horas'].sum():.1f} hs cargadas</div>
                </div>""", unsafe_allow_html=True)

            st.markdown('<div class="grp">', unsafe_allow_html=True)
            for _, row in df_horas_base.sort_values("Fecha", ascending=False).iterrows():
                desc      = str(row.get("Descripcion",""))
                persona   = str(row.get("Persona",""))
                monto_ar  = float(row.get("Monto ARS",0))
                monto_ud  = float(row.get("Monto USD",0))
                horas_val = float(row.get("Horas",0) or 0)
                sheet_row = row.get("SheetRow")
                fecha_r   = row.get("Fecha","")
                fecha_s   = fecha_r.strftime("%-d %b %Y") if hasattr(fecha_r,"strftime") else str(fecha_r)
                ico_c     = ACCENT if persona.upper() == "HENRY" else GOLD

                if horas_val > 0:
                    ph_ars = monto_ar / horas_val
                    ph_usd = monto_ud / horas_val
                    st.markdown(f"""<div class="ing-row">
                      <div style="width:32px;height:32px;border-radius:8px;background:{ico_c};display:flex;align-items:center;justify-content:center;flex-shrink:0">
                        <svg width="17" height="17" viewBox="0 0 18 18"><circle cx="9" cy="9" r="7" fill="none" stroke="white" stroke-width="1.6"/><path d="M9,5 L9,9 L12,11" stroke="white" stroke-width="1.6" fill="none" stroke-linecap="round"/></svg>
                      </div>
                      <div class="row-body"><div class="row-name">{desc}</div>
                      <div class="row-sub">{badge_persona(persona)} &nbsp;{fecha_s} &middot; {horas_val:.1f} hs</div></div>
                      <div class="row-right">
                        <div class="row-amt" style="color:{TEXT}">{fmt_ars(ph_ars)}/hs</div>
                        <div class="row-usd">U$S {ph_usd:,.2f}/hs</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                else:
                    rc1, rc2, rc3 = st.columns([2.6, 1, 0.8])
                    with rc1:
                        st.markdown(f"""<div style="padding:9px 0 0">
                          <div style="font-size:13.5px;font-weight:500">{desc}</div>
                          <div style="font-size:11px;color:{TEXT3};margin-top:2px">{badge_persona(persona)} &nbsp;{fecha_s} &middot; {fmt_ars(monto_ar)} &middot; U$S {monto_ud:,.2f}</div>
                        </div>""", unsafe_allow_html=True)
                    with rc2:
                        st.number_input("Horas", min_value=0.0, step=0.5, key=f"h_add_{sheet_row}", label_visibility="collapsed")
                    with rc3:
                        if st.button("✓", key=f"h_save_{sheet_row}", use_container_width=True):
                            nuevas_horas = st.session_state.get(f"h_add_{sheet_row}", 0)
                            if nuevas_horas and nuevas_horas > 0:
                                try:
                                    actualizar_horas_ingreso(int(sheet_row), nuevas_horas)
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))
            st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PANTALLA: GASTOS
# ══════════════════════════════════════════════════════════════════
elif st.session_state.screen == "gastos":

    st.markdown(f'<div class="sec-lbl">Editor de egresos &mdash; {label_periodo(periodo_viendo)}</div>', unsafe_allow_html=True)

    if df.empty:
        st.markdown(f'<div class="grp" style="padding:28px;text-align:center;color:{TEXT3}">Sin datos para {label_periodo(periodo_viendo)}.</div>', unsafe_allow_html=True)
    else:
        if not es_mes_actual:
            st.markdown(f'<div class="alert alert-o">Editando <strong>{label_periodo(periodo_viendo)}</strong>. Guardar reescribirá la hoja maestra.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div style="background:{SURF2};border-radius:var(--r-card);padding:13px 15px;margin-bottom:12px;font-size:12.5px;color:{TEXT2};line-height:1.6;border:1px solid {GLASS_BORDER};">
  Editá montos, fechas de vencimiento o marcá ítems como pagados directamente en la tabla.<br>
  <strong style="color:{TEXT}">Presioná "Guardar y sincronizar"</strong> para escribir los cambios en Google Sheets.
</div>""", unsafe_allow_html=True)

        COL_CONFIG = {
            "Pagado":      st.column_config.CheckboxColumn("Pagado", width="small"),
            "Item":        st.column_config.TextColumn("Ítem"),
            "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$ %d"),
            "USD":         st.column_config.NumberColumn("USD", format="U$S %.0f", disabled=True, width="small"),
            "Dia Pago":    st.column_config.DateColumn("Vencimiento", format="DD/MM/YY"),
            "Periodo":     st.column_config.TextColumn("Periodo", disabled=True, width="small"),
            "Tasa USD":    st.column_config.NumberColumn("Tasa $", disabled=True, width="small"),
        }
        COL_ORDER = ("Pagado","Item","Monto (ARS)","USD","Dia Pago","Periodo","Tasa USD")

        df_edit = st.data_editor(
            df.reset_index(drop=True),
            column_config=COL_CONFIG,
            column_order=COL_ORDER,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="editor_gastos"
        )

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        bc1, bc2, bc3 = st.columns([2.5, 0.8, 0.8])
        with bc1:
            if st.button("💾 Guardar y sincronizar", type="primary", use_container_width=True):
                try:
                    df_otros = df_maestro[df_maestro["Periodo"] != periodo_viendo].copy()
                    df_combinado = pd.concat([df_otros, df_edit], ignore_index=True)
                    guardar_hoja_maestro(df_combinado, dolar)
                    st.markdown('<div class="toast-ok">✓ Cambios guardados en Google Sheets</div>', unsafe_allow_html=True)
                    st.rerun()
                except Exception as e:
                    st.markdown(f'<div class="toast-err">Error: {e}</div>', unsafe_allow_html=True)
        with bc2:
            if st.button("🔄 Recargar", type="secondary", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with bc3:
            if not df.empty:
                st.download_button(
                    "📥 Excel",
                    data=exportar_excel(df, df_ing_todo),
                    file_name=f"gastos_{periodo_viendo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="sec-lbl">Resumen rápido</div>', unsafe_allow_html=True)
        st.markdown(f"""
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:8px;">
  <div class="kpi-card">
    <div class="kpi-lbl">Total egresos</div>
    <div class="kpi-val" style="color:{TEXT}">{fmt_ars(total_ars)}</div>
    <div class="kpi-sub">{fmt_usd_from_ars(total_ars, dolar)}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-lbl">Pagados</div>
    <div class="kpi-val" style="color:{GREEN}">{fmt_ars(pagado_ars)}</div>
    <div class="kpi-sub">{n_pagados} ítems &middot; {pct_pag}%</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-lbl">Pendientes</div>
    <div class="kpi-val" style="color:{RED}">{fmt_ars(pend_ars)}</div>
    <div class="kpi-sub">{n_pendientes} ítems &middot; {pct_pend}%</div>
  </div>
</div>
""", unsafe_allow_html=True)

        if es_mes_actual:
            pend_quick = df[df["Pagado"] == False]
            if not pend_quick.empty:
                with st.expander(f"Marcar pagados rápido ({len(pend_quick)} pendientes)"):
                    for _i, (_, row) in enumerate(pend_quick.iterrows()):
                        _key_monto = f"monto_qpay_{_i}_{row['Item']}_{row['Periodo']}"
                        _key_btn   = f"qpay_{_i}_{row['Item']}_{row['Periodo']}"
                        _rref      = ref_monto(row["Item"])
                        cn, cm, cb = st.columns([2.5, 1.5, 1])
                        with cn:
                            _sub = f'<div style="font-size:11px;color:{TEXT3};margin-top:1px">mes pasado: {fmt_ars(_rref)}</div>' if _rref > 0 else ''
                            st.markdown(f'<div style="font-size:14px;padding:8px 0 0">{row["Item"]}{_sub}</div>', unsafe_allow_html=True)
                        with cm:
                            st.number_input(
                                "Monto ARS", min_value=0, step=100,
                                value=int(row["Monto (ARS)"]) if row["Monto (ARS)"] > 0 else 0,
                                key=_key_monto, label_visibility="collapsed"
                            )
                        with cb:
                            if st.button("✓ Pagado", key=_key_btn, use_container_width=True):
                                try:
                                    monto_guardado = st.session_state.get(_key_monto, row["Monto (ARS)"])
                                    marcar_pagado_maestro(row["Item"], row["Periodo"], df_maestro, dolar, nuevo_monto=monto_guardado)
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))


# ══════════════════════════════════════════════════════════════════
# PANTALLA: TENDENCIAS
# ══════════════════════════════════════════════════════════════════
elif st.session_state.screen == "tendencias":
    st.markdown('<div class="sec-lbl">Análisis histórico</div>', unsafe_allow_html=True)

    if df_maestro.empty or df_maestro["Periodo"].nunique() < 1:
        st.markdown(f'<div class="grp" style="padding:28px;text-align:center;color:{TEXT3}">Sin datos históricos todavía.</div>', unsafe_allow_html=True)
    else:
        gasto_m = df_maestro.groupby("Periodo")["Monto (ARS)"].sum().reset_index()
        gasto_m.columns = ["Periodo","Gastos"]

        ing_henry_m = pd.DataFrame(columns=["Periodo","Henry"])
        ing_jaike_m = pd.DataFrame(columns=["Periodo","Jaike"])
        ing_total_m = pd.DataFrame(columns=["Periodo","Ingresos"])

        if not df_ing_todo.empty and "Periodo" in df_ing_todo.columns:
            _h = df_ing_todo[df_ing_todo["Persona"].str.upper()=="HENRY"].groupby("Periodo")["Monto ARS"].sum().reset_index()
            _h.columns = ["Periodo","Henry"]
            ing_henry_m = _h
            _j = df_ing_todo[df_ing_todo["Persona"].str.upper()=="JAIKE"].groupby("Periodo")["Monto ARS"].sum().reset_index()
            _j.columns = ["Periodo","Jaike"]
            ing_jaike_m = _j
            _t = df_ing_todo.groupby("Periodo")["Monto ARS"].sum().reset_index()
            _t.columns = ["Periodo","Ingresos"]
            ing_total_m = _t

        hist = (gasto_m
                .merge(ing_total_m, on="Periodo", how="left")
                .merge(ing_henry_m, on="Periodo", how="left")
                .merge(ing_jaike_m, on="Periodo", how="left")
                .fillna(0)
                .sort_values("Periodo", ascending=False)
                .reset_index(drop=True))

        hist["Balance"]  = hist.get("Ingresos", 0) - hist["Gastos"]
        hist["Label"]    = hist["Periodo"].apply(label_periodo)
        tiene_ingresos   = "Ingresos" in hist.columns and hist["Ingresos"].sum() > 0

        total_g  = hist["Gastos"].sum()
        total_i  = hist["Ingresos"].sum() if tiene_ingresos else 0
        bal_tot  = total_i - total_g
        prom_g   = hist["Gastos"].mean()
        prom_i   = hist["Ingresos"].mean() if tiene_ingresos else 0
        n_meses  = len(hist)
        bc_t     = GREEN if bal_tot >= 0 else RED
        bs_t     = "+" if bal_tot >= 0 else ""

        st.markdown(f"""<div class="kpi-grid-3">
          <div class="kpi-card">
            <div class="kpi-lbl">Gastos acumulados</div>
            <div class="kpi-val" style="color:{RED}">{fmt_ars(total_g)}</div>
            <div class="kpi-sub">prom. {fmt_ars(prom_g)}/mes &middot; {n_meses} meses</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-lbl">Ingresos acumulados</div>
            <div class="kpi-val" style="color:{GREEN}">{fmt_ars(total_i) if tiene_ingresos else "&mdash;"}</div>
            <div class="kpi-sub">{"prom. " + fmt_ars(prom_i) + "/mes" if tiene_ingresos else "Sin datos"}</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-lbl">Balance acumulado</div>
            <div class="kpi-val" style="color:{bc_t}">{bs_t}{fmt_ars(bal_tot) if tiene_ingresos else "&mdash;"}</div>
            <div class="kpi-sub">{"Superávit total" if bal_tot >= 0 else "Déficit total"}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        if n_meses >= 1:
            mes_max_g = hist.loc[hist["Gastos"].idxmax()]
            mes_min_g = hist.loc[hist["Gastos"].idxmin()]
            meses_con_balance = hist[hist["Balance"] != 0] if tiene_ingresos else pd.DataFrame()

            kpi2_html = f"""<div class="kpi-grid-2" style="margin-bottom:14px">
              <div class="kpi-card"><div class="kpi-lbl">Mes más caro</div>
                <div class="kpi-val" style="color:{RED};font-size:17px">{mes_max_g['Label']}</div>
                <div class="kpi-sub">{fmt_ars(mes_max_g['Gastos'])}</div></div>
              <div class="kpi-card"><div class="kpi-lbl">Mes más barato</div>
                <div class="kpi-val" style="color:{GREEN};font-size:17px">{mes_min_g['Label']}</div>
                <div class="kpi-sub">{fmt_ars(mes_min_g['Gastos'])}</div></div>
            </div>"""

            if tiene_ingresos and not meses_con_balance.empty:
                mejor_bal = meses_con_balance.loc[meses_con_balance["Balance"].idxmax()]
                peor_bal  = meses_con_balance.loc[meses_con_balance["Balance"].idxmin()]
                kpi2_html += f"""<div class="kpi-grid-2" style="margin-bottom:14px">
                  <div class="kpi-card"><div class="kpi-lbl">Mejor balance</div>
                    <div class="kpi-val" style="color:{GREEN};font-size:17px">{mejor_bal['Label']}</div>
                    <div class="kpi-sub">+{fmt_ars(mejor_bal['Balance'])}</div></div>
                  <div class="kpi-card"><div class="kpi-lbl">Peor balance</div>
                    <div class="kpi-val" style="color:{RED};font-size:17px">{peor_bal['Label']}</div>
                    <div class="kpi-sub">{fmt_ars(peor_bal['Balance'])}</div></div>
                </div>"""
            st.markdown(kpi2_html, unsafe_allow_html=True)

        if n_meses >= 2:
            hist_graf = hist.sort_values("Periodo", ascending=True).tail(12)
            fig = go.Figure()
            if tiene_ingresos:
                fig.add_trace(go.Bar(
                    name="Ingresos", x=hist_graf["Label"], y=hist_graf["Ingresos"],
                    marker_color=GREEN, marker_opacity=0.85,
                    text=[fmt_ars(v) for v in hist_graf["Ingresos"]],
                    textposition="outside", textfont=dict(size=9, color=GREEN),
                ))
            fig.add_trace(go.Bar(
                name="Gastos", x=hist_graf["Label"], y=hist_graf["Gastos"],
                marker_color=RED, marker_opacity=0.85,
                text=[fmt_ars(v) for v in hist_graf["Gastos"]],
                textposition="outside", textfont=dict(size=9, color=RED),
            ))
            if tiene_ingresos:
                fig.add_trace(go.Scatter(
                    name="Balance", x=hist_graf["Label"], y=hist_graf["Balance"],
                    mode="lines+markers",
                    line=dict(color=ACCENT, width=2, dash="dot"),
                    marker=dict(size=6, color=[GREEN if v >= 0 else RED for v in hist_graf["Balance"]],
                                line=dict(color=ACCENT, width=1.5)),
                ))
            fig.update_layout(
                barmode="group", paper_bgcolor=PLOTBG, plot_bgcolor=PLOTBG,
                font=dict(family="Plus Jakarta Sans, sans-serif", color=TEXT2, size=11),
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                            font=dict(size=11, color=TEXT2), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(showgrid=False, tickfont=dict(size=10, color=TEXT2),
                           linecolor=GRID, tickangle=-30),
                yaxis=dict(showgrid=True, gridcolor=GRID,
                           tickfont=dict(size=10, color=TEXT2), zeroline=False,
                           tickprefix="$", tickformat=",.0f"),
                height=280, bargap=0.25, bargroupgap=0.06,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="sec-lbl">Detalle mes a mes</div>', unsafe_allow_html=True)

        for i_row, row in hist.iterrows():
            periodo_r  = row["Periodo"]
            label_r    = row["Label"]
            gastos_r   = row["Gastos"]
            ingresos_r = row.get("Ingresos", 0)
            henry_r    = row.get("Henry", 0)
            jaike_r    = row.get("Jaike", 0)
            balance_r  = row["Balance"]
            es_actual  = (periodo_r == periodo_actual)

            if i_row + 1 < len(hist):
                prev_g = hist.iloc[i_row + 1]["Gastos"]
                var_g  = ((gastos_r - prev_g) / prev_g * 100) if prev_g > 0 else 0
            else:
                var_g = None

            dot_col  = GREEN if balance_r >= 0 else RED
            bal_sym  = "+" if balance_r >= 0 else ""
            total_aporte = henry_r + jaike_r
            pct_h_r = int(henry_r / total_aporte * 100) if total_aporte > 0 else 0
            pct_j_r = int(jaike_r / total_aporte * 100) if total_aporte > 0 else 0

            if var_g is not None:
                if abs(var_g) < 1:
                    var_badge = f'<span class="var-badge-neu">= sin cambio</span>'
                elif var_g > 0:
                    var_badge = f'<span class="var-badge-neg">&#9650; {var_g:+.1f}% vs anterior</span>'
                else:
                    var_badge = f'<span class="var-badge-pos">&#9660; {var_g:.1f}% vs anterior</span>'
            else:
                var_badge = f'<span class="var-badge-neu">primer mes</span>'

            actual_badge = f'<span style="font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;background:{rgba(ACCENT,0.16)};color:{ACCENT};margin-left:7px">actual</span>' if es_actual else ""

            exp_key    = f"exp_{periodo_r}"
            is_expanded = st.session_state.get(exp_key, es_actual)
            chevron    = "▲" if is_expanded else "▼"

            col_hdr, col_btn = st.columns([5, 1])
            with col_hdr:
                n_items_r = len(df_maestro[df_maestro["Periodo"]==periodo_r])
                st.markdown(f"""
<div class="mes-card-header" style="border-radius:{'14px 14px 0 0' if is_expanded else '14px'};margin-bottom:{'0' if is_expanded else '4px'};">
  <div class="mes-dot" style="background:{dot_col};"></div>
  <div class="mes-title">
    <div class="mes-nombre">{label_r}{actual_badge}</div>
    <div class="mes-subtitle">{var_badge} &nbsp;&middot;&nbsp; {n_items_r} ítems</div>
  </div>
  <div class="{'mes-balance-pos' if balance_r >= 0 else 'mes-balance-neg'}">
    {bal_sym}{fmt_ars(abs(balance_r)) if tiene_ingresos else fmt_ars(gastos_r)}
  </div>
</div>""", unsafe_allow_html=True)
            with col_btn:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if st.button(chevron, key=f"btn_{exp_key}", use_container_width=True):
                    st.session_state[exp_key] = not is_expanded
                    st.rerun()

            if is_expanded:
                df_mes_g = df_maestro[df_maestro["Periodo"] == periodo_r]
                n_items  = len(df_mes_g)
                n_pag_r  = int(df_mes_g["Pagado"].apply(lambda x: str(x).upper() in ["TRUE","VERDADERO","SI","1"]).sum()) if not df_mes_g.empty else 0

                kpi_ing_html = f'<div class="mes-mini-kpi"><div class="mes-mini-lbl">Ingresos</div><div class="mes-mini-val" style="color:{GREEN}">{fmt_ars(ingresos_r)}</div><div class="mes-mini-sub">{fmt_usd_from_ars(ingresos_r, dolar)}</div></div>' if tiene_ingresos else ""
                kpi_bal_html = f'<div class="mes-mini-kpi"><div class="mes-mini-lbl">Balance</div><div class="mes-mini-val" style="color:{GREEN if balance_r>=0 else RED}">{bal_sym}{fmt_ars(balance_r)}</div><div class="mes-mini-sub">{"Superávit" if balance_r >= 0 else "Déficit"}</div></div>' if tiene_ingresos else ""

                st.markdown(f"""
<div style="background:{SURFACE};border-radius:0 0 14px 14px;padding:0 17px 17px;border:1px solid {GLASS_BORDER};border-top:none;margin-bottom:4px;">
  <div class="mes-body-grid" style="grid-template-columns:{'1fr 1fr 1fr' if tiene_ingresos else '1fr 1fr'};">
    <div class="mes-mini-kpi">
      <div class="mes-mini-lbl">Gastos</div>
      <div class="mes-mini-val" style="color:{RED}">{fmt_ars(gastos_r)}</div>
      <div class="mes-mini-sub">{n_items} ítems &middot; {n_pag_r} pagados</div>
    </div>
    {kpi_ing_html}
    {kpi_bal_html}
  </div>
""", unsafe_allow_html=True)

                if tiene_ingresos and (henry_r > 0 or jaike_r > 0):
                    st.markdown(f'<div style="font-size:10px;font-weight:600;color:{TEXT3};text-transform:uppercase;letter-spacing:.07em;margin-bottom:8px;">Aportes</div>', unsafe_allow_html=True)
                    if henry_r > 0:
                        st.markdown(f"""
<div class="aporte-row">
  <div class="aporte-av" style="background:{rgba(ACCENT,0.16)};color:{ACCENT};">H</div>
  <div class="aporte-body"><div class="aporte-name">Henry</div><div class="aporte-pct">{pct_h_r}%</div></div>
  <div><div class="aporte-amt" style="color:{ACCENT};">{fmt_ars(henry_r)}</div></div>
</div>
<div style="margin:3px 0 6px 36px"><div class="bar-bg"><div class="bar-fill" style="width:{pct_h_r}%;background:{ACCENT};"></div></div></div>""", unsafe_allow_html=True)
                    if jaike_r > 0:
                        st.markdown(f"""
<div class="aporte-row">
  <div class="aporte-av" style="background:{rgba(GOLD,0.16)};color:{GOLD};">J</div>
  <div class="aporte-body"><div class="aporte-name">Jaike</div><div class="aporte-pct">{pct_j_r}%</div></div>
  <div><div class="aporte-amt" style="color:{GOLD};">{fmt_ars(jaike_r)}</div></div>
</div>
<div style="margin:3px 0 10px 36px"><div class="bar-bg"><div class="bar-fill" style="width:{pct_j_r}%;background:{GOLD};"></div></div></div>""", unsafe_allow_html=True)

                if not df_mes_g.empty:
                    cat_mes = df_mes_g.copy()
                    cat_mes["Cat"] = cat_mes["Item"].apply(categorizar)
                    cat_mes["Monto (ARS)"] = cat_mes["Monto (ARS)"].apply(clean_currency)
                    cat_rank_mes = cat_mes.groupby("Cat")["Monto (ARS)"].sum().sort_values(ascending=False).reset_index()
                    max_cat = cat_rank_mes["Monto (ARS)"].max()
                    st.markdown(f'<div style="font-size:10px;font-weight:600;color:{TEXT3};text-transform:uppercase;letter-spacing:.07em;margin:12px 0 6px;">Gastos por categoría</div>', unsafe_allow_html=True)
                    for _, cat_row in cat_rank_mes.iterrows():
                        color_c = cat_color(cat_row["Cat"])
                        bar_w_c = int(cat_row["Monto (ARS)"] / max_cat * 100) if max_cat > 0 else 0
                        pct_c   = int(cat_row["Monto (ARS)"] / gastos_r * 100) if gastos_r > 0 else 0
                        st.markdown(f"""
<div class="cat-bar-row">
  <span class="cat-bar-name">{cat_row['Cat']}</span>
  <div class="cat-bar-track"><div class="cat-bar-fill" style="width:{bar_w_c}%;background:{color_c};"></div></div>
  <span class="cat-bar-amt" style="color:{color_c};">{fmt_ars(cat_row['Monto (ARS)'])} <span style="color:{TEXT3};font-weight:400">{pct_c}%</span></span>
</div>""", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── RANKING ACUMULADO ──
        st.markdown('<div class="sec-lbl" style="margin-top:18px">Ranking acumulado de categorías</div>', unsafe_allow_html=True)
        cat_acum = df_maestro.copy()
        cat_acum["Cat"] = cat_acum["Item"].apply(categorizar)
        cat_acum["Monto (ARS)"] = cat_acum["Monto (ARS)"].apply(clean_currency)
        cat_rank = cat_acum.groupby("Cat")["Monto (ARS)"].sum().sort_values(ascending=False).reset_index()
        cat_rank["Pct"] = (cat_rank["Monto (ARS)"] / cat_rank["Monto (ARS)"].sum() * 100).round(1)

        st.markdown('<div class="grp" style="padding:14px 16px">', unsafe_allow_html=True)
        max_v = cat_rank["Monto (ARS)"].max()
        for i2, (_, row) in enumerate(cat_rank.iterrows()):
            color = cat_color(row["Cat"])
            bar_w = int(row["Monto (ARS)"] / max_v * 100) if max_v > 0 else 0
            st.markdown(f"""<div style="margin-bottom:12px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-family:var(--font-num);font-size:11px;font-weight:600;color:{TEXT3};width:18px">#{i2+1}</span>
                  <span style="font-size:13.5px;color:{TEXT}">{row['Cat']}</span>
                </div>
                <div>
                  <span style="font-family:var(--font-num);font-size:13.5px;font-weight:600;color:{color}">{fmt_ars(row['Monto (ARS)'])}</span>
                  <span style="font-size:11px;color:{TEXT3};margin-left:6px">{row['Pct']}%</span>
                </div>
              </div>
              <div style="height:3px;background:{SURF3};border-radius:3px;overflow:hidden">
                <div class="cat-bar-fill" style="width:{bar_w}%;background:{color};border-radius:3px"></div>
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
