//Sheila Harold Sarmiento - TFG Ingeniería de Sistemas de Telecomunicaciones, Sonido e Imagen 2026

//declaramos y asignamos mapa
const mapa = L.map("mapa").setView([28.118, -15.523], 18);

L.tileLayer(
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution: "© OpenStreetMap"
    }
).addTo(mapa);

let origen = null;
let destino = null;

let marcadororigen = null;
let marcadordestino = null;

let lineacorta = null;
let lineaaccesible = null;

mapa.on("click", function (e) { //cuando sucede el evento click se ejecuta function(e), e son los datos del evento, es decir, el click (coordenadas)
    if (origen === null) {
        origen = e.latlng; //coordenadas del punto pulsado

        marcadororigen = L.marker([origen.lat, origen.lng]).addTo(mapa);

        console.log("Origen: ", origen);
    } else if (destino === null) {

        destino = e.latlng;

        marcadordestino = L.marker([destino.lat, destino.lng]).addTo(mapa);

        console.log("Destino: ", destino);


        fetch("/calcular-ruta", { //peticion al servidor
            method: "POST",

            headers: {
                "Content-Type": "application/json" //aviso a flask
            },

            body: JSON.stringify({ //convierte objeto javascript en json
                lat_origen: origen.lat,
                lon_origen: origen.lng,
                lat_destino: destino.lat,
                lon_destino: destino.lng
            })
        })
            .then(respuesta => respuesta.json()) //espera la respuesta y pasa los datos de json a javascript
            //interpretamos los datos recibidos
            .then(datos => {
                console.log("Resultado recibido:", datos);

                //DIBUJO RUTA MÁS CORTA
                if (datos.ruta_corta !== null) {
                    lineacorta = L.polyline(
                        datos.ruta_corta.geometria,
                        { color: "RED", weight: 2, offset: 2 }
                    ).addTo(mapa);
                }
                //DIBUJO RUTA ACCESIBLE
                if (datos.ruta_accesible !== null) {
                    lineaaccesible = L.polyline(
                        datos.ruta_accesible.geometria,
                        { color: "green", weight: 2, offset: 0}
                    ).addTo(mapa);
                }

                //centramos el visor en función de la ruta, prioridad a la accesible
                if (lineaaccesible !== null) {
                    mapa.fitBounds(lineaaccesible.getBounds());
                } else if (lineacorta !== null) {
                    mapa.fitBounds(lineacorta.getBounds());
                }

                //escribimos los resultados
                const resultados = document.getElementById("resultados");

                let texto = "";

                if (datos.ruta_corta !== null) {
                    texto += "Ruta más corta: " + datos.ruta_corta.distancia_m.toFixed(2) + " m<br>";
                }

                if (datos.ruta_accesible !== null) {
                    texto += "Ruta accesible: " + datos.ruta_accesible.distancia_m.toFixed(2) + " m";
                } else {
                    texto += "Ruta accesible: no disponible";
                }

                resultados.innerHTML = texto;
            });
    }
});




//se define un nuevo evento que cuando hace clic en el botón nueva ruta activa la función
document.getElementById("nueva-ruta").addEventListener("click", function () {
    if (marcadororigen !== null) {
        mapa.removeLayer(marcadororigen);
    }

    if (marcadordestino !== null) {
        mapa.removeLayer(marcadordestino);
    }

    if (lineacorta !== null) {
        mapa.removeLayer(lineacorta);
    }

    if (lineaaccesible !== null) {
        mapa.removeLayer(lineaaccesible);
    }

    origen = null;
    destino = null;

    marcadororigen = null;
    marcadordestino = null;

    lineacorta = null;
    lineaaccesible = null;

    document.getElementById("resultados").innerHTML = "";

});

if ("serviceWorker" in navigator) {

    navigator.serviceWorker.register("/service-worker.js")
        .then(function () {
            console.log("Service Worker registrado");
        })
        .catch(function (error) {
            console.log("Error al registrar Service Worker:", error);
        });

}