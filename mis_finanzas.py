import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.express as px
import plotly.graph_objects as go
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, timedelta

# ─────────────────────────────────────────────
# 1. CONFIG DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Finanzas AR 🇦🇷",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# 2. CSS GLOBAL — TEMA OSCURO FINANCIERO
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');

/* BASE */
html, body, [class*="css"], .stApp {
    font-family: 'DM Mono', 'Courier New', monospace !important;
    background-color: #080c18 !important;
    color: #e2e8f0 !important;
}

/* OCULTAR elementos de Streamlit que no queremos */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
section[data-testid="stSidebar"] { display: none; }

/* SCROLLBAR */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0d1226; }
::-webkit-scrollbar-thumb { background: rgba(0,229,255,0.3); border-radius: 4px; }

/* ── HEADER ── */
.header-wrap {
    background: linear-gradient(180deg, #0d1226 0%, transparent 100%);
    padding: 24px 40px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-title {
    font-family: 'Syne', sans-serif !important;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #f1f5f9;
}
.header-title span { color: #00e5ff; }
.header-subtitle {
    font-size: 11px;
    color: #475569;
    margin-top: 4px;
    text-transform: capitalize;
}
.dolar-badge {
    background: rgba(0,229,255,0.06);
    border: 1px solid rgba(0,229,255,0.18);
    border-radius: 10px;
    padding: 10px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.dolar-label { font-size: 11px; color: #94a3b8; }
.dolar-value { font-size: 16px; font-weight: 600; color: #00e5ff; }
.glow-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #00e5ff;
    box-shadow: 0 0 8px #00e5ff;
    display: inline-block;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.25} }

/* ── MÉTRICAS ── */
.metric-card {
    background: linear-gradient(135deg, #0f1629 0%, #0a0e1a 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,229,255,0.1); }
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 16px 16px 0 0;
}
.mc-cyan::before   { background: linear-gradient(90deg, #00e5ff, transparent); }
.mc-green::before  { background: linear-gradient(90deg, #00e676, transparent); }
.mc-red::before    { background: linear-gradient(90deg, #ff6b6b, transparent); }
.mc-purple::before { background: linear-gradient(90deg, #7c4dff, transparent); }
.metric-icon { font-size: 13px; color: #475569; margin-bottom: 8px; letter-spacing: 0.08em; text-transform: uppercase; }
.metric-main { font-family: 'Syne', sans-serif !important; font-size: 22px; font-weight: 800; color: #f1f5f9; }
.metric-sub  { font-size: 11px; color: #475569; margin-top: 4px; }
.metric-pct  { font-family: 'Syne', sans-serif !important; font-size: 32px; font-weight: 800; color: #7c4dff; }
.progress-bar { height: 4px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; margin-top: 10px; }
.progress-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #7c4dff, #00e5ff); }

/* ── ALERTA ── */
.alerta-banner {
    background: rgba(255,107,107,0.07);
    border: 1px solid rgba(255,107,107,0.2);
    border-radius: 12px;
    padding: 13px 18px;
    color: #fca5a5;
    font-size: 13px;
    margin-bottom: 6px;
}

/* ── SECCIÓN TITLE ── */
.section-title {
    font-family: 'Syne', sans-serif !important;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: #334155;
    text-transform: uppercase;
    margin-bottom: 14px;
    padding-top: 4px;
}

/* ── TABLA ── */
.stDataFrame, .stDataEditor { border-radius: 14px !important; overflow: hidden; }
[data-testid="stDataEditorContainer"] {
    background: #0f1629 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
}

/* ── CHIP STATUS ── */
.chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.05em;
}

/* ── BOTONES ── */
div[data-testid="stHorizontalBlock"] .stButton button {
    border-radius: 20px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    background: transparent !important;
    color: #94a3b8 !important;
    padding: 6px 16px !important;
    transition: all 0.2s !important;
}
div[data-testid="stHorizontalBlock"] .stButton button:hover {
    border-color: rgba(0,229,255,0.4) !important;
    color: #e2e8f0 !important;
}

/* BOTÓN GUARDAR */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(0,229,255,0.1), rgba(124,77,255,0.1)) !important;
    border: 1px solid rgba(0,229,255,0.3) !important;
    color: #00e5ff !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 14px !important;
    border-radius: 12px !important;
    padding: 14px !important;
    letter-spacing: 0.05em !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, rgba(0,229,255,0.18), rgba(124,77,255,0.18)) !important;
    box-shadow: 0 0 28px rgba(0,229,255,0.15) !important;
}

/* SELECTBOX / FILTROS */
.stSelectbox > div > div {
    background: #0f1629 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Mono', monospace !important;
}

/* SEPARADOR */
hr { border-color: rgba(255,255,255,0.04) !important; margin: 20px 0 !important; }

/* LAYOUT PRINCIPAL */
.main-content { padding: 28px 40px; }

/* SUCCESS / ERROR */
.stSuccess { background: rgba(0,230,118,0.08) !important; border: 1px solid rgba(0,230,118,0.2) !important; border-radius: 12px !important; color: #00e676 !important; }
.stError   { background: rgba(255,107,107,0.08) !important; border: 1px solid rgba(255,107,107,0.2) !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. CATEGORÍAS
# ─────────────────────────────────────────────
ICONOS_MAP = {
    "🏠 Vivienda": "🏠", "⚡ Servicios": "⚡", "📺 Suscripción": "📺",
    "🛒 Alimentos": "🛒", "🚗 Transporte": "🚗", "💳 Tarjetas": "💳",
    "📈 Inversiones": "📈", "👪 Familia": "👪", "🏥 Salud": "🏥", "🎭 Ocio": "🎭"
}
PALETTE = ["#00e5ff","#7c4dff","#ff6b6b","#00e676","#ffd740","#ff80ab","#40c4ff","#69f0ae","#ea80fc","#ff6e40"]

# ─────────────────────────────────────────────
# 4. CONEXIÓN Y DATOS
# ─────────────────────────────────────────────
@st.cache_resource
def obtener_cliente_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json", scope)
    except Exception:
        info_json = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info_json, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos_gsheet():
    client = obtener_cliente_gspread()
    hoja = client.open("Gastos_Henry").sheet1
    data_raw = hoja.get_all_values()
    if not data_raw or len(data_raw) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(data_raw[1:], columns=["Categoría", "Ítem", "Monto (ARS)", "Día Pago", "Pagado"])
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
    df["Día Pago"]    = pd.to_datetime(df["Día Pago"], errors="coerce").dt.date
    df["Pagado"]      = df["Pagado"].apply(lambda x: str(x).upper() in ["TRUE", "VERDADERO", "✅"])
    return df

@st.cache_data(ttl=300)
def get_dolar_blue():
    try:
        return float(requests.get("https://dolarapi.com/v1/dolares/blue", timeout=5).json()["venta"])
    except Exception:
        return 1450.0

# ─────────────────────────────────────────────
# 5. HELPERS
# ─────────────────────────────────────────────
def fmt_ars(n):
    return f"${n:,.0f}".replace(",", ".")

def fmt_usd(n, dolar):
    return f"U$S {n/dolar:,.2f}"

def limpiar_icono(cat):
    for nombre, icono in ICONOS_MAP.items():
        if icono in str(cat):
            return icono
    return "❓"

def obtener_estado(row):
    if row["Pagado"]:
        return "✅ Listo"
    if pd.isna(row["Día Pago"]):
        return "⚪ Sin Fecha"
    return "🔴 Vencido" if row["Día Pago"] < date.today() else "🟢 Al Día"

def procesar_df(df_base, dolar):
    df = df_base.copy()
    total = df["Monto (ARS)"].sum()
    df["Peso (%)"]  = (df["Monto (ARS)"] / total) if total > 0 else 0
    df["USD"]       = df["Monto (ARS)"] / dolar
    df["Cat."]      = df["Categoría"].apply(limpiar_icono)
    df["Estado"]    = df.apply(obtener_estado, axis=1)
    df = df.sort_values(["Pagado", "Día Pago"], ascending=[True, True])
    return df

# ─────────────────────────────────────────────
# 6. CARGA DE DATOS
# ─────────────────────────────────────────────
dolar   = get_dolar_blue()
df_base = cargar_datos_gsheet()

if not df_base.empty:
    df          = procesar_df(df_base, dolar)
    total_ars   = df["Monto (ARS)"].sum()
    pagado_ars  = df[df["Pagado"] == True]["Monto (ARS)"].sum()
    pend_ars    = df[df["Pagado"] == False]["Monto (ARS)"].sum()
    pct_cubierto = int(pagado_ars / total_ars * 100) if total_ars > 0 else 0
    vencidos    = df[(df["Pagado"] == False) & (df["Día Pago"].notna()) & (df["Día Pago"] < date.today())]
    proximos    = df[(df["Pagado"] == False) & (df["Día Pago"].notna()) &
                     (df["Día Pago"] >= date.today()) & (df["Día Pago"] <= date.today() + timedelta(days=3))]
else:
    total_ars = pagado_ars = pend_ars = pct_cubierto = 0
    df = pd.DataFrame()
    vencidos = proximos = pd.DataFrame()

# ─────────────────────────────────────────────
# 7. HEADER
# ─────────────────────────────────────────────
hoy = date.today().strftime("%A %d de %B, %Y")
st.markdown(f"""
<div class="header-wrap">
  <div>
    <div class="header-title">Finanzas <span>AR</span> 🇦🇷</div>
    <div class="header-subtitle">{hoy}</div>
  </div>
  <div class="dolar-badge">
    <span class="glow-dot"></span>
    <span class="dolar-label">USD Blue</span>
    <span class="dolar-value">${dolar:,.0f}</span>
  </div>
</div>
<div class="main-content">
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 8. ALERTAS
# ─────────────────────────────────────────────
if not vencidos.empty:
    items_venc = ", ".join(vencidos["Ítem"].tolist())
    st.markdown(f"""
    <div class="alerta-banner">
        🔴 <strong>{len(vencidos)} pago{'s' if len(vencidos)>1 else ''} vencido{'s' if len(vencidos)>1 else ''}</strong>
        — {items_venc}
    </div>
    """, unsafe_allow_html=True)

if not proximos.empty:
    items_prox = ", ".join(proximos["Ítem"].tolist())
    st.markdown(f"""
    <div class="alerta-banner" style="background:rgba(255,215,64,0.07);border-color:rgba(255,215,64,0.2);color:#fde68a;">
        🟡 <strong>{len(proximos)} vence{'n' if len(proximos)>1 else ''} en los próximos 3 días</strong>
        — {items_prox}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 9. MÉTRICAS
# ─────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"""
<div class="metric-card mc-cyan">
  <div class="metric-icon">📊 Total Gastos</div>
  <div class="metric-main">{fmt_ars(total_ars)}</div>
  <div class="metric-sub">{fmt_usd(total_ars, dolar)}</div>
</div>""", unsafe_allow_html=True)

c2.markdown(f"""
<div class="metric-card mc-green">
  <div class="metric-icon">✅ Pagado</div>
  <div class="metric-main">{fmt_ars(pagado_ars)}</div>
  <div class="metric-sub">{fmt_usd(pagado_ars, dolar)}</div>
</div>""", unsafe_allow_html=True)

c3.markdown(f"""
<div class="metric-card mc-red">
  <div class="metric-icon">⏳ Pendiente</div>
  <div class="metric-main">{fmt_ars(pend_ars)}</div>
  <div class="metric-sub">{fmt_usd(pend_ars, dolar)}</div>
</div>""", unsafe_allow_html=True)

c4.markdown(f"""
<div class="metric-card mc-purple">
  <div class="metric-icon">📈 % Cubierto</div>
  <div class="metric-pct">{pct_cubierto}%</div>
  <div class="progress-bar"><div class="progress-fill" style="width:{pct_cubierto}%"></div></div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 10. GRÁFICOS
# ─────────────────────────────────────────────
col_charts, col_summary = st.columns([3, 1])

with col_charts:
    if not df.empty:
        por_cat = df.groupby("Categoría")["Monto (ARS)"].sum().reset_index()
        
        fig_donut = go.Figure(go.Pie(
            labels=por_cat["Categoría"],
            values=por_cat["Monto (ARS)"],
            hole=0.72,
            marker=dict(colors=PALETTE[:len(por_cat)], line=dict(color="#080c18", width=3)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>",
        ))
        fig_donut.add_annotation(
            text=f"<b>{fmt_ars(total_ars)}</b>",
            x=0.5, y=0.5, font=dict(size=16, color="#f1f5f9", family="Syne"),
            showarrow=False
        )
        fig_donut.update_layout(
            showlegend=True,
            legend=dict(
                orientation="v", x=1.02, y=0.5,
                font=dict(color="#94a3b8", size=11, family="DM Mono"),
                bgcolor="rgba(0,0,0,0)",
            ),
            height=240,
            margin=dict(t=10, b=10, l=10, r=120),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_donut, use_container_width=True)

with col_summary:
    if not df.empty:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=["Pagado", "Pendiente"],
            y=[pagado_ars, pend_ars],
            marker=dict(
                color=["rgba(0,230,118,0.7)", "rgba(255,107,107,0.7)"],
                line=dict(color=["#00e676", "#ff6b6b"], width=1),
            ),
            hovertemplate="%{x}: $%{y:,.0f}<extra></extra>",
        ))
        fig_bar.update_layout(
            height=200,
            margin=dict(t=10, b=10, l=0, r=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickfont=dict(color="#475569", size=11, family="DM Mono"), gridcolor="rgba(0,0,0,0)", linecolor="rgba(0,0,0,0)"),
            yaxis=dict(visible=False),
            bargap=0.3,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 11. TABLA DE GESTIÓN
# ─────────────────────────────────────────────
if not df.empty:
    st.markdown('<div class="section-title">Gestión de Gastos</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3, _ = st.columns([1, 1, 1, 5])
    with col_f1:
        filtro_cat = st.selectbox("Categoría", ["Todas"] + sorted(df["Categoría"].unique().tolist()), label_visibility="collapsed")
    with col_f2:
        filtro_estado = st.selectbox("Estado", ["Todos", "Pendiente", "Pagado", "Vencido"], label_visibility="collapsed")

    df_vista = df.copy()
    if filtro_cat != "Todas":
        df_vista = df_vista[df_vista["Categoría"] == filtro_cat]
    if filtro_estado == "Pendiente":
        df_vista = df_vista[df_vista["Pagado"] == False]
    elif filtro_estado == "Pagado":
        df_vista = df_vista[df_vista["Pagado"] == True]
    elif filtro_estado == "Vencido":
        df_vista = df_vista[df_vista["Estado"] == "🔴 Vencido"]

    df_editado = st.data_editor(
        df_vista,
        column_config={
            "Pagado":      st.column_config.CheckboxColumn("✓"),
            "Cat.":        st.column_config.TextColumn("Cat.", width="small"),
            "Categoría":   None,
            "Ítem":        st.column_config.TextColumn("Ítem"),
            "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d"),
            "USD":         st.column_config.NumberColumn("USD", format="U$S %.2f", disabled=True),
            "Peso (%)":    st.column_config.ProgressColumn("Peso", format="%.1f%%", min_value=0, max_value=1),
            "Día Pago":    st.column_config.DateColumn("Venc.", format="DD/MM"),
            "Estado":      st.column_config.TextColumn("Estado", disabled=True),
        },
        column_order=("Pagado", "Cat.", "Ítem", "Monto (ARS)", "USD", "Peso (%)", "Día Pago", "Estado"),
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="tabla_gastos",
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # 12. GUARDAR
    # ─────────────────────────────────────────────
    col_btn, _ = st.columns([2, 6])
    with col_btn:
        if st.button("✔ Guardar y Sincronizar", type="primary", use_container_width=True):
            try:
                df_save  = df_editado.copy()
                df_subir = df_save[["Categoría", "Ítem", "Monto (ARS)", "Día Pago", "Pagado"]]
                df_subir = df_subir.copy()
                df_subir["Día Pago"] = df_subir["Día Pago"].apply(lambda x: str(x) if pd.notnull(x) else "")

                st.cache_data.clear()
                hoja = obtener_cliente_gspread().open("Gastos_Henry").sheet1
                hoja.clear()
                hoja.append_row(df_subir.columns.tolist())
                hoja.append_rows(df_subir.values.tolist())
                st.success("✅ Base de datos sincronizada con Google Sheets")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

st.markdown("</div>", unsafe_allow_html=True)  # cierre .main-content
