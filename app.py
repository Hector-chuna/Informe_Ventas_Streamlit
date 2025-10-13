import streamlit as st
import pandas as pd
from datetime import date
import sys
import os
import io # Necesario para leer el archivo subido en memoria

# Configuración para importar módulos desde src
# Nota: La carga de módulos desde 'src' necesita que 'src/__init__.py' exista.
# Asegúrate de que los archivos en 'src/' existen (data_processor, ui_handler, etc.)
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Importar las funciones modularizadas y nuevas
from src.data_processor import crear_campos_tiempo
from src.data_pivot import filtrar_datos, crear_tabla_dinamica
from src.visualizer import (
    crear_grafico_barras_comparativo, 
    crear_grafico_circular_proporcion, 
    crear_grafico_lineas_tendencia, 
    generar_pdf_informe
)
from src.formatter import formatear_miles, formatear_porcentaje, obtener_key_ordenamiento
# Importamos la configuración de campos para que la lógica de la barra lateral se ejecute.
from src.ui_handler import dibujar_barra_lateral_y_obtener_config, CAMPOS_INTERNOS 

# -----------------------------------------------------------
# CONSTANTES 
# -----------------------------------------------------------
METRICAS_BASE = {
    'Venta_Neta': 'Monto Total (TOTAL)', 
    'CANTIDAD': 'Cantidad de Unidades (CANTIDAD)'
}

# -----------------------------------------------------------
# FUNCIÓN DE VERIFICACIÓN (TERMINAL/CONSOLE) 
# -----------------------------------------------------------

def verificar_datos_terminal(df: pd.DataFrame):
    """Imprime contadores clave en la terminal para verificar el procesamiento."""
    
    if df.empty:
        print("⚠️ DataFrame vacío.")
        return
        
    # Usamos .get() con un valor por defecto para evitar KeyError en la terminal
    if 'Anio' not in df.columns:
        print("⚠️ DataFrame cargado, pero columnas de tiempo ('Anio', 'Mes') faltantes después del procesamiento.")
        return

    print("-" * 50)
    print(f"VERIFICACIÓN DE DATOS INICIAL (Filas: {len(df):,})")
    print("-" * 50)

    # Solo imprime si las columnas existen
    if 'Cliente_ID' in df.columns and 'Anio' in df.columns:
        clientes_anio = df.groupby('Anio')['Cliente_ID'].nunique()
        print("✅ Clientes Únicos por Año:")
        for anio, count in clientes_anio.items():
            print(f"  > {int(anio)}: {count:,} clientes")

    if 'Marca' in df.columns:
        print(f"✅ Total de Marcas Únicas: {df['Marca'].nunique():,}")
    
    if 'Venta_Neta' in df.columns:
        print(f"✅ Venta Neta Total (Acumulado): ${df['Venta_Neta'].sum():,.2f}")
    
    if 'Vendedor_ID' in df.columns:
        print(f"✅ Total de Vendedores Únicos: {df['Vendedor_ID'].nunique():,}")
        
    # --- CONTADORES DE REGISTROS POR TIPO DE PRODUCTO ---
    if 'Tipo_Producto' in df.columns:
        calzados = df[df['Tipo_Producto'].str.contains('CALZADO', na=False)]['Tipo_Producto'].count()
        confecciones = df[df['Tipo_Producto'].str.contains('CONFEC', na=False)]['Tipo_Producto'].count()
        
        print("\n📝 Conteo de Registros por Tipo de Producto (Estimado):")
        print(f"  > CALZADOS: {calzados:,} registros")
        print(f"  > CONFECCIONES: {confecciones:,} registros")
        
    print("-" * 50)

# -----------------------------------------------------------
# CONFIGURACIÓN INICIAL Y CACHÉ (CARGA Y PREPARACIÓN)
# -----------------------------------------------------------

@st.cache_data
def cargar_y_procesar_datos_completos(uploaded_file):
    """Carga el archivo subido de Streamlit y aplica el procesamiento inicial."""
    
    if uploaded_file is None:
        return None
        
    # Leer el archivo de Excel directamente desde la memoria
    try:
        df_cargado = pd.read_excel(uploaded_file)
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}") 
        return None
        
    if df_cargado.empty:
        return None
    
    df_procesado = df_cargado.copy()
    
    # Mapeo de columnas: Clave = Nombre en Excel | Valor = Nombre interno
    # ¡ESTOS NOMBRES SON CRÍTICOS Y SE HAN CORREGIDO AHORA!
    column_mapping = {
        'TOTAL': 'Venta_Neta', 
        'NOMBRE CLIENTE': 'Cliente_Nombre', # Tenía 'NOMBRE_CLIENTE'
        'COD.CLIENTE': 'Cliente_ID',       # Tenía 'COD_CLIENTE'
        'NOMBRE_VENDEDOR': 'Vendedor_Nombre',
        'C_VENDEDOR': 'Vendedor_ID',
        'MARCA': 'Marca',
        'Tipo': 'Tipo_Producto',           # Usamos 'Tipo' en el Excel para el interno 'Tipo_Producto'
        'F.OPERACION': 'Fecha_Operacion',  # ¡CORREGIDO! Tenía 'F_OPERACION'
        'TIPO1': 'TIPO1',
        'TIPO2': 'TIPO2',
        'TIPO3': 'TIPO3',
        'TIPO_VENTA': 'TIPO_VENTA',
        'CANTIDAD': 'CANTIDAD' 
    }
    
    # 1. RENOMBRAR CAMPOS (solo si existen)
    renaming_dict = {
        k: v for k, v in column_mapping.items() if k in df_procesado.columns
    }
    df_procesado = df_procesado.rename(columns=renaming_dict)
    
    # Si la columna clave 'Fecha_Operacion' no se pudo renombrar o no existe, salimos
    if 'Fecha_Operacion' not in df_procesado.columns or 'Venta_Neta' not in df_procesado.columns:
         st.error(f"Error de Columna: Las columnas clave ('TOTAL', 'F.OPERACION') no se encontraron o no se pudieron mapear correctamente.")
         return None
         
    # 2. CREAR CAMPOS DE TIEMPO
    # (ASUMIMOS QUE crear_campos_tiempo en src/data_processor.py ya está corregido para evitar KeyError)
    df_procesado = crear_campos_tiempo(df_procesado)
    
    # Si la creación de campos de tiempo falló (ej. fechas inválidas), puede que 'Anio' no exista
    if 'Anio' not in df_procesado.columns:
        # Este error solo salta si el procesador falló internamente después del renombrado
        st.error("Error de Procesamiento: No se pudieron generar las columnas de tiempo ('Anio', 'Mes'). Verifique el formato de la columna de fecha.")
        return None
        
    # 3. CORRECCIÓN FINAL ROBUSTA: FORZAR TIPOS DE DATOS Y LIMPIEZA DE TEXTO
    
    # Aseguramos que Venta_Neta y CANTIDAD existan (y si no, se crean como 0)
    for col in ['Venta_Neta', 'CANTIDAD']:
        if col in df_procesado.columns:
            df_procesado[col] = pd.to_numeric(df_procesado[col], errors='coerce').fillna(0)
        else:
            df_procesado[col] = 0.0 # Si no existe, se crea con ceros

    campos_a_string = [
        'Cliente_ID', 'Vendedor_ID', 'Marca', 'Tipo_Producto', 
        'Cliente_Nombre', 'Vendedor_Nombre', 'TIPO1', 'TIPO2', 'TIPO3', 'TIPO_VENTA'
    ]
    for col in campos_a_string:
        if col in df_procesado.columns:
            df_procesado[col] = df_procesado[col].astype(str).str.strip().str.upper().fillna('')
    
    for col in ['Anio', 'Mes']:
        if col in df_procesado.columns:
            df_procesado[col] = pd.to_numeric(df_procesado[col], errors='coerce').fillna(0).astype(int)
    
    return df_procesado.reset_index(drop=True)

# -----------------------------------------------------------
# FUNCIÓN PRINCIPAL DE STREAMLIT
# -----------------------------------------------------------

def main():
    """Función principal que dibuja la interfaz de Streamlit."""
    
    st.set_page_config(
        page_title="Informe de Ventas Estratégico", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )
    
    # --- CAPA DE SEGURIDAD VISUAL Y CARGA DE DATOS ---
    st.title("🔒 Portal de Análisis de Ventas")
    st.subheader("Paso 1: Sube el Archivo Excel")

    uploaded_file = st.file_uploader(
        "📂 **Selecciona el archivo Excel (ventas_historicas.xlsx)**",
        type=['xlsx']
    )
    
    # 1. DETENER SI NO HAY ARCHIVO
    if uploaded_file is None:
        st.info("⚠️ La aplicación está esperando que se cargue un archivo para iniciar el procesamiento.")
        st.markdown("---")
        st.stop()
        
    # 2. PROCESAR SI HAY ARCHIVO NUEVO O NO CACHEADO
    if 'data' not in st.session_state or st.session_state.get('uploaded_name') != uploaded_file.name:
        
        # Limpiar caché y procesar el nuevo archivo
        cargar_y_procesar_datos_completos.clear() 
        with st.spinner(f"Procesando '{uploaded_file.name}'... Esto puede tardar unos segundos."):
            df_ventas = cargar_y_procesar_datos_completos(uploaded_file)
        
        if df_ventas is not None and not df_ventas.empty:
            st.session_state['data'] = df_ventas
            st.session_state['uploaded_name'] = uploaded_file.name
            st.success(f"✅ Archivo '{uploaded_file.name}' cargado y procesado exitosamente. Filas: {len(df_ventas):,}")
        else:
            # El error ya se mostró dentro de la función de caché si falló por columna.
            st.session_state['data'] = None
            st.stop() # Detener si falla el procesamiento
            
    df_ventas = st.session_state['data']
    
    # --- A PARTIR DE AQUÍ SE MUESTRA EL DASHBOARD COMPLETO ---
    st.title("📊 Informe de Ventas y Estrategia de Clientes")
    st.markdown("---")

    # Inicialización de variables (para evitar errores de referencia)
    df_final_comparativo = pd.DataFrame()
    df_pivot_tabla = pd.DataFrame()
    fig_lineas, fig_barras, fig_circular = None, None, None
    
    # 1. LLAMADA AL HANDLER DE LA UI PARA OBTENER FILTROS Y CONFIGURACIÓN
    with st.sidebar:
        st.header("⚙️ Control de Datos y Filtros")
        
        # Muestra la verificación de terminal
        verificar_datos_terminal(df_ventas) 
        
        # Dibuja los filtros y obtiene la configuración
        filtros, config = dibujar_barra_lateral_y_obtener_config(df_ventas, st.session_state['uploaded_name'])

        # Extracción de variables clave
        metrica_seleccionada_key = config['metrica_principal']
        eje_x_seleccionado = config['eje_x']
        metricas_filtrables = config['metricas_filtrables']
        check_tablas = config['check_tablas']
        check_lineas = config['check_lineas']
        check_barras = config['check_barras']
        check_circular = config['check_circular']

    # 3. PROCESAMIENTO DE DATOS CON FILTROS APLICADOS
    
    df_filtrado_base = filtrar_datos(df_ventas, filtros)
    
    if df_filtrado_base.empty:
        st.warning("No hay datos disponibles para la combinación de filtros seleccionada. Ajuste sus filtros.")
        print("❌ FILTRADO: CERO FILAS EN EL DATAFRAME FINAL.")
        return

    print(f"✅ FILTRADO EXITOSO: {len(df_filtrado_base):,} filas restantes.")
    
    # 4. GENERACIÓN DE PANELES Y LÓGICA DE AGRUPACIÓN ANIDADA

    tablas_para_pdf = []
    figuras_para_pdf = []
    
    anios_usados = sorted(df_filtrado_base['Anio'].unique().tolist())
    ordenar_key = obtener_key_ordenamiento() 

    # --- LÓGICA DE AGRUPACIÓN CLAVE (PARA TABLAS SOLAMENTE) ---
    ejes_de_agrupacion = [eje_x_seleccionado]
    
    # Itera sobre los campos internos para ver si se han filtrado a un subconjunto
    for campo_agrupacion, _ in CAMPOS_INTERNOS:
        if campo_agrupacion in df_ventas.columns and campo_agrupacion not in [eje_x_seleccionado]:
             valores_filtrados = filtros.get(campo_agrupacion, [])
             valores_unicos_df = df_ventas[campo_agrupacion].unique().tolist()
             
             # Si se seleccionó un subconjunto (más de 0 y menos que todos), se promueve a agrupación
             if 0 < len(valores_filtrados) < len(valores_unicos_df):
                 ejes_de_agrupacion.append(campo_agrupacion)
                 
    st.info(f"Tabla Agrupada por: {', '.join(ejes_de_agrupacion)}")
        
    # --- TABLA NUMÉRICA Y COMPARACIÓN ---
    if check_tablas:
        st.header(f"🔢 Datos Numéricos Agrupados y Comparación Anual")
        
        if len(anios_usados) == 2:
            st.markdown(f"**Comparación:** {anios_usados[0]} vs {anios_usados[1]}")
            df_final_comparativo = None
            
            for metrica in metricas_filtrables:
                df_pivot = crear_tabla_dinamica(df_filtrado_base, ejes_de_agrupacion, metrica=metrica)
                
                if df_pivot is None or df_pivot.empty:
                    st.warning(f"No se pudieron generar datos para la métrica '{metrica}' con la configuración actual.")
                    continue
                
                col_menor = f'{metrica}_{anios_usados[0]}'
                col_mayor = f'{metrica}_{anios_usados[1]}'
                col_crec = f'%_CRECIMIENTO_{metrica}'
                
                col_menor_formateada = f'{METRICAS_BASE.get(metrica, metrica)[:3]}. {anios_usados[0]}'
                col_mayor_formateada = f'{METRICAS_BASE.get(metrica, metrica)[:3]}. {anios_usados[1]}'
                col_crec_formateada = f'% CREC. {METRICAS_BASE.get(metrica, metrica)[:3]}'
                
                df_pivot[col_menor] = df_pivot[col_menor].apply(formatear_miles)
                df_pivot[col_mayor] = df_pivot[col_mayor].apply(formatear_miles)
                if col_crec in df_pivot.columns:
                    df_pivot[col_crec] = df_pivot[col_crec].apply(formatear_porcentaje)
                
                df_pivot.rename(columns={
                    col_menor: col_menor_formateada,
                    col_mayor: col_mayor_formateada,
                    col_crec: col_crec_formateada
                }, inplace=True)
                
                if df_final_comparativo is None:
                    df_final_comparativo = df_pivot
                else:
                    columnas_a_fusionar = [c for c in df_pivot.columns if c not in ejes_de_agrupacion]
                    df_final_comparativo = pd.merge(df_final_comparativo, df_pivot[columnas_a_fusionar + ejes_de_agrupacion], on=ejes_de_agrupacion, how='outer')


            if df_final_comparativo is not None and not df_final_comparativo.empty:
                col_monto_reciente_name = f'{METRICAS_BASE.get(metrica_seleccionada_key, metrica_seleccionada_key)[:3]}. {anios_usados[1]}'

                if col_monto_reciente_name in df_final_comparativo.columns:
                     df_final_comparativo = df_final_comparativo.sort_values(
                         by=col_monto_reciente_name, 
                         ascending=False, 
                         key=ordenar_key 
                     )
                
                st.dataframe(df_final_comparativo, width='stretch')
                tablas_para_pdf.append({'titulo': 'Comparación Anual', 'df': df_final_comparativo.copy()})
            
        else:
            # Agregación simple (0, 1 o >2 años seleccionados)
            st.markdown(f"**Agregación Simple:** Total en **{', '.join(map(str, anios_usados)) or 'Todos los años'}**")
            
            df_pivot_tabla = crear_tabla_dinamica(df_filtrado_base, ejes_de_agrupacion, metrica=metrica_seleccionada_key)
            
            if not df_pivot_tabla.empty:
                nombre_metrica_salida = f'Sum_{metrica_seleccionada_key}'
                
                df_pivot_tabla = df_pivot_tabla.sort_values(
                    by=nombre_metrica_salida, 
                    ascending=False 
                )
                
                df_pivot_tabla[nombre_metrica_salida] = df_pivot_tabla[nombre_metrica_salida].apply(formatear_miles)
                
                df_pivot_tabla.rename(columns={
                    nombre_metrica_salida: f'{METRICAS_BASE.get(metrica_seleccionada_key, metrica_seleccionada_key)[:3]}. Total'
                }, inplace=True)
                
                st.dataframe(df_pivot_tabla, width='stretch')
                tablas_para_pdf.append({'titulo': 'Agregación Simple', 'df': df_pivot_tabla.copy()})
        
        st.markdown("---")
        
    # --- GRÁFICOS DE BARRAS y CIRCULARES (Ajuste para usar solo el Eje Principal) ---
    col1, col2 = st.columns(2)

    if check_barras:
        with col1:
            st.header("📊 Comparación por Eje X")
            # Agrupamos solo por el eje principal para el gráfico (se necesita un df simple)
            df_agrupado_barras = df_filtrado_base.groupby(eje_x_seleccionado)[metrica_seleccionada_key].sum().reset_index()
            
            if not df_agrupado_barras.empty:
                fig_barras = crear_grafico_barras_comparativo(
                    df_agrupado_barras, eje_x_seleccionado, metrica_seleccionada_key, f"Top 10 por {METRICAS_BASE.get(metrica_seleccionada_key, metrica_seleccionada_key)}"
                )
                st.plotly_chart(fig_barras, use_container_width=True)
                figuras_para_pdf.append(fig_barras)
            else:
                st.warning("No hay datos para generar el gráfico de barras.")


    if check_circular:
        with col2:
            st.header("⭕ Proporción de la Métrica Principal")
            # Usamos el mismo DF agrupado para la consistencia
            df_agrupado_top_circular = df_filtrado_base.groupby(eje_x_seleccionado)[metrica_seleccionada_key].sum().reset_index()
            
            if not df_agrupado_top_circular.empty:
                df_agrupado_top_circular['Porcentaje'] = (df_agrupado_top_circular[metrica_seleccionada_key] / df_agrupado_top_circular[metrica_seleccionada_key].sum()) * 100
                
                fig_circular = crear_grafico_circular_proporcion(
                    df_agrupado_top_circular, eje_x_seleccionado, 'Porcentaje', f"Distribución de {METRICAS_BASE.get(metrica_seleccionada_key, metrica_seleccionada_key)}"
                )
                st.plotly_chart(fig_circular, use_container_width=True)
                figuras_para_pdf.append(fig_circular)
            else:
                st.warning("No hay datos para generar el gráfico circular.")

    
    if check_barras or check_circular:
        st.markdown("---")


    # --- TENDENCIA HISTÓRICA (Líneas) ---
    if check_lineas:
        st.header("📈 Tendencia Histórica Mensual")
        try:
            df_lineas = df_filtrado_base.copy()
            df_lineas['Fecha'] = pd.to_datetime(df_lineas['Anio'].astype(str) + '-' + df_lineas['Mes'].astype(str) + '-01')
            
            # Usamos solo el eje principal para la tendencia, limitando a las 10 principales
            top_items = df_lineas.groupby(eje_x_seleccionado)[metrica_seleccionada_key].sum().nlargest(10).index
            df_lineas_top = df_lineas[df_lineas[eje_x_seleccionado].isin(top_items)]
            
            df_evolucion = df_lineas_top.groupby(['Fecha', eje_x_seleccionado])[metrica_seleccionada_key].sum().reset_index()
            
            if not df_evolucion.empty:
                fig_lineas = crear_grafico_lineas_tendencia(
                    df_evolucion, x_col='Fecha', y_col=metrica_seleccionada_key, color_col=eje_x_seleccionado, titulo="Tendencia Histórica Mensual (Top 10)"
                )
                st.plotly_chart(fig_lineas, use_container_width=True)
                figuras_para_pdf.append(fig_lineas)
            else:
                st.warning("No hay datos para generar el gráfico de líneas.")

        except Exception as e:
            st.error(f"Error al generar gráfico de líneas: {e}")
        
        st.markdown("---")
        
    # --- BOTÓN DE DESCARGA PDF ---
    if st.button("📥 Generar y Descargar Informe PDF"):
        if not tablas_para_pdf and not figuras_para_pdf:
             st.warning("No hay contenido seleccionado (tablas o gráficos) para generar el PDF.")
        else:
            with st.spinner('Generando informe PDF...'):
                # Creamos una lista de años únicos para el título del PDF
                titulo_anios = ', '.join(map(str, sorted(df_filtrado_base['Anio'].unique().tolist())))
                
                pdf_bytes = generar_pdf_informe(
                    titulo_informe=f"Informe de Ventas ({titulo_anios})",
                    contenido_figuras=figuras_para_pdf,
                    contenido_tablas=tablas_para_pdf
                )
                
            st.download_button(
                label="✅ PDF Listo. Clic para Descargar",
                data=pdf_bytes,
                file_name=f"Informe_Ventas_{date.today()}.pdf",
                mime="application/pdf"
            )

# Ejecutar la aplicación
if __name__ == "__main__":
    main()