import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.graph_objects as go
import io
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, timedelta

st.set_page_config(page_title="Finanzas AR", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")

for k, v in [("screen", "inicio"), ("show_add", False), ("show_add_ingreso", False), ("periodo_sel", None), ("tend_mes_exp", None), ("show_horas", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── COLORES (Estilo App Móvil / Fintech Premium) ──
BG      = "#F8F9FA"
SURFACE = "#FFFFFF"
SURF2   = "#F1F3F5"
SURF3   = "#E9ECEF"
GLASS_BORDER   = "#DEE2E6"
GLASS_BORDER_2 = "#CED4DA"
TEXT    = "#212529"
TEXT2   = "#495057"
TEXT3   = "#868E96"
SEP     = "#F1F3F5"
ACCENT  = "#4C6EF5"
GREEN   = "#40C057"
RED     = "#E03131"
ORANGE  = "#FD7E14"
GOLD    = "#FAB005"
PLOTBG  = "rgba(0,0,0,0)"

CAT_COLORS = {
    "Servicios": "#FD7E14", "Hogar": "#40C057", "Supermercado": "#82C91E",
    "Comida": "#E03131", "Transporte": "#4C6EF5", "Suscripciones": "#AE3EC9",
    "Fitness": "#F03E3E", "Salud": "#12B886", "Credito": "#E67700",
    "Personal": "#7950F2", "Viajes": "#15AABF", "Otros": "#868E96",
}

def cat_color(cat):
    c = str(cat)
    for k, v in CAT_COLORS.items():
        if k.lower() in c.lower(): return v
    return "#868E96"

def cat_icon_svg(cat, color, size=36):
    c = str(cat).lower(); s = size; r = s * 0.5
    if "servicio" in c or "luz" in c or "gas" in c:
        ico = f'<polygon points="{s*.6},{s*.08} {s*.32},{s*.52} {s*.52},{s*.52} {s*.4},{s*.92} {s*.68},{s*.45} {s*.48},{s*.45}" fill="{color}"/>'
    elif "hogar" in c or "alquiler" in c:
        ico = f'<polygon points="{s*.5},{s*.15} {s*.85},{s*.48} {s*.77},{s*.48} {s*.77},{s*.82} {s*.23},{s*.82} {s*.23},{s*.48} {s*.15},{s*.48}" fill="{color}"/><rect x="{s*.4}" y="{s*.58}" width="{s*.2}" height="{s*.24}" rx="{s*.04}" fill="{SURFACE}"/>'
    elif "super" in c or "mercado" in c:
        ico = f'<path d="M{s*.12},{s*.2} L{s*.24},{s*.2} L{s*.38},{s*.62} L{s*.78},{s*.62} L{s*.88},{s*.32} L{s*.32},{s*.32}" stroke="{color}" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="{s*.38}" cy="{s*.76}" r="{s*.07}" fill="{color}"/><circle cx="{s*.7}" cy="{s*.76}" r="{s*.07}" fill="{color}"/>'
    elif "credito" in c or "tarjeta" in c or "financ" in c:
        ico = f'<rect x="{s*.1}" y="{s*.28}" width="{s*.8}" height="{s*.44}" rx="{s*.07}" fill="{color}" opacity="0.9"/><rect x="{s*.1}" y="{s*.4}" width="{s*.8}" height="{s*.11}" fill="{SURFACE}"/><rect x="{s*.16}" y="{s*.56}" width="{s*.18}" height="{s*.08}" rx="{s*.03}" fill="{SURFACE}"/>'
    elif "suscripcion" in c:
        ico = f'<rect x="{s*.12}" y="{s*.18}" width="{s*.76}" height="{s*.5}" rx="{s*.07}" fill="{color}" opacity="0.9"/><rect x="{s*.2}" y="{s*.26}" width="{s*.6}" height="{s*.34}" rx="{s*.04}" fill="{SURFACE}"/><polygon points="{s*.38},{s*.36} {s*.38},{s*.5} {s*.58},{s*.43}" fill="{color}"/>'
    elif "transporte" in c or "nafta" in c:
        ico = f'<rect x="{s*.1}" y="{s*.44}" width="{s*.8}" height="{s*.28}" rx="{s*.07}" fill="{color}" opacity="0.9"/><path d="M{s*.24},{s*.44} L{s*.34},{s*.24} L{s*.66},{s*.24} L{s*.76},{s*.44}" fill="{color}" opacity="0.9"/><circle cx="{s*.28}" cy="{s*.76}" r="{s*.09}" fill="{color}"/><circle cx="{s*.72}" cy="{s*.76}" r="{s*.09}" fill="{color}"/>'
    elif "salud" in c or "farmac" in c:
        ico = f'<rect x="{s*.4}" y="{s*.12}" width="{s*.2}" height="{s*.76}" rx="{s*.06}" fill="{color}"/><rect x="{s*.12}" y="{s*.4}" width="{s*.76}" height="{s*.2}" rx="{s*.06}" fill="{color}"/>'
    elif "fitness" in c or "gym" in c:
        ico = f'<rect x="{s*.06}" y="{s*.38}" width="{s*.14}" height="{s*.24}" rx="{s*.05}" fill="{color}"/><rect x="{s*.8}" y="{s*.38}" width="{s*.14}" height="{s*.24}" rx="{s*.05}" fill="{color}"/><rect x="{s*.18}" y="{s*.44}" width="{s*.64}" height="{s*.12}" rx="{s*.04}" fill="{color}"/>'
    elif "comida" in c or "delivery" in c:
        ico = f'<rect x="{s*.15}" y="{s*.3}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="{color}"/><rect x="{s*.15}" y="{s*.46}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="{color}"/><rect x="{s*.15}" y="{s*.62}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="{color}"/>'
    elif "personal" in c or "ocio" in c:
        ico = f'<circle cx="{s*.5}" cy="{s*.35}" r="{s*.17}" fill="{color}"/><path d="M{s*.2},{s*.85} Q{s*.2},{s*.6} {s*.5},{s*.6} Q{s*.8},{s*.6} {s*.8},{s*.85}" fill="{color}"/>'
    elif "viaje" in c:
        ico = f'<path d="M{s*.5},{s*.1} L{s*.88},{s*.58} L{s*.7},{s*.53} L{s*.64},{s*.82} L{s*.5},{s*.72} L{s*.36},{s*.82} L{s*.3},{s*.53} L{s*.12},{s*.58} Z" fill="{color}" opacity="0.9"/>'
    else:
        ico = f'<circle cx="{s*.5}" cy="{s*.38}" r="{s*.16}" fill="{color}" opacity="0.9"/><path d="M{s*.24},{s*.82} Q{s*.24},{s*.6} {s*.5},{s*.6} Q{s*.76},{s*.6} {s*.76},{s*.82}" fill="{color}" opacity="0.9"/>'
    return f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg"><rect width="{s}" height="{s}" rx="{r}" fill="{color}15"/>{ico}</svg>'

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
:root{{
  --bg:{BG};--surface:{SURFACE};--surf2:{SURF2};--surf3:{SURF3};
  --text:{TEXT};--text2:{TEXT2};--text3:{TEXT3};--sep:{SEP};
  --accent:{ACCENT};--green:{GREEN};--red:{RED};--orange:{ORANGE};
  --font-ui:'Plus Jakarta Sans', -apple-system, sans-serif;
}}
html, body, .stApp {{
  font-family:var(--font-ui) !important;
  font-variant-numeric:tabular-nums;
  background: {BG} !important;
  color:{TEXT} !important;
  overflow-x: clip !important;
  width: 100vw !important;
  max-width: 100% !important;
}}
*{{box-sizing:border-box;-webkit-font-smoothing:antialiased;font-family:inherit;}}

#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="collapsedControl"] {{display:none !important;}}
.block-container {{padding:0 !important;max-width:100% !important; overflow-x: clip !important;}}
[data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"], [data-testid="stMain"],
.stMainBlockContainer, section.main, section.main > div:first-child {{padding-top:0 !important;margin-top:0 !important;}}
.wrap {{max-width:480px;margin:0 auto;padding:16px 16px 48px;}}

/* ── HEADER MOBILE CENTRADO ── */
.mobile-hdr {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 0 4px;
}}
.mobile-back-btn {{
  background: {SURFACE};
  border: 1px solid {GLASS_BORDER};
  border-radius: 12px;
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 600; color: {TEXT};
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  cursor: pointer;
}}
.mobile-title {{
  font-size: 20px;
  font-weight: 700;
  color: {TEXT};
  letter-spacing: -0.02em;
}}

/* ── TABS NAVEGACIÓN INFERIOR / SUPERIOR ── */
.pill-outer {{
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}}
.pill-inner {{
  display: inline-flex;
  background: {SURF2};
  padding: 4px;
  border-radius: 14px;
  border: 1px solid {GLASS_BORDER};
  width: 100%;
}}
.pill-inner [data-testid="stHorizontalBlock"] {{
  gap: 4px !important;
  width: 100%;
}}
.pill-inner [data-testid="column"] {{
  flex: 1 !important;
  min-width: 0 !important;
}}
.pill-inner .stButton > button {{
  background: transparent !important;
  border: none !important;
  color: {TEXT2} !important;
  border-radius: 10px !important;
  padding: 8px 0 !important;
  font-size: 12px !important;
  font-weight: 600 !important;
  width: 100% !important;
  box-shadow: none !important;
}}
.pill-active .stButton > button {{
  background: {SURFACE} !important;
  color: {ACCENT} !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
}}

/* ── SELECTBOX ── */
div[data-baseweb="select"] {{
    background: {SURFACE} !important;
    border-radius: 12px !important;
    border: 1px solid {GLASS_BORDER} !important;
}}

/* ── TARJETAS Y FILAS ── */
.card-clean {{
  background: {SURFACE};
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid {GLASS_BORDER};
  box-shadow: 0 4px 16px rgba(0,0,0,0.02);
}}
.row-item {{
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  background: {SURFACE};
  border-radius: 16px;
  margin-bottom: 8px;
  border: 1px solid {GLASS_BORDER};
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
  transition: transform 0.1s ease;
}}
.row-item:active {{
  transform: scale(0.98);
}}
.row-body {{flex: 1; min-width: 0;}}
.row-title {{font-size: 14px; font-weight: 600; color: {TEXT}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
.row-sub {{font-size: 12px; font-weight: 500; color: {TEXT3}; margin-top: 2px;}}
.row-right {{text-align: right; flex-shrink: 0;}}
.row-amt {{font-size: 14px; font-weight: 700; color: {TEXT};}}
.row-arrow {{color: {TEXT3}; font-size: 14px; font-weight: 600; margin-left: 6px;}}

/* ── BOTONES STREAMLIT ── */
.stButton>button[kind="primary"]{{
  background:{ACCENT} !important;
  color:#ffffff !important;
  border:none !important;
  border-radius:12px !important;
  padding:10px 16px !important;
  font-weight:600 !important;
  box-shadow: 0 4px 12px rgba(76,110,245,0.2) !important;
}}
.stButton>button[kind="secondary"]{{
  background:{SURF2} !important;
  color:{TEXT} !important;
  border:1px solid {GLASS_BORDER} !important;
  border-radius:12px !important;
  padding:10px 16px !important;
  font-weight:600 !important;
  box-shadow: none !important;
}}
.sec-lbl{{font-size: 14px; font-weight: 700; color: {TEXT2}; margin: 20px 0 10px 4px; text-transform: uppercase; letter-spacing: 0.04em;}}
.alert{{padding: 12px 16px; border-radius: 12px; font-size: 13px; font-weight: 500; margin-bottom: 12px; background: {SURFACE}; border: 1px solid {GLASS_BORDER};}}
</style>""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# CONEXIÓN Y LOGICA (Intacta)
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
        if not ws: return pd.DataFrame()
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

def guardar_hoja_maestro(df_guardar, dolar_actual=None):
    df_up = df_guardar.copy()
    df_up["Categoria"] = df_up["Item"].apply(categorizar)
    if "Periodo" not in df_up.columns:
        df_up["Periodo"] = date.today().strftime("%Y-%m")
    if "Tasa USD" not in df_up.columns:
        df_up["Tasa USD"] = dolar_actual or 0.0
    df_up = df_up[["Categoria","Item","Monto (ARS)","Dia Pago","Pagado","Periodo","Tasa USD"]]
    df_up["Dia Pago"] = df_up["Dia Pago"].apply(lambda x: str(x) if pd.notnull(x) else "")
    df_up["Pagado"]   = df_up["Pagado"].apply(lambda x: "TRUE" if x else "FALSE")
    hoja = get_gspread().open("Gastos_Henry").sheet1
    hoja.clear()
    hoja.append_row(df_up.columns.tolist())
    hoja.append_rows(df_up.values.tolist())
    st.cache_data.clear()

def categorizar(item):
    i = str(item).lower()
    if any(x in i for x in ["mercadocredito","tarjeta","visa","mastercard","amex","credito","banco","financiamiento","cuota"]): return "Credito/Financiacion"
    elif any(x in i for x in ["luz","edenor","edesur","agua","aysa","gas","metrogas","bbva"]): return "Servicios"
    elif any(x in i for x in ["super","coto","carrefour","dia","jumbo","disco","mercado","almacen"]): return "Supermercado"
    elif any(x in i for x in ["alquiler","expensas","abl","limpieza"]): return "Hogar"
    elif any(x in i for x in ["nafta","ypf","shell","axion","uber","cabify","taxi","sube"]): return "Transporte"
    elif any(x in i for x in ["netflix","spotify","prime","hbo","disney","youtube","internet","claro","movistar"]): return "Suscripciones"
    elif any(x in i for x in ["gym","gimnasio","megatlon","sportclub"]): return "Fitness"
    elif any(x in i for x in ["farmacia","osde","swiss","galeno","medico","salud"]): return "Salud"
    elif any(x in i for x in ["mc","burger","pedidosya","rappi","pizza","restaurante","bar","cafe"]): return "Comida/Delivery"
    elif any(x in i for x in ["ropa","zapat","zara","dafiti","peluqueria"]): return "Indumentaria/Personal"
    else: return "Otros"

def fmt_ars(n):
    s = f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {s}"

# Inicialización de fechas
MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
hoy = date.today()
periodo_actual = hoy.strftime("%Y-%m")
dolar = get_dolar()

df_maestro = cargar_datos_maestro()
df_ing_todo = cargar_ingresos()

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
        return f"{MESES[int(m)-1].capitalize()}"
    except Exception:
        return p

if not df_maestro.empty:
    df_base_periodo = df_maestro[df_maestro["Periodo"] == periodo_viendo].copy()
    df_base_periodo["Categoria"] = df_base_periodo["Item"].apply(categorizar)
    total_ars = df_base_periodo["Monto (ARS)"].sum()
    por_cat = df_base_periodo.groupby("Categoria")["Monto (ARS)"].sum().reset_index().sort_values("Monto (ARS)", ascending=False)
else:
    df_base_periodo = pd.DataFrame()
    total_ars = 0
    por_cat = pd.DataFrame()

# ── ESTRUCTURA VISUAL PRINCIPAL ──
st.markdown('<div class="wrap">', unsafe_allow_html=True)

# Cabecera minimalista estilo app móvil
st.markdown(f"""
<div class="mobile-hdr">
  <div class="mobile-back-btn">‹</div>
  <div class="mobile-title">{label_periodo(periodo_viendo)}</div>
  <div style="width: 38px;"></div>
</div>
""", unsafe_allow_html=True)

# Selector de navegación superior
_sc = st.session_state.screen
_nav_items = [("inicio", "Resumen"), ("gastos", "Editar"), ("ingresos", "Ingresos"), ("tendencias", "Historial")]
st.markdown('<div class="pill-outer"><div class="pill-inner">', unsafe_allow_html=True)
_pcols = st.columns(4)
for i, (key, lbl) in enumerate(_nav_items):
    with _pcols[i]:
        _active = (_sc == key)
        if _active: st.markdown('<div class="pill-active">', unsafe_allow_html=True)
        if st.button(lbl, key=f"pill_{key}", use_container_width=True):
            st.session_state.screen = key
            st.rerun()
        if _active: st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PANTALLA INICIO (Estilo Dona + Lista Prolija)
# ══════════════════════════════════════════════════════════════════
if st.session_state.screen == "inicio":
    
    # Gráfico de Dona Centralizado estilo App
    if not por_cat.empty and total_ars > 0:
        labels = por_cat["Categoria"].tolist()
        values = por_cat["Monto (ARS)"].tolist()
        colors = [cat_color(c) for c in labels]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.75,
            marker=dict(colors=colors, line=dict(color=SURFACE, width=3)),
            textinfo="none",
            hoverinfo="label+percent+value"
        )])
        
        # Total en el centro de la dona formateado prolijamente
        total_str = f"$ {total_ars:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        fig.update_layout(
            showlegend=False,
            paper_bgcolor=PLOTBG,
            plot_bgcolor=PLOTBG,
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            annotations=[dict(
                text=f"<span style='font-size:11px;color:{TEXT3};font-weight:600;'>Total en el mes</span><br><span style='font-size:18px;font-weight:700;color:{TEXT}'>{total_str}</span>",
                x=0.5, y=0.5, font=dict(family="Plus Jakarta Sans, sans-serif"), showarrow=False
            )]
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Selector de período rápido
    opciones_periodos = periodos_disponibles[:8]
    idx_per = opciones_periodos.index(periodo_viendo) if periodo_viendo in opciones_periodos else 0
    nuevo_periodo = st.selectbox("Cambiar período", opciones_periodos, index=idx_per, format_func=label_periodo, label_visibility="collapsed")
    if nuevo_periodo != st.session_state.periodo_sel:
        st.session_state.periodo_sel = nuevo_periodo
        st.rerun()

    st.markdown('<div class="sec-lbl">Desglose por categorías</div>', unsafe_allow_html=True)

    if por_cat.empty:
        st.markdown(f'<div class="alert" style="text-align:center;color:{TEXT3};">Sin gastos registrados en este período.</div>', unsafe_allow_html=True)
    else:
        for _, row in por_cat.iterrows():
            cat_name = row["Categoria"]
            monto = row["Monto (ARS)"]
            pct = int((monto / total_ars) * 100) if total_ars > 0 else 0
            color = cat_color(cat_name)
            ico = cat_icon_svg(cat_name, color, size=40)
            
            monto_fmt = f"$ {monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            st.markdown(f"""
            <div class="row-item">
              <div style="width:40px;height:40px;flex-shrink:0;">{ico}</div>
              <div class="row-body">
                <div class="row-title">{cat_name}</div>
                <div class="row-sub">{pct}% de las salidas</div>
              </div>
              <div class="row-right">
                <div class="row-amt">{monto_fmt}</div>
              </div>
              <div class="row-arrow">›</div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# RESTO DE PANTALLAS (Ingresos, Gastos, Tendencias optimizadas)
# ══════════════════════════════════════════════════════════════════
elif st.session_state.screen == "gastos":
    st.markdown(f'<div class="sec-lbl">Edición de Egresos</div>', unsafe_allow_html=True)
    if not df_base_periodo.empty:
        COL_CONFIG = {
            "Pagado": st.column_config.CheckboxColumn("Pagado", width="small"),
            "Item": st.column_config.TextColumn("Ítem"),
            "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$ %d"),
            "Dia Pago": st.column_config.DateColumn("Vencimiento", format="DD/MM/YY"),
        }
        df_edit = st.data_editor(df_base_periodo[["Pagado","Item","Monto (ARS)","DiaPago"]].reset_index(drop=True), column_config=COL_CONFIG, use_container_width=True, hide_index=True)
        if st.button("Guardar cambios en planilla", type="primary", use_container_width=True):
            try:
                df_otros = df_maestro[df_maestro["Periodo"] != periodo_viendo].copy()
                df_edit["Periodo"] = periodo_viendo
                df_edit["Tasa USD"] = dolar
                df_edit["Categoria"] = df_edit["Item"].apply(categorizar)
                guardar_hoja_maestro(pd.concat([df_otros, df_edit], ignore_index=True), dolar)
                st.success("¡Guardado con éxito!")
            except Exception as e:
                st.error(f"Error: {e}")

elif st.session_state.screen == "ingresos":
    st.markdown(f'<div class="sec-lbl">Ingresos Registrados</div>', unsafe_allow_html=True)
    if not df_ing_todo.empty:
        for _, row in df_ing_todo.iterrows():
            st.markdown(f"""
            <div class="row-item">
              <div class="row-body">
                <div class="row-title">{row.get('Descripcion')} ({row.get('Persona')})</div>
                <div class="row-sub">{row.get('Fecha')}</div>
              </div>
              <div class="row-right">
                <div class="row-amt" style="color:{GREEN}">+ $ {row.get('Monto ARS'):,.2f}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="alert" style="text-align:center;">No hay ingresos registrados.</div>', unsafe_allow_html=True)

elif st.session_state.screen == "tendencias":
    st.markdown(f'<div class="sec-lbl">Histórico mensual</div>', unsafe_allow_html=True)
    if not df_maestro.empty:
        hist = df_maestro.groupby("Periodo")["Monto (ARS)"].sum().reset_index()
        for _, row in hist.iterrows():
            st.markdown(f"""
            <div class="row-item">
              <div class="row-body">
                <div class="row-title">Período {row['Periodo']}</div>
              </div>
              <div class="row-right">
                <div class="row-amt">$ {row['Monto (ARS)']:,.2f}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
