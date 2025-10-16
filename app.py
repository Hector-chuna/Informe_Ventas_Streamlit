# C:\Users\User\Desktop\respaldo\Inf_ventas\app.py (ESTRATEGIA DE ATAQUE - FINAL)

import streamlit as st
import pandas as pd
from datetime import date
import sys
import os
import io 
import numpy as np 
from typing import List, Dict, Any 

# Configuración para importar módulos desde src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# -----------------------------------------------------------
# Importar funciones factorizadas
# -----------------------------------------------------------
from src.data_loader import cargar_y_procesar_datos_completos 
from src.data_pivot import filtrar_datos, crear_tabla_dinamica 
from src.data_processor import calcular_subtotales_anidados 
from src.style_handler import aplicar_formato_y_estilo 
from src.visualizer import (
    crear_grafico_barras_comparativo, 
    crear_grafico_circular_proporcion, 
    crear_grafico_lineas_tendencia, 
    generar_pdf_informe
)
from src.ui_handler import dibujar_barra_lateral_y_obtener_config, CAMPOS_INTERNOS 
from src.debugger_utils import verificar_datos_terminal_inicial, verificar_conteo_filtros_aplicados 

# Importación de constantes clave
from src.data_aggregator import COLUMNAS_AGRUPACION, METRICAS_BASE, MESES_NOMBRES, MONTH_MAPPING 


# -----------------------------------------------------------
# FUNCIÓN DE ESTILO PARA PINTAR SUBTOTALES
# -----------------------------------------------------------

def aplicar_estilos_subtotales(s):
    """
    Función que aplica colores de fondo a la fila según el NIVEL_SUBTOTAL.
    """
    # Definir los colores base (tonos muy suaves/claros)
    colores = {
        'MARCA': '#E6F7E6',      # Verde tenue
        'CLIENTE': '#FFFFE0',    # Amarillo tenue
        'VENDEDOR': '#E0FFFF',   # Celeste tenue
        'GENERAL': '#D0E0FF',    # Azul tenue para Total General
        'DETALLE': ''            # Sin color para filas de detalle
    }
    
    # Obtener el color basado en la columna NIVEL_SUBTOTAL (agregada en data_processor.py 4.2)
    nivel = s.get('NIVEL_SUBTOTAL', 'DETALLE')
    color = colores.get(nivel, '')
    
    # Si la fila es DETALLE o el color es vacío, no aplicar estilo
    if not color:
        return [''] * len(s)

    # Aplicar el color de fondo a TODAS las celdas de la fila de subtotal
    return [f'background-color: {color}' for _ in s]


# -----------------------------------------------------------
# LÓGICA DE DIBUJO DE TABLA (MODIFICADA para estilos y corregido NameError)
# -----------------------------------------------------------

def mostrar_tabla_con_subtotales_y_estilo(df_comparativo: pd.DataFrame, ejes_agrupacion_estrategia: List[str]):
    """
    Orquesta la generación de subtotales y la aplicación de estilos.
    """
    
    # Los ejes que efectivamente generarán subtotales (Vendedor, Cliente, Marca)
    ejes_para_subtotal = [eje for eje in COLUMNAS_AGRUPACION if eje in df_comparativo.columns]
    
    # Columnas que son métricas (valores)
    ejes_de_fila = ejes_para_subtotal + ['Mes_Nombre']
    columnas_metricas_valor = [col for col in df_comparativo.columns if col not in ejes_de_fila and col not in ['Mes', 'Anio', 'NIVEL_SUBTOTAL']] 
    
    
    # Reordenar las columnas del DataFrame antes de generar subtotales
    ejes_fila_final = [eje for eje in ejes_de_fila if eje in df_comparativo.columns]
    
    otras_columnas = [col for col in df_comparativo.columns if col not in ejes_fila_final]
    try:
        # Filtrar solo las columnas que realmente existen antes de reordenar
        cols_finales = [c for c in ejes_fila_final + otras_columnas if c in df_comparativo.columns]
        df_comparativo = df_comparativo[cols_finales]
    except KeyError as e:
        st.warning(f"Error reordenando columnas: {e}. Continuado sin reordenar.")
        
    # Columnas que contienen porcentajes para el formato
    columnas_porcentaje = [col for col in columnas_metricas_valor if '%' in col]


    # 2. Generación del DF con subtotales (incluye la columna NIVEL_SUBTOTAL)
    st.info(f"Aplicando Subtotales a los Ejes: **{', '.join(ejes_para_subtotal)}**")
    
    df_con_subtotales = calcular_subtotales_anidados(
        df=df_comparativo.copy(), 
        ejes_agrupacion=ejes_para_subtotal, 
        cols_a_sumar=columnas_metricas_valor
    )

    # 3. Aplicación del estilo 
    
    # 3a. Aplicar formato numérico (Monto, Porcentaje)
    df_styled = aplicar_formato_y_estilo(
        df_con_subtotales.copy(), columnas_metricas_valor, columnas_porcentaje
    )
    
    # 3b. Aplicar colores de fondo usando style.apply (SOLUCIÓN DE COLORES)
    if 'NIVEL_SUBTOTAL' in df_con_subtotales.columns:
        if not isinstance(df_styled, pd.io.formats.style.Styler):
             df_styled = df_styled.style
             
        styler_final = df_styled.apply(aplicar_estilos_subtotales, axis=1)
        
    else:
        st.warning("La columna 'NIVEL_SUBTOTAL' no fue encontrada. No se aplicarán colores de fondo a los subtotales.")
        styler_final = df_styled


    st.subheader("Tabla de Rendimiento con Subtotales Anidados y Formato de Gerencia")
    # Al final, eliminamos la columna NIVEL_SUBTOTAL para la presentación visual
    st.dataframe(styler_final.hide(subset=['NIVEL_SUBTOTAL'], axis='columns'), width='stretch')
    
    # Se debe devolver el DataFrame original con subtotales (incluyendo NIVEL_SUBTOTAL) para el PDF/Análisis
    return df_con_subtotales.copy()


# -----------------------------------------------------------
# FUNCIÓN PRINCIPAL DE STREAMLIT (Con corrección NameError)
# -----------------------------------------------------------

@st.cache_resource
def obtener_data_cargada():
    """Función para cargar y cachear los datos en st.cache_resource."""
    with st.spinner("Conectando con DuckDB y cargando datos..."):
        df_ventas_temp = cargar_y_procesar_datos_completos() 
    return df_ventas_temp

def main():
    """Función principal que dibuja la interfaz de Streamlit."""
    
    st.set_page_config(
        page_title="Informe de Ventas Estratégico (DuckDB)", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )
    
    st.title("💾 Portal de Análisis de Ventas (DuckDB)")
    st.subheader("Paso 1: Carga de Datos desde la Base de Datos")

    if 'data' not in st.session_state:
        df_ventas_temp = obtener_data_cargada()

        if df_ventas_temp is not None and not df_ventas_temp.empty:
            st.session_state['data'] = df_ventas_temp
            st.session_state['data_source'] = 'DuckDB'
            st.success(f"✅ Base de datos DuckDB cargada exitosamente. Filas: {len(df_ventas_temp):,}")
        else:
            st.session_state['data'] = None
            st.session_state['data_source'] = None
            st.error("Error al cargar datos desde DuckDB. Verifique la conexión y el archivo 'ventas_db.duckdb'.")
            st.stop()
            
    df_ventas = st.session_state['data']
    
    if df_ventas is None:
        st.stop() 

    # -----------------------------------
    # Inicio de la interfaz principal
    # -----------------------------------
    
    st.title("📊 Informe de Ventas y Estrategia de Clientes")
    st.markdown("---")

    tablas_para_pdf = []
    figuras_para_pdf = []
    
    # 1. BARRA LATERAL Y FILTROS
    with st.sidebar:
        st.header("⚙️ Control de Datos y Filtros")
        
        verificar_datos_terminal_inicial(df_ventas)
        
        filtros, config = dibujar_barra_lateral_y_obtener_config(df_ventas.copy(), "ventas_db.duckdb") 
        
    # -------------------------------------------------------------
    # Asignación de variables de configuración
    # -------------------------------------------------------------
    metrica_seleccionada_key = config['metrica_principal']
    eje_x_seleccionado = config['eje_x']
    metricas_filtrables = config['metricas_filtrables']
    check_tablas = config['check_tablas']
    ordenamiento_estrategico = config.get('ordenamiento')
    ejes_tabla_estrategia = config.get('ejes_tabla_estrategia') 
    # -------------------------------------------------------------

    # 2. PROCESAMIENTO DE DATOS CON FILTROS APLICADOS
    
    df_filtrado_base = filtrar_datos(df_ventas.copy(), filtros) 
    
    if df_filtrado_base is None or df_filtrado_base.empty:
        st.warning("No hay datos disponibles para la combinación de filtros seleccionada. Ajuste sus filtros.")
        return

    verificar_conteo_filtros_aplicados(df_filtrado_base, filtros)
    
    # FIX CLAVE 1: GENERACIÓN DE MES_NOMBRE
    if 'Mes' in df_filtrado_base.columns and 'Mes_Nombre' not in df_filtrado_base.columns:
        df_filtrado_base['Mes_Nombre'] = df_filtrado_base['Mes'].astype(int).map(MONTH_MAPPING).fillna('Sin Mes')
    
    # FIX CLAVE 2: VERIFICACIÓN Y CREACIÓN DE LA MÉTRICA SELECCIONADA
    if metrica_seleccionada_key not in df_filtrado_base.columns:
        if 'Monto_Venta' in df_filtrado_base.columns:
            df_filtrado_base[metrica_seleccionada_key] = df_filtrado_base['Monto_Venta']
            st.warning(f"Usando 'Monto_Venta' como alias temporal para '{metrica_seleccionada_key}'.")
        else:
            st.error(f"Error: La métrica principal '{metrica_seleccionada_key}' no se encuentra en el DataFrame. Revise la función de carga.")
            st.stop()


    if ejes_tabla_estrategia is None:
        ejes_tabla_estrategia = COLUMNAS_AGRUPACION
        
    ejes_de_agrupacion = ejes_tabla_estrategia
    
    
    # --- TABLA NUMÉRICA Y COMPARACIÓN ---
    if check_tablas:
        st.header(f"🔢 Datos Numéricos Agrupados y Comparación Anual")
        
        df_tabla_base = pd.DataFrame() 
        anios_usados = sorted(df_filtrado_base['Anio'].unique().tolist())
        
        # Configuración de los Ejes de Agrupación para el Pivot
        if ejes_de_agrupacion == COLUMNAS_AGRUPACION:
            ejes_de_agrupacion_para_pivot = [eje for eje in ejes_de_agrupacion if eje != 'Anio' and eje in df_filtrado_base.columns]
            
            if 'Mes_Nombre' in df_filtrado_base.columns and 'Mes_Nombre' not in ejes_de_agrupacion_para_pivot:
                 ejes_de_agrupacion_para_pivot.append('Mes_Nombre')
                 
            st.info("Estrategia de Ataque Activa: Agrupación anidada por **Vendedor > Cliente > Marca** con detalle por **Mes**.")
        else:
            ejes_de_agrupacion_para_pivot = [eje for eje in ejes_de_agrupacion if eje != 'Anio' and eje in df_filtrado_base.columns]
            st.info(f"Tabla Agrupada por: **{', '.join(ejes_de_agrupacion_para_pivot)}**. El Año se utiliza en el pivote.")

        # Generación de la tabla comparativa (Manejo de múltiples métricas/años)
        if len(anios_usados) >= 1:
            df_final_comparativo = None
            
            for metrica in metricas_filtrables:
                if metrica not in df_filtrado_base.columns and 'Monto_Venta' in df_filtrado_base.columns:
                    df_filtrado_base[metrica] = df_filtrado_base['Monto_Venta']

                df_pivot = crear_tabla_dinamica(df_filtrado_base, ejes_de_agrupacion_para_pivot, metrica=metrica)
                
                if df_pivot is None or df_pivot.empty: continue
                
                if isinstance(df_pivot.index, pd.MultiIndex):
                    ejes_pivot_actualizados = list(df_pivot.index.names)
                    df_pivot = df_pivot.reset_index()
                else:
                    ejes_pivot_actualizados = [col for col in df_pivot.columns if col not in [c for c in df_pivot.columns if metrica in c]]
                    if not ejes_pivot_actualizados and ejes_de_agrupacion_para_pivot:
                        ejes_pivot_actualizados = [ejes_de_agrupacion_para_pivot[0]]
                        
                
                columnas_a_fusionar = [c for c in df_pivot.columns if c not in ejes_pivot_actualizados]
                
                if df_final_comparativo is None:
                    df_final_comparativo = df_pivot
                else:
                    ejes_comunes = [eje for eje in ejes_pivot_actualizados if eje in df_final_comparativo.columns and eje in df_pivot.columns]
                    columnas_existentes_en_pivot = [c for c in columnas_a_fusionar + ejes_comunes if c in df_pivot.columns]
                    
                    df_final_comparativo = pd.merge(
                        df_final_comparativo, 
                        df_pivot[columnas_existentes_en_pivot], # <-- CORRECCIÓN APLICADA AQUÍ
                        on=ejes_comunes, 
                        how='outer'
                    )

            
            if df_final_comparativo is not None and not df_final_comparativo.empty:
                
                # Lógica de Ordenamiento y Renombrado
                ascending = False 
                col_ordenamiento = None
                crecimiento_col_name = f'%_CRECIMIENTO_{metrica_seleccionada_key}'
                monto_col_name = f'{metrica_seleccionada_key}_{anios_usados[-1]}'
                
                if ordenamiento_estrategico == 'Declive' and crecimiento_col_name in df_final_comparativo.columns:
                    col_ordenamiento = crecimiento_col_name
                    ascending = True 
                    st.info("Estrategia activa: Ordenando por **mayor DECLIVE** primero.")
                    
                elif ordenamiento_estrategico == 'Monto' and len(anios_usados) > 0 and monto_col_name in df_final_comparativo.columns:
                    col_ordenamiento = monto_col_name
                    ascending = False 
                    st.info("Estrategia activa: Ordenando por **MAYOR MONTO** de venta reciente.")
                    
                elif crecimiento_col_name in df_final_comparativo.columns:
                    col_ordenamiento = crecimiento_col_name
                    ascending = False
                elif len(anios_usados) > 0 and monto_col_name in df_final_comparativo.columns:
                    col_ordenamiento = monto_col_name
                    ascending = False
                else:
                    metric_cols = [c for c in df_final_comparativo.columns if c not in ejes_de_agrupacion_para_pivot and c != 'Anio' and 'Mes_Nombre' not in c]
                    col_ordenamiento = metric_cols[0] if metric_cols else df_final_comparativo.columns[0]
                    ascending = False
                    
                
                if col_ordenamiento in df_final_comparativo.columns:
                    df_final_comparativo = df_final_comparativo.sort_values(
                        by=col_ordenamiento, 
                        ascending=ascending, 
                        key=lambda x: pd.to_numeric(x, errors='coerce').fillna(-np.inf if ascending else 0)
                    )
                
                final_renaming_dict = {}
                for metrica in metricas_filtrables:
                    if len(anios_usados) >= 2:
                        final_renaming_dict[f'{metrica}_{anios_usados[0]}'] = f'{METRICAS_BASE.get(metrica, metrica)[:3]}. {anios_usados[0]}'
                        final_renaming_dict[f'{metrica}_{anios_usados[-1]}'] = f'{METRICAS_BASE.get(metrica, metrica)[:3]}. {anios_usados[-1]}'
                        final_renaming_dict[f'%_CRECIMIENTO_{metrica}'] = f'% CREC. {METRICAS_BASE.get(metrica, metrica)[:3]}'
                    elif len(anios_usados) == 1 and f'Sum_{metrica}' in df_final_comparativo.columns:
                        final_renaming_dict[f'Sum_{metrica}'] = f'{METRICAS_BASE.get(metrica, metrica)[:3]}. Total'
                            
                df_final_comparativo.rename(columns=final_renaming_dict, inplace=True)
                
                if 'Anio' in df_final_comparativo.columns:
                         df_final_comparativo.drop(columns=['Anio'], inplace=True)

                df_tabla_base = df_final_comparativo
            
            else:
                # LÓGICA DE AGREGACIÓN SIMPLE (Caso Fallback - 1 año o menos)
                st.markdown(f"**Agregación Simple:** Total en **{', '.join(map(str, anios_usados)) or 'Todos los años'}**")
                
                df_pivot_tabla = crear_tabla_dinamica(df_filtrado_base, ejes_de_agrupacion_para_pivot, metrica=metrica_seleccionada_key)
                
                if df_pivot_tabla is not None and not df_pivot_tabla.empty:
                    metric_cols = [c for c in df_pivot_tabla.columns if c not in ejes_de_agrupacion_para_pivot and c != 'Anio']
                    if metric_cols:
                             df_pivot_tabla.rename(columns={metric_cols[0]: f'{METRICAS_BASE.get(metrica_seleccionada_key, metrica_seleccionada_key)[:3]}. Total'}, inplace=True)
                
                df_tabla_base = df_pivot_tabla
        
        # MOSTRAR TABLA Y APLICAR ESTILOS 
        if df_tabla_base is not None and not df_tabla_base.empty:
            
            df_tabla_estilizada = mostrar_tabla_con_subtotales_y_estilo(df_tabla_base, COLUMNAS_AGRUPACION) 
            tablas_para_pdf.append({'titulo': 'Comparación Anual (Subtotales)', 'df': df_tabla_estilizada.copy()})
        
        st.markdown("---")
        
    # ... (El resto de la lógica de gráficos y PDF permanece igual) ...

# Ejecutar la aplicación
if __name__ == "__main__":
    main()