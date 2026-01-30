import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💳", layout="wide")

# Diccionario de Iconos (Para que solo se vea el emoji)
DICCIONARIO_ICONOS = {
    "Vivienda": "🏠", "Servicios": "⚡", "Suscripción": "📺", 
    "Alimentos": "🛒", "Transporte": "🚗", "Tarjetas": "💳", 
    "Inversiones": "📈", "Familia": "👪", "Salud": "🏥", "Ocio": "🎭"
}

# --- 2. LOGICA DE DATOS ---
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        info_json = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info_json, scope)
        return gspread.authorize(creds).open("Gastos_Henry").sheet1
    except:
        st.error("Error de conexión con la base de datos."); st.stop()

def get_dolar_blue():
    try:
        return float(requests.get("https://dolarapi.com/v1/dolares/blue").json()['venta'])
    except: return 1500.0

precio_dolar = get_dolar_blue()
hoja = conectar_google_sheets()
df = pd.DataFrame(hoja.get_all_records())

# Limpieza y Conversión
df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
df["Día Pago"] = pd.to_datetime(df["Día Pago"], errors='coerce').dt.date

# --- 3. INTERFAZ ---
st.title("Finanzas AR 🇦🇷")
total_ars = df["Monto (ARS)"].sum()

# Gráfico de Dona con Total Central
fig = px.pie(df, values='Monto (ARS)', names='Categoría', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
fig.add_annotation(text=f"Total<br>${total_ars:,.0f}", x=0.5, y=0.5, font_size=20, showarrow=False)
fig.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=250)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 4. GESTIÓN DE GASTOS (TABLA COMPACTA) ---
st.subheader("📝 Planilla de Gastos")

# Transformamos la categoría a ICONO para la vista
df_vista = df.copy()
df_vista["Icono"] = df_vista["Categoría"].map(DICCIONARIO_ICONOS).fillna("❓")

df_editado = st.data_editor(
    df_vista,
    column_config={
        "Icono": st.column_config.TextColumn(
            "Cat.", 
            help="🏠Vivienda | ⚡Servicios | 📺Suscrip. | 🛒Alimentos | 🚗Transp. | 💳Tarjetas | 📈Invers. | 👪Familia | 🏥Salud | 🎭Ocio",
            width="small"
        ),
        "Categoría": None, # Ocultamos la columna de texto original
        "Ítem": st.column_config.TextColumn("Ítem", width="medium"),
        "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d", width="small"),
        "Monto (USD)": st.column_config.NumberColumn("USD", format="US$ %.2f", disabled=True, width="small"),
        "Día Pago": st.column_config.DateColumn("Vencimiento", format="DD/MM", width="small"),
    },
    column_order=("Icono", "Ítem", "Monto (ARS)", "Día Pago"), # Reordenamos para ahorrar espacio
    num_rows="dynamic", use_container_width=True, hide_index=True
)

if st.button("✔️ Guardar Cambios en la Nube", type="primary", use_container_width=True):
    # Al guardar, volvemos a poner el nombre de la categoría basado en el icono
    INV_DICCIONARIO = {v: k for k, v in DICCIONARIO_ICONOS.items()}
    df_save = df_editado.copy()
    df_save["Categoría"] = df_save["Icono"].map(INV_DICCIONARIO).fillna("Ocio")
    
    df_subir = df_save[["Categoría", "Ítem", "Monto (ARS)", "Día Pago"]]
    df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace(["NaT", "None", "nan"], "")
    
    hoja.clear()
    hoja.append_row(df_subir.columns.tolist())
    hoja.append_rows(df_subir.values.tolist())
    st.success("✅ ¡Datos guardados!")
    st.rerun()
