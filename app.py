import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==================== CONFIGURACIÓN INICIAL ====================
st.set_page_config(page_title="PlatitAI", layout="wide")

# Estilo de marca
BRAND_STYLE = """
    <h1 style='text-align: center; color: #00A8E8; font-family: sans-serif;'>PlatitAI</h1>
    <p style='text-align: center; color: #666;'>Gestión Financiera Inteligente</p>
"""

# Inicializar todos los estados de sesión necesarios al principio
if 'data' not in st.session_state:
    st.session_state.data = None
if 'tipo_data' not in st.session_state:
    st.session_state.tipo_data = None
if 'budgets' not in st.session_state:
    st.session_state.budgets = {}
if 'fijos' not in st.session_state:
    st.session_state.fijos = []
if 'mis_categorias' not in st.session_state:
    st.session_state.mis_categorias = [
        'Supermercados', 'Restaurantes & Delivery', 'Transporte & Auto', 
        'Salud & Bienestar', 'Hogar & Servicios', 'Viajes & Ocio', 
        'Compras & Tech', 'Transferencias & Otros'
    ]

# ==================== FUNCIONES DE PROCESAMIENTO ====================

def aplicar_inteligencia(df, categorias_usuario):
    # Crear columna Comercio limpia
    df['Comercio'] = df['Descripcion'].astype(str).str.upper().str.replace('*', '', regex=False).str.strip()
    
    reglas_ia = {
        'Supermercados': ['wong', 'metro', 'tottus', 'mass', 'oxxo', 'tambo'],
        'Restaurantes & Delivery': ['rappi', 'pedidosya', 'starbucks', 'kfc', 'cafe', 'pizz'],
        'Transporte & Auto': ['uber', 'cabify', 'taxi', 'grifo', 'peaje', 'gasolin'],
        'Salud & Bienestar': ['farmacia', 'clinica', 'smart fit', 'smartfit', 'dent', 'fisio', 'pacifico'],
        'Hogar & Servicios': ['sodimac', 'maestro', 'promart', 'movistar', 'claro', 'sedapal', 'notaria'],
        'Viajes & Ocio': ['airbnb', 'booking', 'latam', 'spotify', 'youtube', 'netflix'],
        'Compras & Tech': ['apple', 'aliexpress', 'amazon', 'ebay', 'h&m', 'zara'],
        'Transferencias & Otros': ['plin-', 'yape', 'transferencia']
    }

    # Categoría por defecto
    df['Categoria_Final'] = categorias_usuario[-1] if categorias_usuario else "Otros"
    
    # Aplicar reglas basadas en el diccionario
    for cat, palabras in reglas_ia.items():
        if cat in categorias_usuario:
            patron = '|'.join(palabras)
            mask = df['Descripcion'].str.contains(patron, case=False, na=False)
            df.loc[mask, 'Categoria_Final'] = cat
    
    # Si el archivo ya tiene una columna 'Categoria' válida, la priorizamos
    if 'Categoria' in df.columns:
        df['Categoria'] = df['Categoria'].fillna('').astype(str).str.strip()
        mask_valid = df['Categoria'].isin(categorias_usuario)
        df.loc[mask_valid, 'Categoria_Final'] = df['Categoria']

    return df

def cargar_y_procesar(file, is_excel=False):
    try:
        if is_excel:
            df = pd.read_excel(file)
        else:
            try:
                df = pd.read_csv(file, encoding='utf-8-sig', sep=',', quoting=3)
            except:
                df = pd.read_csv(file, encoding='latin1', sep=',', quoting=3)
        
        # Limpieza de nombres de columnas
        df.columns = df.columns.str.replace('"', '').str.strip()
        
        # Validar columnas mínimas
        if not {'Fecha', 'Descripcion', 'Monto'}.issubset(df.columns):
            st.error("El archivo no tiene las columnas necesarias: Fecha, Descripcion, Monto")
            return None
            
        # Limpieza de datos
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = pd.to_numeric(df['Monto'].astype(str).str.replace('"', '', regex=False), errors='coerce')
        df = df.dropna(subset=['Monto', 'Fecha']).drop_duplicates()
        
        # Aplicar inteligencia
        df = aplicar_inteligencia(df, st.session_state.mis_categorias)
        return df
    except Exception as e:
        st.error(f"Error crítico al procesar: {e}")
        return None

# ==================== NAVEGACIÓN LATERAL ====================

with st.sidebar:
    st.markdown(BRAND_STYLE, unsafe_allow_html=True)
    st.markdown("---")
    
    if st.session_state.data is not None:
        # Controles de moneda
        st.subheader("💱 Ajustes de Moneda")
        moneda_display = st.radio("Visualizar en:", ["Soles (S/)", "Dólares ($)"])
        tipo_cambio = st.number_input("Tipo de cambio:", value=3.75, step=0.05)
        
        st.markdown("---")
        # Menú principal
        menu = st.radio("Menú", ["🔥 Dashboard", "🎯 Presupuestos", "🕵️ Inteligencia", "✏️ Recategorizar", "⚙️ Exportar"])
        
        st.markdown("---")
        if st.button("🗑️ Salir y Borrar Todo"):
            st.session_state.data = None
            st.rerun()
    else:
        menu = "Inicio"

# ==================== LÓGICA DE PÁGINAS ====================

if st.session_state.data is None:
    st.title("Bienvenido a PlatitAI")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("1. Configura tus Categorías")
        txt_cats = st.text_area("Una categoría por línea:", value="\n".join(st.session_state.mis_categorias), height=150)
        if st.button("Guardar Estructura"):
            st.session_state.mis_categorias = [c.strip() for c in txt_cats.split("\n") if c.strip()]
            st.success("Estructura actualizada.")
            
        st.markdown("---")
        st.subheader("2. Carga tus Datos")
        
        # Carga de Ejemplo
        if st.button("🚀 Ver con Datos de Ejemplo (gastos.csv)"):
            if os.path.exists('gastos.csv'):
                res = cargar_y_procesar('gastos.csv')
                if res is not None:
                    st.session_state.data = res
                    st.session_state.tipo_data = "MODO EJEMPLO"
                    st.rerun()
            else:
                st.error("No se encontró el archivo gastos.csv")
        
        # Carga de Usuario
        u_file = st.file_uploader("Sube tu CSV o Excel", type=["csv", "xlsx"])
        if u_file:
            if st.button("Procesar mi archivo"):
                res = cargar_y_procesar(u_file, u_file.name.endswith('.xlsx'))
                if res is not None:
                    st.session_state.data = res
                    st.session_state.tipo_data = "TUS DATOS"
                    st.rerun()
    
    with c2:
        st.image("https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=500")
        st.info("PlatitAI detectará automáticamente tus consumos de Uber, Rappi, Wong y más.")

else:
    # --- PROCESAMIENTO DE MONEDA ANTES DE MOSTRAR ---
    working_df = st.session_state.data.copy()
    symbol = "S/" if moneda_display == "Soles (S/)" else "$"
    if symbol == "$":
        working_df['Monto'] = working_df['Monto'] / tipo_cambio

    working_df['Mes'] = working_df['Fecha'].dt.strftime('%Y-%m')
    working_df['Dia'] = working_df['Fecha'].dt.day

    # Título Dinámico
    title_color = "#888" if st.session_state.tipo_data == "MODO EJEMPLO" else "#2E7D32"
    st.markdown(f"<h1 style='text-align: center; color: {title_color};'>{st.session_state.tipo_data}</h1>", unsafe_allow_html=True)
    
    # Filtros comunes (Sidebar)
    all_months = sorted(working_df['Mes'].unique())
    sel_months = st.sidebar.multiselect("Meses", all_months, default=all_months[-2:])
    sel_cats = st.sidebar.multiselect("Categorías", st.session_state.mis_categorias, default=st.session_state.mis_categorias)
    
    df_filtered = working_df[(working_df['Mes'].isin(sel_months)) & (working_df['Categoria_Final'].isin(sel_cats))]

    # --- PÁGINAS DEL DASHBOARD ---

    if menu == "🔥 Dashboard":
        # Métricas MoM
        if len(sel_months) >= 1:
            mes_actual = sel_months[-1]
            total_mes = working_df[working_df['Mes'] == mes_actual]['Monto'].sum()
            
            # Comparar con anterior
            idx = all_months.index(mes_actual)
            if idx > 0:
                total_prev = working_df[working_df['Mes'] == all_months[idx-1]]['Monto'].sum()
                delta = ((total_mes / total_prev) - 1) * 100
            else:
                delta = 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric(f"Gasto en {mes_actual}", f"{symbol} {total_mes:,.2f}", f"{delta:.1f}% vs mes anterior", delta_color="inverse")
            col2.metric("N° Transacciones", len(df_filtered))
            col3.metric("Ticket Promedio", f"{symbol} {df_filtered['Monto'].mean():,.2f}" if not df_filtered.empty else "0")

        st.markdown("---")
        # Gráfico evolutivo por día
        st.subheader("📈 Patrón de Gasto Diario (Día 1 al 31)")
        daily = df_filtered.groupby('Dia')['Monto'].sum().reset_index()
        st.plotly_chart(px.line(daily, x='Dia', y='Monto', markers=True), use_container_width=True)

    elif menu == "🎯 Presupuestos":
        st.header("Metas de Gasto")
        col_limit, col_fijos = st.columns(2)
        with col_limit:
            cat_limit = st.selectbox("Categoría para limitar", st.session_state.mis_categorias)
            val_limit = st.number_input(f"Monto máximo ({symbol})", value=500)
            if st.button("Fijar Meta"):
                st.session_state.budgets[cat_limit] = val_limit
            st.write("Límites actuales:", st.session_state.budgets)

    elif menu == "🕵️ Inteligencia":
        t1, t2 = st.tabs(["🐜 Gastos Hormiga", "🕵️ Suscripciones"])
        with t1:
            umbral = st.slider("Monto hormiga:", 5, 50, 20)
            hormigas = df_filtered[df_filtered['Monto'] <= umbral]
            st.error(f"Total Hormiga: {symbol} {hormigas['Monto'].sum():,.2f}")
            st.plotly_chart(px.pie(hormigas, names='Comercio', values='Monto'), use_container_width=True)
        with t2:
            recurrentes = st.session_state.data.groupby(['Comercio', 'Monto']).agg(Veces=('Fecha', 'count'), Meses=('Fecha', lambda x: x.dt.to_period('M').nunique())).reset_index()
            st.table(recurrentes[recurrentes['Meses'] >= 2])

    elif menu == "✏️ Recategorizar":
        st.header("Edición en Lote")
        res = st.session_state.data.groupby('Comercio').agg(Total=('Monto', 'sum'), Cat=('Categoria_Final', 'first')).reset_index().sort_values('Total', ascending=False)
        res['Nueva'] = res['Cat']
        editado = st.data_editor(res, column_config={"Nueva": st.column_config.SelectboxColumn("Cambiar a:", options=st.session_state.mis_categorias)}, hide_index=True, use_container_width=True)
        if st.button("💾 Guardar Cambios"):
            for _, row in editado.iterrows():
                st.session_state.data.loc[st.session_state.data['Comercio'] == row['Comercio'], 'Categoria_Final'] = row['Nueva']
            st.rerun()

    elif menu == "⚙️ Exportar":
        st.header("Datos Finales")
        st.dataframe(df_filtered)
        csv = st.session_state.data.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Descargar CSV Limpio", csv, "platit_limpio.csv", "text/csv")
