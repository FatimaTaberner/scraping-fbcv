from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import time
import requests
import json
import re

# Abrir Firefox en www.fbcv.es
driver = webdriver.Firefox()
driver.get('https://www.fbcv.es/competiciones/calendario-resultados-y-clasificacion?temporada=2024')

### Para quitar las cookies hay que hacerlo en dos pasos por que hay un elemento "shadow". Primero hay que buscar el cuadro de diálogo y luego el elemento dentro del cuadro.

# div que contiene el cuadro de diálogo y el elemento "shadow"
container = WebDriverWait(driver, 15).until(
    EC.presence_of_element_located((By.CLASS_NAME, "cmp-root-container")))
shadow = container.shadow_root
# buscamos el botón dentro del shadow y hacemos click (aceptar cookies)
button = shadow.find_element(By.CLASS_NAME, 'cmp-button-accept-all')
button.click()
# Desplegar para buscar por nombre.
desplegar = driver.find_element(By.CLASS_NAME, 'mostrar_filtros')
desplegar.click()


### RUTA DE ACCESO A LA FASE DESEADA ###

### Introducir el NOMBRE DE LA ENTIDAD para buscar el equipo.
entidad = input("Introduce el nombre o localidad a buscar: ").upper() # pedimos el nombre al usuario
cuadro_busqueda = driver.find_element(By.NAME, 'filtro1')
cuadro_busqueda.send_keys(entidad) # introducimos el nombre en el cuadro
lupa = driver.find_element(By.CSS_SELECTOR, 'div.buscar-item.activado')
lupa.click()

### Entrar en el CLUB DESEADO.
# Esperar a que desaparezca el fondo de carga tras la búsqueda
WebDriverWait(driver, 10).until(
    EC.invisibility_of_element_located((By.CLASS_NAME, 'fondo-opaco')))
# Esperar a que aparezcan todas las entidades visibles
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, 'nombre-club')))
# Recoger todos los elementos que contienen esa palabra en su texto
clubs = driver.find_elements(By.CLASS_NAME, 'nombre-club')
# Si no se encuentra NINGUNO
if not clubs:
    print(f"\nNo se encontraron entidades que contengan: {entidad}")
    driver.quit()
    exit()
# Si solo hay UNO, lo seleccionamos directamente
if len(clubs) == 1:
    club = clubs[0]
    club.click()
# Si hay VARIOS, mostramos la lista y pedimos que elija
else:
    print("\nSe encontraron varias entidades:")
    for i, club in enumerate(clubs, start=1):
        # Encuentra el span dentro del div
        span = club.find_element(By.TAG_NAME, "span")
        # Resta el texto del span del texto total del div
        nombre = club.text.replace(span.text, '').strip()
        print(f"{i}. {nombre}")
    # Pedir al usuario que elija una opción válida
    while True:
        try:
            seleccion = int(input("\nEscribe el número de la entidad que deseas seleccionar: "))
            if 1 <= seleccion <= len(clubs):
                break
            else:
                print("Número fuera de rango.")
        except ValueError:
            print("Por favor, introduce un número válido.")

    club = clubs[seleccion - 1]
    driver.execute_script("arguments[0].scrollIntoView();", club)
    club.click()

### Desplegar todas las COMPETICIONES
driver.implicitly_wait(2)
for competicion in driver.find_elements(By.CLASS_NAME, 'nombre-competicion'): # Localiza todos los elementos 'competición'
    if competicion.is_displayed(): # Si la competición es visible la despliega
        driver.execute_script("arguments[0].scrollIntoView(true);", competicion)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", competicion)

### Entrar en la CATEGORÍA o EQUIPO deseado
# Recoger todos los elementos de 'categoría'
categorias = driver.find_elements(By.CLASS_NAME, 'categoria')
# Filtra por aquellos que realmente están visibles
cat_visibles = [cat for cat in categorias if cat.is_displayed()]
# Mostrar listadas y numeradas solo las descripciones del <span>
print(f"\nSe han encontrado {len(cat_visibles)} posibles equipos:")
for i, cat in enumerate(cat_visibles, start=1):
    categoria = cat.find_element(By.TAG_NAME, 'span').text.strip()
    equipo = cat.get_attribute('textContent').replace(categoria, '').strip()
    print(f"{i}. {equipo.ljust(35)}\t{categoria}")

# Pedir al usuario que elija (validando input)
while True:
    try:
        seleccion = int(input("\nSelecciona el número del equipo deseado: "))
        if 1 <= seleccion <= len(cat_visibles):
            break
        else:
            print("Número fuera de rango. Intenta de nuevo.")
    except ValueError:
        print("Entrada no válida. Introduce un número.")
# Hacer clic en la categoría elegida
cat_elegida = cat_visibles[seleccion - 1]
driver.execute_script("arguments[0].scrollIntoView(true);", cat_elegida)
# Guardar el nombre del equipo y su categoria
categoria = cat_elegida.find_element(By.TAG_NAME, 'span').text.strip()
equipo = cat_elegida.get_attribute('textContent').replace(categoria, '').strip()
time.sleep(0.2)  # opcional
# clic forzado por JS (salta el problema del overlay)
driver.execute_script("arguments[0].click();", cat_elegida)

### Elegir la LIGA o  FASE deseada (en caso de que hayan más de 1)
# Recoger todas las fases visibles
fases = driver.find_elements(By.CLASS_NAME, 'fase')
fases_visibles = [f for f in fases if f.is_displayed()]
# Validación por si no se encuentra ninguna
if not fases_visibles:
    print("No se encontraron fases visibles.")
    driver.quit()
    exit()
# Si solo hay una, clicarla directamente
if len(fases_visibles) == 1:
    fase_elegida = fases_visibles[0]
    print(f"\nÚnica fase encontrada: {fase_elegida.text.strip()}")
else:
    # Mostrar lista numerada
    print(f"\nSe han encontrado {len(fases_visibles)} fases disponibles:")
    for i, fase in enumerate(fases_visibles, start=1):
        print(f"{i}. {fase.text.strip()}")
    # Pedir al usuario una selección válida
    while True:
        try:
            seleccion = int(input("\nSelecciona el número de la fase deseada: "))
            if 1 <= seleccion <= len(fases_visibles):
                break
            else:
                print("Número fuera de rango.")
        except ValueError:
            print("Introduce un número válido.")
    fase_elegida = fases_visibles[seleccion - 1]
# Scroll y clic forzado
driver.execute_script("arguments[0].scrollIntoView(true);", fase_elegida)
time.sleep(0.2)
driver.execute_script("arguments[0].click();", fase_elegida)
# Obtener el data-grupo (útil para después)
time.sleep(0.2)
grupo_id = fase_elegida.get_attribute("data-grupo")
print(f"\nFase seleccionada.")


### OBTENCIÓN DE LA INFORMACIÓN (equipos, calendario y lugar de juego) ###

# Obtención de EQUIPOS
equipos_btn = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.item.equipos"))) # boton
driver.execute_script("arguments[0].scrollIntoView(true);", equipos_btn) # scroll
equipos_btn.click() # clica el botón
# Espera hasta que estén cargados los elementos con clase 'nombre_equipo'
equipos_elements = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "nombre_equipo")))
# Extrae el texto de cada elemento
nombres_equipos = [el.text for el in equipos_elements]
# Imprime los nombres
print('\nListado de equipos:')
for i, nombre in enumerate(nombres_equipos, start=1):
    print(f"{i}. {nombre}")

# Descarga el CALENDARIO de competición
calendario_btn = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "div.item.calendario"))) # boton
driver.execute_script("arguments[0].scrollIntoView(true);", calendario_btn) # scroll
calendario_btn.click()

# Asegúrate de que los partidos están cargados (usa .wrap-partido o lo que identifique el contenido)
WebDriverWait(driver, 15).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "wrap-partido")))
# Clic en botón 'Versión para Imprimir'
btn_print = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "btnPrint")))
btn_print.click()

# Cambiar a la nueva ventana
WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
driver.switch_to.window(driver.window_handles[-1])
# Espera a que cargue el contenido en la nueva pestaña
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "wrap-partido")))

# html del calendario completo
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
partidos = soup.select("div.wrap-partido")
print(f"Se han encontrado {len(partidos)} partidos en el calendario.")

datos = []

for partido in partidos:
    jornada_div = partido.find_previous("div", class_="cabecera_jornada")
    jornada = jornada_div.text.strip().replace("Jornada", "").split("(")[0].strip()

    equipos = partido.select("div.grid-partidos .item.equipo")
    if len(equipos) != 2:
        continue
    local = equipos[0].text.strip()
    visitante = equipos[1].text.strip()

    if equipo not in [local, visitante]: # 'equipo': definida por el usuario, linea 121 aprox.
        continue  # Filtramos partidos que no nos interesan

    fecha_hora = partido.select_one("div.grid_footer .item").text.strip()
    lugar = partido.select("div.grid_footer .item")[-1].text.strip()

    # Separar fecha y hora
    if " " in fecha_hora:
        fecha, hora = fecha_hora.split(" ")
    else:
        fecha, hora = fecha_hora, ""

    datos.append([int(jornada), local, visitante, fecha, hora, lugar])

# Crear DataFrame
df = pd.DataFrame(datos, columns=["JORNADA", "EQ. LOCAL", "EQ. VISITANTE", "FECHA", "HORA", "LUGAR"])

# Calcular el día de la semana en español a partir de la columna FECHA
dias_esp = {
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": "Sábado",
    "Sunday": "Domingo"}

# Añadir columna 'DIA'
df["DIA"] = df["FECHA"].apply(lambda x: dias_esp.get(datetime.strptime(x, "%d/%m/%Y").strftime("%A"), ""))

# Reordenar columnas si lo deseas (por ejemplo, poner DIA justo después de FECHA)
df = df[["JORNADA", "EQ. LOCAL", "EQ. VISITANTE", "FECHA", "DIA", "HORA", "LUGAR"]]

### BUSCAR LOS LINKS A MAPS EN INCLUIRLOS EN EL DATA FRAME ###

API_KEY = "AIzaSyAhf8CMyYnH1GKTyZ_zQAk4NByTXPg7e00"
base_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"

def obtener_enlace_google_maps_todos(nombre_lugar):
    params = {
        "input": nombre_lugar + ", Valencia, España",  # contexto geográfico
        "inputtype": "textquery",
        "fields": "place_id",
        "key": API_KEY
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if data.get("status") == "OK":
        place_id = data["candidates"][0]["place_id"]
        return f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    else:
        return "NO_ENCONTRADO"

def obtener_enlace_google_maps_visitante(row):
    if row["EQ. VISITANTE"] == equipo:
        return obtener_enlace_google_maps_todos(row["LUGAR"])
    else:
        return ""

df["MAPS LINK"] = df.apply(obtener_enlace_google_maps_visitante, axis=1)


## Exportar DataFrame
# Limpiar nombre del equipo para que sea válido como nombre de archivo
equipo = re.sub(r'[^\w\-]', '_', equipo.strip())  # Reemplaza todo lo que no sea alfanumérico o guion bajo

nombre_excel = f"calendario_partidos_{equipo}.xlsx"

with pd.ExcelWriter(nombre_excel, engine="xlsxwriter") as writer:
    workbook = writer.book
    worksheet_name = "Calendario"

    # Escribe el DataFrame a partir de la fila 2 (índice 1) para dejar espacio arriba
    df.to_excel(writer, index=False, sheet_name=worksheet_name, startrow=1)

    # Agrega la categoría manualmente en la primera celda (fila 0, columna 0)
    worksheet = writer.sheets[worksheet_name]
    bold_centered = workbook.add_format({'bold': True, 'align': 'center'})
    worksheet.merge_range(0, 0, 0, len(df.columns) - 1, categoria, bold_centered)

print(f'\nCalendario exportado de forma correcta ({len(df)} partidos) como {nombre_excel}.')







