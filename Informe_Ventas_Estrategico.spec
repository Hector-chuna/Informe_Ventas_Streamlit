# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import sys

# --- CONFIGURACIÓN DE RUTAS Y HOOKS ---

# 1. Fuerza la recolección de todos los archivos y hooks ocultos de Streamlit.
#    Esto resuelve el error ModuleNotFoundError: No module named 'streamlit'.
try:
    datas, binaries, hiddenimports = collect_all('streamlit')
except Exception as e:
    # Si la recolección automática falla, usamos la lista manual como respaldo
    print(f"Advertencia: collect_all('streamlit') falló: {e}")
    datas = []
    binaries = []
    hiddenimports = ['streamlit', 'pkg_resources.py2_warn', 'pandas._libs.tslibs.timedeltas']

# 2. Define la ruta a la metadata de Streamlit.
#    Esto es CRUCIAL para resolver el error PackageNotFoundError.
#    Debe coincidir con la carpeta 'streamlit-X.Y.Z.dist-info' dentro de tu venv/Lib/site-packages.
STREAMLIT_METADATA_FOLDER = 'streamlit-1.50.0.dist-info'
STREAMLIT_METADATA_PATH = f'venv/Lib/site-packages/{STREAMLIT_METADATA_FOLDER}'


# 3. Agrega todos los archivos y carpetas necesarios al paquete final:
datas += [
    ('ventas_historicas.xlsx', '.'), # El archivo Excel de datos en la raíz del paquete
    ('src', 'src'),                 # La carpeta de módulos 'src'
    # La inclusión de metadatos forzada para resolver el PackageNotFoundError
    (STREAMLIT_METADATA_PATH, STREAMLIT_METADATA_FOLDER) 
]

# ----------------------------------------

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Informe_Ventas_Estrategico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Mantener la consola para ver el puerto de Streamlit
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)