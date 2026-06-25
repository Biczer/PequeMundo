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

    @app.route("/env")
    def env():
        return os.getenv("TEST", "NO")

    from sqlalchemy import text

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
    print("RUTAS CARGADAS")
    return app
