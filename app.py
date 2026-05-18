from flask import Flask, render_template, request, redirect, url_for, session
# CAMBIO CLAVE: Importamos desde la carpeta 'py'
from py.carrito import carrito_bp 

app = Flask(__name__)
# Sin esta clave, el carrito dará error al intentar guardar productos
app.secret_key = 'peque_mundo_secret_key_2026' 

# Registramos el blueprint
app.register_blueprint(carrito_bp)

@app.route("/")
@app.route("/catalogo")
def inicio():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        # Al loguearse, creamos la sesión para que el carrito funcione
        session['usuario'] = email 
        print(f"Usuario {email} ha iniciado sesión")
        return redirect(url_for('inicio'))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('inicio'))

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        return redirect(url_for('login'))
    return render_template("registro.html")

if __name__ == "__main__":
    app.run(debug=True)
