# C:\Users\User\Desktop\respaldo\Inf_ventas\src\visualizer.py (VERSIÓN CORREGIDA - FIX DE COMPATIBILIDAD PANDAS)

import plotly.express as px
import pandas as pd
from fpdf import FPDF, HTMLMixin 
import io
import plotly.io as pio

# 🎯 FIX CLAVE: Cambiar la importación relativa a una importación de paquete robusta
# Se asume que app.py ha configurado correctamente sys.path para que 'src' sea accesible.
try:
    from src.data_aggregator import ANCHOS_COLUMNAS 
except ImportError:
    # Fallback si se ejecuta visualizer.py directamente o la configuración es diferente
    from .data_aggregator import ANCHOS_COLUMNAS 


# ----------------------------------------------------
# CLASE PDF PERSONALIZADA
# ----------------------------------------------------

class PDF(FPDF, HTMLMixin):
    """Clase personalizada de FPDF con pie de página para la numeración."""
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# ----------------------------------------------------
# CONSTANTES DE DIMENSIONES PARA EL PDF (Internas - SRP)
# ----------------------------------------------------
ALTO_FILA_MM = 5 


# ----------------------------------------------------
# FUNCIONES DE GRÁFICOS
# ----------------------------------------------------

def crear_grafico_barras_comparativo(df_agrupado: pd.DataFrame, x_col: str, y_col: str, titulo: str):
    """Crea un gráfico de barras simple con Plotly."""
    # 🔥 FIX: Eliminado 'default_sort_keys=False' para asegurar compatibilidad con versiones antiguas de Pandas (< 2.1.0)
    df_top = df_agrupado.nlargest(10, y_col)
    
    fig = px.bar(
        df_top, 
        x=x_col, 
        y=y_col, 
        title=titulo, 
        template="plotly_white",
        labels={x_col: x_col.replace('_', ' '), y_col: y_col.replace('_', ' ')},
        text_auto='.2s'
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def crear_grafico_circular_proporcion(df: pd.DataFrame, names_col: str, values_col: str, titulo: str):
    """Crea un gráfico circular de proporción con Plotly."""
    # 🔥 FIX: Eliminado 'default_sort_keys=False' para asegurar compatibilidad con versiones antiguas de Pandas (< 2.1.0)
    df_top = df.nlargest(10, values_col)
    
    fig = px.pie(
        df_top, 
        names=names_col, 
        values=values_col, 
        title=titulo,
        hole=.3,
        template="plotly_white"
    )
    return fig

def crear_grafico_lineas_tendencia(df_evolucion: pd.DataFrame, x_col: str, y_col: str, color_col: str, titulo: str):
    """Crea un gráfico de líneas para la tendencia histórica."""
    fig = px.line(
        df_evolucion, 
        x=x_col, 
        y=y_col, 
        color=color_col, 
        title=titulo, 
        template="plotly_white",
        labels={y_col: y_col.replace('_', ' ')},
        markers=True # Añadir marcadores para mejor visualización
    )
    fig.update_xaxes(title_text='Fecha')
    return fig

# ----------------------------------------------------
# FUNCIÓN DE GENERACIÓN DE PDF
# ----------------------------------------------------

def generar_pdf_informe(titulo_informe: str, contenido_figuras: list, contenido_tablas: list) -> bytes:
    """Genera un informe PDF con tablas y gráficos, dibujando las tablas manualmente."""
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('Arial', 'B', 16)
    
    # Título principal
    pdf.cell(0, 10, titulo_informe, 0, 1, 'C')
    pdf.ln(5)
    
    # Contenido de Tablas
    if contenido_tablas:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "1. Tablas de Datos y Comparación", 0, 1, 'L')
        
        for tabla in contenido_tablas:
            pdf.ln(2)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 5, f"Tabla: {tabla['titulo']}", 0, 1, 'L')
            df_tabla = tabla['df'].copy()
            
            # 1. Determinar el ancho de cada columna para esta tabla específica
            col_widths = {}
            columnas_a_dibujar = df_tabla.columns.tolist()

            for col in columnas_a_dibujar:
                if col == 'Cliente_Nombre':
                    col_widths[col] = ANCHOS_COLUMNAS.get('Cliente_Nombre', 50)
                elif col in ['Vendedor_Nombre', 'Marca', 'Tipo_Producto', 'Cliente_ID', 'Vendedor_ID', 'TIPO_VENTA', 'TIPO1', 'TIPO2', 'TIPO3', 'Mes_Nombre']:
                    col_widths[col] = ANCHOS_COLUMNAS.get(col, ANCHOS_COLUMNAS.get('default_agrupacion', 30))
                else:
                    col_widths[col] = ANCHOS_COLUMNAS.get('default_metrica', 25)

            # 2. Dibujar la Cabecera (Header)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(200, 220, 255) # Azul suave para cabecera

            for col in columnas_a_dibujar:
                pdf.cell(
                    w=col_widths[col],
                    h=ALTO_FILA_MM,
                    txt=col.replace('_', ' ').title(),
                    border=1, 
                    ln=0,
                    align='C',
                    fill=True
                )
            pdf.ln(ALTO_FILA_MM) 

            # 3. Dibujar las Filas de Datos (CON LÓGICA DE SUBTOTALES)
            pdf.set_font('Arial', '', 7)
            
            for index, row in df_tabla.iterrows():
                
                # === LÓGICA DE COLOR Y ESTILO PARA SUBTOTALES ===
                # Comprueba si la primera columna no es nula y contiene 'Total' (incluye 'GRAN TOTAL')
                es_subtotal = 'Total' in str(row.get(columnas_a_dibujar[0], ''))
                
                if 'GRAN TOTAL' in str(row.get(columnas_a_dibujar[0], '')):
                    pdf.set_fill_color(170, 204, 255) 
                    fill_cell = True
                    pdf.set_font('Arial', 'B', 7)
                elif es_subtotal:
                    pdf.set_fill_color(224, 236, 255)
                    fill_cell = True
                    pdf.set_font('Arial', 'B', 7)
                else:
                    pdf.set_fill_color(255, 255, 255) 
                    fill_cell = False 
                    pdf.set_font('Arial', '', 7)
                
                
                for col in columnas_a_dibujar:
                    valor = str(row[col])
                    ancho = col_widths[col]
                    
                    # Lógica de truncamiento/recorte de texto (solo para columnas de texto largas)
                    if col in ['Cliente_Nombre', 'Vendedor_Nombre']:
                        # Comprobación de ancho y truncamiento con "..."
                        if pdf.get_string_width(valor) > ancho - 2: 
                            # Se trunca el texto de forma más eficiente
                            max_chars = int(len(valor) * ((ancho - 2) / pdf.get_string_width(valor)))
                            # Evitar el error al intentar truncar un string vacío
                            valor = valor[:max_chars] + "..." if max_chars > 0 else valor
                            
                    # Lógica de alineación
                    align = 'L'
                    # Alineación a la derecha para métricas y porcentajes
                    if ' % ' in col or '%_CREC' in col or 'Tot' in col or 'Monto' in col or 'Cant' in col or col in ['Venta_Neta', 'CANTIDAD']:
                        align = 'R'
                        # Asegurar que los NaN se vean limpios en métricas (se muestran como 'nan' por el str())
                        if valor.lower() in ['nan', 'none', '']:
                            valor = '-'

                    pdf.cell(
                        w=ancho,
                        h=ALTO_FILA_MM, 
                        txt=valor,
                        border=1, 
                        ln=0,
                        align=align,
                        fill=fill_cell
                    )
                
                pdf.ln(ALTO_FILA_MM) 

            pdf.ln(5) 

    # Contenido de Figuras
    if contenido_figuras:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "2. Gráficos y Tendencias", 0, 1, 'L')
        
        for i, figura in enumerate(contenido_figuras):
            try:
                # Añadir un salto de página si el gráfico no cabe
                if pdf.get_y() + 100 > 277 - 15: # 277 es el alto de A4, 15 es el margen del footer
                    pdf.add_page()
                
                img_bytes = pio.to_image(figura, format='png')
                # w=180 es un buen ancho para centrar en una página A4 (210mm)
                pdf.image(io.BytesIO(img_bytes), x=10, w=180) 
                pdf.ln(5)
            except Exception as e:
                # Log del error en la terminal para depuración
                print(f"Error al añadir gráfico al PDF (Índice {i}): {e}")
                
    # Retornar el PDF como bytes
    return bytes(pdf.output(dest='S'))