import os
import pymysql
import pymysql.cursors
from flask import Flask, jsonify, request

app = Flask(__name__)

# ── Configuración de la base de datos ─────────────────────────────────────────
DB_CONFIG = {
    "host":     os.environ.get("DB_HOST",     "localhost"),
    "port":     int(os.environ.get("DB_PORT", 3306)),
    "user":     os.environ.get("DB_USER",     "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "db":       os.environ.get("DB_NAME",     "pequemundo"),
    "charset":  "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

# SQL para crear la tabla si no existe:
# CREATE TABLE productos (
#   id        INT AUTO_INCREMENT PRIMARY KEY,
#   nombre    VARCHAR(150)   NOT NULL,
#   categoria VARCHAR(100)   NOT NULL,
#   descripcion TEXT,
#   precio    INT            NOT NULL,
#   stock     INT            NOT NULL DEFAULT 0,
#   imagen    VARCHAR(200)
# );


def get_conn():
    return pymysql.connect(**DB_CONFIG)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/api/productos")
def listar_productos():
    """
    GET /api/productos
    GET /api/productos?categoria=Cunas
    """
    categoria = request.args.get("categoria", "").strip()
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                if categoria:
                    cur.execute(
                        "SELECT * FROM productos WHERE categoria = %s ORDER BY id",
                        (categoria,)
                    )
                else:
                    cur.execute("SELECT * FROM productos ORDER BY id")
                productos = cur.fetchall()
        return jsonify(productos)
    except pymysql.MySQLError as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


@app.get("/api/productos/<int:id>")
def obtener_producto(id):
    """
    GET /api/productos/1
    """
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
                producto = cur.fetchone()
        if producto is None:
            return jsonify({"error": f"Producto #{id} no encontrado"}), 404
        return jsonify(producto)
    except pymysql.MySQLError as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


@app.get("/api/categorias")
def listar_categorias():
    """
    GET /api/categorias  →  lista de categorías únicas
    """
    try:
        conn = get_conn()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT categoria FROM productos ORDER BY categoria")
                rows = cur.fetchall()
        return jsonify([r["categoria"] for r in rows])
    except pymysql.MySQLError as e:
        return jsonify({"error": "Error de base de datos", "detalle": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5002))
    print(f"[productos_api] Corriendo en http://localhost:{port}")
    app.run(debug=True, port=port)
