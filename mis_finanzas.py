import streamlit as st
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# --- 1. CONFIGURACIÓN Y ESTILO CUSTOM ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💳", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #00D1FF;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
    }
    .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONEXIONES Y DATOS ---
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
        return float(requests.get("https://dolarapi.com/v1/dolares/blue").json()['venta'])
    except: return 1485.0

precio_dolar = get_dolar_blue()

try:
    hoja = conectar_google_sheets()
    df = pd.DataFrame(hoja.get_all_records())
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
    df["Día Pago"] = pd.to_datetime(df["Día Pago"], errors='coerce').dt.date
except:
    st.error("Error cargando datos."); st.stop()

# --- 3. LÓGICA DE ESTADOS Y ALERTAS ---
def calcular_estado(fecha):
    if not fecha or pd.isnull(fecha): return "⚪ Sin Fecha"
    hoy = date.today()
    if fecha < hoy: return "🔴 Vencido"
    if fecha <= hoy + timedelta(days=3): return "🟡 Vence Pronto"
    return "🟢 Al Día"

df["Estado"] = df["Día Pago"].apply(calcular_estado)

# --- 4. DASHBOARD SUPERIOR (KPIs Premium) ---
st.title("Finanzas AR 🇦🇷")
st.caption(f"📅 {date.today().strftime('%d de %B, %Y')}  |  💵 Blue: ${precio_dolar:,.0f}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Gastos Totales (ARS)", f"${df['Monto (ARS)'].sum():,.0f}", delta="Mensual")
with col2:
    st.metric("Gastos Totales (USD)", f"US$ {df['Monto (ARS)'].sum()/precio_dolar:,.2f}", delta_color="off")
with col3:
    vencidos = len(df[df["Estado"] == "🔴 Vencido"])
    st.metric("Pagos Vencidos", vencidos, delta=f"{vencidos} pendientes", delta_color="inverse")

# --- 5. ALERTAS INTELIGENTES ---
if vencidos > 0:
    st.warning(f"⚠️ Tienes **{vencidos}** pagos vencidos. Revisa la tabla abajo.")

st.divider()

# --- 6. FILTROS Y TABLA GESTIÓN ---
st.subheader("📊 Gestión y Filtros Dinámicos")
c_f1, c_f2 = st.columns(2)
with c_f1:
    filtro_cat = st.multiselect("Filtrar por Categoría", options=df["Categoría"].unique())
with c_f2:
    filtro_est = st.multiselect("Filtrar por Estado", options=df["Estado"].unique())

# Aplicar filtros
df_filtrado = df.copy()
if filtro_cat: df_filtrado = df_filtrado[df_filtrado["Categoría"].isin(filtro_cat)]
if filtro_est: df_filtrado = df_filtrado[df_filtrado["Estado"].isin(filtro_est)]

# Editor de datos optimizado
df_editado = st.data_editor(
    df_filtrado,
    column_config={
        "Estado": st.column_config.TextColumn("Estado", disabled=True),
        "Monto (ARS)": st.column_config.NumberColumn("Monto (ARS)", format="$%d"),
        "Día Pago": st.column_config.DateColumn("Día de Pago", format="DD/MM/YY"),
        "Categoría": st.column_config.SelectboxColumn(options=["Vivienda", "Servicios", "Suscripción", "Alimentos", "Deportes", "Transporte", "Ocio", "Salud"])
    },
    num_rows="dynamic", use_container_width=True, hide_index=True
)

# --- 7. ACCIONES ---
col_save, col_info = st.columns([1, 3])
with col_save:
    if st.button("✔️ Guardar y Sincronizar", type="primary", use_container_width=True):
        # Unir cambios filtrados con los no filtrados para no perder datos
        df.update(df_editado)
        df_subir = df.drop(columns=["Estado"])
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace("NaT", "")
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("☁️ Sincronizado")
        st.rerun()

with col_info:
    st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# --- 8. GRÁFICO RESUMEN ---
st.divider()
st.plotly_chart(px.bar(df_filtrado, x='Categoría', y='Monto (ARS)', color='Estado', title="Distribución por Filtro"), use_container_width=True)
