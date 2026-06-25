from flask import Flask
from config import Config
from extensions import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from routes.catalogo import catalogo_bp
    from routes.auth import auth_bp
    from routes.publico import publico_bp
    from routes.carrito import carrito_bp
    from routes.pedidos import pedidos_bp
    from routes.admin import admin_bp
    from routes.vendedor import vendedor_bp
    from routes.mp import mp_bp
    from routes.api import api_bp

    app.register_blueprint(catalogo_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(publico_bp)
    app.register_blueprint(carrito_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vendedor_bp)
    app.register_blueprint(mp_bp)
    app.register_blueprint(api_bp)

    print("✅ APP INICIADA CORRECTAMENTE")

    return app


# 🔥 IMPORTANTE PARA RENDER
app = create_app()
