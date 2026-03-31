import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.graph_objects as go
import io
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, timedelta

st.set_page_config(page_title="Finanzas AR", page_icon="💳", layout="wide", initial_sidebar_state="collapsed")

for k,v in [("screen","inicio"),("show_add",False),("show_add_ingreso",False)]:
    if k not in st.session_state: st.session_state[k]=v

BG="#000000"
SURFACE="#1C1C1E"
SURF2="#2C2C2E"
SURF3="#3A3A3C"
TEXT="#FFFFFF"
TEXT2="rgba(235,235,245,0.6)"
TEXT3="rgba(235,235,245,0.3)"
SEP="rgba(84,84,88,0.65)"
ACCENT="#0A84FF"
GREEN="#32D74B"
RED="#FF453A"
ORANGE="#FF9F0A"
YELLOW="#FFD60A"
PURPLE="#BF5AF2"
TEAL="#5AC8FA"
PLOTBG="rgba(0,0,0,0)"

CAT_IOS={
    "Servicios":"#FF9F0A","Hogar":"#32D74B","Supermercado":"#30D158",
    "Comida":"#FF453A","Transporte":"#0A84FF","Suscripciones":"#BF5AF2",
    "Fitness":"#FF6B35","Salud":"#32D74B","Credito":"#FF9F0A",
    "Personal":"#5AC8FA","Viajes":"#0A84FF","Otros":"#636366",
}

def cat_color(cat):
    c=str(cat)
    for k,v in CAT_IOS.items():
        if k.lower() in c.lower(): return v
    return "#636366"

def sf_icon(cat, color, size=34):
    c=str(cat).lower(); s=size; r=s*0.22
    if "servicio" in c or "luz" in c or "gas" in c:
        icon=f'<polygon points="{s*.6},{s*.08} {s*.32},{s*.52} {s*.52},{s*.52} {s*.4},{s*.92} {s*.68},{s*.45} {s*.48},{s*.45}" fill="white"/>'
    elif "hogar" in c or "alquiler" in c:
        icon=f'<polygon points="{s*.5},{s*.15} {s*.85},{s*.48} {s*.77},{s*.48} {s*.77},{s*.82} {s*.23},{s*.82} {s*.23},{s*.48} {s*.15},{s*.48}" fill="white"/><rect x="{s*.4}" y="{s*.58}" width="{s*.2}" height="{s*.24}" rx="{s*.04}" fill="{color}" opacity="0.8"/>'
    elif "super" in c or "mercado" in c:
        icon=f'<path d="M{s*.12},{s*.2} L{s*.24},{s*.2} L{s*.38},{s*.62} L{s*.78},{s*.62} L{s*.88},{s*.32} L{s*.32},{s*.32}" stroke="white" stroke-width="{s*.07}" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="{s*.38}" cy="{s*.76}" r="{s*.07}" fill="white"/><circle cx="{s*.7}" cy="{s*.76}" r="{s*.07}" fill="white"/>'
    elif "credito" in c or "tarjeta" in c or "financ" in c:
        icon=f'<rect x="{s*.1}" y="{s*.28}" width="{s*.8}" height="{s*.44}" rx="{s*.07}" fill="white" opacity="0.9"/><rect x="{s*.1}" y="{s*.4}" width="{s*.8}" height="{s*.11}" fill="{color}"/><rect x="{s*.16}" y="{s*.56}" width="{s*.18}" height="{s*.08}" rx="{s*.03}" fill="{color}" opacity="0.7"/>'
    elif "suscripcion" in c:
        icon=f'<rect x="{s*.12}" y="{s*.18}" width="{s*.76}" height="{s*.5}" rx="{s*.07}" fill="white" opacity="0.9"/><rect x="{s*.2}" y="{s*.26}" width="{s*.6}" height="{s*.34}" rx="{s*.04}" fill="{color}"/><polygon points="{s*.38},{s*.36} {s*.38},{s*.5} {s*.58},{s*.43}" fill="white"/>'
    elif "transporte" in c or "nafta" in c:
        icon=f'<rect x="{s*.1}" y="{s*.44}" width="{s*.8}" height="{s*.28}" rx="{s*.07}" fill="white" opacity="0.9"/><path d="M{s*.24},{s*.44} L{s*.34},{s*.24} L{s*.66},{s*.24} L{s*.76},{s*.44}" fill="white" opacity="0.9"/><circle cx="{s*.28}" cy="{s*.76}" r="{s*.09}" fill="{color}"/><circle cx="{s*.28}" cy="{s*.76}" r="{s*.045}" fill="white"/><circle cx="{s*.72}" cy="{s*.76}" r="{s*.09}" fill="{color}"/><circle cx="{s*.72}" cy="{s*.76}" r="{s*.045}" fill="white"/>'
    elif "salud" in c or "farmac" in c:
        icon=f'<rect x="{s*.4}" y="{s*.12}" width="{s*.2}" height="{s*.76}" rx="{s*.06}" fill="white"/><rect x="{s*.12}" y="{s*.4}" width="{s*.76}" height="{s*.2}" rx="{s*.06}" fill="white"/>'
    elif "fitness" in c or "gym" in c:
        icon=f'<rect x="{s*.06}" y="{s*.38}" width="{s*.14}" height="{s*.24}" rx="{s*.05}" fill="white"/><rect x="{s*.8}" y="{s*.38}" width="{s*.14}" height="{s*.24}" rx="{s*.05}" fill="white"/><rect x="{s*.18}" y="{s*.44}" width="{s*.64}" height="{s*.12}" rx="{s*.04}" fill="white"/>'
    elif "comida" in c or "delivery" in c:
        icon=f'<rect x="{s*.15}" y="{s*.3}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/><rect x="{s*.15}" y="{s*.46}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/><rect x="{s*.15}" y="{s*.62}" width="{s*.7}" height="{s*.1}" rx="{s*.04}" fill="white"/>'
    elif "personal" in c or "ocio" in c:
        icon=f'<circle cx="{s*.5}" cy="{s*.35}" r="{s*.17}" fill="white"/><path d="M{s*.2},{s*.85} Q{s*.2},{s*.6} {s*.5},{s*.6} Q{s*.8},{s*.6} {s*.8},{s*.85}" fill="white"/>'
    elif "viaje" in c:
        icon=f'<path d="M{s*.5},{s*.1} L{s*.88},{s*.58} L{s*.7},{s*.53} L{s*.64},{s*.82} L{s*.5},{s*.72} L{s*.36},{s*.82} L{s*.3},{s*.53} L{s*.12},{s*.58} Z" fill="white" opacity="0.9"/>'
    else:
        icon=f'<circle cx="{s*.5}" cy="{s*.38}" r="{s*.16}" fill="white" opacity="0.9"/><path d="M{s*.24},{s*.82} Q{s*.24},{s*.6} {s*.5},{s*.6} Q{s*.76},{s*.6} {s*.76},{s*.82}" fill="white" opacity="0.9"/>'
    return f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg"><rect width="{s}" height="{s}" rx="{r}" fill="{color}"/>{icon}</svg>'

st.markdown(f"""
<style>
:root{{
  --bg:{BG};--surface:{SURFACE};--surf2:{SURF2};--surf3:{SURF3};
  --text:{TEXT};--text2:{TEXT2};--text3:{TEXT3};--sep:{SEP};
  --accent:{ACCENT};--green:{GREEN};--red:{RED};--orange:{ORANGE};
}}
html,body,[class*="css"],.stApp{{
  font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Helvetica Neue",Arial,sans-serif !important;
  background:{BG} !important;color:{TEXT} !important;
}}
*{{box-sizing:border-box;-webkit-font-smoothing:antialiased;}}
#MainMenu,footer,header,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{{display:none !important;}}
[data-testid="stBottom"],[data-testid="stBottomBlockContainer"]{{display:none !important;height:0 !important;overflow:hidden !important;}}
.stBottomContainer,.stChatFloatingInputContainer{{display:none !important;}}
.block-container{{padding:0 !important;max-width:100% !important;}}
.wrap{{max-width:980px;margin:0 auto;padding:0 16px 80px;}}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stBaseButton-secondary"]){{
  display:none !important;height:0 !important;min-height:0 !important;
  overflow:hidden !important;margin:0 !important;padding:0 !important;
  visibility:hidden !important;position:absolute !important;
}}
.ios-hdr{{
  position:sticky;top:0;z-index:100;
  background:rgba(0,0,0,0.8);
  backdrop-filter:saturate(180%) blur(20px);
  -webkit-backdrop-filter:saturate(180%) blur(20px);
  border-bottom:0.5px solid rgba(255,255,255,0.1);
  padding:16px 16px 12px;margin:0 -16px 20px;
}}
.ios-hdr-top{{display:flex;justify-content:space-between;align-items:flex-start;}}
.ios-title{{font-size:34px;font-weight:700;letter-spacing:-.02em;color:{TEXT};line-height:1.1;}}
.ios-title span{{color:{ACCENT};}}
.ios-date{{font-size:13px;color:{TEXT2};font-weight:400;margin-top:3px;}}
.dolar-pill{{background:{SURF2};border-radius:20px;padding:7px 14px;text-align:center;}}
.dolar-lbl{{font-size:9px;color:{TEXT2};letter-spacing:.06em;text-transform:uppercase;font-weight:600;}}
.dolar-val{{font-size:17px;font-weight:700;color:{ACCENT};margin-top:1px;letter-spacing:-.01em;}}
.stButton>button[kind="primary"]{{
  background:{ACCENT} !important;color:#fff !important;border:none !important;
  border-radius:14px !important;padding:11px 20px !important;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif !important;
  font-size:15px !important;font-weight:600 !important;
  box-shadow:none !important;transition:transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.15s ease !important;
}}
.stButton>button[kind="primary"]:hover{{opacity:.82 !important;}}
.stButton>button[kind="secondary"]{{
  background:{SURF2} !important;color:{TEXT2} !important;border:none !important;
  border-radius:14px !important;padding:11px 20px !important;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif !important;
  font-size:15px !important;font-weight:600 !important;
  box-shadow:none !important;transition:transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1), opacity 0.15s ease !important;
}}
.stButton>button[kind="secondary"]:hover{{opacity:.7 !important;}}
.stButton>button:active{{transform:scale(0.96) !important;opacity:0.8 !important;}}
.ios-metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:8px;}}
.ios-metrics-2{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;}}
.ios-card{{background:{SURFACE};border-radius:12px;padding:14px 16px;}}
.ios-card-lbl{{font-size:11px;font-weight:500;color:{TEXT2};margin-bottom:6px;letter-spacing:.01em;}}
.ios-card-val{{font-size:22px;font-weight:700;letter-spacing:-.02em;line-height:1;}}
.ios-card-sub{{font-size:11px;color:{TEXT2};margin-top:4px;}}
.ios-card-pct{{font-size:26px;font-weight:700;}}
.ios-pbar{{height:3px;background:rgba(255,255,255,.1);border-radius:3px;overflow:hidden;margin-top:8px;}}
.ios-pfill{{height:100%;border-radius:3px;}}
.ios-section-label{{font-size:13px;font-weight:400;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;padding:0 4px;margin:18px 0 6px;}}
.ios-group{{background:{SURFACE};border-radius:12px;overflow:hidden;margin-bottom:8px;}}
.ios-group-hdr{{display:flex;align-items:center;gap:10px;padding:10px 14px;border-bottom:0.5px solid {SEP};}}
.ios-group-hdr-lbl{{flex:1;font-size:12px;font-weight:600;color:{TEXT2};letter-spacing:.03em;text-transform:uppercase;}}
.ios-group-hdr-amt{{font-size:13px;font-weight:600;}}
.ios-badge{{font-size:10px;font-weight:700;padding:2px 7px;border-radius:20px;background:rgba(255,69,58,.18);color:{RED};margin-left:4px;}}
.ios-row{{display:flex;align-items:center;gap:12px;padding:11px 14px;position:relative;}}
.ios-row::after{{content:"";position:absolute;bottom:0;left:60px;right:0;height:0.5px;background:{SEP};}}
.ios-row:last-child::after{{display:none;}}
.ios-row-body{{flex:1;min-width:0;}}
.ios-row-name{{font-size:15px;font-weight:400;color:{TEXT};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ios-row-name-paid{{font-size:15px;font-weight:400;color:{TEXT2};text-decoration:line-through;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ios-row-sub{{font-size:12px;color:{TEXT2};margin-top:2px;}}
.ios-row-right{{text-align:right;flex-shrink:0;}}
.ios-row-amt{{font-size:15px;font-weight:600;color:{TEXT};letter-spacing:-.01em;}}
.ios-row-amt-paid{{font-size:15px;font-weight:400;color:{TEXT2};text-decoration:line-through;}}
.ios-row-usd{{font-size:11px;color:{TEXT2};margin-top:2px;}}
.badge{{display:inline-flex;align-items:center;font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px;white-space:nowrap;}}
.badge-paid{{background:rgba(50,215,75,.15);color:{GREEN};}}
.badge-venc{{background:rgba(255,69,58,.18);color:{RED};}}
.badge-hoy{{background:rgba(255,69,58,.18);color:{RED};}}
.badge-prox{{background:rgba(255,159,10,.15);color:{ORANGE};}}
.badge-soon{{background:rgba(255,214,10,.12);color:{YELLOW};}}
.badge-ok{{background:rgba(50,215,75,.1);color:{GREEN};}}
.badge-none{{background:rgba(99,99,102,.3);color:{TEXT2};}}
.badge-henry{{background:rgba(10,132,255,.15);color:{ACCENT};}}
.badge-jaike{{background:rgba(191,90,242,.15);color:{PURPLE};}}
.ios-alert{{padding:12px 14px;border-radius:12px;font-size:13px;margin-bottom:8px;line-height:1.5;}}
.ios-alert-r{{background:rgba(255,69,58,.12);color:#FF6B63;}}
.ios-alert-o{{background:rgba(255,159,10,.12);color:#FFB340;}}
.ios-alert-g{{background:rgba(50,215,75,.1);color:#3EDD60;}}
.ios-add-panel{{background:{SURFACE};border-radius:12px;padding:16px;margin-bottom:12px;}}
.ios-add-panel-green{{background:{SURFACE};border-radius:12px;padding:16px;margin-bottom:12px;border-left:3px solid {GREEN};}}
.stTextInput>div>div>input,.stNumberInput>div>div>input{{
  background:{SURF2} !important;border:none !important;border-radius:9px !important;
  color:{TEXT} !important;font-size:15px !important;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif !important;
}}
.toast-ok{{display:inline-flex;align-items:center;gap:8px;padding:10px 14px;border-radius:10px;font-size:13px;font-weight:500;margin-bottom:10px;background:rgba(50,215,75,.12);color:{GREEN};}}
.toast-err{{display:inline-flex;align-items:center;gap:8px;padding:10px 14px;border-radius:10px;font-size:13px;font-weight:500;margin-bottom:10px;background:rgba(255,69,58,.12);color:{RED};}}
.res-row{{display:flex;justify-content:space-between;align-items:center;padding:11px 0;border-bottom:0.5px solid {SEP};font-size:15px;}}
.res-row:last-child{{border-bottom:none;}}
.res-k{{color:{TEXT2};font-weight:400;}}
.cat-bar-row{{margin-bottom:10px;}}
.cat-bar-top{{display:flex;justify-content:space-between;margin-bottom:4px;font-size:13px;}}
.cat-bar-bg{{height:3px;background:rgba(255,255,255,.08);border-radius:3px;overflow:hidden;}}
.cat-bar-fill{{height:100%;border-radius:3px;}}
.ios-section-title{{font-size:20px;font-weight:600;color:{TEXT};margin:20px 0 10px;letter-spacing:-.01em;}}
.ingreso-row{{display:flex;align-items:center;gap:12px;padding:11px 14px;position:relative;}}
.ingreso-row::after{{content:"";position:absolute;bottom:0;left:60px;right:0;height:0.5px;background:{SEP};}}
.ingreso-row:last-child::after{{display:none;}}
.stTabs [data-baseweb="tab-list"]{{background:transparent !important;border-bottom:0.5px solid {SEP} !important;gap:0 !important;padding:0 !important;}}
.stTabs [data-baseweb="tab"]{{background:transparent !important;color:{TEXT2} !important;font-size:14px !important;font-weight:500 !important;border-bottom:2px solid transparent !important;padding:10px 16px !important;margin-bottom:-1px !important;}}
.stTabs [aria-selected="true"]{{color:{ACCENT} !important;border-bottom-color:{ACCENT} !important;}}
.stTabs [data-baseweb="tab-highlight"]{{display:none !important;}}
.stTabs [data-baseweb="tab-panel"]{{padding:12px 0 0 !important;}}
[data-testid="stDataEditorContainer"]{{background:{SURFACE} !important;border:none !important;border-radius:12px !important;overflow:hidden !important;}}
@media(max-width:700px){{
  .ios-metrics{{grid-template-columns:repeat(2,1fr);gap:12px;}}
  .ios-metrics > .ios-card:nth-child(3) {{grid-column:span 2;}}
  .ios-metrics-2{{grid-template-columns:1fr;gap:12px;}}
  .ios-title{{font-size:28px;}}
  .wrap{{padding:0 12px 100px;}}
}}
hr{{display:none !important;}}
[data-testid="stVerticalBlock"]>div{{gap:0 !important;}}
.btab-bar{{
  position:fixed !important;bottom:0 !important;left:0 !important;right:0 !important;
  z-index:2147483647 !important;
  display:flex !important;align-items:stretch;
  background:rgba(0,0,0,0.88) !important;
  backdrop-filter:saturate(180%) blur(24px);
  -webkit-backdrop-filter:saturate(180%) blur(24px);
  border-top:0.5px solid rgba(255,255,255,0.14) !important;
  padding-bottom:env(safe-area-inset-bottom,0px) !important;
  height:calc(58px + env(safe-area-inset-bottom,0px)) !important;
  transform:translateZ(0);
  -webkit-transform:translateZ(0);
  will-change:transform;
  isolation:isolate;
}}
.btab{{
  flex:1;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:3px;
  background:transparent;border:none;cursor:pointer;
  padding:8px 4px 0;
  color:{TEXT2};font-size:10px;font-weight:500;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif;
  letter-spacing:.01em;transition:color .12s;
  -webkit-tap-highlight-color:transparent;
}}
.btab:active{{opacity:.6;}}
.btab-active{{color:{ACCENT} !important;}}
.btab-ico{{width:22px;height:22px;fill:currentColor;transition:color .12s;}}
</style>""", unsafe_allow_html=True)

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
        st.error(f"Error conectando con Google Sheets: {e}")
        st.stop() # CORRECCIÓN: Detiene la app si falla para no borrar datos
    data=[r for r in data if any(str(c).strip() for c in r)]
    if not data or len(data)<2: return pd.DataFrame()
    headers=["Categoria","Item","Monto (ARS)","Dia Pago","Pagado"]
    primera=str(data[0][0]).strip().lower()
    filas=data[1:] if primera in ["categoria","cat","category"] else data
    filas=[r+[""]*(5-len(r)) for r in filas if len(r)>=2]
    if not filas: return pd.DataFrame()
    df=pd.DataFrame(filas,columns=headers)
    df["Monto (ARS)"]=pd.to_numeric(df["Monto (ARS)"],errors="coerce").fillna(0)
    df["Dia Pago"]=pd.to_datetime(df["Dia Pago"],errors="coerce").dt.date
    df["Pagado"]=df["Pagado"].apply(lambda x: str(x).strip().upper() in ["TRUE","VERDADERO","SI","1"])
    df=df[~((df["Monto (ARS)"]==0)&(df["Item"].str.strip()==""))]
    return df.reset_index(drop=True)

@st.cache_data(ttl=600)
def cargar_ingresos():
    try:
        sh=get_gspread().open("Gastos_Henry")
        hojas_nombres=[h.title for h in sh.worksheets()]
        if "Ingresos" not in hojas_nombres:
            ws=sh.add_worksheet(title="Ingresos",rows=200,cols=8)
            ws.append_row(["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha"])
            return pd.DataFrame()
        ws=sh.worksheet("Ingresos")
        data=ws.get_all_values()
        if not data or len(data)<2: return pd.DataFrame()
        headers=["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha"]
        filas=data[1:]
        filas=[r+[""]*(8-len(r)) for r in filas if len(r)>=2]
        if not filas: return pd.DataFrame()
        df=pd.DataFrame(filas,columns=headers)
        df["Monto ARS"]=pd.to_numeric(df["Monto ARS"],errors="coerce").fillna(0)
        df["Monto USD"]=pd.to_numeric(df["Monto USD"],errors="coerce").fillna(0)
        df["Monto Original"]=pd.to_numeric(df["Monto Original"],errors="coerce").fillna(0)
        df["Tasa USD/ARS"]=pd.to_numeric(df["Tasa USD/ARS"],errors="coerce").fillna(0)
        df["Fecha"]=pd.to_datetime(df["Fecha"],errors="coerce").dt.date
        df=df[df["Monto ARS"]>0]
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"Error conectando con Ingresos: {e}")
        st.stop() # CORRECCIÓN

@st.cache_data(ttl=600)
def cargar_historial():
    try:
        sh=get_gspread().open("Gastos_Henry")
        hojas=sh.worksheets(); frames=[]
        for h in hojas:
            if h.title=="Ingresos": continue
            data=h.get_all_values()
            data=[r for r in data if any(str(c).strip() for c in r)]
            if not data or len(data)<2: continue
            headers=["Categoria","Item","Monto (ARS)","Dia Pago","Pagado"]
            primera=str(data[0][0]).strip().lower()
            filas=data[1:] if primera in ["categoria","cat","category"] else data
            filas=[r+[""]*(5-len(r)) for r in filas if len(r)>=2]
            if not filas: continue
            df_h=pd.DataFrame(filas,columns=headers)
            df_h["Monto (ARS)"]=pd.to_numeric(df_h["Monto (ARS)"],errors="coerce").fillna(0)
            df_h=df_h[~((df_h["Monto (ARS)"]==0)&(df_h["Item"].str.strip()==""))]
            df_h["Mes"]=h.title; frames.append(df_h)
        return pd.concat(frames,ignore_index=True) if frames else pd.DataFrame()
    except Exception as e:
        st.error(f"Error conectando con Historial: {e}")
        st.stop() # CORRECCIÓN

@st.cache_data(ttl=300)
def get_dolar():
    try: return float(requests.get("https://dolarapi.com/v1/dolares/blue",timeout=5).json()["venta"])
    except Exception: return 1450.0

@st.cache_data(ttl=3600)
def get_dolar_tendencia():
    try:
        venta=get_dolar()
        hist=requests.get("https://api.argentinadatos.com/v1/cotizaciones/dolares/blue",timeout=5).json()
        if isinstance(hist,list) and len(hist)>=2:
            ayer=float(hist[-2].get("venta",venta))
            diff=venta-ayer
            pct=round((diff/ayer)*100,2) if ayer>0 else 0.0
            return venta,ayer,diff,pct
        return venta,venta,0.0,0.0
    except Exception:
        return get_dolar(),0,0.0,0.0

def guardar_ingreso(desc,persona,moneda,monto_orig,monto_ars,monto_usd,tasa,fecha):
    sh=get_gspread().open("Gastos_Henry")
    hojas_nombres=[h.title for h in sh.worksheets()]
    if "Ingresos" not in hojas_nombres:
        ws=sh.add_worksheet(title="Ingresos",rows=200,cols=8)
        ws.append_row(["Descripcion","Persona","Moneda","Monto Original","Monto ARS","Monto USD","Tasa USD/ARS","Fecha"])
    else:
        ws=sh.worksheet("Ingresos")
    ws.append_row([desc,persona,moneda,monto_orig,monto_ars,monto_usd,tasa,str(fecha)])
    st.cache_data.clear()

def categorizar_inteligente(item):
    i=str(item).lower()
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
    s=f"{n:,.0f}".replace(",","X").replace(".",",").replace("X","."); return f"$ {s}"

def fmt_k(n):
    if n>=1_000_000: return f"$ {n/1_000_000:.1f}M"
    if n>=1_000: return f"$ {n/1_000:.0f}k"
    return fmt_ars(n)

def fmt_usd(n,d): return f"U$S {n/d:,.0f}" if d>0 else "U$S -"
def fmt_usd_val(n): return f"U$S {n:,.0f}"

def badge_venc(row):
    if row["Pagado"]: return '<span class="badge badge-paid">Pagado</span>'
    dia=row["Dia Pago"]
    if pd.isna(dia): return '<span class="badge badge-none">Sin fecha</span>'
    diff=(dia-date.today()).days; fd=dia.strftime("%-d %b")
    if diff<0: return f'<span class="badge badge-venc">Vencido {fd}</span>'
    if diff==0: return '<span class="badge badge-hoy">Hoy</span>'
    if diff<=3: return f'<span class="badge badge-prox">{diff}d - {fd}</span>'
    if diff<=10: return f'<span class="badge badge-soon">{diff}d - {fd}</span>'
    return f'<span class="badge badge-ok">{fd}</span>'

def badge_persona(persona):
    p=str(persona).upper()
    if p=="HENRY": return '<span class="badge badge-henry">Henry</span>'
    if p=="JAIKE": return '<span class="badge badge-jaike">Jaike</span>'
    return f'<span class="badge badge-none">{persona}</span>'

def procesar(df_base,dolar):
    df=df_base.copy()
    df["Categoria"]=df["Item"].apply(categorizar_inteligente)
    total=df["Monto (ARS)"].sum()
    df["Peso"]=(df["Monto (ARS)"]/total).fillna(0) if total>0 else 0
    df["USD"]=(df["Monto (ARS)"]/dolar).round(2) if dolar>0 else 0
    df["Cat"]=df["Categoria"]
    return df.sort_values(["Pagado","Dia Pago"],ascending=[True,True],na_position="last")

def guardar_hoja(df_guardar):
    df_up=df_guardar.copy()
    df_up["Categoria"]=df_up["Item"].apply(categorizar_inteligente)
    df_up=df_up[["Categoria","Item","Monto (ARS)","Dia Pago","Pagado"]]
    df_up["Dia Pago"]=df_up["Dia Pago"].apply(lambda x: str(x) if pd.notnull(x) else "")
    df_up["Pagado"]=df_up["Pagado"].apply(lambda x: "TRUE" if x else "FALSE")
    hoja=get_gspread().open("Gastos_Henry").sheet1
    hoja.clear(); hoja.append_row(df_up.columns.tolist()); hoja.append_rows(df_up.values.tolist())
    st.cache_data.clear()

def marcar_pagado(idx):
    df_act=cargar_datos().copy()
    if idx<len(df_act): df_act.at[idx,"Pagado"]=True; guardar_hoja(df_act)

def exportar_excel(df,df_ing=None):
    output=io.BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        df_exp=df[["Cat","Item","Monto (ARS)","USD","Dia Pago","Pagado"]].copy()
        df_exp.columns=["Categoria","Item","Monto ARS","USD","Vencimiento","Pagado"]
        df_exp.to_excel(writer,index=False,sheet_name="Gastos")
        resumen=df.groupby("Cat")["Monto (ARS)"].sum().reset_index()
        resumen.columns=["Categoria","Total ARS"]; resumen.to_excel(writer,index=False,sheet_name="Resumen")
        if df_ing is not None and not df_ing.empty: df_ing.to_excel(writer,index=False,sheet_name="Ingresos")
    return output.getvalue()

# CARGA

dolar=get_dolar()
dolar_val,dolar_ayer,dolar_diff,dolar_pct=get_dolar_tendencia()
df_base=cargar_datos(); df_ing=cargar_ingresos()

if not df_base.empty:
    df=procesar(df_base,dolar)
    total_ars=df["Monto (ARS)"].sum(); pagado_ars=df[df["Pagado"]==True]["Monto (ARS)"].sum()
    pend_ars=total_ars-pagado_ars; pct=int(pagado_ars/total_ars*100) if total_ars>0 else 0
    vencidos=df[(df["Pagado"]==False)&df["Dia Pago"].notna()&(df["Dia Pago"]<date.today())]
    proximos=df[(df["Pagado"]==False)&df["Dia Pago"].notna()&(df["Dia Pago"]>=date.today())&(df["Dia Pago"]<=date.today()+timedelta(days=3))]
    por_cat=df.groupby("Cat")["Monto (ARS)"].sum().reset_index().sort_values("Monto (ARS)",ascending=False)
else:
    df=por_cat=pd.DataFrame(); total_ars=pagado_ars=pend_ars=pct=0; vencidos=proximos=pd.DataFrame()

total_ing_ars=df_ing["Monto ARS"].sum() if not df_ing.empty else 0
total_ing_usd=df_ing["Monto USD"].sum() if not df_ing.empty else 0
ing_henry=df_ing[df_ing["Persona"].str.upper()=="HENRY"]["Monto ARS"].sum() if not df_ing.empty else 0
ing_jaike=df_ing[df_ing["Persona"].str.upper()=="JAIKE"]["Monto ARS"].sum() if not df_ing.empty else 0
balance_ars=total_ing_ars-total_ars
balance_pct=int(total_ing_ars/total_ars*100) if total_ars>0 else 0

meses=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
hoy=date.today(); hoy_str=f"{hoy.day} de {meses[hoy.month-1]} de {hoy.year}"

st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#000000">
<meta name="apple-mobile-web-app-title" content="Finanzas AR">

<link rel="apple-touch-icon" href="https://fav.farm/💳">
<script>
function haptic(ms){try{navigator.vibrate&&navigator.vibrate(ms||50);}catch(e){}}
document.addEventListener("DOMContentLoaded",function(){
  function patchInputs(){
    document.querySelectorAll("input[type=number]").forEach(function(el){
      if(!el.getAttribute("inputmode")){el.setAttribute("inputmode","decimal");}
    });
    document.querySelectorAll("input[type=text]").forEach(function(el){
      if(!el.getAttribute("inputmode")){el.setAttribute("inputmode","text");}
    });
  }
  function killStreamlitBottom(){
    var selectors=["[data-testid=stBottom]","[data-testid=stBottomBlockContainer]",".stBottomContainer",".stChatFloatingInputContainer"];
    selectors.forEach(function(sel){
      document.querySelectorAll(sel).forEach(function(el){
        el.style.cssText="display:none!important;height:0!important;overflow:hidden!important;";
      });
    });
  }
  patchInputs(); killStreamlitBottom();
  var obs=new MutationObserver(function(){patchInputs();killStreamlitBottom();});
  obs.observe(document.body,{childList:true,subtree:true});
});
</script>
""", unsafe_allow_html=True)

st.markdown('<div class="wrap">', unsafe_allow_html=True)

# HEADER

_trend_icon=""
if dolar_diff>0:
    _trend_icon=f'<span style="color:{RED};font-size:11px;font-weight:700">▲ {dolar_pct:+.1f}%</span>'
elif dolar_diff<0:
    _trend_icon=f'<span style="color:{GREEN};font-size:11px;font-weight:700">▼ {dolar_pct:.1f}%</span>'
else:
    _trend_icon=f'<span style="color:{TEXT2};font-size:11px">—</span>'

st.markdown(f"""
<div class="ios-hdr">
  <div class="ios-hdr-top">
    <div>
      <div class="ios-title">Finanzas <span>AR</span></div>
      <div class="ios-date">{hoy_str}</div>
    </div>
    <div class="dolar-pill">
      <div class="dolar-lbl">USD Blue</div>
      <div class="dolar-val">${dolar:,.0f}</div>
      <div style="margin-top:2px">{_trend_icon}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# HIDDEN NAV BUTTONS

_sc=st.session_state.screen
_hc1,_hc2,_hc3=st.columns(3)
with _hc1:
    if st.button("Inicio",key="nav_inicio",use_container_width=True):
        st.session_state.screen="inicio"; st.rerun()
with _hc2:
    if st.button("Ingresos",key="nav_ingresos",use_container_width=True):
        st.session_state.screen="ingresos"; st.rerun()
with _hc3:
    if st.button("Gastos",key="nav_gastos",use_container_width=True):
        st.session_state.screen="gastos"; st.rerun()

st.markdown(f"""
<div class="btab-bar">
  <button class="btab {'btab-active' if _sc=='inicio' else ''}"
    onclick="(function(){{haptic(8);document.querySelectorAll('[data-testid=stBaseButton-secondary]')[0].click();}})()">
    <svg class="btab-ico" viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>
    <span>Inicio</span>
  </button>
  <button class="btab {'btab-active' if _sc=='ingresos' else ''}"
    onclick="(function(){{haptic(8);document.querySelectorAll('[data-testid=stBaseButton-secondary]')[1].click();}})()">
    <svg class="btab-ico" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
    <span>Ingresos</span>
  </button>
  <button class="btab {'btab-active' if _sc=='gastos' else ''}"
    onclick="(function(){{haptic(8);document.querySelectorAll('[data-testid=stBaseButton-secondary]')[2].click();}})()">
    <svg class="btab-ico" viewBox="0 0 24 24"><path d="M20 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/></svg>
    <span>Gastos</span>
  </button>
</div>
""", unsafe_allow_html=True)

# INICIO

if st.session_state.screen=="inicio":
    bc=GREEN if balance_ars>=0 else RED; bs="+" if balance_ars>=0 else ""

    if total_ing_ars>0:
        msg=f'Ingresos cubren el <strong>{balance_pct}%</strong> de gastos &mdash; Superavit: <strong>{fmt_ars(balance_ars)}</strong>' if balance_ars>=0 else f'Deficit mensual: <strong>{fmt_ars(abs(balance_ars))}</strong>'
        cls="ios-alert-g" if balance_ars>=0 else "ios-alert-r"
        st.markdown(f'<div class="ios-alert {cls}">{msg}</div>',unsafe_allow_html=True)
    if not vencidos.empty:
        nv=len(vencidos)
        st.markdown(f'<div class="ios-alert ios-alert-r"><strong>{nv} pago{"s" if nv>1 else ""} vencido{"s" if nv>1 else ""}</strong> &mdash; {" / ".join(r["Item"] for _,r in vencidos.iterrows())}</div>',unsafe_allow_html=True)
    if not proximos.empty:
        st.markdown(f'<div class="ios-alert ios-alert-o">Vencen en 3 dias: {" / ".join(r["Item"] for _,r in proximos.iterrows())}</div>',unsafe_allow_html=True)

    st.markdown(f"""<div class="ios-metrics">
      <div class="ios-card"><div class="ios-card-lbl">Ingresos</div><div class="ios-card-val" style="color:{GREEN}">{fmt_k(total_ing_ars)}</div><div class="ios-card-sub">{fmt_usd_val(total_ing_usd)}</div></div>
      <div class="ios-card"><div class="ios-card-lbl">Gastos</div><div class="ios-card-val">{fmt_k(total_ars)}</div><div class="ios-card-sub">{fmt_usd(total_ars,dolar)}</div></div>
      <div class="ios-card"><div class="ios-card-lbl">Balance</div><div class="ios-card-val" style="color:{bc}">{bs}{fmt_k(balance_ars)}</div><div class="ios-card-sub">{"Superavit" if balance_ars>=0 else "Deficit"}</div></div>
    </div>""",unsafe_allow_html=True)

    st.markdown(f"""<div class="ios-metrics">
      <div class="ios-card"><div class="ios-card-lbl">Pagado</div><div class="ios-card-val" style="color:{GREEN}">{fmt_k(pagado_ars)}</div><div class="ios-card-sub">{fmt_usd(pagado_ars,dolar)}</div></div>
      <div class="ios-card"><div class="ios-card-lbl">Pendiente</div><div class="ios-card-val" style="color:{RED}">{fmt_k(pend_ars)}</div><div class="ios-card-sub">{fmt_usd(pend_ars,dolar)}</div></div>
      <div class="ios-card"><div class="ios-card-lbl">Cubierto</div><div class="ios-card-pct" style="color:{ACCENT}">{min(balance_pct,999)}%</div><div class="ios-pbar"><div class="ios-pfill" style="width:{min(balance_pct,100)}%;background:{ACCENT}"></div></div></div>
    </div>""",unsafe_allow_html=True)

    if total_ing_ars>0:
        ph=int(ing_henry/total_ing_ars*100) if total_ing_ars>0 else 0
        pj=int(ing_jaike/total_ing_ars*100) if total_ing_ars>0 else 0
        st.markdown(f"""<div class="ios-metrics-2">
          <div class="ios-card" style="border-left:3px solid {ACCENT}"><div class="ios-card-lbl" style="color:{ACCENT}">Henry</div><div class="ios-card-val" style="color:{ACCENT}">{fmt_k(ing_henry)}</div><div class="ios-card-sub">{fmt_usd_val(ing_henry/dolar)} &middot; {ph}%</div></div>
          <div class="ios-card" style="border-left:3px solid {PURPLE}"><div class="ios-card-lbl" style="color:{PURPLE}">Jaike</div><div class="ios-card-val" style="color:{PURPLE}">{fmt_k(ing_jaike)}</div><div class="ios-card-sub">{fmt_usd_val(ing_jaike/dolar)} &middot; {pj}%</div></div>
        </div>""",unsafe_allow_html=True)

    ba1,ba2=st.columns(2)
    with ba1:
        lbl_g="Cancelar" if st.session_state.show_add else "Agregar gasto"
        if st.button(lbl_g,type="secondary" if st.session_state.show_add else "primary",use_container_width=True,key="btn_add_g"):
            st.session_state.show_add=not st.session_state.show_add; st.session_state.show_add_ingreso=False; st.rerun()
    with ba2:
        lbl_i="Cancelar" if st.session_state.show_add_ingreso else "Agregar ingreso"
        if st.button(lbl_i,type="secondary" if st.session_state.show_add_ingreso else "primary",use_container_width=True,key="btn_add_i"):
            st.session_state.show_add_ingreso=not st.session_state.show_add_ingreso; st.session_state.show_add=False; st.rerun()
    st.markdown("<div style='height:10px'></div>",unsafe_allow_html=True)

    if st.session_state.show_add:
        st.markdown('<div class="ios-add-panel">',unsafe_allow_html=True)
        a1,a2,a3,a4=st.columns([2,1.2,1.2,0.8])
        with a1: new_item=st.text_input("Descripcion",placeholder="Ej: Netflix",label_visibility="visible",key="new_item")
        with a2: new_monto=st.number_input("Monto ARS",min_value=0,step=100,label_visibility="visible",key="new_monto")
        with a3: new_fecha=st.date_input("Vencimiento",value=None,label_visibility="visible",key="new_fecha")
        with a4:
            st.markdown("<div style='height:26px'></div>",unsafe_allow_html=True)
            if st.button("Agregar",type="primary",use_container_width=True):
                if not new_item.strip(): st.markdown('<div class="toast-err">Ingresa una descripcion</div>',unsafe_allow_html=True)
                elif new_monto<=0: st.markdown('<div class="toast-err">El monto debe ser mayor a 0</div>',unsafe_allow_html=True)
                else:
                    nueva=pd.DataFrame([{"Categoria":categorizar_inteligente(new_item),"Item":new_item.strip(),"Monto (ARS)":float(new_monto),"Dia Pago":new_fecha,"Pagado":False}])
                    try:
                        guardar_hoja(pd.concat([df_base,nueva],ignore_index=True))
                        st.session_state.show_add=False; st.rerun()
                    except Exception as e: st.markdown(f'<div class="toast-err">Error: {e}</div>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    if st.session_state.show_add_ingreso:
        st.markdown('<div class="ios-add-panel-green">',unsafe_allow_html=True)
        i1,i2,i3=st.columns([2,1,1])
        with i1: ing_desc=st.text_input("Descripcion",placeholder="Ej: Sueldo Henry",label_visibility="visible",key="ing_desc")
        with i2: ing_persona=st.selectbox("Persona",["Henry","Jaike"],label_visibility="visible",key="ing_persona")
        with i3: ing_moneda=st.selectbox("Moneda",["ARS","USD"],label_visibility="visible",key="ing_moneda")
        i4,i5,i6=st.columns([1.5,1.5,1])
        with i4: ing_monto=st.number_input(f"Monto en {st.session_state.get('ing_moneda','ARS')}",min_value=0.0,step=100.0,label_visibility="visible",key="ing_monto")
        with i5:
            moneda_sel=st.session_state.get("ing_moneda","ARS")
            if moneda_sel=="ARS":
                equiv=ing_monto/dolar if dolar>0 else 0
                st.markdown(f'<div style="padding:8px 0 4px"><div style="font-size:11px;color:{TEXT2};font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em">Equiv. USD</div><div style="font-size:20px;font-weight:700;color:{GREEN}">U$S {equiv:,.2f}</div></div>',unsafe_allow_html=True)
                monto_ars_final=ing_monto; monto_usd_final=equiv
            else:
                equiv=ing_monto*dolar
                st.markdown(f'<div style="padding:8px 0 4px"><div style="font-size:11px;color:{TEXT2};font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em">Equiv. ARS</div><div style="font-size:20px;font-weight:700;color:{GREEN}">{fmt_ars(equiv)}</div></div>',unsafe_allow_html=True)
                monto_ars_final=equiv; monto_usd_final=ing_monto
        with i6: ing_fecha=st.date_input("Fecha",value=hoy,label_visibility="visible",key="ing_fecha")
        st.markdown(f'<div style="font-size:12px;color:{TEXT2};margin:8px 0 10px">Tasa fija: <strong style="color:{TEXT}">${dolar:,.0f} ARS/USD</strong></div>',unsafe_allow_html=True)
        if st.button("Guardar ingreso",type="primary",use_container_width=True):
            if not ing_desc.strip(): st.markdown('<div class="toast-err">Ingresa una descripcion</div>',unsafe_allow_html=True)
            elif ing_monto<=0: st.markdown('<div class="toast-err">El monto debe ser mayor a 0</div>',unsafe_allow_html=True)
            else:
                try:
                    guardar_ingreso(ing_desc.strip(),ing_persona,moneda_sel,ing_monto,round(monto_ars_final,2),round(monto_usd_final,4),dolar,ing_fecha)
                    st.session_state.show_add_ingreso=False; st.rerun()
                except Exception as e: st.markdown(f'<div class="toast-err">Error: {e}</div>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    if df.empty:
        st.markdown(f'<div class="ios-group" style="padding:32px;text-align:center;color:{TEXT2}">Sin datos. Agrega tu primer gasto.</div>',unsafe_allow_html=True)
    else:
        busqueda=st.text_input("",placeholder="Buscar gasto...",label_visibility="collapsed",key="busqueda_input")
        st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)
        col_izq,col_der=st.columns([1.6,1],gap="medium")

        with col_izq:
            df_vista=df.copy()
            if busqueda.strip(): df_vista=df_vista[df_vista["Item"].str.contains(busqueda.strip(),case=False,na=False)]
            cats_orden=df_vista.groupby("Cat").apply(lambda g: g["Pagado"].eq(False).sum()).sort_values(ascending=False).index.tolist()
            st.markdown('<div class="ios-section-label">Gastos del mes</div>',unsafe_allow_html=True)
            if df_vista.empty:
                st.markdown(f'<div class="ios-group" style="padding:20px;text-align:center;color:{TEXT2}">Sin resultados</div>',unsafe_allow_html=True)
            else:
                for cat in cats_orden:
                    df_cat=df_vista[df_vista["Cat"]==cat]; t_cat=df_cat["Monto (ARS)"].sum(); color=cat_color(cat)
                    n_pend=int(df_cat["Pagado"].eq(False).sum())
                    badge=f'<span class="ios-badge">{n_pend}</span>' if n_pend>0 else ""
                    icon_hdr=sf_icon(cat,color,size=22)
                    st.markdown(f'<div class="ios-group"><div class="ios-group-hdr"><div style="width:22px;height:22px;border-radius:5px;overflow:hidden;flex-shrink:0">{icon_hdr}</div><span class="ios-group-hdr-lbl">{cat}{badge}</span><span class="ios-group-hdr-amt" style="color:{color}">{fmt_ars(t_cat)}</span></div>',unsafe_allow_html=True)
                    for idx,row in df_cat.iterrows():
                        paid=row["Pagado"]; monto=row["Monto (ARS)"]
                        nc="ios-row-name-paid" if paid else "ios-row-name"
                        ac="ios-row-amt-paid" if paid else "ios-row-amt"
                        op="0.5" if paid else "1"
                        ico=sf_icon(cat,color,size=34)
                        st.markdown(f'<div class="ios-row" style="opacity:{op}"><div style="width:34px;height:34px;flex-shrink:0;border-radius:8px;overflow:hidden">{ico}</div><div class="ios-row-body"><div class="{nc}">{row["Item"]}</div><div class="ios-row-sub">{badge_venc(row)}</div></div><div class="ios-row-right"><div class="{ac}">{fmt_ars(monto)}</div><div class="ios-row-usd">{fmt_usd(monto,dolar)}</div></div></div>',unsafe_allow_html=True)
                    st.markdown("</div>",unsafe_allow_html=True)

            pend_items=df_vista[df_vista["Pagado"]==False]
            if not pend_items.empty:
                with st.expander(f"Marcar como pagado ({len(pend_items)} pendientes)"):
                    for idx,row in pend_items.iterrows():
                        cn,cb=st.columns([3,1])
                        with cn: st.markdown(f'<div style="font-size:14px;padding:5px 0">{row["Item"]} &mdash; {fmt_ars(row["Monto (ARS)"])}</div>',unsafe_allow_html=True)
                        with cb:
                            if st.button("Pagado",key=f"pay_{idx}",use_container_width=True):
                                try: marcar_pagado(idx); st.rerun()
                                except Exception as e: st.error(str(e))

        with col_der:
            fig=go.Figure(go.Pie(labels=por_cat["Cat"],values=por_cat["Monto (ARS)"],hole=0.64,marker=dict(colors=[cat_color(c) for c in por_cat["Cat"]],line=dict(color=BG,width=2)),textinfo="none",hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",direction="clockwise",sort=True))
            fig.add_annotation(text=f"<b>{fmt_k(total_ars)}</b>",x=0.5,y=0.57,font=dict(size=15,color=TEXT,family="-apple-system"),showarrow=False)
            fig.add_annotation(text=fmt_usd(total_ars,dolar),x=0.5,y=0.42,font=dict(size=11,color=TEXT2,family="-apple-system"),showarrow=False)
            fig.update_layout(showlegend=False,height=230,margin=dict(t=6,b=6,l=6,r=6),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG)
            st.markdown(f'<div class="ios-group" style="padding:16px"><div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Distribucion</div>',unsafe_allow_html=True)
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            for _,r in por_cat.iterrows():
                pct_c=int(r["Monto (ARS)"]/total_ars*100) if total_ars>0 else 0; color=cat_color(r["Cat"])
                st.markdown(f'<div style="display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:0.5px solid {SEP}"><div style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0"></div><div style="flex:1;font-size:12px;color:{TEXT2}">{r["Cat"]}</div><div style="font-size:12px;font-weight:600;color:{TEXT}">{pct_c}%</div></div>',unsafe_allow_html=True)
            st.markdown("</div>",unsafe_allow_html=True)

            if total_ing_ars>0:
                fig_bal=go.Figure(go.Pie(labels=["Ingresos","Gastos"],values=[total_ing_ars,total_ars],hole=0.6,marker=dict(colors=[GREEN,RED],line=dict(color=BG,width=2)),textinfo="none",hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>"))
                fig_bal.add_annotation(text="<b>Balance</b>",x=0.5,y=0.6,font=dict(size=12,color=TEXT,family="-apple-system"),showarrow=False)
                fig_bal.add_annotation(text=f"{bs}{fmt_k(balance_ars)}",x=0.5,y=0.42,font=dict(size=12,color=bc,family="-apple-system"),showarrow=False)
                fig_bal.update_layout(showlegend=False,height=190,margin=dict(t=6,b=6,l=6,r=6),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG)
                st.markdown(f'<div class="ios-group" style="padding:16px"><div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Ingresos vs Gastos</div>',unsafe_allow_html=True)
                st.plotly_chart(fig_bal,use_container_width=True,config={"displayModeBar":False})
                st.markdown("</div>",unsafe_allow_html=True)

            n_pag=int(df["Pagado"].sum()); n_pend2=len(df)-n_pag
            mayor=df.loc[df["Monto (ARS)"].idxmax(),"Item"] if not df.empty else "-"; mayor_m=df["Monto (ARS)"].max() if not df.empty else 0
            st.markdown(f"""<div class="ios-group" style="padding:16px">
              <div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px">Resumen</div>
              <div class="res-row"><span class="res-k">Total items</span><span style="font-weight:600">{len(df)}</span></div>
              <div class="res-row"><span class="res-k">Pagados</span><span style="color:{GREEN};font-weight:600">{n_pag}</span></div>
              <div class="res-row"><span class="res-k">Pendientes</span><span style="color:{ORANGE};font-weight:600">{n_pend2}</span></div>
              <div class="res-row"><span class="res-k">Vencidos</span><span style="color:{RED};font-weight:600">{len(vencidos)}</span></div>
              <div class="res-row"><span class="res-k">Prox. 3 dias</span><span style="color:{YELLOW};font-weight:600">{len(proximos)}</span></div>
              <div class="res-row" style="flex-direction:column;align-items:flex-start;gap:2px;border-bottom:none"><span class="res-k">Mayor gasto</span><span style="font-weight:600;color:{TEXT}">{mayor}</span><span style="font-size:12px;color:{TEXT2}">{fmt_ars(mayor_m)}</span></div>
            </div>""",unsafe_allow_html=True)

            pend_cat=df[df["Pagado"]==False].groupby("Cat")["Monto (ARS)"].sum().sort_values(ascending=False)
            if not pend_cat.empty:
                max_p=pend_cat.max()
                st.markdown(f'<div class="ios-group" style="padding:16px"><div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:10px">Pendiente por categoria</div>',unsafe_allow_html=True)
                for cat,val in pend_cat.items():
                    pb=int(val/max_p*100) if max_p>0 else 0; color=cat_color(cat)
                    st.markdown(f'<div class="cat-bar-row"><div class="cat-bar-top"><span style="font-size:13px;color:{TEXT}">{cat}</span><span style="font-size:13px;font-weight:600;color:{color}">{fmt_ars(val)}</span></div><div class="cat-bar-bg"><div class="cat-bar-fill" style="width:{pb}%;background:{color}"></div></div></div>',unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)

        st.markdown(f'<div class="ios-section-title">Analisis del mes</div>',unsafe_allow_html=True)
        cats_sorted=por_cat.sort_values("Monto (ARS)",ascending=True)
        fig_bar=go.Figure(); fig_bar.add_trace(go.Bar(y=cats_sorted["Cat"],x=cats_sorted["Monto (ARS)"],orientation="h",marker=dict(color=[cat_color(c) for c in cats_sorted["Cat"]],opacity=0.9),text=[fmt_ars(v) for v in cats_sorted["Monto (ARS)"]],textposition="outside",textfont=dict(color=TEXT2,size=11,family="-apple-system"),hovertemplate="<b>%{y}</b><br>%{x:,.0f}<extra></extra>"))
        fig_bar.update_layout(height=max(200,len(cats_sorted)*40),margin=dict(t=8,b=8,l=8,r=120),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG,xaxis=dict(showgrid=False,showticklabels=False,zeroline=False),yaxis=dict(showgrid=False,tickfont=dict(color=TEXT,size=13,family="-apple-system")),bargap=0.38)
        st.markdown(f'<div class="ios-group" style="padding:16px"><div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Gasto por categoria</div>',unsafe_allow_html=True)
        st.plotly_chart(fig_bar,use_container_width=True,config={"displayModeBar":False}); st.markdown("</div>",unsafe_allow_html=True)

        df_pag_cat=df[df["Pagado"]==True].groupby("Cat")["Monto (ARS)"].sum(); df_pend_cat=df[df["Pagado"]==False].groupby("Cat")["Monto (ARS)"].sum()
        todas_cats=sorted(set(df_pag_cat.index)|set(df_pend_cat.index))
        fig_stack=go.Figure()
        fig_stack.add_trace(go.Bar(name="Pagado",x=todas_cats,y=[df_pag_cat.get(c,0) for c in todas_cats],marker_color=GREEN,opacity=0.9))
        fig_stack.add_trace(go.Bar(name="Pendiente",x=todas_cats,y=[df_pend_cat.get(c,0) for c in todas_cats],marker_color=RED,opacity=0.8))
        fig_stack.update_layout(barmode="stack",height=270,margin=dict(t=8,b=65,l=8,r=8),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG,legend=dict(font=dict(color=TEXT2,size=12),bgcolor="rgba(0,0,0,0)",orientation="h",x=0,y=1.08),xaxis=dict(tickfont=dict(color=TEXT2,size=11),showgrid=False,tickangle=-25),yaxis=dict(showgrid=False,showticklabels=False))
        st.markdown(f'<div class="ios-group" style="padding:16px"><div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Pagado vs Pendiente</div>',unsafe_allow_html=True)
        st.plotly_chart(fig_stack,use_container_width=True,config={"displayModeBar":False}); st.markdown("</div>",unsafe_allow_html=True)

        df_hist=cargar_historial()
        if not df_hist.empty and df_hist["Mes"].nunique()>1:
            hist_resumen=df_hist.groupby("Mes")["Monto (ARS)"].sum().reset_index()
            fig_hist=go.Figure(); fig_hist.add_trace(go.Bar(x=hist_resumen["Mes"],y=hist_resumen["Monto (ARS)"],marker_color=ACCENT,opacity=0.9,text=[fmt_ars(v) for v in hist_resumen["Monto (ARS)"]],textposition="outside",textfont=dict(color=TEXT2,size=11)))
            fig_hist.update_layout(height=230,margin=dict(t=8,b=8,l=8,r=8),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG,xaxis=dict(showgrid=False,tickfont=dict(color=TEXT2,size=11)),yaxis=dict(showgrid=False,showticklabels=False),bargap=0.3)
            st.markdown(f'<div class="ios-group" style="padding:16px"><div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Historial por mes</div>',unsafe_allow_html=True)
            st.plotly_chart(fig_hist,use_container_width=True,config={"displayModeBar":False}); st.markdown("</div>",unsafe_allow_html=True)

        st.markdown('<div class="ios-group">',unsafe_allow_html=True)
        st.markdown(f'<div style="padding:12px 14px 6px;font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em">Top 5 gastos</div>',unsafe_allow_html=True)
        for _,row in df.nlargest(5,"Monto (ARS)").iterrows():
            color=cat_color(row["Cat"]); pct_top=int(row["Monto (ARS)"]/total_ars*100) if total_ars>0 else 0
            ico=sf_icon(row["Cat"],color,size=34)
            st.markdown(f'<div class="ios-row"><div style="width:34px;height:34px;flex-shrink:0;border-radius:8px;overflow:hidden">{ico}</div><div class="ios-row-body"><div class="ios-row-name">{row["Item"]}</div><div class="ios-row-sub">{row["Cat"]} &middot; {pct_top}% del total</div></div><div class="ios-row-right"><div class="ios-row-amt">{fmt_ars(row["Monto (ARS)"])}</div><div class="ios-row-usd">{fmt_usd(row["Monto (ARS)"],dolar)}</div></div></div>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

        _,ce,_=st.columns([1,1,1])
        with ce: st.download_button(label="Exportar Excel",data=exportar_excel(df,df_ing),file_name=f"gastos_{hoy.strftime('%Y_%m')}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)

# INGRESOS

elif st.session_state.screen=="ingresos":
    bs2="+" if balance_ars>=0 else ""; bc2=GREEN if balance_ars>=0 else RED
    st.markdown('<div class="ios-section-label">Ingresos familiares</div>',unsafe_allow_html=True)
    st.markdown(f"""<div class="ios-metrics">
      <div class="ios-card"><div class="ios-card-lbl">Total</div><div class="ios-card-val" style="color:{GREEN}">{fmt_k(total_ing_ars)}</div><div class="ios-card-sub">{fmt_usd_val(total_ing_usd)}</div></div>
      <div class="ios-card" style="border-left:3px solid {ACCENT}"><div class="ios-card-lbl" style="color:{ACCENT}">Henry</div><div class="ios-card-val" style="color:{ACCENT}">{fmt_k(ing_henry)}</div><div class="ios-card-sub">{fmt_usd_val(ing_henry/dolar) if dolar>0 else "-"}</div></div>
      <div class="ios-card" style="border-left:3px solid {PURPLE}"><div class="ios-card-lbl" style="color:{PURPLE}">Jaike</div><div class="ios-card-val" style="color:{PURPLE}">{fmt_k(ing_jaike)}</div><div class="ios-card-sub">{fmt_usd_val(ing_jaike/dolar) if dolar>0 else "-"}</div></div>
    </div>""",unsafe_allow_html=True)
    st.markdown(f'<div class="ios-card" style="margin-bottom:12px"><div class="ios-card-lbl">Balance vs gastos</div><div class="ios-card-val" style="color:{bc2}">{bs2}{fmt_k(balance_ars)}</div><div class="ios-card-sub">{"Superavit" if balance_ars>=0 else "Deficit"}</div></div>',unsafe_allow_html=True)

    lbl_i2="Cancelar" if st.session_state.show_add_ingreso else "Agregar ingreso"
    if st.button(lbl_i2,type="secondary" if st.session_state.show_add_ingreso else "primary",use_container_width=True,key="btn_ing2"):
        st.session_state.show_add_ingreso=not st.session_state.show_add_ingreso; st.rerun()
    st.markdown("<div style='height:10px'></div>",unsafe_allow_html=True)

    if st.session_state.show_add_ingreso:
        st.markdown('<div class="ios-add-panel-green">',unsafe_allow_html=True)
        i1,i2,i3=st.columns([2,1,1])
        with i1: ing_desc2=st.text_input("Descripcion",placeholder="Ej: Sueldo Henry",label_visibility="visible",key="ing_desc2")
        with i2: ing_persona2=st.selectbox("Persona",["Henry","Jaike"],label_visibility="visible",key="ing_persona2")
        with i3: ing_moneda2=st.selectbox("Moneda",["ARS","USD"],label_visibility="visible",key="ing_moneda2")
        i4,i5,i6=st.columns([1.5,1.5,1]); moneda_sel2=st.session_state.get("ing_moneda2","ARS")
        with i4: ing_monto2=st.number_input(f"Monto en {moneda_sel2}",min_value=0.0,step=100.0,label_visibility="visible",key="ing_monto2")
        with i5:
            if moneda_sel2=="ARS":
                equiv2=ing_monto2/dolar if dolar>0 else 0
                st.markdown(f'<div style="padding:8px 0 4px"><div style="font-size:11px;color:{TEXT2};font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em">Equiv. USD</div><div style="font-size:20px;font-weight:700;color:{GREEN}">U$S {equiv2:,.2f}</div></div>',unsafe_allow_html=True)
                monto_ars2=ing_monto2; monto_usd2=equiv2
            else:
                equiv2=ing_monto2*dolar
                st.markdown(f'<div style="padding:8px 0 4px"><div style="font-size:11px;color:{TEXT2};font-weight:600;margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em">Equiv. ARS</div><div style="font-size:20px;font-weight:700;color:{GREEN}">{fmt_ars(equiv2)}</div></div>',unsafe_allow_html=True)
                monto_ars2=equiv2; monto_usd2=ing_monto2
        with i6: ing_fecha2=st.date_input("Fecha",value=hoy,label_visibility="visible",key="ing_fecha2")
        st.markdown(f'<div style="font-size:12px;color:{TEXT2};margin:8px 0 10px">Tasa fija: <strong style="color:{TEXT}">${dolar:,.0f} ARS/USD</strong></div>',unsafe_allow_html=True)
        if st.button("Guardar",type="primary",use_container_width=True,key="guardar_ing2"):
            if not ing_desc2.strip(): st.markdown('<div class="toast-err">Ingresa una descripcion</div>',unsafe_allow_html=True)
            elif ing_monto2<=0: st.markdown('<div class="toast-err">El monto debe ser mayor a 0</div>',unsafe_allow_html=True)
            else:
                try: guardar_ingreso(ing_desc2.strip(),ing_persona2,moneda_sel2,ing_monto2,round(monto_ars2,2),round(monto_usd2,4),dolar,ing_fecha2); st.session_state.show_add_ingreso=False; st.rerun()
                except Exception as e: st.markdown(f'<div class="toast-err">Error: {e}</div>',unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

    if df_ing.empty:
        st.markdown(f'<div class="ios-group" style="padding:32px;text-align:center;color:{TEXT2}">Sin ingresos registrados.</div>',unsafe_allow_html=True)
    else:
        ing_pers=df_ing.groupby("Persona")["Monto ARS"].sum().reset_index()
        fig_ing=go.Figure(go.Pie(labels=ing_pers["Persona"],values=ing_pers["Monto ARS"],hole=0.6,marker=dict(colors=[ACCENT,PURPLE],line=dict(color=BG,width=2)),textinfo="none",hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>"))
        fig_ing.add_annotation(text="<b>Total</b>",x=0.5,y=0.6,font=dict(size=12,color=TEXT,family="-apple-system"),showarrow=False)
        fig_ing.add_annotation(text=fmt_k(total_ing_ars),x=0.5,y=0.42,font=dict(size=12,color=GREEN,family="-apple-system"),showarrow=False)
        fig_ing.update_layout(showlegend=True,legend=dict(orientation="h",x=0.5,xanchor="center",y=-0.05,font=dict(color=TEXT2,size=12)),height=190,margin=dict(t=6,b=38,l=6,r=6),paper_bgcolor=PLOTBG,plot_bgcolor=PLOTBG)
        st.markdown(f'<div class="ios-group" style="padding:16px"><div style="font-size:12px;font-weight:600;color:{TEXT2};text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Por persona</div>',unsafe_allow_html=True)
        st.plotly_chart(fig_ing,use_container_width=True,config={"displayModeBar":False}); st.markdown("</div>",unsafe_allow_html=True)

        st.markdown('<div class="ios-section-label">Historial</div><div class="ios-group">',unsafe_allow_html=True)
        for _,row in df_ing.sort_values("Fecha",ascending=False).iterrows():
            persona=str(row.get("Persona","")); desc=str(row.get("Descripcion",""))
            monto_ars_r=float(row.get("Monto ARS",0)); monto_usd_r=float(row.get("Monto USD",0))
            tasa_r=float(row.get("Tasa USD/ARS",0)); fecha_r=row.get("Fecha","")
            fecha_str=fecha_r.strftime("%-d %b %Y") if hasattr(fecha_r,"strftime") else str(fecha_r)
            ico_c=ACCENT if persona.upper()=="HENRY" else PURPLE
            st.markdown(f"""<div class="ingreso-row">
              <div style="width:34px;height:34px;border-radius:8px;background:{ico_c};display:flex;align-items:center;justify-content:center;flex-shrink:0">
                <svg width="18" height="18" viewBox="0 0 18 18"><rect x="2" y="5" width="14" height="9" rx="2" fill="white" opacity="0.9"/><rect x="2" y="7" width="14" height="2" fill="{ico_c}"/><circle cx="5" cy="11" r="1.2" fill="{ico_c}" opacity="0.7"/></svg>
              </div>
              <div class="ios-row-body"><div class="ios-row-name">{desc}</div><div class="ios-row-sub">{badge_persona(persona)} &nbsp;{fecha_str} &middot; Tasa ${tasa_r:,.0f}</div></div>
              <div class="ios-row-right"><div class="ios-row-amt" style="color:{GREEN}">{fmt_ars(monto_ars_r)}</div><div class="ios-row-usd">U$S {monto_usd_r:,.2f}</div></div>
            </div>""",unsafe_allow_html=True)
        st.markdown("</div>",unsafe_allow_html=True)

# GASTOS (editor)

elif st.session_state.screen=="gastos":
    if df.empty:
        st.markdown(f'<div class="ios-group" style="padding:32px;text-align:center;color:{TEXT2}">Sin datos en Google Sheets.</div>',unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:14px;color:{TEXT2};margin-bottom:14px">Edita, agrega o marca pagos. Guarda para sincronizar.</div>',unsafe_allow_html=True)
        tab_todos,tab_pend,tab_pag=st.tabs([f"Todos  {len(df)}",f"Pendientes  {len(df[df['Pagado']==False])}",f"Pagados  {len(df[df['Pagado']==True])}"])
        COL_CONFIG={"Pagado":st.column_config.CheckboxColumn("Pagado",width="small"),"Item":st.column_config.TextColumn("Item"),"Monto (ARS)":st.column_config.NumberColumn("ARS",format="$ %d"),"USD":st.column_config.NumberColumn("USD",format="U$S %.0f",disabled=True,width="small"),"Dia Pago":st.column_config.DateColumn("Vencimiento",format="DD/MM/YY")}
        COL_ORDER=("Pagado","Item","Monto (ARS)","USD","Dia Pago")
        
        # CORRECCIÓN: Sólo la pestaña Todos es editable.
        with tab_todos: 
            df_edit=st.data_editor(df,column_config=COL_CONFIG,column_order=COL_ORDER,num_rows="dynamic",use_container_width=True,hide_index=True,key="t_todos")
        with tab_pend: 
            st.dataframe(df[df["Pagado"]==False],column_config=COL_CONFIG,column_order=COL_ORDER,use_container_width=True,hide_index=True)
        with tab_pag: 
            st.dataframe(df[df["Pagado"]==True],column_config=COL_CONFIG,column_order=COL_ORDER,use_container_width=True,hide_index=True)
            
        st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)
        bc1,bc2,bc3=st.columns([2.5,0.8,0.8])
        with bc1:
            if st.button("Guardar y Sincronizar",type="primary",use_container_width=True):
                try:
                    guardar_hoja(df_edit)
                    st.markdown('<div class="toast-ok">Cambios guardados</div>',unsafe_allow_html=True); st.rerun()
                except Exception as e: st.markdown(f'<div class="toast-err">Error: {e}</div>',unsafe_allow_html=True)
        with bc2:
            if st.button("Recargar",type="secondary",use_container_width=True): st.cache_data.clear(); st.rerun()
        with bc3:
            if not df.empty: st.download_button(label="Excel",data=exportar_excel(df,df_ing),file_name=f"gastos_{hoy.strftime('%Y_%m')}.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)
