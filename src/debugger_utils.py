# C:\Users\User\Desktop\respaldo\Inf_ventas\src\debugger_utils.py (OPTIMIZADO)

import pandas as pd
from typing import Dict, Any, Optional

# ====================================================================
# Funciones Auxiliares
# ====================================================================

def _crear_matriz_cliente_vendedor(df: pd.DataFrame, tipo_producto: str) -> pd.DataFrame:
    """
    Función auxiliar para crear la matriz de Clientes Únicos por Vendedor y Año
    para un tipo de producto específico.
    """
    # Se verifica la presencia de columnas esenciales antes de operar
    columnas_esenciales = ['Tipo_Producto', 'Vendedor_Nombre', 'Cliente_ID', 'Anio']
    if not all(col in df.columns for col in columnas_esenciales):
        print(f"Advertencia: Faltan columnas esenciales ({', '.join(columnas_esenciales)}) para crear la matriz de vendedor.")
        return pd.DataFrame()
        
    df_tipo = df[df['Tipo_Producto'] == tipo_producto]
    
    if df_tipo.empty:
        return pd.DataFrame()
        
    # Agrupación: Conteo de IDs de Clientes Únicos por Vendedor y Año
    df_pivot = (
        df_tipo.groupby(['Vendedor_Nombre', 'Anio'])['Cliente_ID']
        .nunique() # CONTEO DE CLIENTES ÚNICOS
        .unstack(fill_value=0)
    )
    
    # Asegurarse de que el Total solo sume columnas numéricas (los años)
    numeric_cols = [col for col in df_pivot.columns if pd.api.types.is_numeric_dtype(df_pivot[col])]
    df_pivot['TOTAL_Clientes'] = df_pivot[numeric_cols].sum(axis=1)
    
    df_pivot = df_pivot.sort_values(by='TOTAL_Clientes', ascending=False)
    
    # Formato y preparación para la salida Markdown
    # Uso de applymap con formato de miles y sin decimales
    df_styled = df_pivot.applymap(lambda x: f'{int(x):,}' if pd.notna(x) else '')
    
    # Las columnas de Año pueden ser enteras (int), se convierten a str
    df_styled.columns = [str(col) for col in df_styled.columns]
    df_styled.reset_index(inplace=True)
    
    return df_styled

# ====================================================================
# Funciones Principales de Debugging
# ====================================================================

def verificar_datos_terminal_inicial(df_base: pd.DataFrame):
    """
    Muestra un resumen matricial de CONTEO DE CLIENTES ÚNICOS por Tipo/Año y el conteo total
    al inicio de la ejecución.
    """
    print("===================================================================")
    print("🚀 AUDITORÍA INICIAL: Resumen Matricial de CLIENTES ÚNICOS (Año x Tipo)")
    
    # 1. Conteo total
    total_filas = len(df_base)
    print(f"Total de filas cargadas desde DuckDB: {total_filas:,}")
    
    # 2. Resumen matricial de CLIENTES ÚNICOS (combinado por Año)
    if all(col in df_base.columns for col in ['Anio', 'Tipo_Producto', 'Cliente_ID']):
        
        # Agrupación y conteo de clientes únicos
        df_summary = df_base.groupby(['Tipo_Producto', 'Anio'])['Cliente_ID'].nunique().reset_index(name='Clientes_Unicos')
        df_pivot = df_summary.pivot_table(
            index='Tipo_Producto', 
            columns='Anio', 
            values='Clientes_Unicos', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Cálculo del total de la fila y la columna
        df_pivot['TOTAL_Clientes_Unicos'] = df_pivot.sum(axis=1, numeric_only=True)
        df_pivot.loc['TOTAL_Tipo'] = df_pivot.sum(numeric_only=True)
        
        print("\n✅ MATRIZ COMBINADA (Clientes Únicos - Formato Markdown para Terminal):")

        # Formateamos los números como enteros con comas (usando .applymap)
        df_styled = df_pivot.applymap(lambda x: f'{int(x):,.0f}' if pd.notna(x) else '')
        
        # Ajuste de nombres de columnas
        df_styled.columns = [str(col).replace('Tipo_Producto', 'TIPO') for col in df_styled.columns]
        df_styled.reset_index(names='TIPO', inplace=True) 
        
        print(df_styled.to_markdown(index=False))
        
    else:
        print("ADVERTENCIA: Faltan columnas clave (Anio, Tipo_Producto, Cliente_ID) para la matriz inicial.")
    
    print("===================================================================\n")


def verificar_conteo_filtros_aplicados(df_filtrado: pd.DataFrame, filtros: Dict[str, Any]):
    """
    Muestra un resumen conciso de los filtros aplicados y el conteo resultante.
    Incluye dos matrices de Conteo de Clientes por Vendedor (Calzados y Confecciones).
    """
    print("===================================================================")
    print(f"✅ CONTEO FINAL: {len(df_filtrado):,} filas restantes después de los filtros.")
    print("FILTROS APLICADOS:")
    
    # 1. Resumen de filtros
    filtro_resumen = {}
    for key, value in filtros.items():
        if isinstance(value, list) and value:
            # Mostrar hasta 3 elementos y la cantidad total
            display_value = f"{', '.join(map(str, value[:3]))} (...+{len(value)-3})" if len(value) > 3 else ', '.join(map(str, value))
            filtro_resumen[key] = f"{len(value)} items: {display_value}"
        # Se elimina el manejo de rangos de tuplas si no se usa en los filtros de la UI.
        # Se mantiene un manejo genérico para valores no vacíos
        elif value is not None and value != '' and value != []:
            filtro_resumen[key] = str(value)

    if filtro_resumen:
        df_filtros_aplicados = pd.DataFrame(list(filtro_resumen.items()), columns=['Filtro', 'Valor'])
        print(df_filtros_aplicados.to_markdown(index=False))
    else:
        print("Ningún filtro selectivo aplicado (se usa toda la base base).")
    
    # 2. Verificación Matricial (Conteo de Clientes por Tipo y Vendedor)
    columnas_matriz = ['Vendedor_Nombre', 'Cliente_ID', 'Tipo_Producto', 'Anio']
    if all(col in df_filtrado.columns for col in columnas_matriz) and not df_filtrado.empty:
        
        print("\n===================================================================")
        print("👥 AUDITORÍA DE FILTRO DE VENDEDOR: Conteo de Clientes Únicos por Año")
        
        # A. Matriz Calzados
        df_calzados = _crear_matriz_cliente_vendedor(df_filtrado, 'CALZADOS')
        if not df_calzados.empty:
            print("\nMATRIZ 1: CALZADOS (Clientes Únicos por Vendedor - Top 10):")
            print(df_calzados.head(10).to_markdown(index=False))
        else:
            print("\nMATRIZ 1: CALZADOS (Sin datos después del filtro o tipo 'CALZADOS' no encontrado).")
            
        # B. Matriz Confecciones
        df_confecciones = _crear_matriz_cliente_vendedor(df_filtrado, 'CONFECCIONES')
        if not df_confecciones.empty:
            print("\nMATRIZ 2: CONFECCIONES (Clientes Únicos por Vendedor - Top 10):")
            print(df_confecciones.head(10).to_markdown(index=False))
        else:
            print("\nMATRIZ 2: CONFECCIONES (Sin datos después del filtro o tipo 'CONFECCIONES' no encontrado).")
        
        
    print("===================================================================\n")