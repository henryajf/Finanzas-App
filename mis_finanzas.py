import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.graph_objects as go
import math
import io
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, timedelta

st.set_page_config(page_title="Finanzas AR", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")

for k,v in [("screen","inicio"),("show_add",False)]:
    if k not in st.session_state: st.session_state[k]=v

BG="#0a0a0a"; SURFACE="#131313"; SURF2="#1a1a1a"; BORDER="rgba(255,255,255,0.07)"; BORDER2="rgba(255,255,255,0.04)"
TEXT="#f0f0f0"; MUTED="#444444"; MUTED2="#777777"; PLOTBG="rgba(0,0,0,0)"
ACCENT="#009ee3"; GREEN="#00c853"; RED="#f23d4f"; ORANGE="#ff9c00"; YELLOW="#fbbf24"

CAT_COLORS={"⚡":"#009ee3","🔌":"#009ee3","🏠":"#00a650","🏡":"#00a650","🛒":"#22c55e","🍔":"#ef4444",
            "🚗":"#ff9c00","🚌":"#ff9c00","💳":"#a855f7","📺":"#ec4899","📈":"#0ea5e9","🏥":"#14b8a6",
            "🎭":"#f59e0b","👪":"#8b5cf6","🏋":"#22d3ee","✈":"#60a5fa","🔘":"#6b7280"}

def cat_color(cat):
    for e,c in CAT_COLORS.items():
        if e in str(cat): return c
    return "#6b7280"

def svg_icon(cat,color,size=22):
    c,s=str(cat),size
    if "⚡" in c or "🔌" in c: path=f'<polygon points="{s*.6},{s*.05} {s*.3},{s*.52} {s*.52},{s*.52} {s*.4},{s*.95} {s*.7},{s*.45} {s*.48},{s*.45}" fill="white"/>'
    elif "🏠" in c or "🏡" in c: path=f'<polygon points="{s*.5},{s*.1} {s*.88},{s*.45} {s*.78},{s*.45} {s*.78},{s*.88} {s*.22},{s*.88} {s*.22},{s*.45} {s*.12},{s*.45}" fill="white"/><rect x="{s*.38}" y="{s*.58}" width="{s*.24}" height="{s*.3}" rx="{s*.03}" fill="{color}" opacity="0.6"/>'
    elif "🛒" in c: path=f'<path d="M{s*.1},{s*.18} L{s*.22},{s*.18} L{s*.35},{s*.65} L{s*.8},{s*.65} L{s*.9},{s*.3} L{s*.3},{s*.3}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="{s*.38}" cy="{s*.8}" r="{s*.07}" fill="white"/><circle cx="{s*.72}" cy="{s*.8}" r="{s*.07}" fill="white"/>'
    elif "💳" in c: path=f'<rect x="{s*.1}" y="{s*.25}" width="{s*.8}" height="{s*.5}" rx="{s*.08}" fill="white" opacity="0.9"/><rect x="{s*.1}" y="{s*.38}" width="{s*.8}" height="{s*.12}" fill="{color}" opacity="0.5"/><rect x="{s*.16}" y="{s*.58}" width="{s*.2}" height="{s*.08}" rx="{s*.03}" fill="{color}" opacity="0.7"/>'
    elif "📺" in c: path=f'<rect x="{s*.1}" y="{s*.15}" width="{s*.8}" height="{s*.55}" rx="{s*.07}" fill="white" opacity="0.9"/><rect x="{s*.18}" y="{s*.23}" width="{s*.64}" height="{s*.39}" rx="{s*.04}" fill="{color}" opacity="0.6"/><polygon points="{s*.4},{s*.35} {s*.4},{s*.52} {s*.62},{s*.435}" fill="white"/>'
    elif "🚗" in c or "🚌" in c: path=f'<rect x="{s*.08}" y="{s*.42}" width="{s*.84}" height="{s*.3}" rx="{s*.07}" fill="white" opacity="0.9"/><path d="M{s*.22},{s*.42} L{s*.32},{s*.22} L{s*.68},{s*.22} L{s*.78},{s*.42}" fill="white" opacity="0.9"/><circle cx="{s*.27}" cy="{s*.76}" r="{s*.1}" fill="{color}" opacity="0.8"/><circle cx="{s*.27}" cy="{s*.76}" r="{s*.05}" fill="white"/><circle cx="{s*.73}" cy="{s*.76}" r="{s*.1}" fill="{color}" opacity="0.8"/><circle cx="{s*.73}" cy="{s*.76}" r="{s*.05}" fill="white"/>'
    elif "🏥" in c: path=f'<rect x="{s*.38}" y="{s*.12}" width="{s*.24}" height="{s*.76}" rx="{s*.06}" fill="white"/><rect x="{s*.12}" y="{s*.38}" width="{s*.76}" height="{s*.24}" rx="{s*.06}" fill="white"/>'
    elif "🍔" in c: path=f'<rect x="{s*.15}" y="{s*.28}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/><rect x="{s*.15}" y="{s*.45}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/><rect x="{s*.15}" y="{s*.62}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/>'
    elif "✈" in c: path=f'<path d="M{s*.5},{s*.1} L{s*.9},{s*.6} L{s*.72},{s*.55} L{s*.65},{s*.85} L{s*.5},{s*.75} L{s*.35},{s*.85} L{s*.28},{s*.55} L{s*.1},{s*.6} Z" fill="white" opacity="0.9"/>'
    else: path=f'<circle cx="{s*.5}" cy="{s*.4}" r="{s*.18}" fill="white" opacity="0.9"/><rect x="{s*.44}" y="{s*.62}" width="{s*.12}" height="{s*.26}" rx="{s*.05}" fill="white" opacity="0.9"/>'
    return f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg">{path}</svg>'

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root{{--bg:{BG};--surface:{SURFACE};--surf2:{SURF2};--border:{BORDER};--text:{TEXT};--muted:{MUTED};--muted2:{MUTED2};--accent:{ACCENT};--green:{GREEN};--red:{RED};--orange:{ORANGE};--r:16px;}}
html,body,[class*="css"],.stApp{{font-family:'Plus Jakarta Sans','Helvetica Neue',sans-serif !important;background:var(--bg) !important;color:var(--text) !important;}}
*{{box-sizing:border-box;}}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{{display:none !important;}}
.block-container{{padding:0 !important;max-width:100% !important;}}
.wrap{{max-width:1060px;margin:0 auto;padding:0 22px 48px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;padding:22px 0 16px;border-bottom:1px solid var(--border);position:relative;overflow:hidden;}}
.hdr-brand{{font-size:22px;font-weight:800;color:var(--text);letter-spacing:-.03em;position:relative;z-index:2;}}
.hdr-brand span{{color:var(--accent);}}
.hdr-date{{font-size:11px;color:var(--muted2);font-weight:500;margin-top:3px;position:relative;z-index:2;}}
.dolar-chip{{background:rgba(0,158,227,.08);border:1px solid rgba(0,158,227,.2);border-radius:12px;padding:8px 16px;text-align:center;position:relative;z-index:2;}}
.dolar-lbl{{font-size:9px;color:var(--muted2);letter-spacing:.08em;text-transform:uppercase;font-weight:700;}}
.dolar-val{{font-size:18px;font-weight:800;color:var(--accent);margin-top:1px;}}
.nav-grid{{display:flex;justify-content:center;gap:12px;padding:14px 0 20px;border-bottom:1px solid var(--border);margin-bottom:22px;}}
.stButton>button[kind="primary"]{{background:{ACCENT} !important;color:#fff !important;border:none !important;border-radius:12px !important;padding:10px 24px !important;font-family:'Plus Jakarta Sans',sans-serif !important;font-size:14px !important;font-weight:700 !important;box-shadow:0 4px 14px rgba(0,158,227,.3) !important;transition:all .2s !important;}}
.stButton>button[kind="primary"]:hover{{background:#007fc0 !important;transform:translateY(-1px) !important;}}
.stButton>button[kind="secondary"]{{background:var(--surface) !important;color:var(--muted2) !important;border:1px solid var(--border) !important;border-radius:12px !important;padding:10px 24px !important;font-family:'Plus Jakarta Sans',sans-serif !important;font-size:14px !important;font-weight:700 !important;transition:all .2s !important;}}
.stButton>button[kind="secondary"]:hover{{border-color:{ACCENT} !important;color:{ACCENT} !important;}}
.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;}}
.mcard{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);padding:18px 20px;position:relative;overflow:hidden;}}
.mcard::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;border-radius:var(--r) var(--r) 0 0;}}
.mc-a::before{{background:linear-gradient(90deg,{ACCENT},transparent);}}
.mc-g::before{{background:linear-gradient(90deg,{GREEN},transparent);}}
.mc-r::before{{background:linear-gradient(90deg,{RED},transparent);}}
.mc-o::before{{background:linear-gradient(90deg,{ORANGE},transparent);}}
.mlbl{{font-size:9px;font-weight:700;color:var(--muted2);letter-spacing:.1em;text-transform:uppercase;margin-bottom:10px;}}
.mval{{font-size:23px;font-weight:800;color:var(--text);letter-spacing:-.02em;line-height:1;}}
.msub{{font-size:11px;color:var(--muted2);margin-top:5px;}}
.mpct{{font-size:28px;font-weight:800;color:{ACCENT};}}
.pbar{{height:4px;background:rgba(255,255,255,.06);border-radius:4px;overflow:hidden;margin-top:10px;}}
.pfill{{height:100%;border-radius:4px;background:linear-gradient(90deg,{ACCENT},#00c9ff);transition:width .6s ease;}}
.alert{{padding:12px 16px;border-radius:12px;font-size:13px;font-weight:500;margin-bottom:10px;display:flex;align-items:flex-start;gap:10px;line-height:1.5;}}
.alert-r{{background:rgba(242,61,79,.08);border:1px solid rgba(242,61,79,.2);color:#ff8a94;}}
.alert-o{{background:rgba(255,156,0,.08);border:1px solid rgba(255,156,0,.2);color:#ffc066;}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r);margin-bottom:16px;overflow:hidden;}}
.card-pad{{padding:20px;}}
.ctitle{{font-size:10px;font-weight:700;color:var(--muted2);letter-spacing:.1em;text-transform:uppercase;margin-bottom:14px;}}
.add-panel{{background:var(--surf2);border:1px solid var(--border);border-radius:var(--r);padding:18px 20px;margin-bottom:16px;}}
.sec-hdr{{display:flex;align-items:center;gap:12px;padding:11px 18px 9px;background:rgba(255,255,255,.018);border-bottom:1px solid {BORDER2};}}
.sec-hdr-icon{{width:26px;height:26px;border-radius:8px;flex-shrink:0;display:flex;align-items:center;justify-content:center;}}
.sec-hdr-name{{flex:1;font-size:11px;font-weight:700;color:var(--muted2);letter-spacing:.03em;text-transform:uppercase;}}
.sec-hdr-total{{font-size:13px;font-weight:800;}}
.sec-badge{{font-size:10px;font-weight:700;padding:2px 7px;border-radius:6px;background:rgba(242,61,79,.14);color:{RED};margin-left:6px;}}
.item-row{{display:flex;align-items:center;gap:14px;padding:13px 18px;border-bottom:1px solid {BORDER2};transition:background .12s;}}
.item-row:last-child{{border-bottom:none;}}
.item-row:hover{{background:rgba(255,255,255,.018);}}
.item-ico{{width:46px;height:46px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;}}
.item-body{{flex:1;min-width:0;}}
.item-name{{font-size:14px;font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:5px;}}
.item-name-paid{{font-size:14px;font-weight:600;color:var(--muted2);text-decoration:line-through;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:5px;}}
.vbadge{{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:700;padding:3px 9px;border-radius:20px;white-space:nowrap;}}
.vb-paid{{background:rgba(0,200,83,.1);color:{GREEN};}}
.vb-venc{{background:rgba(242,61,79,.14);color:{RED};border:1px solid rgba(242,61,79,.25);}}
.vb-hoy{{background:rgba(242,61,79,.12);color:{RED};}}
.vb-prox{{background:rgba(255,156,0,.12);color:{ORANGE};}}
.vb-soon{{background:rgba(251,191,36,.1);color:{YELLOW};}}
.vb-ok{{background:rgba(0,200,83,.08);color:{GREEN};}}
.vb-none{{background:rgba(255,255,255,.05);color:var(--muted2);}}
.item-right{{text-align:right;flex-shrink:0;min-width:90px;}}
.item-monto{{font-size:15px;font-weight:800;color:var(--text);line-height:1;}}
.item-monto-paid{{font-size:15px;font-weight:600;color:var(--muted2);text-decoration:line-through;line-height:1;}}
.item-usd{{font-size:11px;color:var(--muted2);margin-top:4px;}}
.cat-bar-row{{margin-bottom:11px;}}
.cat-bar-top{{display:flex;justify-content:space-between;margin-bottom:4px;font-size:12px;}}
.cat-bar-bg{{height:5px;background:rgba(255,255,255,.06);border-radius:4px;overflow:hidden;}}
.cat-bar-fill{{height:100%;border-radius:4px;}}
.res-row{{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid {BORDER2};font-size:13px;}}
.res-row:last-child{{border-bottom:none;}}
.res-k{{color:var(--muted2);font-weight:500;}}
.section-divider{{border-top:1px solid var(--border);margin:28px 0 24px;}}
.stTabs [data-baseweb="tab-list"]{{background:transparent !important;border-bottom:1px solid var(--border) !important;gap:0 !important;padding:0 !important;}}
.stTabs [data-baseweb="tab"]{{background:transparent !important;color:var(--muted2) !important;font-family:'Plus Jakarta Sans',sans-serif !important;font-size:13px !important;font-weight:700 !important;border-bottom:2px solid transparent !important;padding:11px 18px !important;margin-bottom:-1px !important;}}
.stTabs [aria-selected="true"]{{color:{ACCENT} !important;border-bottom-color:{ACCENT} !important;}}
.stTabs [data-baseweb="tab-highlight"]{{display:none !important;}}
.stTabs [data-baseweb="tab-panel"]{{padding:16px 0 0 !important;}}
[data-testid="stDataEditorContainer"]{{background:var(--surface) !important;border:1px solid var(--border) !important;border-radius:14px !important;overflow:hidden !important;}}
.stTextInput>div>div>input,.stNumberInput>div>div>input{{background:{SURF2} !important;border:1px solid rgba(255,255,255,.1) !important;border-radius:10px !important;color:{TEXT} !important;font-family:'Plus Jakarta Sans',sans-serif !important;}}
.toast-ok{{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;border-radius:11px;font-size:13px;font-weight:600;margin-bottom:12px;background:rgba(0,200,83,.1);border:1px solid rgba(0,200,83,.2);color:{GREEN};}}
.toast-err{{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;border-radius:11px;font-size:13px;font-weight:600;margin-bottom:12px;background:rgba(242,61,79,.1);border:1px solid rgba(242,61,79,.2);color:{RED};}}
@media (max-width:860px){{.metrics{{grid-template-columns:repeat(2,1fr);}}}}
@media (max-width:560px){{.metrics{{grid-template-columns:1fr 1fr;gap:8px;}}.mval{{font-size:18px;}}.wrap{{padding:0 12px 32px;}}}}
hr{{display:none !important;}}
[data-testid="stVerticalBlock"]>div{{gap:0 !important;}}
</style>
""", unsafe_allow_html=True)

# ── CONEXIÓN ──
@st.cache_resource
def get_gspread():
    scope=["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    try: creds=ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json",scope)
    except Exception: creds=ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"],scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos():
    try:
        hoja=get_gspread().open("Gastos_Henry").sheet1
        data=hoja.get_all_values()
    except Exception as e:
        st.error(f"❌ Error conectando con Google Sheets: {e}"); return pd.DataFrame()
    data=[r for r in data if any(str(c).strip() for c in r)]
    if not data or len(data)<2: return pd.DataFrame()
    headers=["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]
    primera=str(data[0][0]).strip().lower()
    filas=data[1:] if primera in ["categoría","categoria","cat","category"] else data
    filas=[r+[""]*(5-len(r)) for r in filas if len(r)>=2]
    if not filas: return pd.DataFrame()
    df=pd.DataFrame(filas,columns=headers)
    df["Monto (ARS)"]=pd.to_numeric(df["Monto (ARS)"],errors="coerce").fillna(0)
    df["Día Pago"]=pd.to_datetime(df["Día Pago"],errors="coerce").dt.date
    df["Pagado"]=df["Pagado"].apply(lambda x: str(x).strip().upper() in ["TRUE","VERDADERO","✅","SI","SÍ","1"])
    df=df[~((df["Monto (ARS)"]==0)&(df["Ítem"].str.strip()==""))]
    return df.reset_index(drop=True)

@st.cache_data(ttl=600)
def cargar_historial():
    try:
        sh=get_gspread().open("Gastos_Henry")
        hojas=sh.worksheets()
        frames=[]
        for h in hojas:
            data=h.get_all_values()
            data=[r for r in data if any(str(c).strip() for c in r)]
            if not data or len(data)<2: continue
            headers=["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]
            primera=str(data[0][0]).strip().lower()
            filas=data[1:] if primera in ["categoría","categoria","cat","category"] else data
            filas=[r+[""]*(5-len(r)) for r in filas if len(r)>=2]
            if not filas: continue
            df_h=pd.DataFrame(filas,columns=headers)
            df_h["Monto (ARS)"]=pd.to_numeric(df_h["Monto (ARS)"],errors="coerce").fillna(0)
            df_h=df_h[~((df_h["Monto (ARS)"]==0)&(df_h["Ítem"].str.strip()==""))]
            df_h["Mes"]=h.title
            frames.append(df_h)
        return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_dolar():
    try: return float(requests.get("https://dolarapi.com/v1/dolares/blue",timeout=5).json()["venta"])
    except Exception: return 1450.0

def categorizar_inteligente(item):
    i=str(item).lower()
    if any(x in i for x in ["mercadocredito","mercado credito","tarjeta","visa","mastercard","amex","crédito","credito","banco","financiamiento","financiación","financiacion","cuota"]): return "💳 Crédito/Financiación"
    elif any(x in i for x in ["luz","edenor","edesur","agua","aysa","gas","metrogas"]): return "⚡ Servicios"
    elif any(x in i for x in ["super","coto","carrefour","dia","jumbo","disco","mercado","almacén","chino"]): return "🛒 Supermercado"
    elif any(x in i for x in ["alquiler","expensas","abl","limpieza"]): return "🏠 Hogar"
    elif any(x in i for x in ["nafta","ypf","shell","axion","uber","cabify","taxi","peaje","sube","transporte"]): return "🚗 Transporte"
    elif any(x in i for x in ["netflix","spotify","prime","hbo","disney","youtube","telecentro","fibertel","internet","claro","personal","movistar","meli","google","apple one","vpn"]): return "📺 Suscripciones"
    elif any(x in i for x in ["gym","gimnasio","megatlon","sportclub","crossfit"]): return "🏋 Fitness"
    elif any(x in i for x in ["farmacia","osde","swiss","galeno","médico","salud","depilife"]): return "🏥 Salud"
    elif any(x in i for x in ["mc","burger","pedidosya","rappi","helado","pizza","restaurante","bar","café"]): return "🍔 Comida/Delivery"
    elif any(x in i for x in ["ropa","zapat","zara","dafiti","peluquería","estética"]): return "🎭 Personal/Ocio"
    elif any(x in i for x in ["vuelo","pasaje","hotel","airbnb"]): return "✈ Viajes"
    else: return "🔘 Otros"

def fmt_ars(n):
    s=f"{n:,.0f}".replace(",","X").replace(".",",").replace("X",".")
    return f"$ {s}"

def fmt_k(n):
    if n>=1_000_000: return f"$ {n/1_000_000:.1f}M"
    if n>=1_000: return f"$ {n/1_000:.0f}k"
    return fmt_ars(n)

def fmt_usd(n,d): return f"U$S {n/d:,.0f}" if d>0 else "U$S —"

def venc_html(row):
    if row["Pagado"]: return '<span class="vbadge vb-paid">✓ Pagado</span>'
    dia=row["Día Pago"]
    if pd.isna(dia): return '<span class="vbadge vb-none">⚪ Sin fecha</span>'
    diff=(dia-date.today()).days
    fmt_dia=dia.strftime("%-d %b")
    if diff<0: return f'<span class="vbadge vb-venc">🔴 Vencido · {fmt_dia}</span>'
    if diff==0: return f'<span class="vbadge vb-hoy">🔴 Hoy · {fmt_dia}</span>'
    if diff<=3: return f'<span class="vbadge vb-prox">🟡 {diff}d · {fmt_dia}</span>'
    if diff<=10: return f'<span class="vbadge vb-soon">🟡 {diff}d · {fmt_dia}</span>'
    return f'<span class="vbadge vb-ok">🟢 {fmt_dia}</span>'

def procesar(df_base,dolar):
    df=df_base.copy()
    df["Categoría"]=df["Ítem"].apply(categorizar_inteligente)
    total=df["Monto (ARS)"].sum()
    df["Peso (%)"]=(df["Monto (ARS)"]/total).fillna(0) if total>0 else 0
    df["USD"]=(df["Monto (ARS)"]/dolar).round(2) if dolar>0 else 0
    df["Cat."]=df["Categoría"]
    return df.sort_values(["Pagado","Día Pago"],ascending=[True,True],na_position="last")

def guardar_hoja(df_guardar):
    df_up=df_guardar.copy()
    df_up["Categoría"]=df_up["Ítem"].apply(categorizar_inteligente)
    df_up=df_up[["Categoría","Ítem","Monto (ARS)","Día Pago","Pagado"]]
    df_up["Día Pago"]=df_up["Día Pago"].apply(lambda x: str(x) if pd.notnull(x) else "")
    df_up["Pagado"]=df_up["Pagado"].apply(lambda x: "TRUE" if x else "FALSE")
    hoja=get_gspread().open("Gastos_Henry").sheet1
    hoja.clear(); hoja.append_row(df_up.columns.tolist()); hoja.append_rows(df_up.values.tolist())
    st.cache_data.clear()

def marcar_pagado(idx):
    df_act=cargar_datos().copy()
    if idx<len(df_act):
        df_act.at[idx,"Pagado"]=True
        guardar_hoja(df_act)

def exportar_excel(df):
    output=io.BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        df_exp=df[["Cat.","Ítem","Monto (ARS)","USD","Día Pago","Pagado"]].copy()
        df_exp.columns=["Categoría","Ítem","Monto ARS","USD","Vencimiento","Pagado"]
        df_exp.to_excel(writer,index=False,sheet_name="Gastos")
        resumen=df.groupby("Cat.")["Monto (ARS)"].sum().reset_index()
        resumen.columns=["Categoría","Total ARS"]
        resumen.to_excel(writer,index=False,sheet_name="Resumen")
    return output.getvalue()

# ── CARGA ──
dolar=get_dolar()
df_base=cargar_datos()

if not df_base.empty:
    df=procesar(df_base,dolar)
    total_ars=df["Monto (ARS)"].sum()
    pagado_ars=df[df["Pagado"]==True]["Monto (ARS)"].sum()
    pend_ars=total_ars-pagado_ars
    pct=int(pagado_ars/total_ars*100) if total_ars>0 else 0
    vencidos=df[(df["Pagado"]==False)&df["Día Pago"].notna()&(df["Día Pago"]<date.today())]
    proximos=df[(df["Pagado"]==False)&df["Día Pago"].notna()&(df["Día Pago"]>=date.today())&(df["Día Pago"]<=date.today()+timedelta(days=3))]
    por_cat=df.groupby("Cat.")["Monto (ARS)"].sum().reset_index().sort_values("Monto (ARS)",ascending=False)
else:
    df=por_cat=pd.DataFrame()
    total_ars=pagado_ars=pend_ars=pct=0
    vencidos=proximos=pd.DataFrame()

# ── HEADER ──
sun_rays=""
for i in range(16):
    angle=i*(360/16)-90; rad=math.radians(angle)
    x1=16+math.cos(rad)*7; y1=16+math.sin(rad)*7
    x2=16+math.cos(rad)*14; y2=16+math.sin(rad)*14
    sun_rays+=f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#d4960e" stroke-width="1.8" stroke-linecap="round"/>'

meses=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
hoy=date.today()
hoy_str=f"{hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

st.markdown('<div class="wrap">', unsafe_allow_html=True)
st.markdown(f"""
<div class="hdr">
  <div style="position:absolute;right:0;top:0;bottom:0;width:280px;pointer-events:none;z-index:0;display:flex;flex-direction:column;border-radius:0 0 0 50px;overflow:hidden;-webkit-mask-image:linear-gradient(to right,transparent 0%,rgba(0,0,0,.1) 20%,rgba(0,0,0,.26) 50%,rgba(0,0,0,.26) 72%,transparent 100%);mask-image:linear-gradient(to right,transparent 0%,rgba(0,0,0,.1) 20%,rgba(0,0,0,.26) 50%,rgba(0,0,0,.26) 72%,transparent 100%);">
    <div style="flex:1;background:linear-gradient(135deg,#3d87c0,#74acdf)"></div>
    <div style="flex:1;background:#b0b0b0;display:flex;align-items:center;justify-content:center"><svg width="34" height="34" viewBox="0 0 32 32">{sun_rays}<circle cx="16" cy="16" r="5.5" fill="#d4960e"/><circle cx="16" cy="16" r="3.2" fill="#9a6608" opacity="0.55"/></svg></div>
    <div style="flex:1;background:linear-gradient(135deg,#74acdf,#3d87c0)"></div>
  </div>
  <div style="position:relative;z-index:2"><div class="hdr-brand">Finanzas <span>AR</span></div><div class="hdr-date">{hoy_str}</div></div>
  <div style="position:relative;z-index:2"><div class="dolar-chip"><div class="dolar-lbl">USD Blue</div><div class="dolar-val">${dolar:,.0f}</div></div></div>
</div>
""", unsafe_allow_html=True)

# ── NAV — solo 2 botones ──
st.markdown('<div class="nav-grid">', unsafe_allow_html=True)
_,n1,n2,_=st.columns([1,0.4,0.4,1])
with n1:
    if st.button("🏠  Inicio",type="primary" if st.session_state.screen=="inicio" else "secondary",use_container_width=True):
        st.session_state.screen="inicio"; st.rerun()
with n2:
    if st.button("📋  Gastos",type="primary" if st.session_state.screen=="gastos" else "secondary",use_container_width=True):
        st.session_state.screen="gastos"; st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# PANTALLA: INICIO
# ══════════════════════════════════════════════
if st.session_state.screen=="inicio":

    # Alertas
    if not vencidos.empty:
        items_v=" · ".join(f"<strong>{r['Ítem']}</strong> ({fmt_ars(r['Monto (ARS)'])})" for _,r in vencidos.iterrows())
        st.markdown(f'<div class="alert alert-r">🔴&nbsp; {len(vencidos)} pago{"s" if len(vencidos)>1 else ""} vencido{"s" if len(vencidos)>1 else ""} — {items_v}</div>',unsafe_allow_html=True)
    if not proximos.empty:
        items_p=" · ".join(f"<strong>{r['Ítem']}</strong> ({r['Día Pago'].strftime('%-d %b')})" for _,r in proximos.iterrows())
        st.markdown(f'<div class="alert alert-o">🟡&nbsp; Próximos 3 días — {items_p}</div>',unsafe_allow_html=True)

    # Métricas
    st.markdown(f"""<div class="metrics">
      <div class="mcard mc-a"><div class="mlbl">📊 Total del mes</div><div class="mval">{fmt_ars(total_ars)}</div><div class="msub">{fmt_usd(total_ars,dolar)}</div></div>
      <div class="mcard mc-g"><div class="mlbl">✅ Pagado</div><div class="mval" style="color:{GREEN}">{fmt_ars(pagado_ars)}</div><div class="msub">{fmt_usd(pagado_ars,dolar)}</div></div>
      <div class="mcard mc-r"><div class="mlbl">⏳ Pendiente</div><div class="mval" style="color:{RED}">{fmt_ars(pend_ars)}</div><div class="msub">{fmt_usd(pend_ars,dolar)}</div></div>
      <div class="mcard mc-o"><div class="mlbl">📈 Cubierto</div><div class="mpct">{pct}%</div><div class="pbar"><div class="pfill" style="width:{pct}%"></div></div></div>
    </div>""",unsafe_allow_html=True)

    # Botón agregar gasto
    lbl="✕  Cancelar" if st.session_state.show_add else "＋  Agregar gasto"
    if st.button(lbl,type="secondary" if st.session_state.show_add else "primary",use_container_width=True):
        st.session_state.show_add=not st.session_state.show_add; st.rerun()
    st.markdown("<div style='height:10px'></div>",unsafe_allow_html=True)

    # Panel agregar rápido
    if st.session_state.show_add:
        st.markdown('<div class="add-panel">',unsafe_allow_html=True)
        st.markdown('<div class="ctitle" style="margin-bottom:12px">Nuevo gasto</div>',unsafe_allow_html=True)
        a1,a2,a3,a4=st.columns([2,1.2,1.2,0.8])
        with a1: new_item=st.text_input("Desc",placeholder="Ej: Netflix",label_visibility="collapsed",key="new_item")
        with a2: new_monto=st.number_input("Monto",min_value=0,step=100,label_visibility="collapsed",key="new_monto")
        with a3: new_fecha=st.date_input("Fecha",value=None,label_visibility="collapsed",key="new_fecha")
        with a4: agregar=st.button("Agregar →",type="primary",use_container_width=True)
        if agregar:
            if not new_item.strip(): st.markdown('<div class="toast-err">✗ Ingresá una descripción</div>',unsafe_allow_html=True)
            elif new_monto<=0: st.markdown('<div class="toast-err">✗ El monto debe ser mayor a 0</div>',unsafe_allow_html=True)
            else:
                nueva=pd.DataFrame([{"Categoría":categorizar_inteligente(new_item),"Ítem":new_item.strip(),"Monto (ARS)":float(new_monto),"Día Pago":new_fecha,"Pagado":False}])
                df_act=pd.concat([df_base,nueva],ignore_index=True)
                try: guardar_hoja(df_act); st.session_state.show_add=False; st.rerun()
                except Exception as e: st.markdown(f'<div class="toast-err">✗ Error: {e}</div>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    if df.empty:
        st.markdown(f'<div class="card card-pad" style="text-align:center;padding:48px;color:{MUTED2}"><div style="font-size:36px;margin-bottom:10px">📭</div><div style="font-weight:600">Sin datos. Usá el botón + para agregar tu primer gasto.</div></div>',unsafe_allow_html=True)
    else:
        # Buscador y filtro
        sb1,sb2=st.columns([1,2])
        with sb1:
            busqueda=st.text_input("🔍",placeholder="Buscar gasto...",label_visibility="collapsed",key="busqueda_input")
        with sb2:
            cats_disponibles=["Todas"]+sorted(df["Cat."].unique().tolist())
            filtro=st.selectbox("Categoría",cats_disponibles,label_visibility="collapsed",key="filtro_select")
        st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)

        df_vista=df.copy()
        if filtro!="Todas": df_vista=df_vista[df_vista["Cat."]==filtro]
        if busqueda.strip(): df_vista=df_vista[df_vista["Ítem"].str.contains(busqueda.strip(),case=False,na=False)]

        col_izq,col_der=st.columns([1.65,1],gap="medium")

        with col_izq:
            cats_orden=df_vista.groupby("Cat.").apply(lambda g: g["Pagado"].eq(False).sum()).sort_values(ascending=False).index.tolist()
            st.markdown('<div class="card">',unsafe_allow_html=True)
            st.markdown('<div style="padding:16px 18px 4px" class="ctitle">Detalle de gastos</div>',unsafe_allow_html=True)
            if df_vista.empty:
                st.markdown(f'<div style="padding:24px;text-align:center;color:{MUTED2};font-size:13px">Sin resultados</div>',unsafe_allow_html=True)
            else:
                for cat in cats_orden:
                    df_cat=df_vista[df_vista["Cat."]==cat]
                    t_cat=df_cat["Monto (ARS)"].sum(); color=cat_color(cat)
                    n_pend=int(df_cat["Pagado"].eq(False).sum())
                    badge=f'<span class="sec-badge">{n_pend} pend.</span>' if n_pend>0 else ""
                    st.markdown(f'<div class="sec-hdr"><div class="sec-hdr-icon" style="background:{color}25">{svg_icon(cat,color,size=16)}</div><span class="sec-hdr-name">{cat}{badge}</span><span class="sec-hdr-total" style="color:{color}">{fmt_ars(t_cat)}</span></div>',unsafe_allow_html=True)
                    for idx,row in df_cat.iterrows():
                        paid=row["Pagado"]; monto=row["Monto (ARS)"]
                        opacity="0.45" if paid else "1"
                        nc="item-name-paid" if paid else "item-name"
                        mc="item-monto-paid" if paid else "item-monto"
                        bg="10" if paid else "20"
                        st.markdown(f'<div class="item-row" style="opacity:{opacity}"><div class="item-ico" style="background:{color}{bg}">{svg_icon(cat,color,size=22)}</div><div class="item-body"><div class="{nc}">{row["Ítem"]}</div><div>{venc_html(row)}</div></div><div class="item-right"><div class="{mc}">{fmt_ars(monto)}</div><div class="item-usd">{fmt_usd(monto,dolar)}</div></div></div>',unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

            # Marcar pagado
            pend_items=df_vista[df_vista["Pagado"]==False]
            if not pend_items.empty:
                with st.expander(f"✓ Marcar como pagado ({len(pend_items)} pendientes)"):
                    for idx,row in pend_items.iterrows():
                        col_n,col_b=st.columns([3,1])
                        with col_n: st.markdown(f'<div style="font-size:13px;font-weight:600;padding:6px 0">{row["Ítem"]} — {fmt_ars(row["Monto (ARS)"])}</div>',unsafe_allow_html=True)
                        with col_b:
                            if st.button("✓ Pagado",key=f"pay_{idx}",use_container_width=True):
                                try: marcar_pagado(idx); st.rerun()
                                except Exception as e: st.error(str(e))

        with col_der:
            # Donut
            fig=go.Figure(go.Pie(labels=por_cat["Cat."],values=por_cat["Monto (ARS)"],hole=0.62,marker=dict(colors=[cat_color(c) for c in por_cat["Cat."]],line=dict(color=SURFACE,width=3)),textinfo="none",hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",direction="clockwise",sort=True))
            fig.add_annotation(text=f"<b>{fmt_k(total_ars)}</b>",x=0.5,y=0.56,font=dict(size=14,color=TEXT,family="Plus Jakarta Sans"),showarrow=False)
            fig.add_annotation(text=fmt_usd(total_ars,dolar),x=0.5,y=0.42,font=dict(size=10,color=MUTED2,family="Plus Jakarta Sans"),showarrow=False)
            fig.update_layout(showlegend=True,legend=dict(orientation="v",x=1.02,y=0.5,font=dict(color=MUTED2,size=10,family="Plus Jakarta Sans"),bgcolor="rgba(0,0,0,0)"),height=270,margin=dict(t=8,b=8,l=8,r=95),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG)
            st.markdown('<div class="card card-pad"><div class="ctitle">Distribución</div>',unsafe_allow_html=True)
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            st.markdown(f'<div style="display:flex;border-top:1px solid {BORDER2};padding-top:14px;margin-top:4px"><div style="flex:1;text-align:center"><div style="font-size:9px;font-weight:700;color:{MUTED2};letter-spacing:.08em;text-transform:uppercase">Pagado</div><div style="font-size:16px;font-weight:800;color:{GREEN};margin-top:4px">{fmt_k(pagado_ars)}</div></div><div style="width:1px;background:{BORDER2}"></div><div style="flex:1;text-align:center"><div style="font-size:9px;font-weight:700;color:{MUTED2};letter-spacing:.08em;text-transform:uppercase">Pendiente</div><div style="font-size:16px;font-weight:800;color:{RED};margin-top:4px">{fmt_k(pend_ars)}</div></div></div>',unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

            n_pag=int(df["Pagado"].sum()); n_pend=len(df)-n_pag
            mayor=df.loc[df["Monto (ARS)"].idxmax(),"Ítem"] if not df.empty else "—"
            mayor_m=df["Monto (ARS)"].max() if not df.empty else 0
            st.markdown(f'<div class="card card-pad"><div class="ctitle">Resumen</div><div class="res-row"><span class="res-k">Total ítems</span><span style="font-weight:700">{len(df)}</span></div><div class="res-row"><span class="res-k">Pagados</span><span style="font-weight:700;color:{GREEN}">{n_pag}</span></div><div class="res-row"><span class="res-k">Pendientes</span><span style="font-weight:700;color:{ORANGE}">{n_pend}</span></div><div class="res-row"><span class="res-k">Vencidos</span><span style="font-weight:700;color:{RED}">{len(vencidos)}</span></div><div class="res-row"><span class="res-k">Próx. 3 días</span><span style="font-weight:700;color:{YELLOW}">{len(proximos)}</span></div><div class="res-row" style="flex-direction:column;align-items:flex-start;gap:2px;border-bottom:none"><span class="res-k">Mayor gasto</span><span style="font-weight:700;color:{TEXT}">{mayor}</span><span style="font-size:11px;color:{MUTED2}">{fmt_ars(mayor_m)}</span></div></div>',unsafe_allow_html=True)

            pend_cat=df[df["Pagado"]==False].groupby("Cat.")["Monto (ARS)"].sum().sort_values(ascending=False)
            if not pend_cat.empty:
                max_p=pend_cat.max()
                st.markdown('<div class="card card-pad"><div class="ctitle">Pendiente por categoría</div>',unsafe_allow_html=True)
                for cat,val in pend_cat.items():
                    pct_bar=int(val/max_p*100) if max_p>0 else 0; color=cat_color(cat)
                    st.markdown(f'<div class="cat-bar-row"><div class="cat-bar-top"><span style="font-weight:600;color:{TEXT}">{cat}</span><span style="font-weight:700;color:{color}">{fmt_ars(val)}</span></div><div class="cat-bar-bg"><div class="cat-bar-fill" style="width:{pct_bar}%;background:{color}"></div></div></div>',unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)

        # ── ANÁLISIS AL FINAL DE INICIO ──
        st.markdown('<div class="section-divider"></div>',unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:10px;font-weight:700;color:{MUTED2};letter-spacing:.1em;text-transform:uppercase;margin-bottom:18px">Análisis del mes</div>',unsafe_allow_html=True)

        # Gráfico horizontal por categoría
        st.markdown('<div class="card card-pad"><div class="ctitle">Gasto por categoría</div>',unsafe_allow_html=True)
        cats_sorted=por_cat.sort_values("Monto (ARS)",ascending=True)
        fig_bar=go.Figure()
        fig_bar.add_trace(go.Bar(y=cats_sorted["Cat."],x=cats_sorted["Monto (ARS)"],orientation="h",marker=dict(color=[cat_color(c) for c in cats_sorted["Cat."]],opacity=0.85),text=[fmt_ars(v) for v in cats_sorted["Monto (ARS)"]],textposition="outside",textfont=dict(color=MUTED2,size=11,family="Plus Jakarta Sans"),hovertemplate="<b>%{y}</b><br>%{x:,.0f}<extra></extra>"))
        fig_bar.update_layout(height=max(260,len(cats_sorted)*44),margin=dict(t=10,b=10,l=10,r=130),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG,xaxis=dict(showgrid=False,showticklabels=False,zeroline=False),yaxis=dict(showgrid=False,tickfont=dict(color=TEXT,size=12,family="Plus Jakarta Sans")),bargap=0.35)
        st.plotly_chart(fig_bar,use_container_width=True,config={"displayModeBar":False})
        st.markdown("</div>",unsafe_allow_html=True)

        # Pagado vs Pendiente apilado
        st.markdown('<div class="card card-pad"><div class="ctitle">Pagado vs Pendiente por categoría</div>',unsafe_allow_html=True)
        df_pag_cat=df[df["Pagado"]==True].groupby("Cat.")["Monto (ARS)"].sum()
        df_pend_cat=df[df["Pagado"]==False].groupby("Cat.")["Monto (ARS)"].sum()
        todas_cats=sorted(set(df_pag_cat.index)|set(df_pend_cat.index))
        fig_stack=go.Figure()
        fig_stack.add_trace(go.Bar(name="Pagado",x=todas_cats,y=[df_pag_cat.get(c,0) for c in todas_cats],marker_color=GREEN,opacity=0.85,hovertemplate="Pagado: %{y:,.0f}<extra></extra>"))
        fig_stack.add_trace(go.Bar(name="Pendiente",x=todas_cats,y=[df_pend_cat.get(c,0) for c in todas_cats],marker_color=RED,opacity=0.75,hovertemplate="Pendiente: %{y:,.0f}<extra></extra>"))
        fig_stack.update_layout(barmode="stack",height=300,margin=dict(t=10,b=80,l=10,r=10),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG,legend=dict(font=dict(color=MUTED2,size=11,family="Plus Jakarta Sans"),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.08),xaxis=dict(tickfont=dict(color=MUTED2,size=10,family="Plus Jakarta Sans"),showgrid=False,tickangle=-30),yaxis=dict(showgrid=False,showticklabels=False))
        st.plotly_chart(fig_stack,use_container_width=True,config={"displayModeBar":False})
        st.markdown("</div>",unsafe_allow_html=True)

        # Historial por mes
        df_hist=cargar_historial()
        if not df_hist.empty and df_hist["Mes"].nunique()>1:
            st.markdown('<div class="card card-pad"><div class="ctitle">Historial por mes</div>',unsafe_allow_html=True)
            hist_resumen=df_hist.groupby("Mes")["Monto (ARS)"].sum().reset_index()
            fig_hist=go.Figure()
            fig_hist.add_trace(go.Bar(x=hist_resumen["Mes"],y=hist_resumen["Monto (ARS)"],marker_color=ACCENT,opacity=0.85,text=[fmt_ars(v) for v in hist_resumen["Monto (ARS)"]],textposition="outside",textfont=dict(color=MUTED2,size=11),hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
            fig_hist.update_layout(height=260,margin=dict(t=10,b=10,l=10,r=10),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG,xaxis=dict(showgrid=False,tickfont=dict(color=MUTED2,size=11)),yaxis=dict(showgrid=False,showticklabels=False),bargap=0.3)
            st.plotly_chart(fig_hist,use_container_width=True,config={"displayModeBar":False})
            st.markdown("</div>",unsafe_allow_html=True)

        # Top 5
        st.markdown('<div class="card card-pad"><div class="ctitle">Top 5 gastos más altos</div>',unsafe_allow_html=True)
        top5=df.nlargest(5,"Monto (ARS)")
        for _,row in top5.iterrows():
            color=cat_color(row["Cat."]); pct_top=int(row["Monto (ARS)"]/total_ars*100) if total_ars>0 else 0
            st.markdown(f'<div class="item-row"><div class="item-ico" style="background:{color}20">{svg_icon(row["Cat."],color,size=22)}</div><div class="item-body"><div class="item-name">{row["Ítem"]}</div><div style="font-size:11px;color:{MUTED2}">{row["Cat."]} · {pct_top}% del total</div></div><div class="item-right"><div class="item-monto">{fmt_ars(row["Monto (ARS)"])}</div><div class="item-usd">{fmt_usd(row["Monto (ARS)"],dolar)}</div></div></div>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        # Exportar al final
        _,ce,_=st.columns([1,1,1])
        with ce: st.download_button(label="⬇  Exportar Excel completo",data=exportar_excel(df),file_name=f"gastos_{hoy.strftime('%Y_%m')}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)

# ══════════════════════════════════════════════
# PANTALLA: GASTOS
# ══════════════════════════════════════════════
elif st.session_state.screen=="gastos":
    if df.empty:
        st.markdown(f'<div class="card card-pad" style="text-align:center;padding:48px;color:{MUTED2}"><div style="font-size:36px;margin-bottom:10px">📭</div><div style="font-weight:600">Sin datos en Google Sheets.</div></div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:13px;color:{MUTED2};margin-bottom:14px;font-weight:500">Editá, agregá o marcá pagos acá. Los cambios se reflejan en Inicio al guardar.</div>',unsafe_allow_html=True)
        tab_todos,tab_pend,tab_pag=st.tabs([f"Todos  {len(df)}",f"Pendientes  {len(df[df['Pagado']==False])}",f"Pagados  {len(df[df['Pagado']==True])}"])
        COL_CONFIG={"Pagado":st.column_config.CheckboxColumn("✓",width="small"),"Ítem":st.column_config.TextColumn("Ítem"),"Monto (ARS)":st.column_config.NumberColumn("ARS",format="$ %d"),"USD":st.column_config.NumberColumn("USD",format="U$S %.0f",disabled=True,width="small"),"Día Pago":st.column_config.DateColumn("Vencimiento",format="DD/MM/YY")}
        COL_ORDER=("Pagado","Ítem","Monto (ARS)","USD","Día Pago")
        def render_tabla(data,key): return st.data_editor(data,column_config=COL_CONFIG,column_order=COL_ORDER,num_rows="dynamic",use_container_width=True,hide_index=True,key=key)
        with tab_todos: df_edit=render_tabla(df,"t_todos")
        with tab_pend: render_tabla(df[df["Pagado"]==False].copy(),"t_pend")
        with tab_pag: render_tabla(df[df["Pagado"]==True].copy(),"t_pag")
        st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)
        bc1,bc2,bc3=st.columns([2.5,0.8,0.8])
        with bc1:
            if st.button("💾  Guardar y Sincronizar",type="primary",use_container_width=True):
                try: guardar_hoja(df_edit); st.markdown('<div class="toast-ok">✓ Cambios guardados en Google Sheets</div>',unsafe_allow_html=True); st.rerun()
                except Exception as e: st.markdown(f'<div class="toast-err">✗ Error: {e}</div>',unsafe_allow_html=True)
        with bc2:
            if st.button("🔄  Recargar",type="secondary",use_container_width=True): st.cache_data.clear(); st.rerun()
        with bc3:
            if not df.empty: st.download_button(label="⬇  Excel",data=exportar_excel(df),file_name=f"gastos_{hoy.strftime('%Y_%m')}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
