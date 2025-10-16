# C:\Users\User\Desktop\respaldo\Inf_ventas\src\data_loader.py (VERSIÓN ACTUALIZADA)

import streamlit as st
import pandas as pd
import duckdb
import os
from typing import Optional, List, Dict

# ====================================================================
# 🎯 MÓDULO: data_loader.py - Carga de datos
# ====================================================================

try:
    # 🎯 Importación estricta de la constante centralizada.
    from src.data_aggregator import COLUMN_MAPPING_TO_DASHBOARD
except ImportError as e:
    print(f"Error Crítico: No se puede importar COLUMN_MAPPING_TO_DASHBOARD desde data_aggregator.py. {e}")
    st.error("Error de Configuración: No se pudo cargar el mapeo de columnas. Revise 'src/data_aggregator.py'.")
    raise SystemExit(1)


# --- Constantes de Conexión y Clave ---
# Nota: Modifiqué la ruta para que sea más robusta asumiendo la estructura Inf_ventas/data/
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'ventas_db.duckdb')
TABLE_NAME = 'ventas_maestra'
# 🔥 FIX CRÍTICO: Corrección de nombre de columna para las auditorías/matriz.
CLIENTE_ID_COL = 'Codcliente' 


# --- Función de Carga de Datos ---

@st.cache_data
def cargar_y_procesar_datos_completos() -> Optional[pd.DataFrame]:
    """
    Carga todos los datos de ventas directamente desde la tabla maestra de DuckDB.
    Utiliza Pandas para el renombramiento, asegurando la existencia de columnas clave.
    
    Retorna: DataFrame de Pandas o None en caso de error.
    """
    
    if not os.path.exists(DB_PATH):
        st.error(f"Error Crítico: No se encontró el archivo de base de datos en: {DB_PATH}")
        st.info("Asegúrese de que el archivo 'ventas_db.duckdb' esté en la carpeta 'data/'.")
        return None
        
    try:
        conn = duckdb.connect(database=DB_PATH, read_only=True)
        
        # 1. Cargar todas las columnas de la tabla
        query = f"SELECT * FROM {TABLE_NAME};"
        df_procesado = conn.execute(query).fetchdf()
        conn.close()
        
        if df_procesado.empty:
            st.warning("La base de datos se cargó, pero la tabla de ventas está vacía.")
            return None
        
        # 2. Renombramiento y Normalización de Nombres de Columnas
        mapeo_renombrado: Dict[str, str] = {}
        columnas_df = set(df_procesado.columns)
        
        lower_to_real_name = {col.lower(): col for col in columnas_df}

        for db_name_expected, dashboard_name in COLUMN_MAPPING_TO_DASHBOARD.items():
            if db_name_expected in columnas_df:
                mapeo_renombrado[db_name_expected] = dashboard_name
            elif db_name_expected.lower() in lower_to_real_name:
                real_name = lower_to_real_name[db_name_expected.lower()]
                mapeo_renombrado[real_name] = dashboard_name
        
        df_procesado.rename(columns=mapeo_renombrado, inplace=True)
        
        
        # 3. VERIFICACIÓN CRÍTICA (Venta_Neta, CANTIDAD, y Cliente_ID)
        
        col_real_monto_usada = "N/A"
        
        # --- 3.1 Venta_Neta ---
        if 'Venta_Neta' not in df_procesado.columns:
            monto_cols = [col for col in df_procesado.columns if 'monto' in col.lower() or 'total' in col.lower() or 'venta' in col.lower() or 'neto' in col.lower()]
            if monto_cols:
                col_real_monto = monto_cols[0]
                df_procesado.rename(columns={col_real_monto: 'Venta_Neta'}, inplace=True)
                col_real_monto_usada = col_real_monto # Guardamos el nombre real
                st.warning(f"La columna clave 'Venta_Neta' no se encontró. Usando '{col_real_monto}' como 'Venta_Neta'.")
            else:
                st.error("COLUMNA CRÍTICA 'Venta_Neta' NO ENCONTRADA. Asegúrese de que el archivo de la DB contenga una columna de monto.")
                return None
        
        # 🎯 AUDITORÍA INTERNA: Muestra la columna que se está utilizando realmente
        st.info(f"Columna de Monto (Venta_Neta) REAL: **{col_real_monto_usada if col_real_monto_usada != 'N/A' else 'Venta_Neta'}**")
        
        # --- 3.2 CANTIDAD ---
        if 'CANTIDAD' not in df_procesado.columns:
            cantidad_cols = [col for col in df_procesado.columns if 'cantidad' in col.lower() or 'unidades' in col.lower() or 'qty' in col.lower()]
            if cantidad_cols:
                col_real_cantidad = cantidad_cols[0]
                df_procesado.rename(columns={col_real_cantidad: 'CANTIDAD'}, inplace=True)
                st.warning(f"La columna clave 'CANTIDAD' no se encontró. Usando '{col_real_cantidad}' como 'CANTIDAD'.")
            else:
                st.warning("COLUMNA CRÍTICA 'CANTIDAD' NO ENCONTRADA. Se inicializa a 0.0.")
                df_procesado['CANTIDAD'] = 0.0

        # 4. Forzar Tipos de Datos Finales (CON LIMPIEZA ADICIONAL)
        df_cols = df_procesado.columns.tolist()
        
        # 4.1 Numéricos (Venta_Neta y CANTIDAD)
        for col in ['Venta_Neta', 'CANTIDAD']:
            if col in df_cols:
                
                # 🔥 FIX CRÍTICO: Limpieza de caracteres no numéricos comunes ANTES de la conversión
                # Esto es crucial si la columna real en la DB tiene símbolos de moneda ($, €) o miles (,)
                df_procesado[col] = df_procesado[col].astype(str).str.replace(r'[$,€\s]', '', regex=True)
                df_procesado[col] = pd.to_numeric(df_procesado[col], errors='coerce').fillna(0)
            
        # 4.2 Tiempos (Anio, Mes)
        for col in ['Anio', 'Mes']:
            if col in df_cols:
                df_procesado[col] = pd.to_numeric(df_procesado[col], errors='coerce').fillna(0).astype('Int64') 
            
        # 4.3 Strings (Categorías)
        # Incluimos CLIENTE_ID_COL para asegurar que sea tratado como string/object.
        CAMPOS_ESPERADOS_STRING: List[str] = [
            v for k, v in COLUMN_MAPPING_TO_DASHBOARD.items() 
            if v not in ['Venta_Neta', 'CANTIDAD', 'Anio', 'Mes']
        ] + [CLIENTE_ID_COL] 
        
        for col in CAMPOS_ESPERADOS_STRING:
            if col in df_cols:
                df_procesado[col] = df_procesado[col].astype(str).fillna('OTROS/SIN ESPECIFICAR').str.strip()

        return df_procesado.reset_index(drop=True)

    except Exception as e:
        st.error(f"Error al cargar datos desde DuckDB: {type(e).__name__}: {str(e)}")
        return None