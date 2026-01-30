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

# --- 3. LÓGICA DE ESTADOS (CORRECCIÓN DE ERROR NAT) ---
def determinar_estado(x):
    if pd.isna(x) or x is None:
        return "⚪ Sin Fecha"
    hoy = date.today()
    if x < hoy:
        return "🔴 Vencido"
    return "🟢 Al Día"

df["Estado"] = df["Día Pago"].apply(determinar_estado)
df["Monto (USD)"] = df["Monto (ARS)"] / precio_dolar

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
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 6. PLANILLA ÚNICA DE GESTIÓN ---
st.subheader("📝 Gestión de Gastos")

categorias_pro = ["Vivienda", "Servicios", "Suscripción", "Alimentos", "Transporte", "Tarjetas", "Inversiones", "Familia", "Salud", "Ocio"]

df_editado = st.data_editor(
    df,
    column_config={
        "Categoría": st.column_config.SelectboxColumn(options=categorias_pro),
        "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d"),
        "Monto (USD)": st.column_config.NumberColumn("USD", format="US$ %.2f", disabled=True),
        "Día Pago": st.column_config.DateColumn("Vencimiento", format="DD/MM/YY"),
        "Estado": st.column_config.TextColumn("Estado", disabled=True)
    },
    num_rows="dynamic", use_container_width=True, hide_index=True
)

# --- 7. BOTÓN DE SINCRONIZACIÓN ---
if st.button("✔️ Guardar Cambios en la Nube", type="primary", use_container_width=True):
    try:
        # Solo subimos las columnas originales para mantener limpio el Google Sheets
        df_subir = df_editado[["Categoría", "Ítem", "Monto (ARS)", "Día Pago"]]
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace(["NaT", "None", "nan"], "")
        
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("✅ ¡Sincronizado correctamente!")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")
