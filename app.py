import os
import json
from flask import Flask
from config import Config
from extensions import db
from routes.auth import auth_bp
from routes.publico import publico_bp
from routes.carrito import carrito_bp
from routes.pedidos import pedidos_bp
from routes.admin import admin_bp
from routes.vendedor import vendedor_bp
from routes.mp import mp_bp
from routes.api import api_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(publico_bp)
    app.register_blueprint(carrito_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vendedor_bp)
    app.register_blueprint(mp_bp)
    app.register_blueprint(api_bp)

    @app.template_filter('from_json')
    def from_json_filter(value):
        try:
            return json.loads(value)
        except Exception:
            return []

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
