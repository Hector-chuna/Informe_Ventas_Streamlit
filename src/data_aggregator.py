# C:\Users\User\Desktop\respaldo\Inf_ventas\src\data_aggregator.py (CONSOLIDADOR ÚNICO DE CONSTANTES - FIX DE NOMBRE)

from typing import Dict, List, Any

# =========================================================================
# 🎯 MÓDULO CORREGIDO: CONCENTRADOR DE CONSTANTES GLOBALES
# =========================================================================

# --- 1. Definiciones de Agrupación/Jerarquía ---

# Jerarquía principal de agrupación para tablas y subtotales (Usado por app.py)
COLUMNAS_AGRUPACION: List[str] = ['Vendedor_Nombre', 'Cliente_Nombre', 'Marca']

# Mapeo de columnas de la BD (DuckDB) a los nombres limpios usados en el dashboard
# (Usado por data_loader.py para estandarizar nombres al cargar.)
COLUMN_MAPPING_TO_DASHBOARD: Dict[str, str] = {
    'Anio': 'Anio',
    'Mes': 'Mes',
    'Codcliente': 'Cliente_ID', # 🔥 FIX CRÍTICO: Mapeo de Codcliente a Cliente_ID para la auditoría de app.py
    'Vendedor_Nombre': 'Vendedor_Nombre', # Usamos Vendedor_Nombre en lugar de 'Vendedor' (por si app.py lo espera)
    'Cliente_Nombre': 'Cliente_Nombre',  # Usamos Cliente_Nombre en lugar de 'Cliente'
    'Codartprov': 'Producto_Nombre', # Usamos un código de artículo como nombre de producto si no hay otro
    'Marca': 'Marca',
    'Tipo_Producto': 'Tipo_Producto',
    'Venta_Neta': 'Venta_Neta',
    'CANTIDAD': 'CANTIDAD',
    # Nota: He usado nombres de columna confirmados en tu auditoría (e.g., 'Marca', 'Vendedor_Nombre', 'Cliente_Nombre')
    # para asegurar que el mapeo sea 1:1.
}

# --- 2. Definiciones de Métricas y Nombres ---

# Nombres legibles para las métricas base usadas en la lógica y la interfaz (Usado por app.py)
METRICAS_BASE: Dict[str, str] = {
    'Venta_Neta': 'Monto Total (TOTAL)', 
    'CANTIDAD': 'Cantidad de Unidades (CANTIDAD)'
}

# Mapeo de números de mes a nombres para estandarización (Usado por ui_handler.py y app.py)
# 🎯 FIX CLAVE: Se nombra como MONTH_MAPPING, que es el nombre que app.py intenta importar.
MONTH_MAPPING: Dict[int, str] = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

# Alias para MESES_NOMBRES, manteniendo compatibilidad con otros módulos.
MESES_NOMBRES: Dict[int, str] = MONTH_MAPPING


# --- 3. Constantes de Formato y Visualización ---

# Anchos de columna para la generación de PDF (Usado por visualizer.py)
ANCHOS_COLUMNAS: Dict[str, float] = {
    'default_agrupacion': 30, 
    'default_metrica': 25, 
    'Cliente_Nombre': 50,
    'Vendedor_Nombre': 40,
}