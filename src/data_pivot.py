# C:\Users\User\Desktop\respaldo\Inf_ventas\src\data_pivot.py (INTEGRO Y OPTIMIZADO)

import streamlit as st 
import pandas as pd
from typing import List, Dict, Any

# ====================================================================
# 1. FUNCIÓN DE FILTRADO (Refactorizada para ser más dinámica)
# ====================================================================

@st.cache_data
def filtrar_datos(df_base: pd.DataFrame, filtros: Dict[str, Any]) -> pd.DataFrame:
    """
    Aplica los filtros de la barra lateral al DataFrame base de manera dinámica, 
    gestionando las columnas de tiempo, IDs y nombres.
    """
    # Siempre operar sobre una copia para no modificar el DataFrame original en caché.
    df_filtrado = df_base.copy()
    
    # Lista de campos que se espera que existan en el DataFrame y vengan del diccionario de filtros
    CAMPOS_AGRUPACION_ESPERADOS = [
        'Anios', 'Meses', 'Vendedor_Nombre', 'Tipo_Producto', 
        'Marca', 'Cliente_ID', 'Cliente_Nombre', 'TIPO_VENTA', 
        'TIPO1', 'TIPO2', 'TIPO3'
    ]
    
    for columna_filtro in CAMPOS_AGRUPACION_ESPERADOS:
        
        # 1. Verificar si el filtro existe y tiene valores
        valores_seleccionados = filtros.get(columna_filtro)
        
        if valores_seleccionados and columna_filtro != 'Anios': # 'Anios' se maneja como lista de años específicos
            # Usar 'Anios' como 'Anio' en el DataFrame
            df_columna = 'Anio' if columna_filtro == 'Anios' else columna_filtro
            
            # 2. Verificar si la columna existe en el DataFrame
            if df_columna in df_filtrado.columns:
                
                # Manejo especial para Cliente_ID: asegurar que ambos (columna y filtro) sean strings para la comparación
                if df_columna == 'Cliente_ID':
                    df_filtrado[df_columna] = df_filtrado[df_columna].astype(str)
                    valores_seleccionados = [str(v) for v in valores_seleccionados]

                # Aplicar filtro genérico usando isin()
                df_filtrado = df_filtrado[df_filtrado[df_columna].isin(valores_seleccionados)]
                
    
    # Filtro por Rango de Año (Manejo explícito para claridad, aunque se incluyó en el loop genérico)
    if 'Anios' in filtros and filtros['Anios'] and 'Anio' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Anio'].isin(filtros['Anios'])]


    return df_filtrado.copy()


# ====================================================================
# 2. FUNCIÓN DE TABLA DINÁMICA (Se mantiene estable y correcta)
# ====================================================================

@st.cache_data
def crear_tabla_dinamica(df_filtrado: pd.DataFrame, ejes_agrupacion: List[str], metrica: str) -> pd.DataFrame:
    """
    Crea una tabla dinámica agrupada por los ejes de agrupación,
    siempre pivoteando por la columna 'Anio' para la comparación Año vs Año.
    """
    
    if df_filtrado.empty:
        return pd.DataFrame()

    # ----------------------------------------------------
    # Definición del Pivote (Siempre Año)
    # ----------------------------------------------------
    pivot_columna = 'Anio' 
    
    # Los ejes de fila deben ser los que vienen de app.py (ejes_agrupacion_para_pivot)
    # Excluye ejes que no existen en el DataFrame filtrado
    ejes_para_agrupar = [eje for eje in ejes_agrupacion if eje in df_filtrado.columns]

    if not ejes_para_agrupar:
        st.warning("No hay ejes de agrupación válidos para la tabla dinámica.")
        return pd.DataFrame() 

    if pivot_columna not in df_filtrado.columns:
        # En caso de que no haya columna 'Anio', se hace una simple agregación
        st.warning("La columna de pivote 'Anio' no está disponible. Realizando agregación simple.")
        df_simple = df_filtrado.groupby(ejes_para_agrupar)[metrica].sum().reset_index()
        df_simple.rename(columns={metrica: f'Sum_{metrica}'}, inplace=True)
        return df_simple
        
    # ----------------------------------------------------
    # Ejecución del Agrupamiento y Pivote
    # ----------------------------------------------------
    
    # Agrupar y pivotar.
    df_pivot = df_filtrado.groupby(ejes_para_agrupar + [pivot_columna])[metrica].sum().unstack(fill_value=0)
    df_pivot = df_pivot.reset_index() 
    
    
    # ----------------------------------------------------
    # Lógica de Comparación Anual y Crecimiento
    # ----------------------------------------------------
    
    # Identificar los años presentes como columnas
    # Se usa df_filtrado['Anio'].unique() para asegurar que los años pivotados son los años de los datos
    anios_presentes = sorted([col for col in df_pivot.columns if isinstance(col, int) and col in df_filtrado['Anio'].unique()])

    if len(anios_presentes) < 2:
        # Si solo hay un año o menos después del filtro, devolver agregación simple.
        if len(anios_presentes) == 1:
            # Renombrar el único año presente a un nombre genérico para la métrica
            df_pivot.rename(columns={anios_presentes[0]: f'Sum_{metrica}'}, inplace=True)
            # Descartar cualquier otra columna numérica que pudiera haber quedado (excepto el renombrado)
            cols_to_keep = ejes_para_agrupar + [f'Sum_{metrica}']
            df_pivot = df_pivot[[c for c in cols_to_keep if c in df_pivot.columns]]
        else:
            # Si no hay años válidos
            return pd.DataFrame() 
        return df_pivot


    # 2. Lógica de Comparación Anual (2 años extremos)
    anio_base = anios_presentes[0]
    anio_actual = anios_presentes[-1]
    
    # Renombrar las columnas pivotadas a un formato consistente (Métrica_Año)
    df_pivot.rename(columns={
        anio_base: f'{metrica}_{anio_base}',
        anio_actual: f'{metrica}_{anio_actual}'
    }, inplace=True)
    
    # Eliminar años intermedios que no se usan en la comparación
    anios_intermedios = [a for a in anios_presentes if a != anio_base and a != anio_actual]
    df_pivot.drop(columns=anios_intermedios, errors='ignore', inplace=True)
    
    col_base = f'{metrica}_{anio_base}'
    col_actual = f'{metrica}_{anio_actual}'
    col_crecimiento = f'%_CRECIMIENTO_{metrica}'
    
    # Cálculo de crecimiento (Avance) - Mejor uso de numpy.where para eficiencia y claridad
    import numpy as np
    
    # Evita la división por cero: si la base es 0, el crecimiento es 100% si el actual > 0, o 0% si actual = 0.
    df_pivot[col_crecimiento] = np.where(
        df_pivot[col_base] != 0,
        ((df_pivot[col_actual] - df_pivot[col_base]) / df_pivot[col_base]) * 100,
        np.where(df_pivot[col_actual] > 0, 100, 0)
    )
    
    # Reordenar para que la columna de crecimiento esté junto a los montos
    col_order = ejes_para_agrupar + [col_base, col_actual, col_crecimiento]
    return df_pivot[[c for c in col_order if c in df_pivot.columns]]