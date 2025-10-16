# C:\Users\User\Desktop\respaldo\Inf_ventas\src\formatter.py (OPTIMIZADO Y ROBUSTO)

import pandas as pd
from typing import Union, Any, Callable

# ====================================================================
# 🎯 RESPONSABILIDAD ÚNICA: FORMATEO Y LOCALIZACIÓN DE VALORES NUMÉRICOS
# ====================================================================

def formatear_miles(valor: Union[int, float, Any]) -> str:
    """
    Formatea un valor numérico a entero con separador de miles ('.') 
    y separador decimal (',') para localización latina (sin decimales).
    """
    # Manejar valores nulos, no numéricos o cero
    if pd.isna(valor) or not isinstance(valor, (int, float)) or valor == 0:
        return '-'
    
    # Redondear a entero (para montos/cantidades)
    valor_redondeado = round(valor)
    
    # 1. Usar el formato estándar de Python f"{:,}" (genera comas como miles y punto como decimal)
    # 2. Reemplazar para localización LATAM/ES: Coma (miles) -> Punto, Punto (decimal) -> Coma
    # Nota: El uso de 'X' es un truco temporal para evitar colisiones.
    return f"{valor_redondeado:,}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatear_decimales(valor: Union[int, float, Any], decimales: int = 2) -> str:
    """
    Formatea un valor numérico a un número con decimales fijos, usando '.' como miles y ',' como decimal.
    
    Args:
        valor: El valor numérico a formatear.
        decimales: Número de posiciones decimales a mostrar (por defecto 2).
    """
    if pd.isna(valor) or not isinstance(valor, (int, float)) or valor == 0:
        return '-'

    # Usar f-string para formatear el número con el formato estándar de Python (coma para miles, punto para decimal)
    # Ejemplo: 12345.678 -> '12,345.68' (si decimales=2)
    str_formateado_py = f"{valor:,.{decimales}f}"
    
    # Aplicar la localización LATAM/ES:
    # 1. Reemplazar el punto decimal ('.') por un marcador temporal 'X'.
    # 2. Reemplazar las comas (',', separador de miles) por el punto de miles ('.').
    # 3. Reemplazar el marcador temporal ('X') por la coma decimal (',').
    return str_formateado_py.replace('.', 'X').replace(',', '.').replace('X', ',')

def formatear_porcentaje(valor: Union[int, float, Any]) -> str:
    """
    Formatea un valor a porcentaje con dos decimales, usando '.' como miles y ',' como decimal.
    """
    if pd.isna(valor):
        return '-'
    
    # Reutilizar la función de formateo de decimales
    numero_localizado = formatear_decimales(valor, decimales=2)
    
    if numero_localizado == '-':
        return '-'
        
    return f"{numero_localizado}%"

def obtener_key_ordenamiento() -> Callable[[pd.Series], pd.Series]:
    """
    Devuelve la función lambda para ordenar una columna de Pandas que contiene 
    strings con formato de miles/porcentaje localizado (ej: '9.973.518' o '25,45%').
    
    La clave de ordenamiento convierte el string localizado de vuelta a float:
    1. Maneja etiquetas de total y valores nulos/cero ('-').
    2. Elimina el símbolo de porcentaje ('%').
    3. Reemplaza el separador de miles ('.') y el separador decimal (',') para que Python lo lea como float.
    """
    return lambda x: x.astype(str).str.replace('TOTAL|Total|GENERAL', '0', case=False) \
                       .str.replace('-', '-99999999999') \
                       .str.replace('%', '', regex=False) \
                       .str.replace('.', '', regex=False) \
                       .str.replace(',', '.', regex=False) \
                       .astype(float)