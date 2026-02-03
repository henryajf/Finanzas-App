import streamlit as st
import pandas as pd
import requests
import gspread
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date, datetime, timedelta

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Finanzas AR 🇦🇷", page_icon="💳", layout="wide")

st.markdown("""<style>.stMetric { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 12px; border-left: 5px solid #6200EE; }</style>""", unsafe_allow_html=True)

ICONOS_MAP = {
    "🏠 Vivienda": "🏠", "⚡ Servicios": "⚡", "📺 Suscripción": "📺", 
    "🛒 Alimentos": "🛒", "🚗 Transporte": "🚗", "💳 Tarjetas": "💳", 
    "📈 Inversiones": "📈", "👪 Familia": "👪", "🏥 Salud": "🏥", "🎭 Ocio": "🎭"
}

# --- 2. CONEXIÓN CON CACHÉ ---
@st.cache_resource
def obtener_cliente_gspread():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json", scope)
    except:
        info_json = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info_json, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos_gsheet():
    client = obtener_cliente_gspread()
    hoja = client.open("Gastos_Henry").sheet1
    data_raw = hoja.get_all_values()
    if not data_raw or len(data_raw) < 2: return pd.DataFrame()
    
    # Usamos la primera fila como encabezados
    df = pd.DataFrame(data_raw[1:], columns=data_raw[0])
    
    # NORMALIZACIÓN DE COLUMNAS (Para que no falle si cambia el nombre)
    df.columns = [c.strip() for c in df.columns]
    
    # Mapeo flexible: buscamos columnas que contengan estas palabras clave
    def buscar_col(keywords, default):
        for c in df.columns:
            if any(k.lower() in c.lower() for k in keywords): return c
        return default

    col_monto = buscar_col(["monto", "ars"], "Monto (ARS)")
    col_fecha = buscar_col(["fecha", "pago", "venc"], "Día Pago")
    col_pago = buscar_col(["pagado", "listo"], "Pagado")
    
    # Aseguramos que existan las columnas con nombres estándar
    if col_monto in df.columns: df["Monto (ARS)"] = pd.to_numeric(df[col_monto], errors='coerce').fillna(0)
    else: df["Monto (ARS)"] = 0
        
    if col_fecha in df.columns: df["Día Pago"] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
    else: df["Día Pago"] = None
        
    if col_pago in df.columns: 
        df["Pagado"] = df[col_pago].apply(lambda x: str(x).upper() in ["TRUE", "VERDADERO", "1", "✅"])
    else: df["Pagado"] = False

    return df[["Categoría", "Ítem", "Monto (ARS)", "Día Pago", "Pagado"]].copy()

def get_dolar_blue():
    try:
        return float(requests.get("https://dolarapi.com/v1/dolares/blue").json()['venta'])
    except: return 1450.0

# --- 3. PROCESAMIENTO ---
precio_dolar = get_dolar_blue()
df = cargar_datos_gsheet()

if not df.empty:
    # Cálculos Totales
    total_ars = df["Monto (ARS)"].sum()
    total_usd = total_ars / precio_dolar
    pend_ars = df[df["Pagado"] == False]["Monto (ARS)"].sum()
    pend_usd = pend_ars / precio_dolar

    # Lógica de Porcentaje y Conversión
    df["Peso (%)"] = df["Monto (ARS)"] / total_ars if total_ars > 0 else 0
    df["USD"] = df["Monto (ARS)"] / precio_dolar
    df["Icono"] = df["Categoría"].apply(lambda x: next((v for k, v in ICONOS_MAP.items() if x in k), "❓"))
    
    # Estado visual
    df["Estado"] = df.apply(lambda r: "✅ Listo" if r["Pagado"] else ("🔴 Vencido" if r["Día Pago"] and r["Día Pago"] < date.today() else "🟢 Al Día"), axis=1)

    # Ordenar: Pendientes arriba
    df = df.sort_values(by=["Pagado", "Día Pago"], ascending=[True, True])
else:
    total_ars = total_usd = pend_ars = pend_usd = 0

# --- 4. DASHBOARD SUPERIOR ---
st.title("Finanzas AR 🇦🇷")
st.caption(f"📅 Hoy: {date.today().strftime('%d/%m/%Y')} | 💵 Tasa Dólar Blue: **${precio_dolar:,.0f}**")

# Métricas Principales
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Gastos (ARS)", f"${total_ars:,.0f}")
c2.metric("Total Gastos (USD)", f"U$S {total_usd:,.2f}")
c3.metric("Pendiente (ARS)", f"${pend_ars:,.0f}")
c4.metric("Pendiente (USD)", f"U$S {pend_usd:,.2f}")

st.divider()

# --- 5. GRÁFICO Y TABLA ---
if not df.empty:
    fig = px.pie(df, values='Monto (ARS)', names='Categoría', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig.add_annotation(text=f"Total<br>${total_ars:,.0f}", x=0.5, y=0.5, font_size=20, showarrow=False)
    fig.update_layout(showlegend=False, height=250, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📝 Gestión de Gastos")
    df_editado = st.data_editor(
        df,
        column_config={
            "Pagado": st.column_config.CheckboxColumn("¿Listo?", width="small"),
            "Icono": st.column_config.SelectboxColumn("Cat.", options=list(ICONOS_MAP.keys()), width="small"),
            "Categoría": None,
            "Monto (ARS)": st.column_config.NumberColumn("ARS", format="$%d", width="small"),
            "Peso (%)": st.column_config.ProgressColumn("Peso (%)", format="%.1f%%", min_value=0, max_value=1),
            "USD": st.column_config.NumberColumn("USD", format="U$S %.2f", disabled=True, width="small"),
            "Día Pago": st.column_config.DateColumn("Venc.", format="DD/MM", width="small"),
            "Estado": st.column_config.TextColumn("Estado", disabled=True, width="small")
        },
        column_order=("Pagado", "Icono", "Ítem", "Monto (ARS)", "Peso (%)", "USD", "Día Pago", "Estado"),
        num_rows="dynamic", use_container_width=True, hide_index=True
    )
else:
    st.warning("⚠️ No se encontraron datos. Verifica que tu Google Sheets tenga los encabezados correctos.")

# --- 6. GUARDADO ---
if st.button("✔️ Guardar y Sincronizar", type="primary", use_container_width=True):
    try:
        df_save = df_editado.copy()
        df_save["Categoría"] = df_save["Icono"].apply(lambda x: x.split(" ")[-1] if " " in x else x)
        df_subir = df_save[["Categoría", "Ítem", "Monto (ARS)", "Día Pago", "Pagado"]]
        df_subir["Día Pago"] = df_subir["Día Pago"].astype(str).replace(["NaT", "None", "nan"], "")
        
        st.cache_data.clear()
        hoja = obtener_cliente_gspread().open("Gastos_Henry").sheet1
        hoja.clear()
        hoja.append_row(df_subir.columns.tolist())
        hoja.append_rows(df_subir.values.tolist())
        st.success("✅ ¡Datos restaurados y guardados!")
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
