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
# 2. CSS — RESPONSIVE: MOBILE + WEB
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

/* ── VARIABLES ── */
:root {
  --bg:      #0a0a0a;
  --surface: #111111;
  --surface2:#161616;
  --border:  rgba(255,255,255,0.07);
  --text:    #f5f5f5;
  --muted:   #555555;
  --accent:  #e8ff47;
  --green:   #34d399;
  --red:     #f87171;
  --yellow:  #fbbf24;
  --radius:  16px;
}

/* ── BASE ── */
html, body, [class*="css"], .stApp {
  font-family: 'Instrument Sans', 'Helvetica Neue', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
* { box-sizing: border-box; }

/* Ocultar chrome de Streamlit */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── LAYOUT PRINCIPAL ── */
.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}
.main-wrap {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px 40px;
}

/* ── HEADER ── */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 0 20px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 24px;
}
.header-left { display: flex; flex-direction: column; gap: 4px; }
.header-label {
  font-size: 10px; font-weight: 500; color: var(--muted);
  letter-spacing: .1em; text-transform: uppercase;
}
.header-date {
  font-family: 'Instrument Serif', Georgia, serif !important;
  font-size: 28px; font-weight: 400;
  letter-spacing: -.02em; line-height: 1;
  color: var(--text);
}
.header-right { display: flex; gap: 10px; align-items: center; }
.dolar-chip {
  background: rgba(232,255,71,0.06);
  border: 1px solid rgba(232,255,71,0.18);
  border-radius: 10px;
  padding: 8px 14px; text-align: right;
}
.dolar-chip-label { font-size: 9px; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; }
.dolar-chip-val   { font-size: 17px; font-weight: 600; color: var(--accent); margin-top: 1px; }

/* ── GRID DE MÉTRICAS ── */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.metric-card {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
}
.metric-card::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  border-radius: var(--radius) var(--radius) 0 0;
}
.mc-accent::after { background: linear-gradient(90deg, var(--accent), transparent); }
.mc-green::after  { background: linear-gradient(90deg, var(--green),  transparent); }
.mc-red::after    { background: linear-gradient(90deg, var(--red),    transparent); }
.mc-blue::after   { background: linear-gradient(90deg, #60a5fa,       transparent); }
.metric-label {
  font-size: 9px; font-weight: 500; color: var(--muted);
  letter-spacing: .1em; text-transform: uppercase; margin-bottom: 10px;
}
.metric-val {
  font-family: 'Instrument Serif', Georgia, serif !important;
  font-size: 26px; font-weight: 400; color: var(--text);
  letter-spacing: -.01em; line-height: 1;
}
.metric-sub { font-size: 11px; color: var(--muted); margin-top: 5px; }
.metric-pct {
  font-family: 'Instrument Serif', Georgia, serif !important;
  font-size: 32px; font-weight: 400; color: var(--accent);
}
.progress-bar {
  height: 3px; background: rgba(255,255,255,0.06);
  border-radius: 4px; overflow: hidden; margin-top: 10px;
}
.progress-fill {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, var(--accent), #a3e635);
}

/* ── ALERTAS ── */
.alerta {
  padding: 10px 16px; border-radius: 12px;
  font-size: 12px; margin-bottom: 10px;
  display: flex; align-items: center; gap: 8px;
}
.alerta-red  { background: rgba(248,113,113,0.07); border: 1px solid rgba(248,113,113,0.2); color: #fca5a5; }
.alerta-warn { background: rgba(251,191,36,0.07);  border: 1px solid rgba(251,191,36,0.2);  color: #fde68a; }

/* ── LAYOUT DOS COLUMNAS ── */
.two-col {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
  align-items: start;
}

/* ── CARD ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
}
.card-title {
  font-size: 10px; font-weight: 500; color: var(--muted);
  letter-spacing: .1em; text-transform: uppercase; margin-bottom: 14px;
}

/* ── RESUMEN LATERAL ── */
.resumen-row {
  display: flex; justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
}
.resumen-row:last-child { border-bottom: none; }
.resumen-key { color: var(--muted); }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important; padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-family: 'Instrument Sans', sans-serif !important;
  font-size: 12px !important; font-weight: 500 !important;
  letter-spacing: .03em !important;
  border-bottom: 2px solid transparent !important;
  padding: 10px 20px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--text) !important;
  border-bottom-color: var(--accent) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 14px 0 0 !important; }

/* ── DATA EDITOR ── */
[data-testid="stDataEditorContainer"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  overflow: hidden !important;
}

/* ── BOTONES ── */
.stButton > button[kind="primary"] {
  background: var(--accent) !important;
  color: #0a0a0a !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 14px 24px !important;
  font-family: 'Instrument Sans', sans-serif !important;
  font-size: 13px !important; font-weight: 600 !important;
  letter-spacing: .02em !important;
  transition: all .2s !important;
}
.stButton > button[kind="primary"]:hover {
  background: #d4eb3a !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 20px rgba(232,255,71,0.2) !important;
}
.stButton > button[kind="secondary"] {
  background: transparent !important;
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  font-family: 'Instrument Sans', sans-serif !important;
  font-size: 12px !important;
  transition: all .2s !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: rgba(255,255,255,0.2) !important;
  color: var(--text) !important;
}

/* ── SUCCESS / ERROR ── */
div[data-testid="stAlert"] {
  border-radius: 12px !important;
  font-size: 13px !important;
}

/* ── RESPONSIVE: TABLET ── */
@media (max-width: 900px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
  .main-wrap { padding: 0 16px 40px; }
}

/* ── RESPONSIVE: MÓVIL ── */
@media (max-width: 600px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .metric-val { font-size: 20px; }
  .metric-pct { font-size: 24px; }
  .header-date { font-size: 22px; }
  .dolar-chip-val { font-size: 14px; }
  .main-wrap { padding: 0 12px 32px; }
  .app-header { padding: 16px 0 14px; margin-bottom: 16px; }
  .card { padding: 14px; }
}

/* Ocultar separadores */
hr { display: none !important; }
[data-testid="stVerticalBlock"] > div { gap: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 3. PALETA Y CONSTANTES
# ─────────────────────────────────────────────
PALETTE = [
    "#e8ff47","#a3e635","#34d399","#22d3ee",
    "#818cf8","#f472b6","#fb923c","#fbbf24",
    "#60a5fa","#c084fc","#f87171","#4ade80",
]

# ─────────────────────────────────────────────
# 4. CONEXIÓN A GOOGLE SHEETS
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
    """
    Lee la hoja Gastos_Henry.
    Columna A: Categoría (puede ser solo emoji o texto completo)
    Columna B: Ítem
    Columna C: Monto (ARS)
    Columna D: Día Pago
    Columna E: Pagado (TRUE/FALSE)
    """
    try:
        hoja = get_gspread().open("Gastos_Henry").sheet1
        data = hoja.get_all_values()
    except Exception as e:
        st.error(f"❌ No se pudo conectar a Google Sheets: {e}")
        return pd.DataFrame()

    # Filtrar filas completamente vacías
    data = [r for r in data if any(str(c).strip() for c in r)]

    if not data or len(data) < 2:
        return pd.DataFrame()

    # Usar la primera fila como headers si corresponde, sino asignar nombres fijos
    primera = [str(c).strip() for c in data[0]]
    headers_esperados = ["Categoría", "Ítem", "Monto (ARS)", "Día Pago", "Pagado"]

    if primera[0].lower() in ["categoría", "categoria", "cat"]:
        filas = data[1:]
    else:
        # No tiene header — los datos empiezan en fila 1
        filas = data

    # Rellenar filas cortas
    filas = [r + [""] * (5 - len(r)) for r in filas if len(r) >= 2]

    df = pd.DataFrame(filas, columns=headers_esperados[:len(filas[0])] if filas else headers_esperados)

    # Asegurar que existen las columnas necesarias
    for col in headers_esperados:
        if col not in df.columns:
            df[col] = ""

    # Conversiones
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
    df["Día Pago"]    = pd.to_datetime(df["Día Pago"], errors="coerce").dt.date
    df["Pagado"]      = df["Pagado"].apply(
        lambda x: str(x).strip().upper() in ["TRUE", "VERDADERO", "✅", "SI", "SÍ", "1"]
    )

    # Eliminar filas donde monto y item son ambos vacíos/0
    df = df[~((df["Monto (ARS)"] == 0) & (df["Ítem"].str.strip() == ""))]
    df = df.reset_index(drop=True)

    return df


@st.cache_data(ttl=300)
def get_dolar():
    try:
        r = requests.get("https://dolarapi.com/v1/dolares/blue", timeout=5)
        return float(r.json()["venta"])
    except Exception:
        return 1450.0

# ─────────────────────────────────────────────
# 5. HELPERS
# ─────────────────────────────────────────────
def fmtK(n):
    """Formato compacto: $1.2M / $320k / $8500"""
    if n >= 1_000_000: return f"${n/1_000_000:.1f}M"
    if n >= 1_000:     return f"${n/1_000:.0f}k"
    return f"${n:,.0f}"

def fmtARS(n):
    return f"${n:,.0f}".replace(",", ".")

def fmtUSD(n, d):
    if d == 0: return "U$S —"
    return f"U$S {n/d:,.0f}"

def get_estado(row):
    if row["Pagado"]:
        return "✅ Listo"
    if pd.isna(row["Día Pago"]):
        return "⚪ Sin Fecha"
    if row["Día Pago"] < date.today():
        return "🔴 Vencido"
    if row["Día Pago"] <= date.today() + timedelta(days=3):
        return "🟡 Próximo"
    return "🟢 Al Día"

def procesar(df_base, dolar):
    df    = df_base.copy()
    total = df["Monto (ARS)"].sum()
    df["Peso (%)"] = (df["Monto (ARS)"] / total).fillna(0) if total > 0 else 0
    df["USD"]      = (df["Monto (ARS)"] / dolar).round(2) if dolar > 0 else 0
    # Cat. = lo que haya en Categoría tal cual (ya sea emoji o texto)
    df["Cat."]     = df["Categoría"].apply(lambda x: str(x).strip() if str(x).strip() else "—")
    df["Estado"]   = df.apply(get_estado, axis=1)
    return df.sort_values(["Pagado", "Día Pago"], ascending=[True, True], na_position="last")

# ─────────────────────────────────────────────
# 6. CARGA DE DATOS
# ─────────────────────────────────────────────
dolar   = get_dolar()
df_base = cargar_datos()

if not df_base.empty:
    df          = procesar(df_base, dolar)
    total_ars   = df["Monto (ARS)"].sum()
    pagado_ars  = df[df["Pagado"] == True]["Monto (ARS)"].sum()
    pend_ars    = total_ars - pagado_ars
    pct         = int(pagado_ars / total_ars * 100) if total_ars > 0 else 0
    vencidos    = df[
        (df["Pagado"] == False) &
        df["Día Pago"].notna() &
        (df["Día Pago"] < date.today())
    ]
    proximos    = df[
        (df["Pagado"] == False) &
        df["Día Pago"].notna() &
        (df["Día Pago"] >= date.today()) &
        (df["Día Pago"] <= date.today() + timedelta(days=3))
    ]
else:
    df = pd.DataFrame()
    total_ars = pagado_ars = pend_ars = pct = 0
    vencidos = proximos = pd.DataFrame()

# ─────────────────────────────────────────────
# 7. RENDER — INICIO DEL WRAPPER
# ─────────────────────────────────────────────
st.markdown('<div class="main-wrap">', unsafe_allow_html=True)

# ── HEADER ──────────────────────────────────
hoy_str = date.today().strftime("%-d de %B")
st.markdown(f"""
<div class="app-header">
  <div class="header-left">
    <span class="header-label">Finanzas AR 🇦🇷</span>
    <span class="header-date">{hoy_str}</span>
  </div>
  <div class="header-right">
    <div class="dolar-chip">
      <div class="dolar-chip-label">USD Blue</div>
      <div class="dolar-chip-val">${dolar:,.0f}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── ALERTAS ─────────────────────────────────
if not vencidos.empty:
    items = ", ".join(vencidos["Ítem"].astype(str).tolist())
    st.markdown(
        f'<div class="alerta alerta-red">🔴 <strong>{len(vencidos)} pago{"s" if len(vencidos)>1 else ""} vencido{"s" if len(vencidos)>1 else ""}</strong> — {items}</div>',
        unsafe_allow_html=True,
    )

if not proximos.empty:
    items = ", ".join(proximos["Ítem"].astype(str).tolist())
    st.markdown(
        f'<div class="alerta alerta-warn">🟡 <strong>{len(proximos)} vence{"n" if len(proximos)>1 else ""} en los próximos 3 días</strong> — {items}</div>',
        unsafe_allow_html=True,
    )

# ── MÉTRICAS ────────────────────────────────
st.markdown(f"""
<div class="metrics-grid">
  <div class="metric-card mc-accent">
    <div class="metric-label">📊 Total del mes</div>
    <div class="metric-val">{fmtK(total_ars)}</div>
    <div class="metric-sub">{fmtUSD(total_ars, dolar)}</div>
  </div>
  <div class="metric-card mc-green">
    <div class="metric-label">✅ Pagado</div>
    <div class="metric-val">{fmtK(pagado_ars)}</div>
    <div class="metric-sub">{fmtUSD(pagado_ars, dolar)}</div>
  </div>
  <div class="metric-card mc-red">
    <div class="metric-label">⏳ Pendiente</div>
    <div class="metric-val">{fmtK(pend_ars)}</div>
    <div class="metric-sub">{fmtUSD(pend_ars, dolar)}</div>
  </div>
  <div class="metric-card mc-blue">
    <div class="metric-label">📈 Cubierto</div>
    <div class="metric-pct">{pct}%</div>
    <div class="progress-bar">
      <div class="progress-fill" style="width:{pct}%"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 8. LAYOUT DOS COLUMNAS: TABLA | SIDEBAR
# ─────────────────────────────────────────────
col_main, col_side = st.columns([2.8, 1], gap="medium")

# ── COLUMNA PRINCIPAL: TABLA ─────────────────
with col_main:
    if df.empty:
        st.markdown("""
        <div class="card" style="text-align:center;padding:40px;color:var(--muted)">
          <div style="font-size:32px;margin-bottom:12px">📭</div>
          <div style="font-size:14px">No se encontraron datos en Google Sheets</div>
          <div style="font-size:12px;margin-top:6px">Verificá la conexión o el nombre de la hoja</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="card-title" style="padding-top:4px">Gestión de Gastos</div>', unsafe_allow_html=True)

        tab_todos, tab_pend, tab_pag = st.tabs([
            f"Todos ({len(df)})",
            f"Pendientes ({len(df[df['Pagado']==False])})",
            f"Pagados ({len(df[df['Pagado']==True])})",
        ])

        COL_CONFIG = {
            "Pagado":      st.column_config.CheckboxColumn("✓", width="small"),
            "Cat.":        st.column_config.TextColumn("Cat.", width="small"),
            "Categoría":   None,
            "Ítem":        st.column_config.TextColumn("Ítem"),
            "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d"),
            "USD":         st.column_config.NumberColumn("USD", format="U$S %.0f", disabled=True, width="small"),
            "Peso (%)":    st.column_config.ProgressColumn("Peso", format="%.1f%%", min_value=0, max_value=1, width="small"),
            "Día Pago":    st.column_config.DateColumn("Venc.", format="DD/MM/YY", width="small"),
            "Estado":      st.column_config.TextColumn("Estado", disabled=True, width="medium"),
        }
        COL_ORDER = ("Pagado", "Cat.", "Ítem", "Monto (ARS)", "USD", "Peso (%)", "Día Pago", "Estado")

        def render_tabla(data, key):
            return st.data_editor(
                data,
                column_config=COL_CONFIG,
                column_order=COL_ORDER,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key=key,
            )

        with tab_todos:
            df_edit = render_tabla(df, "tabla_todos")

        with tab_pend:
            render_tabla(df[df["Pagado"] == False].copy(), "tabla_pend")

        with tab_pag:
            render_tabla(df[df["Pagado"] == True].copy(), "tabla_pag")

        # ── BOTONES ──────────────────────────
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns([3, 1])

        with btn_col1:
            if st.button("✔ Guardar y Sincronizar", type="primary", use_container_width=True):
                try:
                    df_save  = df_edit.copy()
                    df_subir = df_save[["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]].copy()
                    df_subir["Día Pago"] = df_subir["Día Pago"].apply(
                        lambda x: str(x) if pd.notnull(x) else ""
                    )
                    df_subir["Pagado"] = df_subir["Pagado"].apply(
                        lambda x: "TRUE" if x else "FALSE"
                    )
                    st.cache_data.clear()
                    hoja = get_gspread().open("Gastos_Henry").sheet1
                    hoja.clear()
                    hoja.append_row(df_subir.columns.tolist())
                    hoja.append_rows(df_subir.values.tolist())
                    st.success("✓ Sincronizado con Google Sheets")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

        with btn_col2:
            if st.button("🔄 Recargar", type="secondary", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

# ── COLUMNA LATERAL: GRÁFICOS + RESUMEN ──────
with col_side:
    if not df.empty:
        # DONUT
        por_cat = df.groupby("Cat.")["Monto (ARS)"].sum().reset_index().sort_values("Monto (ARS)", ascending=False)

        fig = go.Figure(go.Pie(
            labels=por_cat["Cat."],
            values=por_cat["Monto (ARS)"],
            hole=0.65,
            marker=dict(
                colors=PALETTE[:len(por_cat)],
                line=dict(color="#111", width=2),
            ),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            direction="clockwise",
            sort=True,
        ))
        fig.add_annotation(
            text=f"<b>{fmtK(total_ars)}</b>",
            x=0.5, y=0.5,
            font=dict(size=14, color="#f5f5f5", family="Instrument Serif"),
            showarrow=False,
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="v", x=1.05, y=0.5,
                font=dict(color="#777", size=10, family="Instrument Sans"),
                bgcolor="rgba(0,0,0,0)",
            ),
            height=220,
            margin=dict(t=0, b=0, l=0, r=100),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.markdown('<div class="card"><div class="card-title">Por categoría</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

        # RESUMEN
        n_total   = len(df)
        n_pagados = len(df[df["Pagado"] == True])
        n_pend    = len(df[df["Pagado"] == False])
        n_venc    = len(vencidos)
        n_prox    = len(proximos)
        mayor     = df.loc[df["Monto (ARS)"].idxmax(), "Ítem"] if not df.empty else "—"

        st.markdown(f"""
        <div class="card">
          <div class="card-title">Resumen</div>
          <div class="resumen-row">
            <span class="resumen-key">Items totales</span>
            <span>{n_total}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Pagados</span>
            <span style="color:var(--green);font-weight:600">{n_pagados}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Pendientes</span>
            <span style="color:var(--yellow);font-weight:600">{n_pend}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Vencidos</span>
            <span style="color:var(--red);font-weight:600">{n_venc}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Próximos 3d</span>
            <span style="color:var(--yellow);font-weight:600">{n_prox}</span>
          </div>
          <div class="resumen-row">
            <span class="resumen-key">Mayor gasto</span>
            <span style="font-size:11px">{mayor}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CIERRE DEL WRAPPER
# ─────────────────────────────────────────────
st.markdown("</div>", unsafe_allow_html=True)
