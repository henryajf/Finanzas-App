import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime

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
    except: return 1500.0

precio_dolar = get_dolar_blue()

try:
    hoja = conectar_google_sheets()
    data = hoja.get_all_records()
    df = pd.DataFrame(data)
except:
    st.error("Error de conexión con Google Sheets.")
    st.stop()

# --- LIMPIEZA PARA COMPATIBILIDAD ---
def formatear_fecha_lectura(val):
    if not val or val == "None" or val == "": return None
    try:
        # Intenta leer formato AAAA-MM-DD (estándar de base de datos)
        return pd.to_datetime(val).date()
    except:
        return None

df["Día Pago"] = df["Día Pago"].apply(formatear_fecha_lectura)
df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)

# --- 3. ESTILO DE FUENTE (SOLO TEXTO) ---
def estilo_fuente_vencimiento(val):
    if not val or pd.isnull(val): return ""
    hoy = date.today()
    # Cambia solo el color de la letra: Rojo si ya pasó, Verde si es futuro
    color_texto = '#FF0000' if val < hoy else '#008000'
    return f'color: {color_texto}; font-weight: bold;'

# --- 4. INTERFAZ ---
st.title("Finanzas AR 🇦🇷")
st.caption(f"Hoy: **{date.today().strftime('%d/%m/%Y')}** | Dólar Blue: **${precio_dolar:,.0f}**")

total_ars = df["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar

c1, c2 = st.columns(2)
c1.metric("Total Gastos (ARS)", f"${total_ars:,.0f}")
c2.metric("Total Gastos (USD)", f"US$ {total_usd:,.2f}")

st.divider()

t1, t2 = st.tabs(["📊 Gráficos", "📝 Gestión y Vencimientos"])

with t1:
    fig = px.pie(df, values='Monto (ARS)', names='Categoría', hole=0.6)
    st.plotly_chart(fig, use_container_width=True)

with t2:
    st.write("Letras en **Rojo**: Vencido | Letras en **Verde**: Pendiente")
    
    # Preparamos una copia visual con formato Día/Mes/Año
    df_visual = df.copy()
    
    # Aplicamos el estilo de fuente y mostramos
    st.dataframe(
        df_visual.style.applymap(estilo_fuente_vencimiento, subset=['Día Pago'])
        .format({"Día Pago": lambda x: x.strftime('%d/%m/%Y') if pd.notnull(x) else ""}),
        use_container_width=True, 
        hide_index=True
    )
    
    st.divider()
    st.subheader("Modificar datos")
    df_editado = st.data_editor(
        df,
        column_config={
            "Monto (ARS)": st.column_config.NumberColumn(format="$%d"),
            "Día Pago": st.column_config.DateColumn("Día de Pago", format="DD/MM/YYYY"),
            "Categoría": st.column_config.SelectboxColumn(options=["Vivienda", "Servicios", "Suscripción", "Alimentos", "Deportes", "Transporte", "Ocio", "Salud"])
        },
        num_rows="dynamic", use_container_width=True, hide_index=True
    )

    if st.button("💾 Guardar Cambios en la Nube", type="primary", use_container_width=True):
        df_subir = df_editado.copy()
        # Guardamos como texto AAAA-MM-DD para máxima compatibilidad con Sheets y Python
        df_subir["Día Pago"] = df_subir["Día Pago"].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else "")
        
        try:
            hoja.clear()
            hoja.append_row(df_subir.columns.tolist())
            hoja.append_rows(df_subir.values.tolist())
            st.success("✅ ¡Datos sincronizados con Google Drive!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar: {e}")
