import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# --- 1. CONFIGURACIÓN PREMIUM ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💳", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #6200EE; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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
        return float(requests.get("https://dolarapi.com/v1/dolares/blue").json()['venta'])
    except: return 1500.0

precio_dolar = get_dolar_blue()

try:
    hoja = conectar_google_sheets()
    df = pd.DataFrame(hoja.get_all_records())
    df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
    df["Monto (USD)"] = df["Monto (ARS)"] / precio_dolar # Columna USD calculada
    df["Día Pago"] = pd.to_datetime(df["Día Pago"], errors='coerce').dt.date
except:
    st.error("Error cargando base de datos."); st.stop()

# Lógica de estados
df["Estado"] = df["Día Pago"].apply(lambda x: "🔴 Vencido" if x and x < date.today() else ("🟢 Al Día" if x else "⚪ Sin Fecha"))

# --- 3. DASHBOARD SUPERIOR ---
st.title("Finanzas AR 🇦🇷")
st.caption(f"💵 Dólar Blue: ${precio_dolar:,.0f} | Actualizado: {datetime.now().strftime('%H:%M')}")

total_ars = df["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar

col1, col2 = st.columns(2)
with col1: st.metric("Total Gastado (ARS)", f"${total_ars:,.0f}")
with col2: st.metric("Equivalente (USD)", f"US$ {total_usd:,.2f}")

st.divider()

# --- 4. GRÁFICO DE DONA (ESTILO PREMIUM) ---
# Inspirado en la interfaz de billeteras digitales
if total_ars > 0:
    fig = px.pie(df, values='Monto (ARS)', names='Categoría', hole=0.7, 
                 title="Distribución de Gastos",
                 color_discrete_sequence=px.colors.qualitative.Pastel)
    
    # Texto en el centro de la dona
    fig.add_annotation(text=f"Total<br>${total_ars:,.0f}", x=0.5, y=0.5, font_size=20, showarrow=False)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.1))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- 5. GESTIÓN UNIFICADA (COLUMNAS ESPEJO ARS/USD) ---
st.subheader("📝 Planilla de Gastos")
st.info("💡 La columna USD se actualiza sola al cambiar el monto en ARS.")

# Categorías extendidas basadas en el nuevo diseño
categorias_pro = ["Vivienda", "Servicios", "Suscripción", "Alimentos", "Transporte", "Tarjetas", "Inversiones", "Familia", "Salud", "Ocio"]

df_editado = st.data_editor(
    df,
    column_config={
        "Categoría": st.column_config.SelectboxColumn(options=categorias_pro),
        "Monto (ARS)": st.column_config.NumberColumn("Gasto (ARS)", format="$%d"),
        "Monto (USD)": st.column_config.NumberColumn("Gasto (USD)", format="US$ %.2f", disabled=True), # Columna al lado
        "Día Pago": st.column_config.DateColumn("Vencimiento", format="DD/MM/YY"),
        "Estado": st.column_config.TextColumn("Estado", disabled=True)
    },
    num_rows="dynamic", use_container_width=True, hide_index=True
)

if st.button("✔️ Sincronizar con la Nube", type="primary", use_container_width=True):
    df_subir = df_editado.drop(columns=["Monto (USD)", "Estado"]) # Solo subimos datos base
    df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace("NaT", "")
    hoja.clear()
    hoja.append_row(df_subir.columns.tolist())
    hoja.append_rows(df_subir.values.tolist())
    st.success("✅ ¡Sincronizado!")
    st.rerun()
