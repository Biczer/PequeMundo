import os
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # Supabase Postgres URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False



def create_app():
    print("APP INICIADA")

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    
    from auth import auth_bp
    from publico import publico_bp
    from carrito import carrito_bp
    from pedidos import pedidos_bp
    from admin import admin_bp
    from vendedor import vendedor_bp
    from mercado_pago import mp_bp
    from api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(publico_bp)
    app.register_blueprint(carrito_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vendedor_bp)
    app.register_blueprint(mp_bp)
    app.register_blueprint(api_bp)

   
    @app.route("/env")
    def env():
        return os.getenv("TEST", "NO")

    
    @app.route("/testdb")
    def testdb():
        try:
            db.session.execute(text("SELECT 1"))
            return "Conexión OK"
        except Exception as e:
            return str(e)

   
    @app.template_filter('from_json')
    def from_json_filter(value):
        try:
            return json.loads(value)
        except Exception:
            return []

    
    @app.route("/ping")
    def ping():
        return "PONG"

    @app.route("/debug-db")
    def debug_db():
        from models import Producto 
        productos = Producto.query.all()
        return {"count": len(productos)}

    
    @app.route("/")
    def home():
        from models import Producto  
        productos = Producto.query.all()
        return {
            "productos": [p.id for p in productos]
        }
    @app.route("/catalogo")
    def catalogo():
    try:
        productos = db.session.execute(text("SELECT * FROM producto")).fetchall()
        return {"productos": [dict(p._mapping) for p in productos]}
    except Exception as e:
        return str(e), 500
    print("RUTAS CARGADAS")
    return app
