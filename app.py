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


if __name__ == "__main__":
    app.run(debug=True)