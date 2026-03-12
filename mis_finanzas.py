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
    layout="centered",          # centered = mejor en móvil
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 2. CSS — MINIMALISTA MOBILE-FIRST
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

/* ── BASE ── */
:root {
  --bg:       #0a0a0a;
  --surface:  #111111;
  --border:   rgba(255,255,255,0.07);
  --text:     #f5f5f5;
  --muted:    #555555;
  --accent:   #e8ff47;
  --green:    #34d399;
  --red:      #f87171;
  --yellow:   #fbbf24;
}

html, body, [class*="css"], .stApp {
  font-family: 'Instrument Sans', 'Helvetica Neue', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}

/* Ocultar UI chrome de Streamlit */
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

/* Contenedor centrado y angosto — simula móvil */
.block-container {
  max-width: 430px !important;
  padding: 0 !important;
  margin: 0 auto !important;
}

/* ── HEADER ── */
.app-header {
  padding: 20px 20px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.header-label {
  font-size: 10px;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: .08em;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.header-date {
  font-family: 'Instrument Serif', Georgia, serif !important;
  font-size: 26px;
  font-weight: 400;
  letter-spacing: -.01em;
  line-height: 1.1;
  color: var(--text);
}
.dolar-chip {
  background: rgba(232,255,71,0.07);
  border: 1px solid rgba(232,255,71,0.18);
  border-radius: 10px;
  padding: 8px 12px;
  text-align: right;
}
.dolar-chip-label { font-size: 9px; color: var(--muted); letter-spacing: .06em; text-transform: uppercase; }
.dolar-chip-val   { font-size: 16px; font-weight: 600; color: var(--accent); margin-top: 1px; }

/* ── HERO CARD ── */
.hero-card {
  margin: 0 16px 14px;
  background: #161616;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 20px;
}
.hero-label {
  font-size: 10px; font-weight: 500; color: var(--muted);
  letter-spacing: .06em; text-transform: uppercase; margin-bottom: 10px;
}
.hero-total {
  font-family: 'Instrument Serif', Georgia, serif !important;
  font-size: 44px; font-weight: 400;
  letter-spacing: -.02em; line-height: 1;
  color: var(--text);
}
.hero-sub { font-size: 11px; color: var(--muted); margin-top: 4px; }
.hero-split {
  display: flex; gap: 14px; align-items: center; margin-top: 14px;
}
.hero-split-divider { width: 1px; height: 28px; background: var(--border); }
.split-label { font-size: 9px; color: var(--muted); letter-spacing: .06em; text-transform: uppercase; }
.split-val-green { font-size: 14px; font-weight: 600; color: var(--green); margin-top: 2px; }
.split-val-red   { font-size: 14px; font-weight: 600; color: var(--red);   margin-top: 2px; }

/* ── ALERTA ── */
.alerta {
  margin: 0 16px 12px;
  background: rgba(248,113,113,0.07);
  border: 1px solid rgba(248,113,113,0.18);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 12px;
  color: #fca5a5;
}
.alerta-warn {
  background: rgba(251,191,36,0.07);
  border-color: rgba(251,191,36,0.2);
  color: #fde68a;
}

/* ── CARD GENÉRICA ── */
.card {
  margin: 0 16px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px;
}
.card-title {
  font-size: 10px; font-weight: 500; color: var(--muted);
  letter-spacing: .08em; text-transform: uppercase; margin-bottom: 12px;
}

/* ── TABLA / DATA EDITOR ── */
[data-testid="stDataEditorContainer"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  overflow: hidden !important;
}
[data-testid="stDataFrame"] th {
  background: var(--bg) !important;
  color: var(--muted) !important;
  font-size: 10px !important;
  letter-spacing: .06em !important;
  text-transform: uppercase !important;
  font-family: 'Instrument Sans', sans-serif !important;
}
[data-testid="stDataFrame"] td {
  font-size: 13px !important;
  color: var(--text) !important;
  font-family: 'Instrument Sans', sans-serif !important;
  border-color: var(--border) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
  padding: 0 16px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: 'Instrument Sans', sans-serif !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  letter-spacing: .02em !important;
  border-bottom: 1.5px solid transparent !important;
  padding: 10px 16px !important;
  flex: 1 !important;
  justify-content: center !important;
}
.stTabs [aria-selected="true"] {
  color: var(--text) !important;
  border-bottom-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* ── SELECTBOX ── */
.stSelectbox > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--text) !important;
  font-size: 13px !important;
}

/* ── BOTÓN GUARDAR ── */
.stButton > button[kind="primary"] {
  width: 100% !important;
  background: var(--accent) !important;
  color: #0a0a0a !important;
  border: none !important;
  border-radius: 14px !important;
  padding: 16px !important;
  font-family: 'Instrument Sans', sans-serif !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  letter-spacing: .01em !important;
  transition: all .2s !important;
}
.stButton > button[kind="primary"]:hover {
  background: #d4eb3a !important;
  transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"]:active { transform: scale(.98) !important; }

/* ── SUCCESS / ERROR ── */
[data-testid="stAlert"] {
  background: rgba(52,211,153,0.07) !important;
  border: 1px solid rgba(52,211,153,0.2) !important;
  border-radius: 12px !important;
  color: var(--green) !important;
  font-size: 13px !important;
}

/* Ocultar separadores y padding extra */
hr { display: none !important; }
[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. CATEGORÍAS
# ─────────────────────────────────────────────
ICONOS_MAP = {
    "🏠 Vivienda": "🏠", "⚡ Servicios": "⚡", "📺 Suscripción": "📺",
    "🛒 Alimentos": "🛒", "🚗 Transporte": "🚗", "💳 Tarjetas": "💳",
    "📈 Inversiones": "📈", "👪 Familia": "👪", "🏥 Salud": "🏥", "🎭 Ocio": "🎭",
}
PALETTE = ["#e8ff47","#a3e635","#34d399","#22d3ee","#818cf8","#f472b6","#fb923c","#fbbf24","#60a5fa","#c084fc"]

# ─────────────────────────────────────────────
# 4. CONEXIÓN
# ─────────────────────────────────────────────
@st.cache_resource
def get_gspread():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json", scope)
    except Exception:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos():
    hoja = get_gspread().open("Gastos_Henry").sheet1
    data = hoja.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(data[1:], columns=["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"])
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
    df["Día Pago"]    = pd.to_datetime(df["Día Pago"], errors="coerce").dt.date
    df["Pagado"]      = df["Pagado"].apply(lambda x: str(x).upper() in ["TRUE","VERDADERO","✅"])
    return df

@st.cache_data(ttl=300)
def get_dolar():
    try:
        return float(requests.get("https://dolarapi.com/v1/dolares/blue", timeout=5).json()["venta"])
    except Exception:
        return 1450.0

# ─────────────────────────────────────────────
# 5. HELPERS
# ─────────────────────────────────────────────
def fmtK(n):
    return f"${n/1000:.0f}k" if n >= 1000 else f"${n:,.0f}"

def fmtARS(n):
    return f"${n:,.0f}".replace(",", ".")

def fmtUSD(n, d):
    return f"U$S {n/d:,.2f}"

def icono(cat):
    for k, v in ICONOS_MAP.items():
        if v in str(cat): return v
    return "❓"

def estado(row):
    if row["Pagado"]:  return "✅ Listo"
    if pd.isna(row["Día Pago"]): return "⚪ Sin Fecha"
    return "🔴 Vencido" if row["Día Pago"] < date.today() else "🟡 Pendiente"

def procesar(df_base, dolar):
    df = df_base.copy()
    total = df["Monto (ARS)"].sum()
    df["Peso (%)"] = df["Monto (ARS)"] / total if total > 0 else 0
    df["USD"]      = df["Monto (ARS)"] / dolar
    df["Cat."]     = df["Categoría"].apply(icono)
    df["Estado"]   = df.apply(estado, axis=1)
    return df.sort_values(["Pagado","Día Pago"], ascending=[True,True])

# ─────────────────────────────────────────────
# 6. CARGA
# ─────────────────────────────────────────────
dolar   = get_dolar()
df_base = cargar_datos()

if not df_base.empty:
    df         = procesar(df_base, dolar)
    total      = df["Monto (ARS)"].sum()
    pagado_v   = df[df["Pagado"]==True]["Monto (ARS)"].sum()
    pendiente_v= total - pagado_v
    pct        = int(pagado_v / total * 100) if total > 0 else 0
    vencidos   = df[(df["Pagado"]==False) & df["Día Pago"].notna() & (df["Día Pago"] < date.today())]
    proximos   = df[(df["Pagado"]==False) & df["Día Pago"].notna() &
                    (df["Día Pago"] >= date.today()) & (df["Día Pago"] <= date.today()+timedelta(days=3))]
else:
    total = pagado_v = pendiente_v = pct = 0
    df = vencidos = proximos = pd.DataFrame()

# ─────────────────────────────────────────────
# 7. HEADER
# ─────────────────────────────────────────────
hoy_str = date.today().strftime("%-d de %B")   # "12 de julio"
st.markdown(f"""
<div class="app-header">
  <div>
    <div class="header-label">Finanzas AR 🇦🇷</div>
    <div class="header-date">{hoy_str}</div>
  </div>
  <div class="dolar-chip">
    <div class="dolar-chip-label">USD Blue</div>
    <div class="dolar-chip-val">${dolar:,.0f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 8. HERO CARD
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hero-card">
  <div class="hero-label">Total del mes</div>
  <div class="hero-total">{fmtK(total)}</div>
  <div class="hero-sub">{fmtUSD(total, dolar)} · {pct}% cubierto</div>
  <div class="hero-split">
    <div>
      <div class="split-label">Pagado</div>
      <div class="split-val-green">{fmtK(pagado_v)}</div>
    </div>
    <div class="hero-split-divider"></div>
    <div>
      <div class="split-label">Pendiente</div>
      <div class="split-val-red">{fmtK(pendiente_v)}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 9. ALERTAS
# ─────────────────────────────────────────────
if not vencidos.empty:
    items = ", ".join(vencidos["Ítem"].tolist())
    st.markdown(f'<div class="alerta">🔴 <strong>{len(vencidos)} vencido{"s" if len(vencidos)>1 else ""}</strong> — {items}</div>', unsafe_allow_html=True)

if not proximos.empty:
    items = ", ".join(proximos["Ítem"].tolist())
    st.markdown(f'<div class="alerta alerta-warn">🟡 <strong>{len(proximos)} vence{"n" if len(proximos)>1 else ""} en 3 días</strong> — {items}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 10. GRÁFICO DONUT
# ─────────────────────────────────────────────
if not df.empty:
    por_cat = df.groupby("Categoría")["Monto (ARS)"].sum().reset_index()
    
    fig = go.Figure(go.Pie(
        labels=por_cat["Categoría"],
        values=por_cat["Monto (ARS)"],
        hole=0.68,
        marker=dict(colors=PALETTE[:len(por_cat)], line=dict(color="#111", width=2)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
        direction="clockwise",
        sort=False,
    ))
    fig.add_annotation(
        text=f"<b>{fmtK(total)}</b>",
        x=0.5, y=0.5,
        font=dict(size=15, color="#f5f5f5", family="Instrument Serif"),
        showarrow=False,
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="v", x=1.0, y=0.5,
            font=dict(color="#888", size=10, family="Instrument Sans"),
            bgcolor="rgba(0,0,0,0)",
            itemclick=False,
        ),
        height=200,
        margin=dict(t=0, b=0, l=0, r=110),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.markdown('<div class="card"><div class="card-title">Por categoría</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 11. TABLA CON TABS
# ─────────────────────────────────────────────
if not df.empty:
    tab_todos, tab_pend, tab_pag = st.tabs(["Todos", "Pendiente", "Pagado"])

    def render_tabla(df_filtrado):
        return st.data_editor(
            df_filtrado,
            column_config={
                "Pagado":      st.column_config.CheckboxColumn("✓", width="small"),
                "Cat.":        st.column_config.TextColumn("", width="small"),
                "Categoría":   None,
                "Ítem":        st.column_config.TextColumn("Ítem"),
                "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d"),
                "USD":         st.column_config.NumberColumn("USD", format="U$S %.0f", disabled=True, width="small"),
                "Peso (%)":    st.column_config.ProgressColumn("Peso", format="%.0f%%", min_value=0, max_value=1, width="small"),
                "Día Pago":    st.column_config.DateColumn("Venc.", format="DD/MM", width="small"),
                "Estado":      st.column_config.TextColumn("Estado", disabled=True, width="medium"),
            },
            column_order=("Pagado","Cat.","Ítem","Monto (ARS)","USD","Peso (%)","Día Pago","Estado"),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
        )

    with tab_todos:
        df_edit = render_tabla(df)

    with tab_pend:
        render_tabla(df[df["Pagado"]==False])

    with tab_pag:
        render_tabla(df[df["Pagado"]==True])

    # ─────────────────────────────────────────────
    # 12. GUARDAR
    # ─────────────────────────────────────────────
    st.markdown("<div style='padding:16px 16px 32px'>", unsafe_allow_html=True)
    if st.button("Guardar y Sincronizar", type="primary", use_container_width=True):
        try:
            df_save  = df_edit.copy()
            df_subir = df_save[["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]].copy()
            df_subir["Día Pago"] = df_subir["Día Pago"].apply(lambda x: str(x) if pd.notnull(x) else "")

            st.cache_data.clear()
            hoja = get_gspread().open("Gastos_Henry").sheet1
            hoja.clear()
            hoja.append_row(df_subir.columns.tolist())
            hoja.append_rows(df_subir.values.tolist())
            st.success("✓ Sincronizado con Google Sheets")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
