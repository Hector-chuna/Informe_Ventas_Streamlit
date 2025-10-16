# C:\Users\User\Desktop\respaldo\Inf_ventas\src\style_handler.py (CORREGIDO - NO DUPLICA FORMATO)

import pandas as pd
import numpy as np
from typing import List

# ====================================================================
# 🎯 CORRECCIÓN CLAVE: Importación estricta de las funciones de formateo (SSOT).
# Se eliminó la lógica duplicada (fallback) local.
# ====================================================================
try:
    from .formatter import formatear_miles, formatear_porcentaje, formatear_decimales
except ImportError as e:
    # Si formatter.py no existe o las funciones no están ahí, es un error fatal de diseño.
    print(f"Error Crítico: No se pudo importar la lógica de formateo desde formatter.py. {e}")
    raise # Permitimos que el error se propague, forzando el uso de la fuente única.

# ====================================================================
# --- Funciones de Estilo Condicional ---
# (Lógica propia de este módulo, por lo que se mantiene)
# ====================================================================

def resaltar_negativo_positivo(s: pd.Series, columnas_porcentaje: List[str]):
    """
    Aplica formato condicional (Rojo/Verde tenue) a las columnas de porcentaje.
    Esta función se aplica a un DataFrame completo (axis=None).
    """
    df_styled = pd.DataFrame('', index=s.index, columns=s.columns)
    
    for col in columnas_porcentaje:
        if col in s.columns:
            # Lógica de conversión inversa para aplicar la máscara numérica
            # Transforma el string localizado ('1.234,56%') a un float que Python pueda leer.
            numeric_col = pd.to_numeric(
                s[col].astype(str).str.replace('%', '', regex=False) \
                                 .str.replace('.', '', regex=False) \
                                 .str.replace(',', '.', regex=False), # Decimal de coma a punto
                errors='coerce'
            )
            
            mask_numeric = numeric_col.notna()
            mask_neg = mask_numeric & (numeric_col < 0)
            mask_pos = mask_numeric & (numeric_col > 0)
            
            # Rojo tenue (#FFCCCC) para negativo, Verde tenue (#CCFFCC) para positivo
            df_styled.loc[mask_neg, col] = 'background-color: #FFCCCC' 
            df_styled.loc[mask_pos, col] = 'background-color: #CCFFCC' 

    return df_styled

def resaltar_subtotales(s: pd.Series):
    """
    Aplica color de fondo diferente a las filas de subtotales.
    Esta función se aplica fila por fila (axis=1).
    """
    # Definición de estilos
    style_subtotal = 'background-color: #E6F7FF; font-weight: bold;' # Azul muy tenue
    style_gran_total = 'background-color: #B3E0FF; font-weight: bolder;' # Azul tenue

    # Lógica de detección: Buscamos las etiquetas en cualquiera de los valores de la fila
    
    # Convierte todos los valores de la serie a string para la búsqueda
    s_str = s.astype(str)
    
    # Palabras clave del TOTAL GENERAL (debe ser la primera comprobación)
    if s_str.str.contains('TOTAL GENERAL', case=False, regex=False).any():
        return [style_gran_total] * len(s)
        
    # Palabras clave de SUBTOTALES (Total MARCA, Total CLIENTE, etc.)
    # Se busca el patrón 'Total X' donde X es cualquier palabra.
    if s_str.str.contains(r'Total\s+\w+', case=False).any():
        return [style_subtotal] * len(s)

    return [''] * len(s)

# ====================================================================
# --- Función de Orquestación de Estilo y Formato ---
# ====================================================================

def aplicar_formato_y_estilo(df: pd.DataFrame, metricas_cols: List[str], porcentaje_cols: List[str]):
    """Aplica formato de miles/porcentaje y los estilos condicionales al DataFrame."""
    
    # Usamos las funciones importadas
    formatters = {}
    for col in metricas_cols:
        if col in df.columns:
            if col in porcentaje_cols:
                # Usa la función importada para porcentajes
                formatters[col] = formatear_porcentaje 
            else:
                # Usa la función importada para miles/montos
                formatters[col] = formatear_miles
            
    
    # Aplicar el formato, el estilo de subtotales (por fila) y el estilo condicional (por columna)
    # Se añade na_rep para valores NaN
    df_styled = df.style.format(formatters, na_rep="-") \
                        .apply(resaltar_subtotales, axis=1) \
                        .apply(resaltar_negativo_positivo, subset=metricas_cols, columnas_porcentaje=porcentaje_cols, axis=None)
                        
    return df_styled