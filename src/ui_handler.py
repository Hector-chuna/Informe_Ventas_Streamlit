import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Tuple

# CONSTANTES DE AGRUPACIÓN
# CORREGIDO: Lista de tuplas (nombre_interno, etiqueta_visible) para el desempaquetado.
CAMPOS_INTERNOS: List[Tuple[str, str]] = [
    ('Tipo_Producto', 'Tipo de Producto'),
    ('Cliente_ID', 'ID de Cliente'),
    ('Cliente_Nombre', 'Nombre del Cliente'),
    ('Marca', 'Marca'), 
    ('Vendedor_Nombre', 'Nombre del Vendedor'),
    ('TIPO_VENTA', 'Tipo de Venta'),
    ('TIPO1', 'TIPO1'),
    ('TIPO2', 'TIPO2'),
    ('TIPO3', 'TIPO3')
]

ESTRATEGIAS = {
    "Personalizado (Ajustar Manualmente)": {},
    "🎯 Ataque Estratégico (Declive)": {
        'Tipo_Producto': None, 
        'Eje_X': 'Cliente_Nombre',
        'Metrica': 'Venta_Neta', 
        'Ordenamiento': 'Declive' 
    },
    "🏆 Premiar (Alto Valor)": {
        'Tipo_Producto': None, 
        'Eje_X': 'Cliente_Nombre',
        'Metrica': 'Venta_Neta',
        'Ordenamiento': 'Monto' 
    },
}

def dibujar_barra_lateral_y_obtener_config(df_ventas: pd.DataFrame, archivo_excel: str) -> Tuple[Dict[str, List[Any]], Dict[str, Any]]:
    """
    Dibuja todos los widgets de la barra lateral (filtros, métricas, eje X)
    y devuelve la configuración final para el procesamiento.
    """
    
    # --- SELECCIÓN DE ESTRATEGIA ---
    st.subheader("Selección Rápida de Estrategia")
    estrategia_actual = st.selectbox(
        "Seleccione una Estrategia de Análisis:",
        options=list(ESTRATEGIAS.keys()),
        key='estrategia_select'
    )
    
    config = ESTRATEGIAS[estrategia_actual]
    
    # --- FILTROS TEMPORALES (MULTISELECT) ---
    st.subheader("Filtros Temporales")
    
    # Manejo de años
    if 'Anio' in df_ventas.columns:
        anios_disponibles = sorted(df_ventas['Anio'].unique().tolist())
    else:
        st.error("Columna 'Anio' no encontrada. Verifique la carga de datos.")
        anios_disponibles = []

    
    # 1. Filtro de Años (Limitado a 2)
    default_anios = anios_disponibles[-2:] if len(anios_disponibles) >= 2 else anios_disponibles
    anios_seleccionados = st.multiselect(
        "1. Seleccionar Año(s) para Comparación (Máx. 2):",
        options=anios_disponibles,
        default=default_anios,
        key='anio_select'
    )
    
    if len(anios_seleccionados) > 2:
        st.warning("Solo se pueden seleccionar un máximo de dos años para la comparación.")
        anios_seleccionados = anios_seleccionados[-2:]
    
    if not anios_seleccionados and anios_disponibles:
        anios_seleccionados = anios_disponibles 
        st.info("Mostrando todos los años disponibles por defecto.")
    elif not anios_disponibles:
        anios_seleccionados = []


    # 2. Nivel de Análisis Temporal (Meses/Trimestres)
    nivel_temporal = st.selectbox(
        "2. Nivel de Análisis Temporal:",
        options=['Total Anual', 'Semestre', 'Trimestre', 'Mes'],
        index=0 
    )
    
    meses_a_filtrar = list(range(1, 13))
    
    if nivel_temporal == 'Semestre':
        opciones = {'Primer Semestre': list(range(1, 7)), 'Segundo Semestre': list(range(7, 13))}
        semestre_select = st.multiselect("Seleccionar Semestre:", list(opciones.keys()), default=list(opciones.keys()))
        meses_a_filtrar = [m for s in semestre_select for m in opciones[s]]
        
    elif nivel_temporal == 'Trimestre':
        opciones = {'1er Trimestre (Ene-Mar)': list(range(1, 4)), '2do Trimestre (Abr-Jun)': list(range(4, 7)), 
                    '3er Trimestre (Jul-Sep)': list(range(7, 10)), '4to Trimestre (Oct-Dic)': list(range(10, 13))}
        trimestre_select = st.multiselect("Seleccionar Trimestre:", list(opciones.keys()), default=list(opciones.keys()))
        meses_a_filtrar = [m for t in trimestre_select for m in opciones[t]]
        
    elif nivel_temporal == 'Mes':
        meses_nombres = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                         7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
        mes_select = st.multiselect("Seleccionar Mes:", list(meses_nombres.values()), default=list(meses_nombres.values()))
        meses_a_filtrar = [k for k, v in meses_nombres.items() if v in mes_select]

    # --- FILTROS DE AGRUPAMIENTO ESENCIALES ---
    st.subheader("Filtros de Agrupamiento")
    
    filtros_aplicados = {}

    # Ahora el bucle itera sobre tuplas de 2 elementos
    for campo_interno, etiqueta_visible in CAMPOS_INTERNOS:
        if campo_interno not in df_ventas.columns:
            continue 
        
        try:
            # Asegurar que los valores sean strings para una mejor comparación/filtrado
            columna_serie = df_ventas[campo_interno].astype(str) 
            # Excluir el nombre vacío o espacios en blanco para la selección
            valores_unicos = sorted([v for v in columna_serie.unique().tolist() if v.strip() != '']) 
        except Exception:
            valores_unicos = [] 
            
        default_val = config.get(campo_interno, valores_unicos) 
        
        # Lógica especial para Cliente_Nombre (Búsqueda de Texto Parcial)
        if campo_interno == 'Cliente_Nombre':
            busqueda = st.text_input(f"🔍 Filtrar {etiqueta_visible} (Texto Parcial):", key=f'busqueda_{campo_interno}')
            if busqueda:
                valores_filtrados = [v for v in valores_unicos if busqueda.upper() in v.upper()]
                if valores_filtrados:
                    filtros_aplicados[campo_interno] = valores_filtrados
                else:
                    st.warning(f"No se encontraron coincidencias para '{busqueda}'.")
                    filtros_aplicados[campo_interno] = [] 
            else:
                filtros_aplicados[campo_interno] = valores_unicos
        
        # Lógica de Multiselect (Incluye Vendedor_Nombre y todos los demás campos)
        else: 
            seleccion = st.multiselect(
                f"Filtrar por {etiqueta_visible}:",
                options=valores_unicos,
                # Usar valores_unicos como default para que el filtro esté activo por defecto
                default=default_val if default_val is not None else valores_unicos,
                key=f'multiselect_{campo_interno}'
            )
            filtros_aplicados[campo_interno] = seleccion
    
    # --- SELECCIÓN DE MÉTRICAS Y EJE X ---
    st.subheader("Métricas de Cálculo")
    
    metricas_base = {
        'Venta_Neta': 'Monto Total (TOTAL)', 
        'CANTIDAD': 'Cantidad de Unidades (CANTIDAD)'
    }
    
    metricas_filtrables = st.multiselect(
        "Métricas a Incluir en el Análisis:",
        options=list(metricas_base.keys()),
        default=list(metricas_base.keys()),
        format_func=lambda x: metricas_base[x]
    )
    
    metrica_seleccionada_key = st.selectbox(
        "Métrica Principal (Eje Y):",
        options=metricas_filtrables if metricas_filtrables else ['Venta_Neta'],
        format_func=lambda x: metricas_base[x],
        index=0
    )
    
    # Opciones para el Eje X (Usamos solo los nombres internos de CAMPOS_INTERNOS)
    eje_x_options = [c[0] for c in CAMPOS_INTERNOS]

    eje_x_seleccionado = st.selectbox(
        "Eje de Agrupación para Gráficos/Tablas:",
        options=eje_x_options,
        # Buscar el índice usando el nombre interno del campo
        index=eje_x_options.index(config.get('Eje_X', 'Vendedor_Nombre')) if config.get('Eje_X', 'Vendedor_Nombre') in eje_x_options else 0
    )
    
    # --- CONTROLES DE PANELES DE VISUALIZACIÓN ---
    st.sidebar.subheader("Vistas del Informe")
    
    check_tablas = st.sidebar.checkbox("✅ Datos Numéricos (Tabla)", value=True)
    check_lineas = st.sidebar.checkbox("✅ Evolución (Líneas)", value=True)
    check_barras = st.sidebar.checkbox("✅ Comparación (Barras)", value=False)
    check_circular = st.sidebar.checkbox("✅ Proporción (Circular)", value=False)
    
    # Recolectar todos los filtros
    filtros = {
        'Anio': anios_seleccionados, 
        'Mes': meses_a_filtrar,
        **filtros_aplicados
    }

    configuracion_visual = {
        'metricas_filtrables': metricas_filtrables,
        'metrica_principal': metrica_seleccionada_key,
        'eje_x': eje_x_seleccionado,
        'check_tablas': check_tablas,
        'check_lineas': check_lineas,
        'check_barras': check_barras,
        'check_circular': check_circular,
        'anios_seleccionados': anios_seleccionados
    }

    return filtros, configuracion_visual