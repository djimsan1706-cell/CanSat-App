import flet as ft
import requests
import time
import threading

# --- CONFIGURACIÓN FIREBASE ---
FIREBASE_URL = "https://cansat-nmddl-default-rtdb.firebaseio.com/telemetria.json"

def main(page: ft.Page):
    # Configuración de la ventana
    page.title = "CanSat NMDLL"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = "auto"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Elementos de estado
    status_text = ft.Text("🟡 Conectando a la base de datos...", color="yellow", size=14)

    # Variables de texto en vivo
    txt_tiempo = ft.Text("-- s", size=26, weight="bold", color="white")
    txt_alt = ft.Text("-- m", size=26, weight="bold", color="blue")
    txt_temp = ft.Text("-- °C", size=26, weight="bold", color="orange")
    txt_uv = ft.Text("--", size=26, weight="bold", color="purple")
    txt_co2 = ft.Text("-- ppm", size=26, weight="bold", color="red")
    txt_tvoc = ft.Text("-- ppb", size=26, weight="bold", color="green")
    
    # Variables de recuperación GPS
    txt_gps = ft.Text("Ubicación: Buscando satélites...", size=14, color="grey")
    coordenadas_actuales = {"lat": 0.0, "lon": 0.0}

    # Función para lanzar Google Maps nativo
    def abrir_google_maps(e):
        if coordenadas_actuales["lat"] != 0.0:
            url_mapa = f"https://www.google.com/maps/search/?api=1&query={coordenadas_actuales['lat']},{coordenadas_actuales['lon']}"
            page.launch_url(url_mapa)

    # Botón de rescate (desactivado hasta tener señal GPS válida)
    btn_rescate = ft.ElevatedButton(
        text="📍 ABRIR MAPA DE RESCATE",
        icon="map",  # <-- CORRECCIÓN: Pasamos el icono como texto directo
        color="white",
        bgcolor="blue",
        disabled=True,
        on_click=abrir_google_maps,
        width=300,
        height=50
    )

    def crear_tarjeta(titulo, valor_texto):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [ft.Text(titulo, size=14, color="grey"), valor_texto],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=20, width=160, height=100,
            ), elevation=5,
        )

    # Maquetación de la pantalla (UI)
    page.add(
        ft.Text("🛰️ No Me Des La Lata - IES Padre Manjón", size=28, weight="bold"),
        status_text,
        ft.Divider(height=20, color="grey"),
        
        # Panel de Rescate GPS
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Mapa", size=16, weight="bold"),
                    txt_gps,
                    btn_rescate
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=20, width=330
            ), color="#1e1e1e"
        ),
        
        ft.Divider(height=20, color="grey"),
        ft.Row([crear_tarjeta("Tiempo", txt_tiempo), crear_tarjeta("Altitud", txt_alt)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([crear_tarjeta("Temperatura", txt_temp), crear_tarjeta("Índice UV", txt_uv)], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([crear_tarjeta("Dióxido Carbono", txt_co2), crear_tarjeta("TVOC", txt_tvoc)], alignment=ft.MainAxisAlignment.CENTER),
    )

    # Hilo secundario para leer Firebase
    def actualizar_datos():
        while True:
            try:
                respuesta = requests.get(FIREBASE_URL)
                if respuesta.status_code == 200 and respuesta.json() is not None:
                    datos = respuesta.json()
                    ultimo_id = list(datos.keys())[-1]
                    ultimo_dato = datos[ultimo_id]

                    # Actualizar telemetría
                    txt_tiempo.value = f"{int(ultimo_dato.get('Tiempo', 0))} s"
                    txt_alt.value = f"{ultimo_dato.get('Altitud', 0)} m"
                    txt_temp.value = f"{ultimo_dato.get('Temperatura', 0)} °C"
                    txt_uv.value = f"{ultimo_dato.get('UV', 0)}"
                    txt_co2.value = f"{int(ultimo_dato.get('CO2', 0))} ppm"
                    txt_tvoc.value = f"{int(ultimo_dato.get('TVOC', 0))} ppb"
                    
                    # Lógica del GPS
                    lat = float(ultimo_dato.get('Latitud', 0.0))
                    lon = float(ultimo_dato.get('Longitud', 0.0))
                    
                    if lat != 0.0 and lon != 0.0:
                        coordenadas_actuales["lat"] = lat
                        coordenadas_actuales["lon"] = lon
                        txt_gps.value = f"Ubicación: {lat}, {lon}"
                        txt_gps.color = "white"
                        btn_rescate.disabled = False
                        btn_rescate.bgcolor = "green"
                    else:
                        txt_gps.value = "Ubicación: Esperando cobertura GPS..."
                    
                    status_text.value = "🟢 Recibiendo telemetría en directo"
                    status_text.color = "green"
                else:
                    status_text.value = "🟠 Base de datos vacía..."
                    status_text.color = "orange"
                    
            except Exception as e:
                status_text.value = "🔴 Pérdida de conexión con la nube"
                status_text.color = "red"
            
            page.update()
            time.sleep(1)

    hilo_datos = threading.Thread(target=actualizar_datos, daemon=True)
    hilo_datos.start()

ft.app(target=main)