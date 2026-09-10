# rutas_accesibles_tfg

# Rutas accesibles · Arucas

Prototipo de aplicación web progresiva (PWA) desarrollado como parte del Trabajo de Fin de Grado en Ingeniería de Sistemas de Telecomunicación, Sonido e Imagen, elaborado por Sheila Harold Sarmiento

La aplicación permite calcular y comparar dos recorridos peatonales dentro de la zona digitalizada de Arucas:

- **Ruta más corta**, calculada únicamente a partir de la distancia.
- **Ruta accesible**, calculada mediante una función de coste que tiene en cuenta diferentes características de accesibilidad de la red peatonal.

El sistema utiliza una red geoespacial propia obtenida a partir de datos de campo y procesada mediante GeoPandas, NetworkX, Shapely y pyproj. La interfaz web se ha desarrollado con Flask y Leaflet.

---

## Acceso a la aplicación

La aplicación se encuentra desplegada mediante Render y puede utilizarse directamente desde el navegador:

**https://rutas-accesibles-tfg.onrender.com**

Al utilizar el plan gratuito de Render, el servidor puede entrar en reposo después de un periodo de inactividad. En ese caso, la primera carga puede tardar unos segundos adicionales.

---

## Instalación como PWA

### Android

1. Abrir la aplicación en Google Chrome.
2. Pulsar el menú de tres puntos `⋮`.
3. Seleccionar **Instalar aplicación** o **Añadir a pantalla de inicio**.
4. Confirmar la instalación.

La aplicación aparecerá en el dispositivo con su propio icono y podrá abrirse en modo independiente del navegador.

### iOS

1. Abrir la aplicación mediante Safari.
2. Pulsar **Compartir**.
3. Seleccionar **Añadir a pantalla de inicio**.
4. Confirmar.

> La aplicación requiere conexión a Internet para realizar el cálculo de rutas, ya que el procesamiento se ejecuta en el servidor Flask.

---

## Uso

1. Abrir el mapa.
2. Seleccionar el punto de origen.
3. Seleccionar el punto de destino.
4. La aplicación calcula automáticamente:
   - la ruta más corta;
   - la ruta accesible.
5. Ambas rutas se representan sobre el mapa junto con su distancia.
6. El botón **Nueva ruta** permite reiniciar la selección.

Para facilitar la comprobación del funcionamiento del prototipo y la verificación de las rutas calculadas, se recomienda realizar las pruebas en el entorno de la **plaza de San Juan**, dentro de la zona digitalizada.

---

## Ejecución en local

### Requisitos

Se recomienda utilizar Python 3 y disponer de `pip`.

Clonar el repositorio:

```bash
git clone https://github.com/haroldsarmientosheila-star/rutas_accesibles_tfg.git
