import plotly.express as px
import pandas as pd
# Asegúrate de que esta importación sea correcta (pip install fpdf2)
from fpdf import FPDF, HTMLMixin 
import io
import plotly.io as pio

# ----------------------------------------------------
# CLASE PDF PERSONALIZADA
# ----------------------------------------------------

class PDF(FPDF, HTMLMixin):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# ----------------------------------------------------
# CONSTANTES DE DIMENSIONES PARA EL PDF
# ----------------------------------------------------
# Dimensiones en mm (milímetros), que es la unidad por defecto de FPDF
ALTO_FILA_MM = 5  # 0.5 cm

# Anchos fijos de columnas en mm
ANCHOS_COLUMNAS = {
    'Cliente_Nombre': 50,  
    'Vendedor_Nombre': 40,
    'default_agrupacion': 30, 
    'default_metrica': 25,    
}


# ----------------------------------------------------
# FUNCIONES DE GRÁFICOS (Ahora aseguradas)
# ----------------------------------------------------

def crear_grafico_barras_comparativo(df_agrupado: pd.DataFrame, x_col: str, y_col: str, titulo: str):
    """Crea un gráfico de barras simple con Plotly."""
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
    fig = px.pie(
        df.nlargest(10, values_col), 
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
        labels={y_col: y_col.replace('_', ' ')}
    )
    fig.update_xaxes(title_text='Fecha')
    return fig

# ----------------------------------------------------
# FUNCIÓN DE GENERACIÓN DE PDF (Formato Manual)
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
                    col_widths[col] = ANCHOS_COLUMNAS['Cliente_Nombre']
                elif col in ['Vendedor_Nombre', 'Marca', 'Tipo_Producto', 'Cliente_ID', 'Vendedor_ID', 'TIPO_VENTA', 'TIPO1', 'TIPO2', 'TIPO3']:
                    # Usar el ancho de default_agrupacion o el específico si existe
                    col_widths[col] = ANCHOS_COLUMNAS.get(col, ANCHOS_COLUMNAS['default_agrupacion'])
                else:
                    # Usar el ancho de default_metrica para todas las demás (métricas)
                    col_widths[col] = ANCHOS_COLUMNAS['default_metrica']

            # 2. Dibujar la Cabecera (Header)
            pdf.set_font('Arial', 'B', 8)
            pdf.set_fill_color(200, 220, 255) 

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

            # 3. Dibujar las Filas de Datos
            pdf.set_font('Arial', '', 7)
            
            for index, row in df_tabla.iterrows():
                
                for col in columnas_a_dibujar:
                    valor = str(row[col])
                    ancho = col_widths[col]
                    
                    if col == 'Cliente_Nombre':
                        # Truncar el Nombre del Cliente
                        ancho_texto = pdf.get_string_width(valor)
                        
                        if ancho_texto > ancho - 2: 
                            while pdf.get_string_width(valor + "...") > ancho - 2 and len(valor) > 0:
                                valor = valor[:-1]
                            valor += "..."
                        
                        align = 'L'
                        
                    elif ' % ' in col or '%_CREC' in col:
                        align = 'C' 
                    elif 'Tot' in col or 'Monto' in col or 'Cant' in col:
                        align = 'R'
                    else:
                        align = 'L'

                    pdf.cell(
                        w=ancho,
                        h=ALTO_FILA_MM, 
                        txt=valor,
                        border=1, 
                        ln=0,
                        align=align
                    )
                pdf.ln(ALTO_FILA_MM) 

            pdf.ln(5) 

    # Contenido de Figuras
    if contenido_figuras:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "2. Gráficos y Tendencias", 0, 1, 'L')
        
        for i, figura in enumerate(contenido_figuras):
            try:
                img_bytes = pio.to_image(figura, format='png')
                pdf.image(io.BytesIO(img_bytes), x=10, w=180) 
                pdf.ln(5)
            except Exception as e:
                # Aquí podrías querer usar st.error(f"Error al añadir gráfico al PDF: {e}") 
                # si pudieras interactuar con Streamlit, pero en el backend usamos print.
                print(f"Error al añadir gráfico al PDF: {e}")
                
    # Retornar el PDF como bytes
    return bytes(pdf.output(dest='S'))