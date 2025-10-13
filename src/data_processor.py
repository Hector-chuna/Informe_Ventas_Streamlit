import pandas as pd
from typing import List

def crear_campos_tiempo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte la columna de fecha a datetime y extrae campos de tiempo.
    Asume que la columna de fecha ya fue renombrada a 'Fecha_Operacion'.
    """
    
    df_procesado = df.copy()
    
    if 'Fecha_Operacion' not in df_procesado.columns:
        print("Error en data_processor: Columna 'Fecha_Operacion' no encontrada.")
        return df_procesado
    
    try:
        # Forzar la columna a formato datetime.
        df_procesado['Fecha_Operacion'] = pd.to_datetime(df_procesado['Fecha_Operacion'], errors='coerce')
        
        # Filtrar filas donde la fecha no pudo ser convertida
        df_procesado.dropna(subset=['Fecha_Operacion'], inplace=True)
        
        # Extracción de campos de tiempo
        df_procesado['Anio'] = df_procesado['Fecha_Operacion'].dt.year.astype(int)
        df_procesado['Mes'] = df_procesado['Fecha_Operacion'].dt.month.astype(int)
        
    except Exception as e:
        print(f"Error al procesar campos de tiempo: {e}")
        
    return df_procesado