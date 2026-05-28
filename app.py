from flask import Flask, render_template, request, redirect

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        print("Correo login:", email)
        print("Contraseña login:", password)

        return redirect("/")

    return render_template("login.html")


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


@app.route("/catalogo")
def catalogo():
    return render_template("catalogo.html")

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


@app.route("/historial")
def historial():
    pedidos = [
        {
            "id": 1042,
            "fecha": "24 mayo 2026",
            "estado": "entregado",
            "id_transaccion": "TXN-8A3F2C1D",
            "total": "329.980",
            "items": [
                {"nombre": "Cuna Clásica", "cantidad": 1, "precio": "129.990", "imagen": "peque-mueble.webp"},
                {"nombre": "Cómoda 3 Cajones", "cantidad": 2, "precio": "199.980", "imagen": "peque-mueble.webp"},
            ]
        },
        {
            "id": 1041,
            "fecha": "10 mayo 2026",
            "estado": "pendiente",
            "id_transaccion": "TXN-5E9B4A7C",
            "total": "89.990",
            "items": [
                {"nombre": "Escritorio Infantil", "cantidad": 1, "precio": "89.990", "imagen": "peque-mueble.webp"},
            ]
        },
    ]
    return render_template("historial.html", pedidos=pedidos)


if __name__ == "__main__":
    app.run(debug=True)