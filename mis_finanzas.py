import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💰", layout="wide")

hide_st_style = """<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>"""
st.markdown(hide_st_style, unsafe_allow_html=True)

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
    sheet = client.open("Gastos_Henry").sheet1
    return sheet

# --- 2. FUNCIONES DE DATOS ---
def get_dolar_blue():
    try:
        url = "https://dolarapi.com/v1/dolares/blue"
        r = requests.get(url)
        return float(r.json()['venta'])
    except:
        return 1485.00

def cargar_datos(sheet):
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["Categoría", "Ítem", "Monto (ARS)", "Monto (USD)", "Día Pago"])
    df_temp = pd.DataFrame(data)
    # Convertimos la columna de fecha a formato fecha de Python para el editor
    if "Día Pago" in df_temp.columns:
        df_temp["Día Pago"] = pd.to_datetime(df_temp["Día Pago"], errors='coerce').dt.date
    return df_temp

# --- INICIO ---
precio_dolar = get_dolar_blue()

try:
    hoja = conectar_google_sheets()
    df = cargar_datos(hoja)
    st.toast("☁️ Sincronizado con Google Drive")
except Exception as e:
    st.error(f"⚠️ Error de conexión: {e}")
    st.stop()

# Cálculos automáticos
df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
df["Monto (USD)"] = df["Monto (ARS)"] / precio_dolar
df = df[["Categoría", "Ítem", "Monto (ARS)", "Monto (USD)", "Día Pago"]]

# --- INTERFAZ ---
st.title("Finanzas AR 🇦🇷") # Título actualizado
st.caption(f"Cotización Dólar Blue: **${precio_dolar:,.0f}**")

# Métricas
total_ars = df["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar
c1, c2 = st.columns(2)
c1.metric("Total Pesos", f"${total_ars:,.0f}")
c2.metric("Total USD", f"US$ {total_usd:,.0f}")

st.divider()

tab1, tab2 = st.tabs(["📊 Gráficos", "📝 Editar Gastos"])

with tab1:
    gastos_cat = df.groupby("Categoría")["Monto (ARS)"].sum().reset_index()
    fig = px.pie(gastos_cat, values='Monto (ARS)', names='Categoría', hole=0.6)
    fig.update_layout(legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.caption("Usa el calendario para seleccionar la fecha de pago:")
    
    df_editado = st.data_editor(
        df,
        column_config={
            "Monto (ARS)": st.column_config.NumberColumn(format="$%d"),
            "Monto (USD)": st.column_config.NumberColumn(format="$%.2f", disabled=True),
            "Día Pago": st.column_config.DateColumn(
                "Día de Pago", 
                format="DD/MM/YYYY", # Cómo se ve en la app
                help="Selecciona la fecha de vencimiento"
            ),
            "Categoría": st.column_config.SelectboxColumn(
                options=["Vivienda", "Servicios", "Suscripción", "Alimentos", "Deportes", "Transporte", "Ocio", "Salud"]
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    
    if st.button("💾 Guardar en Google Drive", type="primary", use_container_width=True):
        df_subir = df_editado.copy()
        df_subir = df_subir.drop(columns=["Monto (USD)"])
        # Convertimos las fechas a texto para que Google Sheets las acepte sin errores
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str)
        
        try:
            hoja.clear()
            hoja.append_row(df_subir.columns.tolist())
            hoja.append_rows(df_subir.values.tolist())
            st.success("✅ ¡Sincronizado!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
