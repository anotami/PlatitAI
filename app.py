import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuración de página
st.set_page_config(page_title="PlatitAI - Gestor Financiero", layout="wide")

# ==================== ESTADO DE SESIÓN ====================
if 'data' not in st.session_state:
    st.session_state.data = None

if 'tipo_data' not in st.session_state:
    st.session_state.tipo_data = None # Para saber si es "Ejemplo" o "Usuario"

if 'mis_categorias' not in st.session_state:
    st.session_state.mis_categorias = [
        'Supermercados', 'Restaurantes & Delivery', 'Transporte & Auto', 
        'Salud & Bienestar', 'Hogar & Servicios', 'Viajes & Ocio', 
        'Compras & Tech', 'Transferencias & Otros'
    ]

# ==================== FUNCIONES DE PROCESAMIENTO ====================

def aplicar_inteligencia(df, categorias_usuario):
    df['Comercio'] = df['Descripcion'].str.upper().str.replace('*', '', regex=False).str.strip()
    
    reglas = {
        'Supermercados': ['wong', 'metro', 'tottus', 'mass', 'oxxo', 'tambo', 'market', 'jumbo', 'carrefour'],
        'Restaurantes & Delivery': ['rappi', 'pedidosya', 'dominos', 'restaurante', 'cafe', 'starbucks', 'kfc', 'mcdonalds'],
        'Transporte & Auto': ['uber', 'cabify', 'taxi', 'grifo', 'peaje', 'estacion', 'apparka', 'rutas de lima'],
        'Salud & Bienestar': ['farmacia', 'clinica', 'pacifico', 'smart fit', 'smartfit', 'dent', 'fisio', 'spa'],
        'Hogar & Servicios': ['sodimac', 'maestro', 'promart', 'movistar', 'claro', 'enel', 'sedapal', 'notaria'],
        'Viajes & Ocio': ['airbnb', 'booking', 'latam', 'hotel', 'cineplanet', 'spotify', 'youtube', 'despegar', 'avianca'],
        'Compras & Tech': ['apple', 'aliexpress', 'amazon', 'ebay', 'dji', 'h&m', 'zara', 'miniso', 'tai loy', 'falabella'],
        'Transferencias & Otros': ['plin-', 'yape', 'cargo da ']
    }
    
    default_cat = categorias_usuario[-1] if categorias_usuario else "Sin Categoría"
    df['Categoria_Final'] = default_cat
    
    for cat_maestra, palabras in reglas.items():
        if cat_maestra in categorias_usuario:
            patron = '|'.join(palabras)
            mask = df['Descripcion'].str.contains(patron, case=False, na=False)
            df.loc[mask, 'Categoria_Final'] = cat_maestra
    
    if 'Categoria' in df.columns:
        mask_manual = df['Categoria'].isin(categorias_usuario)
        df.loc[mask_manual, 'Categoria_Final'] = df['Categoria']
    
    return df

def cargar_datos(file, is_excel=False):
    try:
        df = pd.read_excel(file) if is_excel else pd.read_csv(file, encoding='latin1', sep=',', quoting=3)
        df.columns = df.columns.str.replace('"', '').str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = pd.to_numeric(df['Monto'].astype(str).str.replace('"', '', regex=False), errors='coerce')
        df = df.dropna(subset=['Monto', 'Fecha'])
        return aplicar_inteligencia(df, st.session_state.mis_categorias)
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# ==================== BARRA LATERAL (MENÚ) ====================

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #00A8E8;'>PlatitAI</h1>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?q=80&w=200", use_container_width=True)
    st.markdown("---")
    
    if st.session_state.data is None:
        st.info("Sube tus datos para habilitar el menú")
        menu = "Inicio"
    else:
        menu = st.radio(
            "Navegación",
            ["🔥 Vista General", "📊 Análisis Detallado", "✏️ Recategorizar", "⚙️ Exportar"],
            index=0
        )
        st.markdown("---")
        if st.button("🗑️ Reiniciar Sesión", use_container_width=True):
            st.session_state.data = None
            st.session_state.tipo_data = None
            st.rerun()

# ==================== LÓGICA DE PÁGINAS ====================

if st.session_state.data is None:
    # --- PANTALLA DE INICIO ---
    st.title("Bienvenido a PlatitAI")
    
    col_txt, col_cfg = st.columns([1, 1])
    
    with col_txt:
        st.markdown("""
        ### Tu dinero, bajo control.
        Organiza tus movimientos bancarios de forma inteligente.
        
        **Pasos:**
        1. Ajusta tus categorías a la derecha.
        2. Selecciona datos de ejemplo o sube los tuyos.
        """)
        
        uploaded_file = st.file_uploader("Subir CSV o Excel", type=["csv", "xlsx"])
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 Usar Datos de Ejemplo", use_container_width=True):
                if os.path.exists('gastos.csv'):
                    st.session_state.data = cargar_datos('gastos.csv')
                    st.session_state.tipo_data = "Ejemplo"
                    st.rerun()
                else:
                    st.error("gastos.csv no encontrado.")
        with c2:
            if uploaded_file and st.button("Procesar Mi Archivo", use_container_width=True):
                st.session_state.data = cargar_datos(uploaded_file, uploaded_file.name.endswith('.xlsx'))
                st.session_state.tipo_data = "Usuario"
                st.rerun()

    with col_cfg:
        st.subheader("⚙️ Configuración inicial")
        cats_editadas = st.text_area(
            "Define tus categorías (una por línea):", 
            value="\n".join(st.session_state.mis_categorias),
            height=180
        )
        if st.button("💾 Guardar Estructura"):
            st.session_state.mis_categorias = [c.strip() for c in cats_editadas.split("\n") if c.strip()]
            st.success("Estructura guardada.")

else:
    # --- CABECERA DINÁMICA ---
    if st.session_state.tipo_data == "Ejemplo":
        st.markdown("<h1 style='text-align: center; color: #888888;'>🛠️ Datos de Ejemplo</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #2E7D32;'>👤 Tus Datos</h1>", unsafe_allow_html=True)
    
    st.markdown("---")

    df = st.session_state.data
    df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')
    
    # Filtros comunes en Sidebar
    with st.sidebar:
        st.subheader("🔍 Filtros")
        meses = sorted(df['Mes'].unique())
        meses_sel = st.multiselect("Meses", meses, default=meses)
        
        categorias_presentes = sorted(df['Categoria_Final'].unique())
        cats_sel = st.multiselect("Categorías", categorias_presentes, default=categorias_presentes)
    
    df_f = df[(df['Mes'].isin(meses_sel)) & (df['Categoria_Final'].isin(cats_sel))]

    if menu == "🔥 Vista General":
        m1, m2, m3 = st.columns(3)
        m1.metric("Gasto Total", f"S/ {df_f['Monto'].sum():,.2f}")
        m2.metric("Operaciones", len(df_f))
        m3.metric("Ticket Promedio", f"S/ {df_f['Monto'].mean():,.2f}" if not df_f.empty else "0")
        
        st.markdown("---")
        if not df_f.empty:
            pivot = df_f.pivot_table(index='Categoria_Final', columns='Mes', values='Monto', aggfunc='sum').fillna(0)
            st.subheader("Mapa de Calor: Intensidad Mensual")
            st.plotly_chart(px.imshow(pivot, text_auto='.0f', color_continuous_scale='Blues', aspect="auto"), use_container_width=True)

    elif menu == "📊 Análisis Detallado":
        st.subheader("Gasto Acumulado por Mes")
        fig_bar = px.bar(df_f.groupby(['Mes', 'Categoria_Final'])['Monto'].sum().reset_index(), 
                        x='Mes', y='Monto', color='Categoria_Final', text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)
        
        c_l, c_r = st.columns(2)
        with c_l:
            st.subheader("Top 10 Comercios")
            top_c = df_f.groupby('Comercio')['Monto'].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_c, x='Monto', y='Comercio', orientation='h', color='Monto'), use_container_width=True)
        with c_r:
            st.subheader("Composición por Categoría")
            st.plotly_chart(px.pie(df_f, names='Categoria_Final', values='Monto', hole=0.4), use_container_width=True)

    elif menu == "✏️ Recategorizar":
        st.header("✏️ Editor Manual")
        st.write("Cambia la categoría de un comercio para todos sus registros.")
        
        resumen = df.groupby('Comercio').agg(
            Total=('Monto', 'sum'),
            Categoria_Actual=('Categoria_Final', 'first')
        ).reset_index().sort_values('Total', ascending=False)

        resumen['Nueva_Categoria'] = resumen['Categoria_Actual']

        df_editado = st.data_editor(
            resumen,
            column_config={
                "Nueva_Categoria": st.column_config.SelectboxColumn(
                    "🎯 Nueva Categoria", 
                    options=st.session_state.mis_categorias
                )
            },
            disabled=["Comercio", "Total", "Categoria_Actual"],
            hide_index=True,
            use_container_width=True
        )

        if st.button("💾 Aplicar Cambios"):
            for _, row in df_editado.iterrows():
                if row['Categoria_Actual'] != row['Nueva_Categoria']:
                    st.session_state.data.loc[st.session_state.data['Comercio'] == row['Comercio'], 'Categoria_Final'] = row['Nueva_Categoria']
            st.success("Dashboard actualizado.")
            st.rerun()

    elif menu == "⚙️ Exportar":
        st.header("⚙️ Gestión de Datos")
        st.write("Revisa tu tabla final y descárgala.")
        st.dataframe(df_f[['Fecha', 'Comercio', 'Categoria_Final', 'Monto']].sort_values('Fecha', ascending=False), use_container_width=True)
        
        csv_download = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Datos Procesados (CSV)", data=csv_download, file_name="platit_data.csv", mime="text/csv")
