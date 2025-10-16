# C:\Users\User\Desktop\respaldo\Inf_ventas\src\ui_handler.py (LIMPIEZA FINAL Y SSOT)

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Tuple
import numpy as np 

# ====================================================================
# 🎯 CORRECCIÓN CLAVE: Importación estricta de constantes desde data_aggregator.py (SSOT).
# Se eliminan los fallbacks y la redefinición local de METRICAS_BASE.
# ====================================================================
try:
    # Importación de las dos constantes requeridas desde la fuente única
    from .data_aggregator import MESES_NOMBRES, METRICAS_BASE
except ImportError as e:
    print(f"Error Crítico: No se pueden importar constantes esenciales desde data_aggregator.py. {e}")
    st.error("Error de Configuración: Revise 'src/data_aggregator.py' para asegurar MESES_NOMBRES y METRICAS_BASE.")
    raise SystemExit(1) 


# CONSTANTES DE AGRUPACIÓN (Específicas de la UI/Filtros, se mantienen aquí)
# Lista de tuplas (nombre_interno, etiqueta_visible)
CAMPOS_INTERNOS: List[Tuple[str, str]] = [
    ('Tipo_Producto', 'Tipo de Producto'),
    ('Cliente_Nombre', 'Nombre del Cliente'), 
    ('Marca', 'Marca'), 
    ('Vendedor_Nombre', 'Nombre del Vendedor'),
    ('TIPO_VENTA', 'Tipo de Venta'),
    ('TIPO1', 'TIPO1'),
    ('TIPO2', 'TIPO2'),
    ('TIPO3', 'TIPO3')
]


# ====================================================================
# DEFINICIÓN DE ESTRATEGIAS (ACTUALIZADA)
# ====================================================================

ESTRATEGIAS = {
    "Personalizado (Ajustar Manualmente)": {},
    "🎯 Ataque Estratégico (Declive)": {
        'Anios': [2024, 2025], # <-- Años Fijos
        'Tipo_Producto': ['CALZADOS'], # <-- Producto Fijo
        'Nivel_Temporal': 'Semestre', # <-- Fija el control de Semestre
        'Meses': list(range(7, 13)), # <-- Meses del 2do Semestre
        'Eje_X': 'Cliente_Nombre',
        'Metrica': 'Venta_Neta', 
        'Ordenamiento': 'Declive',
        'Ejes_Tabla': ['Vendedor_Nombre', 'Cliente_Nombre', 'Marca', 'Mes_Nombre'], 
        'Vistas': {'check_tablas': True, 'check_lineas': True, 'check_barras': False, 'check_circular': False}
    },
    "🏆 Premiar (Alto Valor)": {
        'Tipo_Producto': None, 
        'Eje_X': 'Cliente_Nombre',
        'Metrica': 'Venta_Neta',
        'Ordenamiento': 'Monto',
        'Ejes_Tabla': ['Vendedor_Nombre', 'Cliente_Nombre', 'Marca'],
        'Vistas': {'check_tablas': True, 'check_lineas': True, 'check_barras': True, 'check_circular': False}
    },
    "📊 Rendimiento Calzados x Vendedor": {
        'Tipo_Producto': ['CALZADOS'], 
        'Eje_X': 'Vendedor_Nombre', 
        'Metrica': 'Venta_Neta', 
        'Ejes_Tabla': ['Vendedor_Nombre', 'Cliente_Nombre'],
        'Vistas': {'check_tablas': True, 'check_lineas': True, 'check_barras': True, 'check_circular': False}
    },
}

# ====================================================================
# FUNCIÓN PRINCIPAL DE WIDGETS (AJUSTADA Y OPTIMIZADA)
# ====================================================================

def dibujar_barra_lateral_y_obtener_config(df_ventas: pd.DataFrame, db_name: str) -> Tuple[Dict[str, List[Any]], Dict[str, Any]]:
    """
    Dibuja todos los widgets de la barra lateral (filtros, métricas, eje X)
    y devuelve la configuración final para el procesamiento.
    """
    
    # --- 1. PRE-PROCESAMIENTO: Asegurar Mes_Nombre para las estrategias ---
    if 'Mes_Nombre' not in df_ventas.columns and 'Mes' in df_ventas.columns:
        df_ventas = df_ventas.copy() 
        # Uso de la constante MESES_NOMBRES importada
        df_ventas['Mes_Nombre'] = df_ventas['Mes'].map(MESES_NOMBRES).fillna('Sin Mes')


    # --- 2. SELECCIÓN DE ESTRATEGIA ---
    st.sidebar.subheader("Selección Rápida de Estrategia")
    estrategia_actual = st.sidebar.selectbox(
        "Seleccione una Estrategia de Análisis:",
        options=list(ESTRATEGIAS.keys()),
        key='estrategia_select'
    )
    
    config = ESTRATEGIAS[estrategia_actual].copy()
    filtros_aplicados = {}


    # --- 3. FILTROS TEMPORALES ---
    st.sidebar.subheader("Filtros Temporales")
    
    # AÑOS
    if 'Anio' in df_ventas.columns:
        anios_disponibles = sorted(df_ventas['Anio'].dropna().unique().tolist())
    else:
        st.sidebar.error("Columna 'Anio' no encontrada.")
        anios_disponibles = []

    default_anios = config.get('Anios', anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles)
    anios_seleccionados = st.sidebar.multiselect(
        "1. Seleccionar Año(s) para Comparación (Máx. 2):",
        options=anios_disponibles,
        default=default_anios, 
        key='anio_select'
    )
    if len(anios_seleccionados) > 2:
        st.sidebar.warning("Solo se pueden seleccionar un máximo de dos años para la comparación.")
        anios_seleccionados = anios_seleccionados[-2:]
    
    
    # MESES / NIVEL TEMPORAL
    default_nivel_temporal = config.get('Nivel_Temporal', 'Total Anual') 
    
    if 'Meses' in config:
        st.sidebar.info(f"Nivel Fijo: **{default_nivel_temporal}** (Meses {min(config['Meses'])}-{max(config['Meses'])}).")
        nivel_temporal = default_nivel_temporal
        meses_a_filtrar = config['Meses']
    else:
        nivel_temporal = st.sidebar.selectbox(
            "2. Nivel de Análisis Temporal:",
            options=['Total Anual', 'Semestre', 'Trimestre', 'Mes'],
            index=['Total Anual', 'Semestre', 'Trimestre', 'Mes'].index(default_nivel_temporal)
        )
        
        meses_a_filtrar = list(range(1, 13))
        
        # Lógica de selección de meses interactiva
        if nivel_temporal == 'Semestre':
            opciones = {'Primer Semestre': list(range(1, 7)), 'Segundo Semestre': list(range(7, 13))}
            semestre_select = st.sidebar.multiselect("Seleccionar Semestre:", list(opciones.keys()), default=list(opciones.keys()), key='semestre_select')
            meses_a_filtrar = [m for s in semestre_select for m in opciones[s]]
        elif nivel_temporal == 'Trimestre':
            opciones = {'1er Trimestre (Ene-Mar)': list(range(1, 4)), '2do Trimestre (Abr-Jun)': list(range(4, 7)), 
                        '3er Trimestre (Jul-Sep)': list(range(7, 10)), '4to Trimestre (Oct-Dic)': list(range(10, 13))}
            trimestre_select = st.sidebar.multiselect("Seleccionar Trimestre:", list(opciones.keys()), default=list(opciones.keys()))
            meses_a_filtrar = [m for t in trimestre_select for m in opciones[t]]
        elif nivel_temporal == 'Mes':
            # Usa MESES_NOMBRES importado para la UI
            meses_nombres_ui = MESES_NOMBRES
            mes_select = st.sidebar.multiselect("Seleccionar Mes:", list(meses_nombres_ui.values()), default=list(meses_nombres_ui.values()))
            # Mapeo inverso de nombres a números de mes para el filtrado
            meses_a_filtrar = [k for k, v in meses_nombres_ui.items() if v in mes_select]


    # --- 4. FILTROS DE AGRUPAMIENTO ESENCIALES ---
    st.sidebar.subheader("Filtros de Agrupamiento")
    
    for campo_interno, etiqueta_visible in CAMPOS_INTERNOS:
        if campo_interno == 'Cliente_ID':
             continue
        
        if campo_interno not in df_ventas.columns:
            continue 
        
        columna_serie = df_ventas[campo_interno].astype(str) 
        valores_unicos = sorted([v for v in columna_serie.unique().tolist() if v.strip() != '']) 
            
        default_val = config.get(campo_interno) 
        
        default_selection = default_val if default_val is not None else valores_unicos
        
        if campo_interno == 'Cliente_Nombre':
            busqueda = st.sidebar.text_input(f"🔍 Filtrar {etiqueta_visible} (Texto Parcial):", key=f'busqueda_{campo_interno}')
            
            lista_base = default_selection 
            
            if busqueda:
                valores_filtrados = [v for v in lista_base if busqueda.upper() in v.upper()]
                filtros_aplicados[campo_interno] = valores_filtrados if valores_filtrados else []
                if not valores_filtrados and busqueda:
                    st.sidebar.warning(f"No se encontraron coincidencias para '{busqueda}'.")
            else:
                filtros_aplicados[campo_interno] = lista_base
            
        else: 
            seleccion = st.sidebar.multiselect(
                f"Filtrar por {etiqueta_visible}:",
                options=valores_unicos,
                default=default_selection, 
                key=f'multiselect_{campo_interno}'
            )
            filtros_aplicados[campo_interno] = seleccion 
    
    # --- 5. SELECCIÓN DE MÉTRICAS Y EJE X ---
    st.sidebar.subheader("Métricas de Cálculo")
    
    # ✅ CORREGIDO: Usamos METRICAS_BASE importado
    # La línea de redefinición local: metricas_base = {'Venta_Neta': 'Monto Total (TOTAL)', 'CANTIDAD': 'Cantidad de Unidades (CANTIDAD)'} fue eliminada.
    
    default_metrica = config.get('Metrica', 'Venta_Neta')
    metricas_filtrables = st.sidebar.multiselect(
        "Métricas a Incluir en el Análisis:",
        options=list(METRICAS_BASE.keys()),
        default=list(METRICAS_BASE.keys()),
        format_func=lambda x: METRICAS_BASE[x] # Usamos METRICAS_BASE importado
    )
    
    metrica_seleccionada_key = st.sidebar.selectbox(
        "Métrica Principal (Eje Y):",
        options=metricas_filtrables if metricas_filtrables else [default_metrica],
        format_func=lambda x: METRICAS_BASE[x], # Usamos METRICAS_BASE importado
        index=metricas_filtrables.index(default_metrica) if default_metrica in metricas_filtrables else 0
    )
    
    # Opciones para el Eje X
    eje_x_options = [c[0] for c in CAMPOS_INTERNOS if c[0] in df_ventas.columns]
    if 'Mes_Nombre' in df_ventas.columns:
        eje_x_options.insert(0, 'Mes_Nombre')
        
    default_eje_x = config.get('Eje_X', 'Vendedor_Nombre')
    
    eje_x_seleccionado = st.sidebar.selectbox(
        "Eje de Agrupación para Gráficos/Tablas:",
        options=eje_x_options,
        index=eje_x_options.index(default_eje_x) if default_eje_x in eje_x_options else 0,
        key='eje_x_select'
    )
    
    # --- 6. CONTROLES DE PANELES DE VISUALIZACIÓN ---
    st.sidebar.subheader("Vistas del Informe")
    
    vistas_config = config.get('Vistas', {'check_tablas': True, 'check_lineas': True, 'check_barras': True, 'check_circular': False})
    
    check_tablas = st.sidebar.checkbox("✅ Datos Numéricos (Tabla)", value=vistas_config.get('check_tablas', True))
    check_lineas = st.sidebar.checkbox("✅ Evolución (Líneas)", value=vistas_config.get('check_lineas', True))
    check_barras = st.sidebar.checkbox("✅ Comparación (Barras)", value=vistas_config.get('check_barras', True))
    check_circular = st.sidebar.checkbox("✅ Proporción (Circular)", value=vistas_config.get('check_circular', False))
    
    # ===================================================================
    # RECOLECCIÓN FINAL DE FILTROS Y CONFIGURACIÓN
    # ===================================================================
    campos_a_incluir = [c[0] for c in CAMPOS_INTERNOS if c[0] != 'Cliente_ID']
    
    filtros = {
        'Anios': anios_seleccionados, 
        'Meses': meses_a_filtrar, 
        **{k: v for k, v in filtros_aplicados.items() if k in campos_a_incluir} 
    }
    
    configuracion_visual = {
        'metricas_filtrables': metricas_filtrables,
        'metrica_principal': metrica_seleccionada_key,
        'eje_x': eje_x_seleccionado,
        'check_tablas': check_tablas,
        'check_lineas': check_lineas,
        'check_barras': check_barras,
        'check_circular': check_circular,
        'anios_seleccionados': anios_seleccionados,
        'ordenamiento': config.get('Ordenamiento'),
        'ejes_tabla_estrategia': config.get('Ejes_Tabla'), 
    }

    return filtros, configuracion_visual