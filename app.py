# Sheila Harold Sarmiento - TFG Ingeniería de Sistemas de Telecomunicaciones, Sonido e Imagen 2026

from flask import Flask, render_template, request, jsonify, send_from_directory
from src.rutas import calcular_rutas_usuario

app = Flask(__name__)

@app.route("/")
def inicio ():
    return render_template("index.html")

@app.route("/calcular-ruta", methods=["POST"])
def calcular():

    datos = request.get_json() #convierte los dato en elementos utilizables por python

    lat_origen = datos["lat_origen"]
    lon_origen = datos["lon_origen"]
    lat_destino = datos["lat_destino"]
    lon_destino = datos["lon_destino"]

    ruta_corta, ruta_accesible= calcular_rutas_usuario(
        lat_origen,
        lon_origen,
        lat_destino,
        lon_destino
    )

    return jsonify({ #convierte en una respuesta JSON
        "ruta_corta": ruta_corta,
        "ruta_accesible": ruta_accesible
    })

@app.route("/service-worker.js")
def service_worker():
    return send_from_directory(
        "static",
        "service-worker.js",
        mimetype="application/javascript"
    )

@app.route("/manifest.json")
def manifest():
    return send_from_directory(
        "static",
        "manifest.json",
        mimetype="application/manifest+json"
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

