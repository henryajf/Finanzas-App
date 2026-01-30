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

# Diccionario de Iconos
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
    
    # Limpieza y conversión
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
    df["Día Pago"] = pd.to_datetime(df["Día Pago"], errors='coerce').dt.date
    # Aseguramos que exista la columna Pagado (booleana)
    if "Pagado" not in df.columns:
        df["Pagado"] = False
    else:
        df["Pagado"] = df["Pagado"].astype(bool)
except Exception as e:
    st.error(f"Error: {e}"); st.stop()

# --- 3. LÓGICA DE ESTADOS Y ORDEN ---
def determinar_estado(row):
    if row["Pagado"]: return "✅ Realizado"
    if pd.isna(row["Día Pago"]): return "⚪ Sin Fecha"
    return "🔴 Vencido" if row["Día Pago"] < date.today() else "🟢 Al Día"

df["Estado"] = df.apply(determinar_estado, axis=1)
df["Monto (USD)"] = df["Monto (ARS)"] / precio_dolar
df["Cat."] = df["Categoría"].apply(lambda x: next((v for k, v in ICONOS_MAP.items() if x in k), "❓"))

# ORDENAR: Primero los NO pagados (False < True), luego por fecha
df = df.sort_values(by=["Pagado", "Día Pago"], ascending=[True, True])

# --- 4. DASHBOARD SUPERIOR ---
st.title("Finanzas AR 🇦🇷")
total_ars = df[df["Pagado"] == False]["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar

col1, col2 = st.columns(2)
with col1: st.metric("Pendiente de Pago (ARS)", f"${total_ars:,.0f}")
with col2: st.metric("Pendiente (USD)", f"U$S {total_usd:,.2f}")

st.divider()

# --- 5. GRÁFICO DE DONA (Solo Pendientes) ---
df_pendientes = df[df["Pagado"] == False]
if not df_pendientes.empty:
    fig = px.pie(df_pendientes, values='Monto (ARS)', names='Categoría', hole=0.7, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.add_annotation(text=f"Total<br>${total_ars:,.0f}", x=0.5, y=0.5, font_size=20, showarrow=False)
    fig.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 6. PLANILLA ÚNICA CON CHECKBOX ---
st.subheader("📝 Gestión de Pagos")

df_editado = st.data_editor(
    df,
    column_config={
        "Pagado": st.column_config.CheckboxColumn("¿Listo?", width="small"),
        "Cat.": st.column_config.SelectboxColumn("Icono", options=list(ICONOS_MAP.keys()), width="small"),
        "Categoría": None,
        "Ítem": st.column_config.TextColumn("Ítem", width="medium"),
        "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d", width="small"),
        "Monto (USD)": st.column_config.NumberColumn("USD", format="U$S %.2f", disabled=True, width="small"),
        "Día Pago": st.column_config.DateColumn("Venc.", format="DD/MM", width="small"),
        "Estado": st.column_config.TextColumn("Estado", disabled=True, width="small")
    },
    column_order=("Pagado", "Cat.", "Ítem", "Monto (ARS)", "Monto (USD)", "Día Pago", "Estado"),
    num_rows="dynamic", use_container_width=True, hide_index=True
)

# --- 7. BOTÓN DE SINCRONIZACIÓN ---
if st.button("✔️ Guardar y Reordenar Lista", type="primary", use_container_width=True):
    try:
        df_save = df_editado.copy()
        df_save["Categoría"] = df_save["Cat."].apply(lambda x: x.split(" ")[-1] if " " in x else x)
        
        # Preparamos para subir (incluimos la nueva columna Pagado)
        df_subir = df_save[["Categoría", "Ítem", "Monto (ARS)", "Día Pago", "Pagado"]]
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace(["NaT", "None", "nan"], "")
        
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("✅ ¡Lista actualizada!")
        st.rerun()
    except Exception as e:
        st.error(f"Error al guardar: {e}")
