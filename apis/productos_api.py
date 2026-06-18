import os
import mysql.connector
from flask import Flask, jsonify, request
from database.conexion import get_connection

app = Flask(__name__)


@app.get("/api/productos")
def listar_productos():
    categoria = request.args.get("categoria", "").strip()
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if categoria:
            cursor.execute(
                "SELECT * FROM producto WHERE categoria = %s AND estado = 'Activo' ORDER BY id",
                (categoria,)
            )
        else:
            cursor.execute("SELECT * FROM producto WHERE estado = 'Activo' ORDER BY id")
        productos = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(productos)
    except mysql.connector.Error as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


@app.get("/api/productos/<int:id>")
def obtener_producto(id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM producto WHERE id = %s", (id,))
        producto = cursor.fetchone()
        cursor.close()
        conn.close()
        if producto is None:
            return jsonify({"error": f"Producto #{id} no encontrado"}), 404
        return jsonify(producto)
    except mysql.connector.Error as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


@app.get("/api/categorias")
def listar_categorias():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT categoria FROM producto WHERE estado = 'Activo' ORDER BY categoria"
        )
        categorias = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(categorias)
    except mysql.connector.Error as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5002))
    print(f"[productos_api] Corriendo en http://localhost:{port}")
    app.run(debug=True, port=port)
