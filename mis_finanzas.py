import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(page_title="Finanzas Cloud", page_icon="☁️", layout="wide")

hide_st_style = """<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} .block-container {padding-top: 1rem;}</style>"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 1. CONEXIÓN CON GOOGLE SHEETS ---
def conectar_google_sheets():
    # Definimos el alcance (permisos)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Buscamos las credenciales. 
    # Primero intenta buscar el archivo local 'mis-credenciales.json'
    # Si no está, intenta buscar en los 'Secretos' de Streamlit Cloud (para cuando lo subas)
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("mis-credenciales.json", scope)
    except:
        # Esto servirá cuando lo subas a la nube en el futuro
        import json
        info_json = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info_json, scope)
        
    client = gspread.authorize(creds)
    
    # Abrimos la hoja por su nombre
    sheet = client.open("Gastos_Henry").sheet1
    return sheet

# --- 2. FUNCIONES DE DATOS ---
def get_dolar_blue():
    try:
        url = "https://dolarapi.com/v1/dolares/blue"
        r = requests.get(url)
        return float(r.json()['venta'])
    except:
        return 1476.00

def cargar_datos(sheet):
    data = sheet.get_all_records()
    if not data: # Si la hoja está vacía, devuelve estructura vacía
        return pd.DataFrame(columns=["Categoría", "Ítem", "Monto (ARS)", "Monto (USD)", "Día Pago"])
    return pd.DataFrame(data)

# --- INICIO DE LA APP ---
precio_dolar = get_dolar_blue()

try:
    hoja = conectar_google_sheets()
    df = cargar_datos(hoja)
    st.toast("☁️ Conectado a Google Drive exitosamente")
except Exception as e:
    st.error(f"⚠️ Error conectando a Google: {e}")
    st.stop()

# Si la hoja es nueva y no tiene columnas, creamos una estructura base para que no falle
if df.empty:
    df = pd.DataFrame({
        "Categoría": ["Ejemplo"], "Ítem": ["Prueba"], "Monto (ARS)": [0], "Monto (USD)": [0], "Día Pago": ["1"]
    })

# Cálculos al vuelo (siempre actualizados)
# Aseguramos que Monto (ARS) sea número
df["Monto (ARS)"] = pd.to_numeric(df["Monto (ARS)"], errors='coerce').fillna(0)
df["Monto (USD)"] = df["Monto (ARS)"] / precio_dolar

# Reordenamos
df = df[["Categoría", "Ítem", "Monto (ARS)", "Monto (USD)", "Día Pago"]]

# --- INTERFAZ ---
st.title("☁️ Finanzas en la Nube")
st.caption(f"Dólar Blue: **${precio_dolar:,.0f}**")

# Métricas
total_ars = df["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar
c1, c2 = st.columns(2)
c1.metric("Total Pesos", f"${total_ars:,.0f}")
c2.metric("Total USD", f"US$ {total_usd:,.0f}")

st.divider()

tab1, tab2 = st.tabs(["📊 Ver Gráficos", "📝 Editar en Drive"])

with tab1:
    if not df.empty and total_ars > 0:
        gastos_cat = df.groupby("Categoría")["Monto (ARS)"].sum().reset_index()
        fig = px.pie(gastos_cat, values='Monto (ARS)', names='Categoría', hole=0.6)
        fig.update_layout(legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Agrega gastos para ver gráficos.")

with tab2:
    st.caption("Edita aquí. Al guardar, se actualiza tu Google Sheet real.")
    
    df_editado = st.data_editor(
        df,
        column_config={
            "Monto (ARS)": st.column_config.NumberColumn(format="$%d"),
            "Monto (USD)": st.column_config.NumberColumn(format="$%.1f", disabled=True),
            "Categoría": st.column_config.SelectboxColumn(
                options=["Vivienda", "Servicios", "Suscripción", "Alimentos", "Deportes", "Transporte", "Ocio", "Salud"]
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    
    if st.button("💾 Guardar en Google Drive", type="primary", use_container_width=True):
        # Limpieza antes de subir
        df_subir = df_editado.copy()
        # Quitamos la columna USD porque esa se calcula sola, no queremos ensuciar el Excel
        df_subir = df_subir.drop(columns=["Monto (USD)"])
        
        # Subir a Google Sheets (Borra todo y escribe lo nuevo)
        try:
            hoja.clear() # Borra contenido viejo
            # Escribir encabezados
            hoja.append_row(df_subir.columns.tolist())
            # Escribir datos
            hoja.append_rows(df_subir.values.tolist())
            st.success("✅ ¡Guardado en la Nube! Revisa tu Google Sheet.")
            st.rerun() # Recarga para ver los cambios
        except Exception as e:
            st.error(f"Error guardando: {e}")