import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

# Configuración de página
st.set_page_config(page_title="PlatitAI - Inteligencia Financiera", layout="wide")

# ==================== ESTADO DE SESIÓN ====================
if 'data' not in st.session_state:
    st.session_state.data = None
if 'tipo_data' not in st.session_state:
    st.session_state.tipo_data = None
if 'mis_categorias' not in st.session_state:
    st.session_state.mis_categorias = [
        'Supermercados', 'Restaurantes & Delivery', 'Transporte & Auto', 
        'Salud & Bienestar', 'Hogar & Servicios', 'Viajes & Ocio', 
        'Compras & Tech', 'Transferencias & Otros'
    ]

# ==================== LÓGICA DE EXTRACCIÓN (GMAIL STYLE) ====================

def extraer_datos_de_texto(cuerpo, fecha_msg):
    """Simula la lógica de tu script de Apps Script para procesar correos"""
    # 1. Extracción de Monto y Moneda
    monto_regex = r"(?:consumo de|Total|Monto|Importe)\D*([S\/$]+)\D*([0-9,.]+)"
    match = re.search(monto_regex, cuerpo, re.IGNORECASE)
    
    monto = 0.0
    moneda = "S/"
    if match:
        moneda = "$" if "$" in match.group(1) else "S/"
        monto = float(match.group(2).replace(",", ""))

    # 2. Extracción de Comercio
    comercio = "Desconocido"
    emp_match = re.search(r"Empresa\s+([^\n\r]+)", cuerpo, re.IGNORECASE)
    if emp_match:
        comercio = emp_match.group(1).split(" con tu ")[0].strip()
        
    return {
        "Fecha": fecha_msg,
        "Descripcion": comercio,
        "Monto": monto,
        "Moneda": moneda
    }

# ==================== CARGA Y PROCESAMIENTO ====================

def aplicar_inteligencia(df, categorias_usuario):
    df['Comercio'] = df['Descripcion'].str.upper().str.strip()
    
    reglas = {
        'Supermercados': ['wong', 'metro', 'tottus', 'mass', 'oxxo', 'tambo'],
        'Restaurantes & Delivery': ['rappi', 'pedidosya', 'starbucks', 'kfc', 'mcdonalds', 'cafe'],
        'Transporte & Auto': ['uber', 'cabify', 'taxi', 'grifo', 'peaje'],
        'Salud & Bienestar': ['farmacia', 'clinica', 'smart fit', 'pacifico'],
        'Hogar & Servicios': ['sodimac', 'maestro', 'promart', 'enel', 'sedapal'],
        'Viajes & Ocio': ['airbnb', 'booking', 'latam', 'netflix', 'spotify'],
        'Compras & Tech': ['apple', 'aliexpress', 'amazon', 'falabella'],
        'Transferencias & Otros': ['plin-', 'yape', 'transferencia']
    }
    
    default_cat = categorias_usuario[-1] if categorias_usuario else "Otros"
    df['Categoria_Final'] = default_cat
    
    for cat_maestra, palabras in reglas.items():
        if cat_maestra in categorias_usuario:
            patron = '|'.join(palabras)
            mask = df['Descripcion'].str.contains(patron, case=False, na=False)
            df.loc[mask, 'Categoria_Final'] = cat_maestra
            
    return df

# ==================== PANTALLA DE INICIO ====================

if st.session_state.data is None:
    st.markdown("<h1 style='text-align: center; color: #00A8E8;'>PlatitAI</h1>", unsafe_allow_html=True)
    
    tab_manual, tab_gmail = st.tabs(["📄 Carga Manual", "📧 Conectar Gmail (Beta)"])
    
    with tab_manual:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Sube tus estados de cuenta")
            file = st.file_uploader("CSV o Excel", type=["csv", "xlsx"])
            if st.button("🚀 Usar Datos de Ejemplo"):
                if os.path.exists('gastos.csv'):
                    # Lógica de carga similar a las versiones anteriores
                    st.session_state.data = pd.read_csv('gastos.csv', encoding='latin1')
                    st.session_state.data = aplicar_inteligencia(st.session_state.data, st.session_state.mis_categorias)
                    st.session_state.tipo_data = "Ejemplo"
                    st.rerun()
        with col2:
            st.markdown("### Configuración de Categorías")
            cats = st.text_area("Categorías maestras:", value="\n".join(st.session_state.mis_categorias), height=150)
            if st.button("Guardar"):
                st.session_state.mis_categorias = [c.strip() for c in cats.split("\n") if c.strip()]

    with tab_gmail:
        st.markdown("### Importación Automática desde Gmail")
        st.info("PlatitAI buscará correos de 'notificaciones@notificacionesbcp.com.pe' y otros bancos.")
        
        c1, c2 = st.columns(2)
        with c1:
            fecha_inicio = st.date_input("Desde qué fecha buscar", pd.to_datetime("2025-01-01"))
        with c2:
            palabras_clave = st.text_input("Palabras clave de búsqueda", '("Tarjeta de Débito BCP" OR "Tarjeta de Crédito BCP" OR "Consumo")')
        
        if st.button("🔍 Escanear Correos y Sincronizar"):
            # Aquí iría la integración con google-auth-oauthlib para Python
            st.warning("Para habilitar la conexión real en GitHub, necesitas configurar tus Credenciales de Google Cloud (OAuth 2.0).")
            st.markdown("""
            **Pasos para activar:**
            1. Ve a [Google Cloud Console](https://console.cloud.google.com/).
            2. Crea un proyecto y habilita la **Gmail API**.
            3. Descarga tu `credentials.json` y súbelo como un 'Secret' en Streamlit Cloud.
            """)

# ==================== DASHBOARD Y ANÁLISIS ====================
# (Aquí continúa el código del Dashboard, Suscripciones, Gastos Hormiga y Top 10 que definimos anteriormente)
if st.session_state.data is not None:
    # Muestra el dashboard con los datos cargados o importados
    st.sidebar.markdown(f"**Modo:** {st.session_state.tipo_data}")
    # ... resto del código de visualización ...
