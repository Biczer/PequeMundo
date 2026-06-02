import os
import json
from flask import Flask, render_template, request, redirect, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-pequemundo-2024')

USUARIOS_DEMO = {
    'admin@pequemundo.cl': {'password': 'admin123', 'nombre': 'Admin', 'rol': 'Admin'},
    'cliente@test.cl':     {'password': 'cliente123', 'nombre': 'María González', 'rol': 'Cliente'},
}


ESTADOS_VALIDOS = ["Pendiente", "Enviado", "Entregado"]
TRANSICIONES    = {"Pendiente": "Enviado", "Enviado": "Entregado", "Entregado": None}
API_KEY         = "dev-api-key-pequemundo"


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        usuario = USUARIOS_DEMO.get(email)
        if usuario and usuario["password"] == password:
            session["usuario"] = usuario["nombre"]
            session["rol"] = usuario["rol"]
            return redirect("/dashboard" if usuario["rol"] == "Admin" else "/")
        return render_template("login.html", error="Correo o contraseña incorrectos")
    return render_template("login.html")


@app.route("/cerrar_sesion")
def cerrar_sesion():
    session.clear()
    return redirect("/")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        telefono = request.form["telefono"]
        password = request.form["password"]
        confirmar_password = request.form["confirmar_password"]

        print("Nombre:", nombre)
        print("Correo registro:", email)
        print("Teléfono:", telefono)
        print("Contraseña:", password)
        print("Confirmar contraseña:", confirmar_password)

        return redirect("/login")

    return render_template("registro.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/catalogo")
def catalogo():
    return render_template("catalogo.html")


@app.route("/producto/<int:id>")
def detalle_producto(id):
    return render_template("detalle.html")


@app.route("/api/productos")
def api_productos():
    ruta = os.path.join(os.path.dirname(__file__), "data", "productos.json")
    with open(ruta, encoding="utf-8") as f:
        productos = json.load(f)
    categoria = request.args.get("categoria", "")
    if categoria:
        productos = [p for p in productos if p["categoria"] == categoria]
    return jsonify(productos)


@app.route("/api/productos/<int:id>")
def api_producto(id):
    ruta = os.path.join(os.path.dirname(__file__), "data", "productos.json")
    with open(ruta, encoding="utf-8") as f:
        productos = json.load(f)
    producto = next((p for p in productos if p["id"] == id), None)
    if producto is None:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(producto)

@app.route("/carrito")
def carrito():
    items = [
        {"id": 1, "nombre": "Cuna Clásica",       "precio": 129990, "cantidad": 1, "imagen": "peque-mueble.webp"},
        {"id": 2, "nombre": "Cómoda 3 Cajones",    "precio": 99990,  "cantidad": 2, "imagen": "peque-mueble.webp"},
        {"id": 3, "nombre": "Escritorio Infantil", "precio": 89990,  "cantidad": 1, "imagen": "peque-mueble.webp"},
    ]
    subtotal = sum(i["precio"] * i["cantidad"] for i in items)
    costo_rm = 9990
    costo_region = 14990
    entrega = "domicilio_rm"
    total = subtotal + costo_rm
    return render_template("carrito.html",
        items=items, subtotal=subtotal, total=total,
        entrega=entrega, costo_rm=costo_rm, costo_region=costo_region
    )


def leer_pedidos():
    ruta = os.path.join(os.path.dirname(__file__), "data", "pedidos.json")
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)

@app.route("/historial")
def historial():
    pedidos = leer_pedidos()
    return render_template("historial.html", pedidos=pedidos)

if __name__ == "__main__":
    app.run(debug=True)