import pandas as pd

def filtrar_datos(df: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    """Aplica filtros al DataFrame."""
    df_filtrado = df.copy()
    
    # Filtrado por Año y Mes (obligatorio)
    if 'Anio' in filtros and filtros['Anio']:
        df_filtrado = df_filtrado[df_filtrado['Anio'].isin(filtros['Anio'])]
    if 'Mes' in filtros and filtros['Mes']:
        df_filtrado = df_filtrado[df_filtrado['Mes'].isin(filtros['Mes'])]

    # Filtrado por campos de producto/cliente/vendedor
    for columna, valores in filtros.items():
        if columna in df_filtrado.columns and columna not in ['Anio', 'Mes']:
            # Asegurar que los valores seleccionados no estén vacíos o sean la lista completa (a menos que se quiera filtrar por vacío)
            if valores and len(valores) < len(df[columna].unique().tolist()):
                df_filtrado = df_filtrado[df_filtrado[columna].isin(valores)]
            # Caso especial: Si el filtro es Cliente_Nombre o Vendedor_Nombre y es una búsqueda parcial (lista de resultados)
            elif columna in ['Cliente_Nombre', 'Vendedor_Nombre'] and valores:
                 # Esta lista de 'valores' contiene los nombres que coinciden con la búsqueda parcial
                 df_filtrado = df_filtrado[df_filtrado[columna].isin(valores)]
                 
    return df_filtrado

def crear_tabla_dinamica(df: pd.DataFrame, ejes_agrupacion: list, metrica: str) -> pd.DataFrame:
    """
    Crea una tabla dinámica agrupando por la lista de ejes de agrupación (anidado) 
    y agregando la métrica.
    """
    if df.empty or metrica not in df.columns:
        return pd.DataFrame()

    # Si solo hay dos años, se asume que es una comparación (necesita la columna Anio)
    if len(df['Anio'].unique()) == 2:
        
        # 1. Agrupación por EJES + Año para la comparación
        cols_agrupacion = ejes_agrupacion + ['Anio']
        df_agrupado = df.groupby(cols_agrupacion)[metrica].sum().reset_index()

        # 2. Pivotear para crear columnas de año
        df_pivot = df_agrupado.pivot_table(
            index=ejes_agrupacion,
            columns='Anio',
            values=metrica,
            fill_value=0
        ).reset_index()

        # 3. Calcular el crecimiento
        anios = sorted(df['Anio'].unique().tolist())
        col_menor = anios[0]
        col_mayor = anios[1]

        df_pivot['CRECIMIENTO'] = df_pivot[col_mayor] - df_pivot[col_menor]
        
        # Manejar división por cero
        df_pivot['%_CRECIMIENTO'] = df_pivot.apply(
            lambda row: (row['CRECIMIENTO'] / row[col_menor]) * 100 if row[col_menor] != 0 else (100 if row[col_mayor] > 0 else 0), 
            axis=1
        )
        
        # Renombrar columnas para mantener la consistencia con app.py
        df_pivot.rename(columns={
            col_menor: f'{metrica}_{col_menor}',
            col_mayor: f'{metrica}_{col_mayor}',
            '%_CRECIMIENTO': f'%_CRECIMIENTO_{metrica}'
        }, inplace=True)
        
        df_pivot.drop(columns=['CRECIMIENTO'], inplace=True, errors='ignore')
        
        return df_pivot
        
    # Si hay 0, 1 o más de 2 años (Agregación Simple)
    else:
        df_agrupado = df.groupby(ejes_agrupacion)[metrica].sum().reset_index()
        df_agrupado.rename(columns={metrica: f'Sum_{metrica}'}, inplace=True)
        return df_agrupado
    