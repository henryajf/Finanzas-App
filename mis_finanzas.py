import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime

# --- 1. CONFIGURACIÓN Y ESTILO ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💳", layout="wide")

# Diccionario de Iconos con nombre para el selector
ICONOS_MAP = {
    "🏠 Vivienda": "🏠", "⚡ Servicios": "⚡", "📺 Suscripción": "📺", 
    "🛒 Alimentos": "🛒", "🚗 Transporte": "🚗", "💳 Tarjetas": "💳", 
    "📈 Inversiones": "📈", "👪 Familia": "👪", "🏥 Salud": "🏥", "🎭 Ocio": "🎭"
}

# --- 2. LOGICA DE DATOS ---
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        info_json = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info_json, scope)
        return gspread.authorize(creds).open("Gastos_Henry").sheet1
    except:
        st.error("Error de conexión con Google Sheets."); st.stop()

def get_dolar_blue():
    try:
        return float(requests.get("https://dolarapi.com/v1/dolares/blue").json()['venta'])
    except: return 1520.0 # Valor estimado actual en CABA

precio_dolar = get_dolar_blue()
hoja = conectar_google_sheets()
data = hoja.get_all_records()
df = pd.DataFrame(data)

# Limpieza de datos
df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
df["Día Pago"] = pd.to_datetime(df["Día Pago"], errors='coerce').dt.date
df["Monto (USD)"] = df["Monto (ARS)"] / precio_dolar

# --- 3. DASHBOARD SUPERIOR (ESTILO DONA CENTRAL) ---
st.title("Finanzas AR 🇦🇷")
total_ars = df["Monto (ARS)"].sum()

fig = px.pie(df, values='Monto (ARS)', names='Categoría', hole=0.75, color_discrete_sequence=px.colors.qualitative.Pastel)
fig.add_annotation(text=f"TOTAL<br>${total_ars:,.0f}", x=0.5, y=0.5, font_size=24, font_color="white", showarrow=False)
fig.update_layout(showlegend=False, height=280, margin=dict(t=0, b=0, l=0, r=0))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 4. GESTIÓN DE GASTOS (TABLA COMPACTA CON ICONOS) ---
st.subheader("📝 Control de Pagos")

# Preparamos la columna para mostrar solo el icono en la tabla
df_vista = df.copy()
# Buscamos el icono correspondiente al texto guardado
df_vista["Cat."] = df_vista["Categoría"].apply(lambda x: next((v for k, v in ICONOS_MAP.items() if x in k), "❓"))

# Configuración del editor de datos
df_editado = st.data_editor(
    df_vista,
    column_config={
        "Cat.": st.column_config.SelectboxColumn(
            "Cat.",
            options=list(ICONOS_MAP.keys()), # Aquí eliges "🏠 Vivienda"
            width="small",
            help="Selecciona la categoría usando los iconos"
        ),
        "Categoría": None, # Ocultamos la columna técnica de texto
        "Ítem": st.column_config.TextColumn("Ítem", width="medium"),
        "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d", width="small"),
        "Monto (USD)": st.column_config.NumberColumn("USD", format="U$S %.2f", disabled=True, width="small"),
        "Día Pago": st.column_config.DateColumn("Venc.", format="DD/MM", width="small"), # Fecha ultra angosta
    },
    column_order=("Cat.", "Ítem", "Monto (ARS)", "Monto (USD)", "Día Pago"),
    num_rows="dynamic", use_container_width=True, hide_index=True
)

# --- 5. GUARDADO INTELIGENTE ---
if st.button("✔️ Sincronizar Cambios", type="primary", use_container_width=True):
    df_save = df_editado.copy()
    # Limpiamos el nombre de la categoría (quitamos el emoji para guardar solo el texto o mantenerlo limpio)
    df_save["Categoría"] = df_save["Cat."].apply(lambda x: x.split(" ")[-1] if " " in x else x)
    
    df_subir = df_save[["Categoría", "Ítem", "Monto (ARS)", "Día Pago"]]
    df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace(["NaT", "None", "nan"], "")
    
    try:
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("✅ Base de datos actualizada")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")
