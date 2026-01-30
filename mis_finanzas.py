import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# --- 1. CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💳", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #6200EE; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    </style>
    """, unsafe_allow_html=True)

# Diccionario de Iconos para el Selector
ICONOS_MAP = {
    "🏠 Vivienda": "🏠", "⚡ Servicios": "⚡", "📺 Suscripción": "📺", 
    "🛒 Alimentos": "🛒", "🚗 Transporte": "🚗", "💳 Tarjetas": "💳", 
    "📈 Inversiones": "📈", "👪 Familia": "👪", "🏥 Salud": "🏥", "🎭 Ocio": "🎭"
}

# --- 2. CONEXIÓN Y DATOS ---
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json", scope)
    except:
        info_json = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info_json, scope)
    return gspread.authorize(creds).open("Gastos_Henry").sheet1

def get_dolar_blue():
    try:
        r = requests.get("https://dolarapi.com/v1/dolares/blue")
        return float(r.json()['venta'])
    except: return 1500.0

precio_dolar = get_dolar_blue()

try:
    hoja = conectar_google_sheets()
    data = hoja.get_all_records()
    df = pd.DataFrame(data)
    
    # Limpieza y conversión de datos
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
    df["Día Pago"] = pd.to_datetime(df["Día Pago"], errors='coerce').dt.date
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# --- 3. LÓGICA DE ESTADOS ---
def determinar_estado(x):
    if pd.isna(x) or x is None:
        return "⚪ Sin Fecha"
    hoy = date.today()
    if x < hoy:
        return "🔴 Vencido"
    return "🟢 Al Día"

df["Estado"] = df["Día Pago"].apply(determinar_estado)
df["Monto (USD)"] = df["Monto (ARS)"] / precio_dolar

# Mapeo de iconos para la vista de tabla
df["Cat."] = df["Categoría"].apply(lambda x: next((v for k, v in ICONOS_MAP.items() if x in k), "❓"))

# --- 4. DASHBOARD SUPERIOR ---
st.title("Finanzas AR 🇦🇷")
st.caption(f"📅 Hoy: {date.today().strftime('%d/%m/%Y')} | 💵 Dólar Blue: ${precio_dolar:,.0f}")

total_ars = df["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar

col1, col2 = st.columns(2)
with col1: st.metric("Total Gastado (ARS)", f"${total_ars:,.0f}")
with col2: st.metric("Equivalente (USD)", f"US$ {total_usd:,.2f}")

st.divider()

# --- 5. GRÁFICO DE DONA ---
if total_ars > 0:
    fig = px.pie(df, values='Monto (ARS)', names='Categoría', hole=0.7, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.add_annotation(text=f"Total<br>${total_ars:,.0f}", x=0.5, y=0.5, font_size=20, showarrow=False)
    fig.update_layout(showlegend=False, height=300, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 6. PLANILLA ÚNICA DE GESTIÓN (Compacta) ---
st.subheader("📝 Gestión de Gastos")

df_editado = st.data_editor(
    df,
    column_config={
        "Cat.": st.column_config.SelectboxColumn(
            "Icono", 
            options=list(ICONOS_MAP.keys()), 
            width="small",
            help="🏠Vivienda | ⚡Servicios | 📺Suscrip. | 🛒Alimentos | 🚗Transp. | 💳Tarjetas | 📈Invers. | 👪Familia | 🏥Salud | 🎭Ocio"
        ),
        "Categoría": None, # Oculta la columna de texto técnica
        "Ítem": st.column_config.TextColumn("Ítem", width="medium"),
        "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d", width="small"),
        "Monto (USD)": st.column_config.NumberColumn("USD", format="U$S %.2f", disabled=True, width="small"),
        "Día Pago": st.column_config.DateColumn("Venc.", format="DD/MM", width="small"),
        "Estado": st.column_config.TextColumn("Estado", disabled=True, width="small")
    },
    column_order=("Cat.", "Ítem", "Monto (ARS)", "Monto (USD)", "Día Pago", "Estado"),
    num_rows="dynamic", use_container_width=True, hide_index=True
)

# --- 7. BOTÓN DE SINCRONIZACIÓN ---
if st.button("✔️ Guardar Cambios en la Nube", type="primary", use_container_width=True):
    try:
        df_save = df_editado.copy()
        # Restauramos el nombre de categoría limpio antes de subir
        df_save["Categoría"] = df_save["Cat."].apply(lambda x: x.split(" ")[-1] if " " in x else x)
        
        df_subir = df_save[["Categoría", "Ítem", "Monto (ARS)", "Día Pago"]]
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace(["NaT", "None", "nan"], "")
        
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("✅ ¡Sincronizado correctamente!")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")
