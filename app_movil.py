import flet as ft
import requests
import time
import threading

# URL de la base de datos (se cambia si abrimos otro proyecto en Firebase)
url_bd = "https://cansat-nmddl-default-rtdb.firebaseio.com/telemetria.json"

def main(page: ft.Page):
    # Setup basico de la app
    page.title = "App Rescate NMDLL"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = "auto"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Textos de la interfaz (declarados antes para que no pete el movil al actualizar)
    txt_estado = ft.Text("Iniciando sistemas...", color="yellow", size=14)
    
    t_tiempo = ft.Text("-- s", size=24, weight="bold", color="white")
    t_alt = ft.Text("-- m", size=24, weight="bold", color="blue")
    t_temp = ft.Text("-- C", size=24, weight="bold", color="orange")
    t_uv = ft.Text("--", size=24, weight="bold", color="purple")
    t_co2 = ft.Text("-- ppm", size=24, weight="bold", color="red")
    t_tvoc = ft.Text("-- ppb", size=24, weight="bold", color="green")
    
    txt_gps = ft.Text("GPS: Buscando satelites...", size=14, color="grey")
    coords = {"lat": 0.0, "lon": 0.0}

    # Funcion para abrir la app nativa de Maps en Android
    def abrir_mapa(e):
        lat = coords["lat"]
        lon = coords["lon"]
        # Filtro de seguridad: si es 0.0 nos manda a la costa de Africa
        if lat != 0.0 and lon != 0.0:
            link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            page.launch_url(link)

    # Boton de rescate (apagado por defecto hasta que haya cobertura)
    btn_mapa = ft.ElevatedButton(
        text="ABRIR MAPA DE RESCATE",
        icon="map", 
        color="white",
        bgcolor="blue",
        disabled=True,
        on_click=abrir_mapa,
        width=300,
        height=50
    )

    # Funcion para no repetir el codigo de las cajas grises 20 veces
    def caja_dato(titulo, valor):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [ft.Text(titulo, size=12, color="grey"), valor],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=15, width=150, height=90,
            ), elevation=5,
        )

    # DIBUJAMOS LA PANTALLA ANTES DE NADA
    page.add(
        ft.Text("CanSat IES Padre Manjon", size=24, weight="bold"),
        txt_estado,
        ft.Divider(height=20, color="grey"),
        
        # Caja principal del GPS
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Localizacion GPS", size=16, weight="bold"),
                    txt_gps,
                    btn_mapa
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20, width=320
            ), color="#1e1e1e"
        ),
        
        ft.Divider(height=20, color="grey"),
        
        # Rejilla de datos
        ft.Row([caja_dato("Tiempo", t_tiempo), caja_dato("Altitud", t_alt)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([caja_dato("Temperatura", t_temp), caja_dato("Indice UV", t_uv)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([caja_dato("CO2", t_co2), caja_dato("TVOC", t_tvoc)], alignment=ft.MainAxisAlignment.CENTER),
    )

    # VITAL: Forzamos al movil a renderizar la pantalla en negro antes de pedir internet
    page.update()

    # Hilo secundario para descargar datos sin congelar la app
    def bucle_descarga():
        # Parche: Le damos 2 segundos al movil para respirar y cargar la UI graficamente
        time.sleep(2)
        
        while True:
            try:
                res = requests.get(url_bd)
                if res.status_code == 200 and res.json() != None:
                    datos = res.json()
                    # Pillamos el ultimo paquete que haya entrado
                    ultimo_id = list(datos.keys())[-1]
                    paquete = datos[ultimo_id]

                    # Volcamos datos a la pantalla
                    t_tiempo.value = f"{int(paquete.get('Tiempo', 0))} s"
                    t_alt.value = f"{paquete.get('Altitud', 0)} m"
                    t_temp.value = f"{paquete.get('Temperatura', 0)} C"
                    t_uv.value = f"{paquete.get('UV', 0)}"
                    t_co2.value = f"{int(paquete.get('CO2', 0))} ppm"
                    t_tvoc.value = f"{int(paquete.get('TVOC', 0))} ppb"
                    
                    # Logica de activacion del mapa
                    lat = float(paquete.get('Latitud', 0.0))
                    lon = float(paquete.get('Longitud', 0.0))
                    
                    if lat != 0.0 and lon != 0.0:
                        coords["lat"] = lat
                        coords["lon"] = lon
                        txt_gps.value = f"Coords: {lat}, {lon}"
                        txt_gps.color = "white"
                        btn_mapa.disabled = False
                        btn_mapa.bgcolor = "green"
                    else:
                        txt_gps.value = "Esperando cobertura GPS..."
                    
                    txt_estado.value = "Recibiendo datos..."
                    txt_estado.color = "green"
                else:
                    txt_estado.value = "Base de datos vacia"
                    txt_estado.color = "orange"
                    
            except Exception as e:
                txt_estado.value = "Sin conexion a Internet"
                txt_estado.color = "red"
            
            # Refrescamos la pantalla con los nuevos valores
            page.update()
            # Esperamos 1 segundo para no quemar la cuota gratuita de Firebase
            time.sleep(1)

    # Arrancamos el hilo secundario
    hilo = threading.Thread(target=bucle_descarga, daemon=True)
    hilo.start()

ft.app(target=main)