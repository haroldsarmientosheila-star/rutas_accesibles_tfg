# Sheila Harold Sarmiento - TFG Ingeniería de Sistemas de Telecomunicaciones, Sonido e Imagen 2026

import geopandas as gpd
import networkx as nx
import pyproj as pp
import shapely as sh
from shapely.ops import substring
from pathlib import Path

# carga y lectura .gpkg
BASE_DIR = Path(__file__).resolve().parent.parent

arucas_gpkg = BASE_DIR / "data" / "processed" / "red-peatonal-piloto.gpkg"

tramos_red = gpd.read_file(arucas_gpkg, layer="tramos_4083")


# transformación de coordenadas del mapa (EPSG:4326)
# al SRC de la red peatonal (EPSG:4083)

transformar_src = pp.Transformer.from_crs("EPSG:4326", "EPSG:4083", always_xy=True)

# transformación inversa para devolver la geometría a leaflet

in_transformar_src = pp.Transformer.from_crs("EPSG:4083", "EPSG:4326", always_xy=True)

# denominación nodo inicio y nodo final de cada tramo


def generar_nodos(tramos_red):

    tramos_red = tramos_red.copy()  # copia por si acaso
    nodos = {}

    def anyadir_nodo(coordenada):
        if coordenada not in nodos:
            nodos[coordenada] = f"N_{len(nodos)+1:03d}"

        return nodos[coordenada]

    nodo_a = []
    nodo_b = []

    for t in tramos_red.geometry:
        nodo_a.append(anyadir_nodo(tuple(t.coords[0])))
        nodo_b.append(anyadir_nodo(tuple(t.coords[-1])))

    tramos_red["nodo_a"] = nodo_a
    tramos_red["nodo_b"] = nodo_b

    return tramos_red, nodos


# construcción grafo general


def generar_grafo(tramos_red):

    g = nx.DiGraph()

    for _, t in tramos_red.iterrows():

        nodo_a = t["nodo_a"]
        nodo_b = t["nodo_b"]  # sacamos nodo_b de la fila en concreto

        # A->B
        g.add_edge(nodo_a, nodo_b, tramo_id=t["tramo_id"], longitud_m=t["longitud_m"])
        # B->A
        g.add_edge(nodo_b, nodo_a, tramo_id=t["tramo_id"], longitud_m=t["longitud_m"])

    return g


################################### IMPLEMENTACIÓN FUNCIÓN DE COSTES -> CÁLCULO DE RUTAS ACCESIBLE #############################################


# VALORES EXCLUYENTES
ANCHO_MIN = 85
ESTADO_PAV = "muy_deficiente"
ESCALONES = True

PENDIENTE_SUBIDA_MAX = 20
PENDIENTE_BAJADA_MAX = 18

# FACTORES
FACTOR_ESTADO_SUPERFICIE = {
    "bueno": 0,
    "aceptable": 0.2,
    "regular": 0.5,
    "deficiente": 1,
}

FACTOR_TIPO_USO_VIA = {
    "peatonal": 0,
    "via_separada": 0.2,
    "via_compartida": 1,
}


def FACTOR_ANCHO(ancho_cm):

    if ancho_cm > 150:
        return 0
    if ancho_cm > 120:
        return 0.3
    elif ancho_cm > 90:
        return 0.6
    else:  # 85-90 cm
        return 1


def FACTOR_PENDIENTE(pendiente_pct, sube_baja):

    if sube_baja == "sube":

        if pendiente_pct < 4:
            return 0
        if pendiente_pct < 8:
            return 0.15
        if pendiente_pct < 11:
            return 0.3
        if pendiente_pct < 15:
            return 0.5
        if pendiente_pct < 17:
            return 0.7
        else:  # 17-20%
            return 1

    else:  # sube_baja=="baja"

        if pendiente_pct < 4:
            return 0
        if pendiente_pct < 8:
            return 0.2
        if pendiente_pct < 11:
            return 0.5
        if pendiente_pct < 15:
            return 0.7
        else:  # 15-18%
            return 1


# PESOS

LAMBDA = 2  # para priorizar los criterios de accesibilidad frente a la longitud

Wpdt = 0.4
Wsup = 0.3
Wancho = 0.2
Wuso = 0.1


# FUNCION EXCLUYENTE
def sentido_pdt(fila, sentido):
    # determinar si en ese sentido se sube o se baja
    if fila["cota_a_m"] > fila["cota_b_m"]:  # sentido subida y bajada
        if sentido == "ab":
            return "baja"
        else:
            return "sube"
    else:  # b>a
        if sentido == "ab":
            return "sube"
        else:  # sentido == "ba"
            return "baja"


def es_excluyente(fila, sentido):

    # EXCLUSIONES GENERALES

    if fila["escalones"] == ESCALONES:
        return True

    if fila["ancho_cm"] < ANCHO_MIN:
        return True
    if fila["estado_superficie"] == ESTADO_PAV:
        return True

    # EXCLUSIONES SEGÚN SENTIDO
    sube_baja = sentido_pdt(fila, sentido)

    if sube_baja == "sube" and fila["pendiente_pct"] > PENDIENTE_SUBIDA_MAX:
        return True

    if sube_baja == "baja" and fila["pendiente_pct"] > PENDIENTE_BAJADA_MAX:
        return True

    return False


# FUNCIÓN DE COSTES


def calcular_coste(fila, sentido):  # sentido tiene que ser "ab" o "ba"

    sube_baja = sentido_pdt(fila, sentido)

    estado_superficie = FACTOR_ESTADO_SUPERFICIE[fila["estado_superficie"]]

    tipo_uso_via = FACTOR_TIPO_USO_VIA[fila["tipo_uso_via"]]

    ancho_cm = FACTOR_ANCHO(fila["ancho_cm"])

    pendiente_pct = FACTOR_PENDIENTE(fila["pendiente_pct"], sube_baja)

    S = (
        Wsup * estado_superficie
        + Wancho * ancho_cm
        + Wpdt * pendiente_pct
        + Wuso * tipo_uso_via
    )  # penalización de accesibilidad

    coste = fila["longitud_m"] * (1 + LAMBDA * S)
    return coste


# GRAFO ACCESIBLE


def generar_grafo_accesible(tramos_red):
    g_accesible = nx.DiGraph()

    for _, t in tramos_red.iterrows():

        nodo_a = t["nodo_a"]
        nodo_b = t["nodo_b"]

        # A->B
        if not es_excluyente(t, "ab"):
            coste = calcular_coste(t, "ab")
            g_accesible.add_edge(
                nodo_a,
                nodo_b,
                tramo_id=t["tramo_id"],
                longitud_m=t["longitud_m"],
                pendiente_pct=t["pendiente_pct"],
                sube_baja=sentido_pdt(t, "ab"),
                ancho_cm=t["ancho_cm"],
                estado_superficie=t["estado_superficie"],
                tipo_tramo=t["tipo_tramo"],
                tipo_uso_via=t["tipo_uso_via"],
                coste=coste,
            )

        # B->A
        if not es_excluyente(t, "ba"):
            coste = calcular_coste(t, "ba")
            g_accesible.add_edge(
                nodo_b,
                nodo_a,
                tramo_id=t["tramo_id"],
                longitud_m=t["longitud_m"],
                pendiente_pct=t["pendiente_pct"],
                sube_baja=sentido_pdt(t, "ba"),
                ancho_cm=t["ancho_cm"],
                estado_superficie=t["estado_superficie"],
                tipo_tramo=t["tipo_tramo"],
                tipo_uso_via=t["tipo_uso_via"],
                coste=coste,
            )
    return g_accesible


# CÁLCULO DE RUTAS

# !!! Recordar que "peso" hace referencia a la característica a la que
# se le da importancia a la hora de calcular la ruta.
# En este caso, variará entre "longitud_m" y el coste obtenido con calcular_coste().


def calcular_ruta(
    grafo, origen, destino, peso
):  # misma función para ruta_corta y ruta_accesible (dependiente del grafo y peso introducido)

    try:

        ruta_nodos = nx.shortest_path(grafo, source=origen, target=destino, weight=peso)

        ruta_tramos = []
        distancia_total = 0

        coste_total = nx.shortest_path_length(
            grafo, source=origen, target=destino, weight=peso
        )

        for i in range(len(ruta_nodos) - 1):  # obtener la ruta en tramos

            nodo_actual = ruta_nodos[i]
            nodo_siguiente = ruta_nodos[i + 1]

            datos = grafo.get_edge_data(nodo_actual, nodo_siguiente)

            ruta_tramos.append(datos["tramo_id"])

            distancia_total += datos[
                "longitud_m"
            ]  # vamos sumando las distancias de cada tramo

        return {
            "nodos": ruta_nodos,
            "tramos": ruta_tramos,
            "distancia_m": distancia_total,
            "coste": coste_total,
        }

    except nx.NetworkXNoPath:
        return None

    except nx.NodeNotFound:
        return None


# Asociar coordenadas usuario con nodo


def punto_mas_cercano(tramos_red, latitud, longitud):

    # Invertimos latitud y longitud porque always_xy=true
    x, y = transformar_src.transform(longitud, latitud)

    # coordenadas clic usuario a punto geométrico
    punto = sh.Point(x, y)

    # calculamos la distancia del punto a todos los tramos y seleccionamos el más cercano
    distancias = tramos_red.geometry.distance(punto)

    indice_tramo = distancias.idxmin()

    tramo = tramos_red.loc[
        indice_tramo
    ]  # tramo_prox antes ///// variable con todos los atributos de dicho tramo

    # geometría de tramo
    linea = tramo.geometry

    # distancia recorrida desde el inicio de la línea (coords[0]) hasta el punto proyectado sobre la misma
    posicion = linea.project(punto)

    # verificar que el punto introducido no coincide con uno de los dos nodos del tramo

    tolerancia = 0.1  # metros

    if (
        posicion <= tolerancia
    ):  # si la posición es menor que la tolerancia quiere decir que está a menos 0.1 m de distancia del punto incial, por lo que en vez de crear un nuevo nodo le asignamos el que ya existe
        punto_usuario = sh.Point(linea.coords[0])
        extremo = "a"
    elif (
        linea.length - posicion <= tolerancia
    ):  # idem, pero esta vez con la distancia al punto final
        punto_usuario = sh.Point(linea.coords[-1])
        extremo = "b"
    else:
        punto_usuario = linea.interpolate(
            posicion
        )  # coordenadas del punto sobre el tramo más cercano
        extremo = None

    return {
        "indice": indice_tramo,
        "tramo": tramo,
        "punto": punto_usuario,
        "posicion": posicion,
        "extremo": extremo,
    }


def insertar_punto_usuario(tramos_red, latitud, longitud, etiqueta):

    tramos_temp = tramos_red.copy()  # copia por si acaso

    nuevo_punto = punto_mas_cercano(tramos_temp, latitud, longitud)

    if nuevo_punto["extremo"] is not None:
        return tramos_temp, nuevo_punto

    indice = nuevo_punto["indice"]
    tramo_original = nuevo_punto["tramo"]
    punto_usuario = nuevo_punto["punto"]
    posicion = nuevo_punto["posicion"]

    # leer segmento donde está el punto con todos sus atributos originaless
    linea_punto = tramo_original.geometry

    geometria1 = substring(linea_punto, 0, posicion)  # de A -> Nuevo punto
    geometria2 = substring(
        linea_punto, posicion, linea_punto.length
    )  # de B -> Nuevo punto

    tramo_1 = tramo_original.copy()  # Nuevo tramo de A -> Nuevo punto
    tramo_2 = tramo_original.copy()  # Nuevo tramo de nuevo punto -> B

    #!!!!! cambia la geometry y longitud_m + calcular cota para P -> cambiar cotas nuevos tramos -> recalcular pendiente (mayor coherencia)

    tramo_1["geometry"] = geometria1
    tramo_2["geometry"] = geometria2

    tramo_1["longitud_m"] = geometria1.length
    tramo_2["longitud_m"] = geometria2.length

    proporcion = posicion / linea_punto.length

    cota_punto = tramo_original["cota_a_m"] + proporcion * (
        tramo_original["cota_b_m"] - tramo_original["cota_a_m"]
    )  # por facilitar el procedimiento se estima la cota en ese punto suponiendo que la pendiente
    # entre los nodos originales cambia de forma uniforme

    # reasignación de cotas
    tramo_1["cota_a_m"] = tramo_original["cota_a_m"]
    tramo_1["cota_b_m"] = cota_punto

    tramo_2["cota_a_m"] = cota_punto
    tramo_2["cota_b_m"] = tramo_original["cota_b_m"]

    # cálculo pendientes
    tramo_1["pendiente_pct"] = (
        abs(tramo_1["cota_b_m"] - tramo_1["cota_a_m"]) / tramo_1["longitud_m"] * 100
    )

    tramo_2["pendiente_pct"] = (
        abs(tramo_2["cota_b_m"] - tramo_2["cota_a_m"]) / tramo_2["longitud_m"] * 100
    )

    # etiquetammos tramos temporales
    tramo_1["tramo_id"] = str(tramo_original["tramo_id"]) + "_" + etiqueta + "_1"

    tramo_2["tramo_id"] = str(tramo_original["tramo_id"]) + "_" + etiqueta + "_2"

    # eliminamos tramo original de tramos_temp

    tramos_temp = tramos_temp.drop(index=indice).reset_index(drop=True)

    # añadimos los dos nuevos tramos temporales

    tramos_temp.loc[len(tramos_temp)] = tramo_1
    tramos_temp.loc[len(tramos_temp)] = tramo_2

    return tramos_temp, nuevo_punto


def obtener_geometria_ruta(ruta, tramos_temp):

    if ruta is None:
        return None

    coordenadas_ruta = []

    for i in range(len(ruta["tramos"])):

        tramo_id = ruta["tramos"][i]  # tramo id [i] de la ruta resultante

        nodo_actual = ruta["nodos"][i]
        nodo_siguiente = ruta["nodos"][i + 1]

        # Buscar el tramo

        tramo = tramos_temp[tramos_temp["tramo_id"] == tramo_id].iloc[0]

        coordenadas = list(tramo.geometry.coords)

        # comprobar sentido recorrido

        if nodo_actual == tramo["nodo_b"] and nodo_siguiente == tramo["nodo_a"]:
            coordenadas.reverse()

        if i > 0:
            coordenadas = coordenadas[
                1:
            ]  # borramos la primera coordenada de todos los tramos excepto el primero para no tenerlas repetidas

        # EPSG:4083 -> EPSG:4326

        for x, y in coordenadas:
            longitud, latitud = in_transformar_src.transform(x, y)

            coordenadas_ruta.append(
                [latitud, longitud]
            )  # devolvemos al revés porque es lo que espera leaflet

    return coordenadas_ruta


########## BIG CHORIZO ##############


def calcular_rutas_usuario(
    latitud_origen, longitud_origen, latitud_destino, longitud_destino
):

    # copia temporal de la red original

    tramos_temp = tramos_red.copy()

    # insertar origen

    tramos_temp, punto_origen = insertar_punto_usuario(
        tramos_temp, latitud_origen, longitud_origen, "O"
    )

    # Insertar destino sobre tramos_temp ya modificado

    tramos_temp, punto_destino = insertar_punto_usuario(
        tramos_temp, latitud_destino, longitud_destino, "D"
    )

    # Generar nodos

    tramos_temp, nodos_temp = generar_nodos(tramos_temp)

    # ID nuevos nodos

    origen = nodos_temp[tuple(punto_origen["punto"].coords[0])]

    destino = nodos_temp[tuple(punto_destino["punto"].coords[0])]

    # Generación de grafos

    g_temp = generar_grafo(tramos_temp)

    g_accesible_temp = generar_grafo_accesible(tramos_temp)

    # CÁLCULO DE RUTAS

    ruta_corta = calcular_ruta(g_temp, origen, destino, "longitud_m")
    ruta_accesible = calcular_ruta(g_accesible_temp, origen, destino, "coste")

    # GEOMETRÍAS TRANSFORMADAS

    if ruta_corta is not None:
        ruta_corta["geometria"] = obtener_geometria_ruta(ruta_corta, tramos_temp)

    if ruta_accesible is not None:
        ruta_accesible["geometria"] = obtener_geometria_ruta(
            ruta_accesible, tramos_temp
        )

    return ruta_corta, ruta_accesible


#######VERIFICACIÓN

"""ruta_corta, ruta_accesible, tramos_temp = calcular_rutas_usuario(
    28.11788454,
    -15.52312209,
    28.11899787,
    -15.52247281
)

print("\nRUTA CORTA:")
print(ruta_corta)

print("\nRUTA ACCESIBLE:")
print(ruta_accesible)"""

"""ruta_corta, ruta_accesible = calcular_rutas_usuario(
    28.11788454,
    -15.52312209,
    28.11899787,
    -15.52247281
)

print("\nRUTA CORTA:")
print(ruta_corta)

print("\nGEOMETRÍA CORTA:")
print(ruta_corta["geometria"] if ruta_corta else None)

print("\nRUTA ACCESIBLE:")
print(ruta_accesible)"""
