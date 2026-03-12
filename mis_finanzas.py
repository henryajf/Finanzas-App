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
MUTED    = "#444444"
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
# 4. SVG ÍCONOS (AJUSTADOS PARA FONDO SÓLIDO)
# ─────────────────────────────────────────────
def svg_icon(cat: str, size: int = 22) -> str:
    """Devuelve un SVG blanco minimalista (sin opacidades internas) para el círculo sólido."""
    c = str(cat)
    s = size
    fill = "white"

    if "⚡" in c or "🔌" in c:
        path = f'<polygon points="{s*0.6},{s*0.05} {s*0.3},{s*0.52} {s*0.52},{s*0.52} {s*0.4},{s*0.95} {s*0.7},{s*0.45} {s*0.48},{s*0.45}" fill="white"/>'
    elif "🏠" in c or "🏡" in c:
        path = (
            f'<polygon points="{s*0.5},{s*0.1} {s*0.88},{s*0.45} {s*0.78},{s*0.45} {s*0.78},{s*0.88} {s*0.22},{s*0.88} {s*0.22},{s*0.45} {s*0.12},{s*0.45}" fill="white"/>'
            f'<rect x="{s*0.38}" y="{s*0.58}" width="{s*0.24}" height="{s*0.3}" rx="{s*0.03}" fill="white"/>'
        )
    elif "🛒" in c:
        path = (
            f'<path d="M{s*.1},{s*.18} L{s*.22},{s*.18} L{s*.35},{s*.65} L{s*.8},{s*.65} L{s*.9},{s*.3} L{s*.3},{s*.3}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<circle cx="{s*.38}" cy="{s*.8}" r="{s*.07}" fill="white"/>'
            f'<circle cx="{s*.72}" cy="{s*.8}" r="{s*.07}" fill="white"/>'
        )
    elif "💳" in c:
        path = (
            f'<rect x="{s*.1}" y="{s*.25}" width="{s*.8}" height="{s*.5}" rx="{s*.08}" fill="white"/>'
            f'<rect x="{s*.1}" y="{s*.38}" width="{s*.8}" height="{s*.12}" fill="#555" opacity="0.5"/>'
        )
    elif "📺" in c:
        path = (
            f'<rect x="{s*.1}" y="{s*.15}" width="{s*.8}" height="{s*.55}" rx="{s*.07}" fill="white"/>'
            f'<rect x="{s*.18}" y="{s*.23}" width="{s*.64}" height="{s*.39}" rx="{s*.04}" fill="#555"/>'
            f'<polygon points="{s*.4},{s*.35} {s*.4},{s*.52} {s*.62},{s*.435}" fill="white"/>'
        )
    elif "🚗" in c or "🚌" in c:
        path = (
            f'<rect x="{s*.08}" y="{s*.42}" width="{s*.84}" height="{s*.3}" rx="{s*.07}" fill="white"/>'
            f'<path d="M{s*.22},{s*.42} L{s*.32},{s*.22} L{s*.68},{s*.22} L{s*.78},{s*.42}" fill="white"/>'
            f'<circle cx="{s*.27}" cy="{s*.76}" r="{s*.1}" fill="white"/>'
            f'<circle cx="{s*.73}" cy="{s*.76}" r="{s*.1}" fill="white"/>'
        )
    # ... (resto de SVGs ajustados a fill blanco sólido) ...
    else:
        path = f'<circle cx="{s*.5}" cy="{s*.5}" r="{s*.35}" fill="white"/>'

    return f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">{path}</svg>'


# ─────────────────────────────────────────────
# 5. CSS GLOBAL (OPTIMIZADO ESTÉTICAMENTE)
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {{
  --bg:      {BG};
  --surface: {SURFACE};
  --border:  {BORDER};
  --text:    {TEXT};
  --muted2:  {MUTED2};
}}

html, body, [class*="css"], .stApp {{
  font-family: 'Plus Jakarta Sans',sans-serif !important;
  background: var(--bg) !important;
}}

/* ... (Estilos de nav y metrics se mantienen iguales) ... */
.wrap {{ max-width: 1060px; margin: 0 auto; padding: 0 22px 48px; }}
.hdr {{ display: flex; justify-content: space-between; align-items: center; padding: 22px 0 16px; border-bottom: 1px solid var(--border); position: relative; overflow: hidden; }}
.nav-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 14px 0 20px; border-bottom: 1px solid var(--border); margin-bottom: 22px; }}
.stButton > button {{ border-radius: 12px !important; font-weight: 700 !important; }}
.metrics {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 20px; }}

/* ── ITEM ROW OPTIMIZADO — LOOK MERCADO PAGO ── */
.item-row {{
  display: flex; align-items: center; gap: 14px;
  padding: 16px 18px;
  border-bottom: 1px solid {BORDER2};
  transition: background .12s;
}}
.item-row:last-child {{ border-bottom: none; }}
.item-row:hover {{ background: rgba(255,255,255,0.015); }}

.item-ico {{
  width: 44px; height: 44px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}}

.item-body {{ flex: 1; min-width: 0; }}
.item-name {{ font-size: 15px; font-weight: 500; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px; }}
.item-name-paid {{ font-size: 15px; font-weight: 400; color: var(--muted2); text-decoration: line-through; }}

.item-right {{ text-align: right; display: flex; align-items: center; gap: 12px; }}
.mp-amounts {{ display: flex; flex-direction: column; }}
.item-monto {{ font-size: 16px; font-weight: 600; color: var(--text); line-height: 1.2; }}
.item-monto-paid {{ font-size: 16px; font-weight: 500; color: var(--muted2); text-decoration: line-through; }}
.item-usd {{ font-size: 12px; color: var(--muted2); margin-top: 2px; }}
.item-arrow {{ color: #444; font-size: 20px; font-weight: 300; margin-left: 4px; }}

/* Badges de vencimiento sutiles */
.vbadge {{ font-size: 11px; font-weight: 600; margin-top: 4px; display: inline-block; }}
.vb-pagado {{ color: {GREEN}; }}
.vb-vencido {{ color: {RED}; }}
.vb-pendiente {{ color: {ORANGE}; }}

/* Cards y otros estilos se mantienen */
.card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 16px; overflow: hidden; }}
.ctitle {{ font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .1em; padding: 20px 20px 10px; }}
.sec-hdr {{ display: flex; align-items: center; gap: 12px; padding: 11px 18px 9px; background: rgba(255,255,255,.018); border-bottom: 1px solid {BORDER2}; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. CONEXIÓN Y DATOS (SE MANTIENEN IGUALES)
# ─────────────────────────────────────────────
@st.cache_resource
def get_gspread():
    # ... (Misma lógica de credenciales) ...
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos():
    # ... (Misma lógica de carga de df) ...
    try:
        hoja = get_gspread().open("Gastos_Henry").sheet1
        data = hoja.get_all_values()
        df = pd.DataFrame(data[1:], columns=["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"])
        df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors="coerce").fillna(0)
        df["Día Pago"]    = pd.to_datetime(df["Día Pago"], errors="coerce").dt.date
        df["Pagado"]      = df["Pagado"].apply(lambda x: str(x).strip().upper() in ["TRUE","SI","1"])
        return df
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=300)
def get_dolar():
    # ... (Misma lógica dolarapi) ...
    try: return float(requests.get("https://dolarapi.com/v1/dolares/blue").json()["venta"])
    except Exception: return 1450.0

# ─────────────────────────────────────────────
# 7. HELPERS ACTUALIZADOS PARA EL NUEVO LOOK
# ─────────────────────────────────────────────
# (Misma categorización_inteligente, fmt_ars, fmt_usd)

def venc_html_mp(row):
    """Badge de vencimiento sutil debajo del ítem."""
    if row["Pagado"]:
        return '<span class="vbadge vb-pagado">✓ Pagado</span>'
    dia = row["Día Pago"]
    if pd.isna(dia):
        return '<span class="vbadge">⚪ Sin fecha</span>'
    diff = (dia - date.today()).days
    if diff < 0:
        return f'<span class="vbadge vb-vencido">Vencido {dia.strftime("%d/%m")}</span>'
    return f'<span class="vbadge vb-pendiente">Vence en {diff}d</span>'

# ─────────────────────────────────────────────
# 8-9. CARGA Y HEADER (SE MANTIENEN IGUALES)
# ─────────────────────────────────────────────
# (Lógica de carga y renderizado de header con sol de mayo se mantiene)

# ═════════════════════════════════════════════
# PANTALLA: INICIO (CORREGIDO DETALLE DE GASTOS)
# ═════════════════════════════════════════════
if st.session_state.screen == "inicio":
    # ... (Renderizado de Alertas y Métricas se mantiene igual) ...

    if not df.empty:
        col_izq, col_der = st.columns([1.65, 1], gap="medium")

        # ── COL IZQUIERDA: LISTA AGRUPADA (NUEVO LOOK) ────
        with col_izq:
            # Ordenación por categoría (mismo criterio lógico)
            cats_orden = df.groupby("Categoría").apply(lambda g: g["Pagado"].eq(False).sum()).sort_values(ascending=False).index.tolist()

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="ctitle">Detalle de gastos</div>', unsafe_allow_html=True)

            for cat in cats_orden:
                df_cat = df[df["Categoría"] == cat]
                color = cat_color(cat)
                
                # Header de sección corregido
                icon_header = svg_icon(cat, size=16)
                st.markdown(f"""
                <div class="sec-hdr">
                  <div style="width:26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center;background:{color}15">{icon_header}</div>
                  <span style="flex:1;font-size:11px;font-weight:700;color:var(--muted2);text-transform:uppercase;">{cat}</span>
                  <span style="font-size:13px;font-weight:800;color:{color}">{fmt_ars(df_cat["Monto (ARS)"].sum())}</span>
                </div>
                """, unsafe_allow_html=True)

                for _, row in df_cat.iterrows():
                    paid = row["Pagado"]
                    monto = row["Monto (ARS)"]
                    usd_val = f"U$S {monto/dolar:,.0f}"
                    
                    # Llamada al nuevo helper de vencimiento y SVG blanco
                    v_badge = venc_html_mp(row)
                    icon_lg = svg_icon(cat, size=22)
                    
                    # Lógica de clases y opacidad mantenida
                    opacity = "0.5" if paid else "1"
                    name_cls = "item-name-paid" if paid else "item-name"
                    monto_cls = "item-monto-paid" if paid else "item-monto"

                    # ── HTML DE FILA TOTALMENTE ACTUALIZADO (Look MP) ──
                    st.markdown(f"""
                    <div class="item-row" style="opacity:{opacity}">
                      <div class="item-ico" style="background-color: {color};">
                        {icon_lg}
                      </div>
                      
                      <div class="item-body">
                        <div class="{name_cls}">{row['Ítem']}</div>
                        {v-badge}
                      </div>
                      
                      <div class="item-right">
                        <div class="mp-amounts">
                            <div class="{monto_cls}">{fmt_ars(monto)}</div>
                            <div class="item-usd">{usd_val}</div>
                        </div>
                        <div class="item-arrow">&rsaquo;</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ... (Columna derecha: Donut, Resumen y Barras se mantiene igual) ...

# ═════════════════════════════════════════════
# PANTALLA: GASTOS (SE MANTIENE IGUAL)
# ═════════════════════════════════════════════
# ... (Todo el bloque elif st.session_state.screen == "gastos": se mantiene idéntico) ...
