import pandas as pd
import os
import streamlit as st

@st.cache_data
def cargar_datos(archivo_nombre: str) -> pd.DataFrame or None:
    """
    Carga el DataFrame desde el archivo Excel especificado.
    """
    
    if not os.path.exists(archivo_nombre):
        print(f"\n⚠️ ADVERTENCIA: No se encontró el archivo '{archivo_nombre}'.")
        if 'streamlit' in st.session_state:
            st.error(f"Error: No se encontró el archivo de datos: '{archivo_nombre}'")
        return None

    try:
        df = pd.read_excel(archivo_nombre, sheet_name=0) 
        
        # 1. Limpieza y normalización de nombres de columnas
        # Convierte 'F.OPERACION' a 'F_OPERACION', 'COD.CLIENTE' a 'COD_CLIENTE', etc.
        df.columns = [col.strip().replace(' ', '_').replace('.', '_').replace('/', '_').upper() for col in df.columns]
        
        return df
    
    except Exception as e:
        print(f"\n❌ ERROR FATAL al leer el archivo Excel: {e}")
        return None