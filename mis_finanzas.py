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
    st.error("Error de conexión.")
    st.stop()

# --- ARREGLO DE FECHAS (Importante para que se vean) ---
def limpiar_fecha(val):
    if not val or val == "None": return None
    try:
        # Si ya es una fecha AAAA-MM-DD
        return datetime.strptime(str(val), "%Y-%m-%d").date()
    except:
        try:
            # Si es formato "26-1", le agregamos el año 2026
            dia, mes = str(val).split('-')
            return date(2026, int(mes), int(dia))
        except:
            return None

df["Día Pago"] = df["Día Pago"].apply(limpiar_fecha)
df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)

# --- 3. ESTILO DE SEMÁFORO ---
def color_vencimiento(val):
    if not val or pd.isnull(val): return ""
    hoy = date.today()
    # Rojo si ya pasó, Verde si es hoy o futuro
    color = '#ffcccc' if val < hoy else '#ccffcc'
    texto = '#990000' if val < hoy else '#006600'
    return f'background-color: {color}; color: {texto}; font-weight: bold'

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
    st.write("🔴 Rojo: Vencido | 🟢 Verde: Pendiente")
    
    # Tabla con colores (Solo visualización)
    df_ver = df.copy()
    df_ver["Día Pago"] = df_ver["Día Pago"].apply(lambda x: x.strftime('%d/%m/%Y') if x else "Sin fecha")
    st.dataframe(df.style.applymap(color_vencimiento, subset=['Día Pago']), use_container_width=True, hide_index=True)
    
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
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str)
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("¡Datos sincronizados!")
        st.rerun()
