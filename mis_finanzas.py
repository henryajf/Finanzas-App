import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Finanzas Personales", page_icon="💰", layout="wide")

# --- 1. OBTENER DOLAR BLUE AUTOMÁTICO ---
def get_dolar_blue():
    try:
        url = "https://dolarapi.com/v1/dolares/blue"
        r = requests.get(url)
        data = r.json()
        return float(data['venta'])
    except:
        return 1476.00 # Valor de respaldo

precio_dolar = get_dolar_blue()

# --- 2. SISTEMA DE GUARDADO ---
ARCHIVO_CSV = "mis_gastos.csv"

if os.path.exists(ARCHIVO_CSV):
    df = pd.read_csv(ARCHIVO_CSV)
    df['Día Pago'] = df['Día Pago'].astype(str)
else:
    # Datos base
    data = {
        "Categoría": ["Suscripción", "Servicios", "Servicios", "Vivienda", "Suscripción", "Suscripción", 
                      "Servicios", "Suscripción", "Suscripción", "Vivienda", "Servicios", "Servicios", 
                      "Suscripción", "Alimentos", "Deportes", "Ocio", "Transporte"],
        "Ítem": ["Personal Flow", "AySA", "MetroGas", "Alquiler", "Google ONE", "Apple ONE", 
                 "ABL de AGIP", "Meli+", "VPN", "Expensas", "Internet", "Edesur", 
                 "Netflix", "Supermercado", "Gymnasio", "Recreación", "Trasporte"],
        "Monto (ARS)": [19732, 20267, 24469, 477850, 14746, 17639, 
                        14027, 3490, 4990, 111874, 34353, 45866, 
                        0, 0, 0, 0, 0],
        "Día Pago": ["26-1", "2-2", "2-2", "3-2", "4-2", "4-2", 
                     "6-2", "8-2", "14-2", "14-2", "21-2", "23-2", 
                     "N/A", "Var", "Var", "Var", "Var"]
    }
    df = pd.DataFrame(data)

# --- 3. CÁLCULO DE LA COLUMNA USD (NUEVO) ---
# Calculamos la columna al vuelo para que siempre esté actualizada con el dólar de HOY
df["Monto (USD)"] = df["Monto (ARS)"] / precio_dolar

# Reordenamos las columnas para que USD quede al lado de ARS
orden_columnas = ["Categoría", "Ítem", "Monto (ARS)", "Monto (USD)", "Día Pago"]
# Filtramos para asegurarnos de tener solo estas columnas
df = df[orden_columnas] 

# --- 4. INTERFAZ VISUAL ---
st.title("Finanzas personales")
st.markdown(f"**Dólar Blue Hoy:** :green[**${precio_dolar:,.2f}**]")

col1, col2 = st.columns([1.6, 1]) # Hice un poco más ancha la tabla

with col1:
    st.subheader("📝 Tus Gastos")
    
    # TABLA EDITABLE
    df_editado = st.data_editor(
        df,
        column_config={
            "Monto (ARS)": st.column_config.NumberColumn(format="$%d"),
            # Configuración NUEVA para la columna USD
            "Monto (USD)": st.column_config.NumberColumn(
                format="$%.2f",  # Muestra 2 decimales
                disabled=True,   # No se edita (se calcula solo)
                help="Calculado automáticamente según el Dólar Blue del día"
            ),
            "Día Pago": st.column_config.TextColumn("Fecha Pago", help="Ej: 05-02"),
            "Categoría": st.column_config.SelectboxColumn(
                options=["Vivienda", "Servicios", "Suscripción", "Alimentos", "Deportes", "Transporte", "Ocio", "Salud", "Deudas"]
            )
        },
        num_rows="dynamic",
        height=550,
        use_container_width=True
    )
    
    # BOTÓN GUARDAR
    if st.button("💾 Guardar Cambios", type="primary"):
        # Antes de guardar, borramos la columna USD para no ensuciar el archivo 
        # (ya que el dólar cambia todos los días, mejor recalcularla al abrir)
        df_a_guardar = df_editado.drop(columns=["Monto (USD)"])
        df_a_guardar.to_csv(ARCHIVO_CSV, index=False)
        st.success("¡Datos guardados! (Los montos en USD se recalcularán mañana con la nueva tasa).")

# --- 5. CÁLCULOS Y GRÁFICOS ---
total_ars = df_editado["Monto (ARS)"].sum()
total_usd = total_ars / precio_dolar

# Agrupar para gráfico
gastos_cat = df_editado.groupby("Categoría")["Monto (ARS)"].sum().reset_index()

with col2:
    st.subheader("💡 Resumen del Mes")
    
    m1, m2 = st.columns(2)
    m1.metric("Total en Pesos", f"${total_ars:,.0f}")
    m2.metric("Total en Dólares", f"US$ {total_usd:,.2f}")

    st.markdown("---")
    
    fig = px.pie(gastos_cat, values='Monto (ARS)', names='Categoría', 
                 title='Distribución de Gastos', hole=0.5)
    st.plotly_chart(fig, use_container_width=True)

    mayor_gasto = df_editado.loc[df_editado["Monto (ARS)"].idxmax()]
    st.warning(f"⚠️ Mayor gasto: **{mayor_gasto['Ítem']}** (${mayor_gasto['Monto (ARS)']:,.0f})")
