# C:\Users\User\Desktop\respaldo\Inf_ventas\src\data_processor.py

import pandas as pd
import numpy as np
from typing import List

# Se asume que 'df' viene ordenado correctamente por los ejes de agrupación

def calcular_subtotales_anidados(df: pd.DataFrame, ejes_agrupacion: List[str], cols_a_sumar: List[str]) -> pd.DataFrame:
    """
    Calcula e inserta subtotales anidados en la posición correcta (después de cada grupo)
    mediante una reconstrucción determinística del DataFrame.
    
    :param df: DataFrame ya ordenado que contiene los datos de detalle.
    :param ejes_agrupacion: Lista de columnas para las cuales se deben calcular los subtotales 
                            (Ej: ['Vendedor_Nombre', 'Cliente_Nombre', 'Marca']).
    :param cols_a_sumar: Lista de columnas métricas que deben sumarse.
    :return: DataFrame con las filas de subtotales insertadas en la posición correcta.
    """

    if not ejes_agrupacion or df.empty:
        return df

    # --- 1. CONFIGURACIÓN INICIAL ---
    
    # Aseguramos que el DF base sea una copia limpia y manejamos NaN/None con un string vacío para el quiebre
    df_base = df.copy()
    for col in ejes_agrupacion:
        df_base[col] = df_base[col].fillna('')

    df_list = []
    ejes_y_detalle = ejes_agrupacion + ['Mes_Nombre']
    
    # Añadimos la columna de CLASIFICACIÓN DE NIVEL e inicializamos en DETALLE
    df_base['NIVEL_SUBTOTAL'] = 'DETALLE'
    
    # Definición de nombres de ejes para evitar errores de índice
    eje_vendedor = ejes_agrupacion[0]
    eje_cliente = ejes_agrupacion[1]
    eje_marca = ejes_agrupacion[2]


    # --- 3. RECONSTRUCCIÓN DETERMINÍSTICA DEL DATAFRAME ---
    
    # 3a. Iterar sobre los grupos del nivel más alto (Vendedor)
    for vendedor, df_vendedor in df_base.groupby(eje_vendedor, dropna=False):
        
        # 3b. Iterar sobre los grupos del segundo nivel (Cliente)
        for cliente, df_cliente in df_vendedor.groupby(eje_cliente, dropna=False):
            
            # 3c. Iterar sobre los grupos del tercer nivel (Marca)
            for marca, df_marca in df_cliente.groupby(eje_marca, dropna=False):
                
                # A. Agregar filas de DETALLE (Meses)
                df_list.append(df_marca)
                
                # B. Insertar Subtotal MARCA
                sub_marca = df_marca[cols_a_sumar].sum().to_frame().T
                
                # Asignar etiquetas
                sub_marca[eje_marca] = f'Total {eje_marca.replace("_Nombre", "")}'.upper()
                sub_marca['Mes_Nombre'] = ''
                
                # CLASIFICACIÓN DE NIVEL: MARCA
                sub_marca['NIVEL_SUBTOTAL'] = 'MARCA' 
                
                # Propagar las claves de jerarquía
                sub_marca[eje_vendedor] = vendedor
                sub_marca[eje_cliente] = cliente
                for col in ejes_agrupacion[3:]:
                    if col not in sub_marca.columns:
                        sub_marca[col] = ''
                
                df_list.append(sub_marca)
                
            # C. Insertar Subtotal CLIENTE
            sub_cliente = df_vendedor.loc[df_vendedor[eje_cliente] == cliente].groupby(eje_cliente)[cols_a_sumar].sum().reset_index()
            
            # Rellenar con los valores correctos de la jerarquía superior
            sub_cliente[eje_cliente] = f'Total {eje_cliente.replace("_Nombre", "")}'.upper()
            sub_cliente[eje_marca] = ''
            sub_cliente['Mes_Nombre'] = ''
            
            # CLASIFICACIÓN DE NIVEL: CLIENTE
            sub_cliente['NIVEL_SUBTOTAL'] = 'CLIENTE' 

            sub_cliente[eje_vendedor] = df_vendedor.iloc[0][eje_vendedor]
            
            df_list.append(sub_cliente)
            
        # D. Insertar Subtotal VENDEDOR
        sub_vendedor = df_base.loc[df_base[eje_vendedor] == vendedor].groupby(eje_vendedor)[cols_a_sumar].sum().reset_index()
        
        # Asignar etiquetas
        sub_vendedor[eje_vendedor] = f'Total {eje_vendedor.replace("_Nombre", "")}'.upper()
        sub_vendedor[eje_cliente] = ''
        sub_vendedor[eje_marca] = ''
        sub_vendedor['Mes_Nombre'] = ''
        
        # CLASIFICACIÓN DE NIVEL: VENDEDOR
        sub_vendedor['NIVEL_SUBTOTAL'] = 'VENDEDOR' 

        df_list.append(sub_vendedor)


    # E. CONCATENACIÓN FINAL Y COPIA EXPLÍCITA
    df_final_con_subtotales = pd.concat(df_list, ignore_index=True).copy()
    
    # 4. Total General (Calculado una sola vez sobre el DF original)
    df_total_general = df[cols_a_sumar].sum().to_frame().T
    
    # Rellenar la fila de Total General con las etiquetas correctas
    df_total_general[eje_vendedor] = 'TOTAL GENERAL'
    for eje in ejes_agrupacion[1:] + ['Mes_Nombre']:
        if eje in df_total_general.columns:
            df_total_general[eje] = ''
            
    # CLASIFICACIÓN DE NIVEL: GENERAL
    df_total_general['NIVEL_SUBTOTAL'] = 'GENERAL' 


    # 5. Limpieza Final: Aseguramos que los valores sean strings vacíos para presentación
    for col in ejes_y_detalle:
        if col in df_final_con_subtotales.columns:
             df_final_con_subtotales[col] = df_final_con_subtotales[col].fillna('')
             
    # Eliminamos duplicados por seguridad
    df_final_con_subtotales.drop_duplicates(inplace=True)

    # 6. Insertar Total General al final
    total_vendedor_label = f'TOTAL {eje_vendedor.replace("_NOMBRE", "")}'.upper()
    
    if 'TOTAL GENERAL' not in df_final_con_subtotales[eje_vendedor].values and \
       (df_base[eje_vendedor].nunique() > 1 or total_vendedor_label not in df_final_con_subtotales[eje_vendedor].values):
         df_final_con_subtotales = pd.concat([df_final_con_subtotales, df_total_general], ignore_index=True)
         
    
    return df_final_con_subtotales.copy()