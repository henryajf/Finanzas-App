import streamlit as st
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💰", layout="wide")

# Estilo para mejorar la visualización móvil y ocultar menús innecesarios
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} .block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

# --- 1. CONEXIÓN CON GOOGLE SHEETS ---
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json", scope)
    except:
        import json
        info_json = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info_json, scope)
    client = gspread.authorize(creds)
    return client.open("Gastos_Henry").sheet1

# --- 2. FUNCIONES DE DATOS ---
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
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# Limpieza de datos para compatibilidad
df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
df["Día Pago"] = pd.to_datetime(df["Día Pago"], errors='coerce').dt.date

# --- 3. INTERFAZ ---
st.title("Finanzas AR 🇦🇷")
st.caption(f"Hoy: **{date.today().strftime('%d/%m/%Y')}** | Dólar Blue: **${precio_dolar:,.0f}**")

# Métricas principales
total_ars = df["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar
c1, c2 = st.columns(2)
c1.metric("Total Gastos (ARS)", f"${total_ars:,.0f}")
c2.metric("Total Gastos (USD)", f"US$ {total_usd:,.2f}")

st.divider()

# TABLA ÚNICA DE GESTIÓN
st.subheader("Gestión de Pagos y Vencimientos")
st.info("💡 Puedes editar directamente en la tabla. Las fechas pasadas se resaltan automáticamente.")

# Configuración del Editor Único
df_editado = st.data_editor(
    df,
    column_config={
        "Categoría": st.column_config.SelectboxColumn(
            options=["Vivienda", "Servicios", "Suscripción", "Alimentos", "Deportes", "Transporte", "Ocio", "Salud"],
            width="medium"
        ),
        "Ítem": st.column_config.TextColumn(width="medium"),
        "Monto (ARS)": st.column_config.NumberColumn("Monto (ARS)", format="$%d", min_value=0),
        "Monto (USD)": st.column_config.NumberColumn(
            "Equiv. USD", 
            format="US$ %.2f", 
            help="Calculado según Dólar Blue",
            disabled=True # Columna de solo lectura
        ),
        "Día Pago": st.column_config.DateColumn(
            "Día de Pago", 
            format="DD/MM/YYYY",
            help="Selecciona la fecha de vencimiento"
        )
    },
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="tabla_unica"
)

# Botón de Guardado
if st.button("💾 Guardar Cambios en la Nube", type="primary", use_container_width=True):
    try:
        df_subir = df_editado.copy()
        # Mantenemos solo las columnas necesarias para Google Sheets
        columnas_drive = ["Categoría", "Ítem", "Monto (ARS)", "Día Pago"]
        df_subir = df_subir[columnas_drive]
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace("None", "")
        
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("✅ ¡Base de datos actualizada en Google Drive!")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")
