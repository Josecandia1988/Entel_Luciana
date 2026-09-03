# Dashboard KPI Entel, socios y tiendas

Aplicación Streamlit construida para leer el archivo `Precierre` y mostrar sus indicadores en tres niveles:

- Entel: total del canal.
- Socio: consolidado de cada socio.
- Tienda: PDV informados individualmente bajo cada socio.

## Uso local

1. Instala Python 3.11 o superior.
2. Abre una terminal dentro de esta carpeta.
3. Ejecuta `pip install -r requirements.txt`.
4. Ejecuta `streamlit run app.py`.
5. Carga el Excel desde el panel lateral.

## Publicación

Sube `app.py` y `requirements.txt` a un repositorio de GitHub. En Streamlit Community Cloud crea una aplicación nueva, selecciona el repositorio y usa `app.py` como archivo principal.

No es necesario subir el Precierre a GitHub: el usuario puede cargarlo desde la aplicación. Si se incluye un archivo llamado exactamente `Precierre 310826.xlsx` junto a `app.py`, se usará como demostración hasta que el usuario cargue otro.

## Hojas utilizadas

`Movil`, `VOZ`, `RU`, `Fibra`, `Funnel`, `Solicitudes`, `Equipos`, `Seguros`, `Accesorios`, `Rechazo` y `Q Movil`.

Las hojas vacías o incompletas no detienen la aplicación. Cuando una métrica no está disponible en el nivel seleccionado se muestra como no disponible, sin sustituirla por un total de otro nivel.
