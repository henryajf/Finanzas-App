import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.graph_objects as go
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
# 2. CSS — ESTILO MERCADO PAGO
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* ── VARIABLES ── */
:root {
  --bg:       #f5f5f5;
  --white:    #ffffff;
  --surface:  #ffffff;
  --border:   #ebebeb;
  --text:     #1a1a1a;
  --muted:    #999999;
  --accent:   #009ee3;
  --green:    #00a650;
  --red:      #f23d4f;
  --yellow:   #ff9c00;
  --radius:   16px;
  --shadow:   0 2px 12px rgba(0,0,0,0.06);
}

/* ── BASE ── */
html, body, [class*="css"], .stApp {
  font-family: 'Plus Jakarta Sans', 'Helvetica Neue', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
* { box-sizing: border-box; }

/* Ocultar chrome de Streamlit */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── WRAPPER ── */
.main-wrap {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 24px 48px;
}

/* ── HEADER ── */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28px 0 20px;
  margin-bottom: 4px;
}
.header-brand {
  font-size: 20px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -.03em;
}
.header-brand span { color: var(--accent); }
.header-date {
  font-size: 13px;
  color: var(--muted);
  font-weight: 500;
  margin-top: 2px;
}
.dolar-chip {
  background: var(--white);
  border: 1.5px solid var(--border);
  border-radius: 12px;
  padding: 8px 16px;
  text-align: center;
  box-shadow: var(--shadow);
}
.dolar-chip-label { font-size: 9px; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; font-weight: 600; }
.dolar-chip-val   { font-size: 18px; font-weight: 700; color: var(--accent); margin-top: 1px; }

/* ── MÉTRICAS TOP ── */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.metric-card {
  background: var(--white);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
}
.metric-label {
  font-size: 11px; font-weight: 600; color: var(--muted);
  letter-spacing: .04em; text-transform: uppercase; margin-bottom: 8px;
}
.metric-val {
  font-size: 26px; font-weight: 800; color: var(--text);
  letter-spacing: -.02em; line-height: 1;
}
.metric-val-green { color: var(--green); }
.metric-val-red   { color: var(--red); }
.metric-sub { font-size: 11px; color: var(--muted); margin-top: 5px; font-weight: 500; }
.progress-wrap { margin-top: 10px; }
.progress-bar {
  height: 4px; background: #ebebeb;
  border-radius: 4px; overflow: hidden;
}
.progress-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, var(--accent), #00c9ff);
  transition: width .8s ease;
}

/* ── ALERTAS ── */
.alerta {
  padding: 12px 16px; border-radius: 12px;
  font-size: 13px; font-weight: 500;
  margin-bottom: 10px;
  display: flex; align-items: center; gap: 10px;
}
.alerta-red  { background: #fff0f1; border: 1px solid #ffd6d9; color: #c0392b; }
.alerta-warn { background: #fff8ee; border: 1px solid #ffe5b4; color: #b7681a; }

/* ── LAYOUT DOS COLUMNAS ── */
.two-col {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
  align-items: start;
}

/* ── CARD ── */
.card {
  background: var(--white);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  overflow: hidden;
  margin-bottom: 16px;
}
.card-header {
  padding: 18px 20px 0;
  font-size: 13px; font-weight: 700;
  color: var(--muted);
  letter-spacing: .04em;
  text-transform: uppercase;
}

/* ── LISTA DE CATEGORÍAS (estilo MP) ── */
.cat-list { padding: 8px 0; }
.cat-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  cursor: default;
  transition: background .15s;
}
.cat-row:last-child { border-bottom: none; }
.cat-row:hover { background: #fafafa; }
.cat-icon {
  width: 44px; height: 44px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}
.cat-name {
  flex: 1;
  font-size: 15px; font-weight: 600; color: var(--text);
}
.cat-amount {
  font-size: 15px; font-weight: 700; color: var(--text);
  white-space: nowrap;
}
.cat-arrow { color: var(--muted); font-size: 13px; margin-left: 4px; }

/* ── RESUMEN LATERAL ── */
.resumen-card {
  background: var(--white);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  border: 1px solid var(--border);
  padding: 20px;
  margin-bottom: 16px;
}
.resumen-title {
  font-size: 11px; font-weight: 700; color: var(--muted);
  letter-spacing: .06em; text-transform: uppercase; margin-bottom: 14px;
}
.resumen-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 9px 0;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}
.resumen-row:last-child { border-bottom: none; }
.resumen-key { color: var(--muted); font-weight: 500; }
.resumen-val { font-weight: 700; color: var(--text); }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 2px solid var(--border) !important;
  gap: 0 !important; padding: 0 20px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 13px !important; font-weight: 600 !important;
  border-bottom: 2px solid transparent !important;
  padding: 12px 16px !important;
  margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* ── DATA EDITOR ── */
[data-testid="stDataEditorContainer"] {
  background: var(--white) !important;
  border: none !important;
  border-radius: 0 !important;
}
[data-testid="stDataFrame"] th {
  background: #fafafa !important;
  color: var(--muted) !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: .04em !important;
  text-transform: uppercase !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  border-color: var(--border) !important;
}
[data-testid="stDataFrame"] td {
  font-size: 13px !important;
  color: var(--text) !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  border-color: var(--border) !important;
}

/* ── BOTONES ── */
.stButton > button[kind="primary"] {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 14px 24px !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 14px !important; font-weight: 700 !important;
  letter-spacing: .01em !important;
  transition: all .2s !important;
  box-shadow: 0 4px 14px rgba(0,158,227,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
  background: #0088c7 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(0,158,227,0.35) !important;
}
.stButton > button[kind="secondary"] {
  background: var(--white) !important;
  color: var(--muted) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 12px !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
  font-size: 13px !important; font-weight: 600 !important;
  transition: all .2s !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}

/* ── SUCCESS / ERROR ── */
div[data-testid="stAlert"] {
  border-radius: 12px !important;
  font-size: 13px !important;
  font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── RESPONSIVE ── */
@media (max-width: 860px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .metrics-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
  .metric-val { font-size: 20px; }
  .main-wrap { padding: 0 12px 32px; }
  .app-header { padding: 16px 0 14px; }
  .cat-row { padding: 12px 14px; gap: 10px; }
  .cat-icon { width: 36px; height: 36px; font-size: 16px; }
  .cat-name { font-size: 13px; }
  .cat-amount { font-size: 13px; }
}

hr { display: none !important; }
[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. CONSTANTES
# ─────────────────────────────────────────────
# Colores por categoría (estilo MP: un color por tipo)
CAT_COLORS = {
    "⚡": "#009ee3", "🔌": "#009ee3",  # servicios → azul
    "🏠": "#00a650",                    # vivienda → verde
    "🛒": "#00a650",                    # super → verde
    "🚗": "#ff9c00",                    # transporte → naranja
    "💳": "#a855f7",                    # tarjetas → violeta
    "📺": "#ec4899",                    # suscripciones → rosa
    "📈": "#0ea5e9",                    # inversiones → celeste
    "🏥": "#14b8a6",                    # salud → teal
    "🎭": "#f59e0b",                    # ocio → amarillo
    "👪": "#8b5cf6",                    # familia → púrpura
    "🍔": "#ef4444",                    # comida → rojo
}
DEFAULT_COLOR = "#6b7280"

PALETTE_DONUT = [
    "#009ee3","#00a650","#a855f7","#ec4899",
    "#ff9c00","#f59e0b","#14b8a6","#0ea5e9",
    "#ef4444","#8b5cf6","#6b7280","#34d399",
]

# ─────────────────────────────────────────────
# 4. CONEXIÓN
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
        st.error(f"❌ No se pudo conectar a Google Sheets: {e}")
        return pd.DataFrame()

    # Filtrar filas vacías
    data = [r for r in data if any(str(c).strip() for c in r)]
    if not data or len(data) < 2:
        return pd.DataFrame()

    headers_esperados = ["Categoría", "Ítem", "Monto (ARS)", "Día Pago", "Pagado"]
    primera = [str(c).strip().lower() for c in data[0]]

    if primera[0] in ["categoría", "categoria", "cat", "category"]:
        filas = data[1:]
    else:
        filas = data

    filas = [r + [""] * (5 - len(r)) for r in filas if len(r) >= 2]
    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas, columns=headers_esperados)

    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
    df["Día Pago"]    = pd.to_datetime(df["Día Pago"], errors="coerce").dt.date
    df["Pagado"]      = df["Pagado"].apply(
        lambda x: str(x).strip().upper() in ["TRUE", "VERDADERO", "✅", "SI", "SÍ", "1"]
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
# 5. HELPERS
# ─────────────────────────────────────────────
def fmtARS(n):
    s = f"{n:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"$ {s}"

def fmtK(n):
    if n >= 1_000_000: return f"$ {n/1_000_000:.1f}M"
    if n >= 1_000:     return f"$ {n/1_000:.0f}k"
    return fmtARS(n)

def fmtUSD(n, d):
    if d == 0: return "U$S —"
    return f"U$S {n/d:,.0f}"

def get_estado(row):
    if row["Pagado"]:               return "✅ Listo"
    if pd.isna(row["Día Pago"]):    return "⚪ Sin Fecha"
    if row["Día Pago"] < date.today(): return "🔴 Vencido"
    if row["Día Pago"] <= date.today() + timedelta(days=3): return "🟡 Próximo"
    return "🟢 Al Día"

def get_cat_color(cat_str):
    cat = str(cat_str).strip()
    for emoji, color in CAT_COLORS.items():
        if emoji in cat:
            return color
    return DEFAULT_COLOR

def procesar(df_base, dolar):
    df    = df_base.copy()
    total = df["Monto (ARS)"].sum()
    df["Peso (%)"] = (df["Monto (ARS)"] / total).fillna(0) if total > 0 else 0
    df["USD"]      = (df["Monto (ARS)"] / dolar).round(2) if dolar > 0 else 0
    df["Cat."]     = df["Categoría"].apply(lambda x: str(x).strip() or "—")
    df["Estado"]   = df.apply(get_estado, axis=1)
    return df.sort_values(["Pagado", "Día Pago"], ascending=[True, True], na_position="last")

# ─────────────────────────────────────────────
# 6. CARGA
# ─────────────────────────────────────────────
dolar   = get_dolar()
df_base = cargar_datos()

if not df_base.empty:
    df         = procesar(df_base, dolar)
    total_ars  = df["Monto (ARS)"].sum()
    pagado_ars = df[df["Pagado"] == True]["Monto (ARS)"].sum()
    pend_ars   = total_ars - pagado_ars
    pct        = int(pagado_ars / total_ars * 100) if total_ars > 0 else 0
    vencidos   = df[
        (df["Pagado"] == False) & df["Día Pago"].notna() &
        (df["Día Pago"] < date.today())
    ]
    proximos   = df[
        (df["Pagado"] == False) & df["Día Pago"].notna() &
        (df["Día Pago"] >= date.today()) &
        (df["Día Pago"] <= date.today() + timedelta(days=3))
    ]
    por_cat    = (
        df.groupby("Cat.")["Monto (ARS)"]
        .sum().reset_index()
        .sort_values("Monto (ARS)", ascending=False)
    )
else:
    df = por_cat = pd.DataFrame()
    total_ars = pagado_ars = pend_ars = pct = 0
    vencidos = proximos = pd.DataFrame()

# ─────────────────────────────────────────────
# 7. RENDER
# ─────────────────────────────────────────────
st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

# ── HEADER ──────────────────────────────────
meses = ["enero","febrero","marzo","abril","mayo","junio",
         "julio","agosto","septiembre","octubre","noviembre","diciembre"]
hoy   = date.today()
hoy_str = f"{hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

st.markdown(f"""
<div class="app-header">
  <div>
    <div class="header-brand">Finanzas <span>AR</span> 🇦🇷</div>
    <div class="header-date">{hoy_str}</div>
  </div>
  <div class="dolar-chip">
    <div class="dolar-chip-label">USD Blue</div>
    <div class="dolar-chip-val">${dolar:,.0f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── ALERTAS ─────────────────────────────────
if not isinstance(vencidos, pd.DataFrame): vencidos = pd.DataFrame()
if not isinstance(proximos, pd.DataFrame): proximos = pd.DataFrame()

if not vencidos.empty:
    items = ", ".join(vencidos["Ítem"].astype(str).tolist())
    st.markdown(
        f'<div class="alerta alerta-red">🔴 <strong>{len(vencidos)} pago{"s" if len(vencidos)>1 else ""} vencido{"s" if len(vencidos)>1 else ""}</strong> — {items}</div>',
        unsafe_allow_html=True,
    )
if not proximos.empty:
    items = ", ".join(proximos["Ítem"].astype(str).tolist())
    st.markdown(
        f'<div class="alerta alerta-warn">🟡 <strong>{len(proximos)} vence{"n" if len(proximos)>1 else ""} en 3 días</strong> — {items}</div>',
        unsafe_allow_html=True,
    )

# ── MÉTRICAS ────────────────────────────────
st.markdown(f"""
<div class="metrics-grid">
  <div class="metric-card">
    <div class="metric-label">Total del mes</div>
    <div class="metric-val">{fmtARS(total_ars)}</div>
    <div class="metric-sub">{fmtUSD(total_ars, dolar)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Pagado</div>
    <div class="metric-val metric-val-green">{fmtARS(pagado_ars)}</div>
    <div class="metric-sub">{fmtUSD(pagado_ars, dolar)}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Pendiente · {pct}% cubierto</div>
    <div class="metric-val metric-val-red">{fmtARS(pend_ars)}</div>
    <div class="progress-wrap">
      <div class="progress-bar">
        <div class="progress-fill" style="width:{pct}%"></div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 8. DOS COLUMNAS
# ─────────────────────────────────────────────
col_main, col_side = st.columns([2.6, 1], gap="medium")

# ── COLUMNA PRINCIPAL ────────────────────────
with col_main:
    if df.empty:
        st.markdown("""
        <div class="card" style="padding:48px;text-align:center;color:#999">
          <div style="font-size:40px;margin-bottom:12px">📭</div>
          <div style="font-size:15px;font-weight:600">Sin datos</div>
          <div style="font-size:13px;margin-top:6px">Verificá la conexión con Google Sheets</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # LISTA ESTILO MERCADO PAGO
        st.markdown('<div class="card"><div class="card-header">Por categoría</div><div class="cat-list">', unsafe_allow_html=True)
        for _, row in por_cat.iterrows():
            cat   = str(row["Cat."]).strip()
            monto = row["Monto (ARS)"]
            color = get_cat_color(cat)
            st.markdown(f"""
            <div class="cat-row">
              <div class="cat-icon" style="background:{color}22;color:{color}">{cat}</div>
              <span class="cat-name">{cat}</span>
              <span class="cat-amount">{fmtARS(monto)}</span>
              <span class="cat-arrow">›</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

        # TABLA CON TABS
        st.markdown('<div class="card">', unsafe_allow_html=True)
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
        COL_ORDER = ("Pagado", "Cat.", "Ítem", "Monto (ARS)", "USD", "Peso (%)", "Día Pago", "Estado")

        def render_tabla(data, key):
            return st.data_editor(
                data, column_config=COL_CONFIG, column_order=COL_ORDER,
                num_rows="dynamic", use_container_width=True, hide_index=True, key=key,
            )

        with tab_todos:
            df_edit = render_tabla(df, "t_todos")
        with tab_pend:
            render_tabla(df[df["Pagado"] == False].copy(), "t_pend")
        with tab_pag:
            render_tabla(df[df["Pagado"] == True].copy(), "t_pag")

        st.markdown("</div>", unsafe_allow_html=True)

        # BOTONES
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        bc1, bc2 = st.columns([3, 1])
        with bc1:
            if st.button("Guardar y Sincronizar", type="primary", use_container_width=True):
                try:
                    df_s  = df_edit.copy()
                    df_up = df_s[["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]].copy()
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

# ── COLUMNA LATERAL ──────────────────────────
with col_side:
    if not df.empty:
        # DONUT GRANDE (estilo MP)
        fig = go.Figure(go.Pie(
            labels=por_cat["Cat."],
            values=por_cat["Monto (ARS)"],
            hole=0.60,
            marker=dict(
                colors=[get_cat_color(c) for c in por_cat["Cat."]],
                line=dict(color="#ffffff", width=3),
            ),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
            direction="clockwise",
            sort=True,
        ))
        fig.add_annotation(
            text=f"<b>{fmtARS(total_ars)}</b>",
            x=0.5, y=0.5,
            font=dict(size=13, color="#1a1a1a", family="Plus Jakarta Sans"),
            showarrow=False,
        )
        fig.update_layout(
            showlegend=False,
            height=260,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.markdown('<div class="resumen-card">', unsafe_allow_html=True)
        st.markdown('<div class="resumen-title">Distribución</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        # RESUMEN
        n_total = len(df)
        n_pag   = len(df[df["Pagado"] == True])
        n_pend  = len(df[df["Pagado"] == False])
        n_venc  = len(vencidos)
        mayor   = df.loc[df["Monto (ARS)"].idxmax(), "Ítem"] if not df.empty else "—"
        mayor_m = df["Monto (ARS)"].max()

        st.markdown(f"""
        <div class="resumen-card">
          <div class="resumen-title">Resumen</div>
          <div class="resumen-row">
            <span class="resumen-key">Total ítems</span>
            <span class="resumen-val">{n_total}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Pagados</span>
            <span class="resumen-val" style="color:var(--green)">{n_pag}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Pendientes</span>
            <span class="resumen-val" style="color:var(--yellow)">{n_pend}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Vencidos</span>
            <span class="resumen-val" style="color:var(--red)">{n_venc}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Mayor gasto</span>
            <span class="resumen-val" style="font-size:12px">{mayor}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key" style="font-size:11px">{fmtARS(mayor_m)}</span>
            <span></span>
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

