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

# ─────────────────────────────────────────────
# 4. SVG ÍCONOS
# ─────────────────────────────────────────────
def svg_icon(cat: str, color: str, size: int = 22) -> str:
    c = str(cat)
    s = size
    if "⚡" in c or "🔌" in c:
        path = f'<polygon points="{s*0.6},{s*0.05} {s*0.3},{s*0.52} {s*0.52},{s*0.52} {s*0.4},{s*0.95} {s*0.7},{s*0.45} {s*0.48},{s*0.45}" fill="white"/>'
    elif "🏠" in c or "🏡" in c:
        path = f'<polygon points="{s*0.5},{s*0.1} {s*0.88},{s*0.45} {s*0.78},{s*0.45} {s*0.78},{s*0.88} {s*0.22},{s*0.88} {s*0.22},{s*0.45} {s*0.12},{s*0.45}" fill="white"/><rect x="{s*0.38}" y="{s*0.58}" width="{s*0.24}" height="{s*0.3}" rx="{s*0.03}" fill="{color}" opacity="0.6"/>'
    elif "🛒" in c:
        path = f'<path d="M{s*.1},{s*.18} L{s*.22},{s*.18} L{s*.35},{s*.65} L{s*.8},{s*.65} L{s*.9},{s*.3} L{s*.3},{s*.3}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="{s*.38}" cy="{s*.8}" r="{s*.07}" fill="white"/><circle cx="{s*.72}" cy="{s*.8}" r="{s*.07}" fill="white"/>'
    elif "💳" in c:
        path = f'<rect x="{s*.1}" y="{s*.25}" width="{s*.8}" height="{s*.5}" rx="{s*.08}" fill="white" opacity="0.9"/><rect x="{s*.1}" y="{s*.38}" width="{s*.8}" height="{s*.12}" fill="{color}" opacity="0.5"/><rect x="{s*.16}" y="{s*.58}" width="{s*.2}" height="{s*.08}" rx="{s*.03}" fill="{color}" opacity="0.7"/>'
    elif "📺" in c:
        path = f'<rect x="{s*.1}" y="{s*.15}" width="{s*.8}" height="{s*.55}" rx="{s*.07}" fill="white" opacity="0.9"/><rect x="{s*.18}" y="{s*.23}" width="{s*.64}" height="{s*.39}" rx="{s*.04}" fill="{color}" opacity="0.6"/><polygon points="{s*.4},{s*.35} {s*.4},{s*.52} {s*.62},{s*.435}" fill="white"/><rect x="{s*.38}" y="{s*.74}" width="{s*.24}" height="{s*.08}" rx="{s*.03}" fill="white" opacity="0.5"/>'
    elif "🚗" in c or "🚌" in c:
        path = f'<rect x="{s*.08}" y="{s*.42}" width="{s*.84}" height="{s*.3}" rx="{s*.07}" fill="white" opacity="0.9"/><path d="M{s*.22},{s*.42} L{s*.32},{s*.22} L{s*.68},{s*.22} L{s*.78},{s*.42}" fill="white" opacity="0.9"/><circle cx="{s*.27}" cy="{s*.76}" r="{s*.1}" fill="{color}" opacity="0.8"/><circle cx="{s*.27}" cy="{s*.76}" r="{s*.05}" fill="white"/><circle cx="{s*.73}" cy="{s*.76}" r="{s*.1}" fill="{color}" opacity="0.8"/><circle cx="{s*.73}" cy="{s*.76}" r="{s*.05}" fill="white"/>'
    elif "🏥" in c:
        path = f'<rect x="{s*.38}" y="{s*.12}" width="{s*.24}" height="{s*.76}" rx="{s*.06}" fill="white"/><rect x="{s*.12}" y="{s*.38}" width="{s*.76}" height="{s*.24}" rx="{s*.06}" fill="white"/>'
    elif "📈" in c:
        path = f'<polyline points="{s*.1},{s*.75} {s*.32},{s*.5} {s*.52},{s*.62} {s*.72},{s*.28} {s*.9},{s*.35}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/><polyline points="{s*.72},{s*.18} {s*.9},{s*.18} {s*.9},{s*.35}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    elif "🎭" in c:
        path = f'<polygon points="{s*.5},{s*.1} {s*.61},{s*.38} {s*.92},{s*.38} {s*.68},{s*.56} {s*.77},{s*.85} {s*.5},{s*.67} {s*.23},{s*.85} {s*.32},{s*.56} {s*.08},{s*.38} {s*.39},{s*.38}" fill="white"/>'
    elif "🍔" in c:
        path = f'<rect x="{s*.28}" y="{s*.12}" width="{s*.08}" height="{s*.76}" rx="{s*.04}" fill="white"/><path d="M{s*.24},{s*.12} Q{s*.2},{s*.35} {s*.36},{s*.38} Q{s*.52},{s*.35} {s*.48},{s*.12}" fill="white"/><rect x="{s*.62}" y="{s*.12}" width="{s*.1}" height="{s*.4}" rx="{s*.04}" fill="white"/><rect x="{s*.60}" y="{s*.48}" width="{s*.14}" height="{s*.4}" rx="{s*.06}" fill="white"/>'
    else:
        path = f'<circle cx="{s*.5}" cy="{s*.4}" r="{s*.18}" fill="white" opacity="0.9"/><rect x="{s*.44}" y="{s*.62}" width="{s*.12}" height="{s*.26}" rx="{s*.05}" fill="white" opacity="0.9"/>'
    return f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">{path}</svg>'

# ─────────────────────────────────────────────
# 5. CSS GLOBAL + HACK MOVIL
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

#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}

.wrap {{ max-width: 1060px; margin: 0 auto; padding: 0 22px 48px; }}

/* HEADER */
.hdr {{ display: flex; justify-content: space-between; align-items: center; padding: 22px 0 16px; border-bottom: 1px solid var(--border); position: relative; overflow: hidden; }}
.hdr-brand {{ font-size: 22px; font-weight: 800; color: var(--text); letter-spacing: -.03em; }}
.hdr-brand span {{ color: var(--accent); }}
.hdr-date {{ font-size: 11px; color: var(--muted2); font-weight: 500; margin-top: 3px; }}
.dolar-chip {{ background: rgba(0,158,227,.08); border: 1px solid rgba(0,158,227,.2); border-radius: 12px; padding: 8px 16px; text-align: center; }}
.dolar-lbl {{ font-size: 9px; color: var(--muted2); letter-spacing: .08em; text-transform: uppercase; font-weight: 700; }}
.dolar-val {{ font-size: 18px; font-weight: 800; color: var(--accent); }}

/* ── NAV GRID HACK (Fuerza 2 columnas en móvil) ── */
[data-testid="column"] {{
    width: 100% !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
}}

/* Forzamos el contenedor de botones a no colapsar */
div[data-testid="stHorizontalBlock"] {{
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
}}

.stButton > button {{
  width: 100% !important;
  border-radius: 12px !important;
  padding: 12px 10px !important;
  font-weight: 700 !important;
  font-size: 14px !important;
  transition: all .2s !important;
  border: 1px solid var(--border) !important;
}}

.stButton > button[kind="primary"] {{
  background: {ACCENT} !important; border: none !important; color: white !important;
  box-shadow: 0 4px 12px rgba(0,158,227,0.2) !important;
}}

.stButton > button[kind="secondary"] {{
  background: var(--surface) !important; color: var(--muted2) !important;
}}

/* GRID MÉTRICAS */
.metrics {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin: 20px 0; }}
@media (max-width: 860px) {{ .metrics {{ grid-template-columns: 1fr 1fr; }} }}

.mcard {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); padding: 18px; position: relative; }}
.mlbl {{ font-size:9px; font-weight:700; color:var(--muted); letter-spacing:.1em; text-transform:uppercase; }}
.mval {{ font-size:22px; font-weight:800; color:var(--text); margin: 5px 0; }}
.mpct {{ font-size:26px; font-weight:800; color:{ACCENT}; }}

/* LISTA GASTOS */
.card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--r); margin-bottom: 16px; overflow: hidden; }}
.card-pad {{ padding: 20px; }}
.ctitle {{ font-size: 10px; font-weight: 700; color: var(--muted); letter-spacing: .1em; text-transform: uppercase; margin-bottom: 14px; }}
.item-row {{ display: flex; align-items: center; gap: 14px; padding: 12px 18px; border-bottom: 1px solid {BORDER2}; }}
.item-ico {{ width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
.item-name {{ font-size: 14px; font-weight: 700; color: var(--text); }}
.item-monto {{ font-size: 15px; font-weight: 800; color: var(--text); }}

.vbadge {{ font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 20px; }}
.vb-paid {{ background:rgba(0,200,83,.1); color:{GREEN}; }}
.vb-venc {{ background:rgba(242,61,79,.14); color:{RED}; }}

/* ALERTAS */
.alert {{ padding: 12px; border-radius: 12px; font-size: 13px; margin-bottom: 10px; display: flex; gap: 8px; }}
.alert-r {{ background:rgba(242,61,79,.08); border:1px solid rgba(242,61,79,.2); color:#ff8a94; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. DATOS Y LÓGICA
# ─────────────────────────────────────────────
@st.cache_resource
def get_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos():
    try:
        hoja = get_gspread().open("Gastos_Henry").sheet1
        data = hoja.get_all_values()
        if not data or len(data) < 2: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"])
        df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
        df["Día Pago"]    = pd.to_datetime(df["Día Pago"], errors="coerce").dt.date
        df["Pagado"]      = df["Pagado"].apply(lambda x: str(x).strip().upper() in ["TRUE","VERDADERO","✅","SI","SÍ","1"])
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=300)
def get_dolar():
    try: return float(requests.get("https://dolarapi.com/v1/dolares/blue").json()["venta"])
    except: return 1450.0

def categorizar_inteligente(item: str) -> str:
    i = str(item).lower()
    if any(x in i for x in ["tarjeta", "visa", "cuota", "credito"]): return "💳 Crédito"
    if any(x in i for x in ["luz", "agua", "gas", "internet"]): return "⚡ Servicios"
    if any(x in i for x in ["super", "chino", "mercado"]): return "🛒 Super"
    if any(x in i for x in ["alquiler", "expensas"]): return "🏠 Hogar"
    return "🔘 Otros"

def fmt_ars(n): return f"$ {n:,.0f}".replace(",",".").replace("$ .", "$ 0")

# ─────────────────────────────────────────────
# 7. RENDER
# ─────────────────────────────────────────────
dolar = get_dolar()
df = cargar_datos()

st.markdown('<div class="wrap">', unsafe_allow_html=True)

# HEADER
st.markdown(f"""
<div class="hdr">
  <div>
    <div class="hdr-brand">Finanzas <span>AR</span></div>
    <div class="hdr-date">{date.today().strftime('%d de %B, %Y')}</div>
  </div>
  <div class="dolar-chip">
    <div class="dolar-lbl">Blue</div>
    <div class="dolar-val">${dolar:,.0f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# NAVEGACIÓN (FORZADA 2 COLUMNAS EN MÓVIL)
# ─────────────────────────────────────────────
st.markdown('<div style="margin: 15px 0;">', unsafe_allow_html=True)
nav_col1, nav_col2 = st.columns(2)
with nav_col1:
    if st.button("🏠 Inicio", type="primary" if st.session_state.screen=="inicio" else "secondary", use_container_width=True):
        st.session_state.screen = "inicio"
        st.rerun()
with nav_col2:
    if st.button("📋 Gastos", type="primary" if st.session_state.screen=="gastos" else "secondary", use_container_width=True):
        st.session_state.screen = "gastos"
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PANTALLA INICIO
# ─────────────────────────────────────────────
if st.session_state.screen == "inicio":
    if not df.empty:
        total = df["Monto (ARS)"].sum()
        pagado = df[df["Pagado"]]["Monto (ARS)"].sum()
        pend = total - pagado
        pct = int(pagado/total*100) if total > 0 else 0

        # MÉTRICAS
        st.markdown(f"""
        <div class="metrics">
          <div class="mcard"><div class="mlbl">Total</div><div class="mval">{fmt_ars(total)}</div></div>
          <div class="mcard"><div class="mlbl">Pagado</div><div class="mval" style="color:{GREEN}">{fmt_ars(pagado)}</div></div>
          <div class="mcard"><div class="mlbl">Pendiente</div><div class="mval" style="color:{RED}">{fmt_ars(pend)}</div></div>
          <div class="mcard"><div class="mlbl">Progreso</div><div class="mpct">{pct}%</div></div>
        </div>
        """, unsafe_allow_html=True)

        col_l, col_r = st.columns([1.5, 1])
        with col_l:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div style="padding:18px 18px 0" class="ctitle">Gastos del mes</div>', unsafe_allow_html=True)
            for _, r in df.iterrows():
                color = cat_color(r["Categoría"])
                icon = svg_icon(r["Categoría"], color)
                badge = '<span class="vbadge vb-paid">Pagado</span>' if r["Pagado"] else '<span class="vbadge vb-venc">Pendiente</span>'
                st.markdown(f"""
                <div class="item-row" style="opacity: {'0.5' if r['Pagado'] else '1'}">
                    <div class="item-ico" style="background:{color}20">{icon}</div>
                    <div style="flex:1">
                        <div class="item-name">{r['Ítem']}</div>
                        {badge}
                    </div>
                    <div class="item-monto">{fmt_ars(r['Monto (ARS)'])}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_r:
            # Grafico Donut
            fig = go.Figure(go.Pie(labels=df["Categoría"], values=df["Monto (ARS)"], hole=.6))
            fig.update_layout(margin=dict(t=0,b=0,l=0,r=0), height=220, showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
            st.markdown('<div class="card card-pad"><div class="ctitle">Distribución</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PANTALLA GASTOS
# ─────────────────────────────────────────────
else:
    st.markdown('<div class="card card-pad">', unsafe_allow_html=True)
    st.markdown('<div class="ctitle">Editor de Gastos</div>', unsafe_allow_html=True)
    
    df_edit = st.data_editor(
        df,
        column_config={
            "Pagado": st.column_config.CheckboxColumn("✓"),
            "Monto (ARS)": st.column_config.NumberColumn("Monto", format="$ %d"),
            "Día Pago": st.column_config.DateColumn("Vencimiento")
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )

    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
        try:
            hoja = get_gspread().open("Gastos_Henry").sheet1
            hoja.clear()
            # Autocategorizar si el usuario no puso nada
            df_edit["Categoría"] = df_edit.apply(lambda r: r["Categoría"] if r["Categoría"] else categorizar_inteligente(r["Ítem"]), axis=1)
            hoja.append_row(df_edit.columns.tolist())
            hoja.append_rows(df_edit.astype(str).values.tolist())
            st.success("Guardado correctamente")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
