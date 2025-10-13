import pandas as pd

def formatear_miles(valor):
    """Formatea un valor numérico a entero con separador de miles (.)."""
    if pd.isna(valor) or valor == 0:
        return '-'
    if isinstance(valor, (int, float)):
        # Redondear y formatear a string con separador de miles '.'
        return f"{round(valor):,}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)

def formatear_porcentaje(valor):
    """Formatea un valor a porcentaje con dos decimales."""
    if pd.isna(valor):
        return '-'
    # Reemplazar ',' por 'X' y '.' por ',' y luego 'X' por '.' para usar punto como separador de miles y coma como decimal
    return f"{valor:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

def obtener_key_ordenamiento():
    """Devuelve la función lambda para ordenar tablas con formato de miles/porcentaje (string)."""
    # Esta función convierte el string de formato ('9.973.518') a un float ordenable
    return lambda x: x.astype(str).str.replace('-', '0').str.replace('%', '').str.replace('.', '').str.replace(',', '.').astype(float)