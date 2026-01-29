import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💰", layout="wide")

# --- 1. CONEXIÓN CLOUD ---
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

# --- 2. LOGICA DE DATOS ---
def get_dolar_blue():
    try:
        r = requests.get("https://dolarapi.com/v1/dolares/blue")
        return float(r.json()['venta'])
    except: return 1500.0 # Valor de respaldo

precio_dolar = get_dolar_blue()

try:
    hoja = conectar_google_sheets()
    data = hoja.get_all_records()
    df = pd.DataFrame(data)
except:
    st.error("No se pudo cargar la base de datos. Verifica tu Google Sheets.")
    st.stop()

# Convertir a formato fecha y limpiar montos
df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
df["Día Pago"] = pd.to_datetime(df["Día Pago"], errors='coerce').dt.date

# --- 3. FUNCIÓN DE COLOR (SEMÁFORO) ---
def color_vencimiento(val):
    if val is None or pd.isnull(val):
        return ""
    hoy = date.today()
    if val < hoy:
        return 'background-color: #ffcccc; color: #990000; font-weight: bold' # Rojo suave
    else:
        return 'background-color: #ccffcc; color: #006600; font-weight: bold' # Verde suave

# --- 4. INTERFAZ ---
st.title("Finanzas AR 🇦🇷")
st.caption(f"Hoy es: **{date.today().strftime('%d/%m/%Y')}** | Dólar Blue: **${precio_dolar:,.0f}**")

total_ars = df["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar

c1, c2 = st.columns(2)
c1.metric("Total Gastos (ARS)", f"${total_ars:,.0f}")
c2.metric("Total Gastos (USD)", f"US$ {total_usd:,.2f}")

st.divider()

t1, t2 = st.tabs(["📊 Gráficos de Gastos", "📝 Gestión y Vencimientos"])

with t1:
    if total_ars > 0:
        fig = px.pie(df, values='Monto (ARS)', names='Categoría', hole=0.6)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar gráficos.")

with t2:
    st.subheader("Planilla de Pagos")
    st.write("🔴 Rojo: Vencido | 🟢 Verde: A tiempo")
    
    # Aplicamos el estilo de colores a la visualización
    df_styled = df.style.applymap(color_vencimiento, subset=['Día Pago'])
    
    # Nota: El editor de datos (st.data_editor) no soporta colores de fondo dinámicos 
    # de la misma forma que st.dataframe, así que mostramos la tabla con colores arriba.
    st.dataframe(df_styled, use_container_width=True, hide_index=True)
    
    st.divider()
    st.write("### Modificar Datos")
    df_editado = st.data_editor(
        df,
        column_config={
            "Monto (ARS)": st.column_config.NumberColumn(format="$%d"),
            "Día Pago": st.column_config.DateColumn("Día de Pago", format="DD/MM/YYYY"),
            "Categoría": st.column_config.SelectboxColumn(options=["Vivienda", "Servicios", "Suscripción", "Alimentos", "Deportes", "Transporte", "Ocio", "Salud"])
        },
        num_rows="dynamic", use_container_width=True, hide_index=True, key="editor"
    )

    if st.button("💾 Guardar Cambios en la Nube", type="primary", use_container_width=True):
        df_subir = df_editado.copy()
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str)
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("✅ ¡Actualizado en Google Drive!")
        st.rerun()
