from extensions import db

class Producto(db.Model):
    __tablename__ = 'producto'

    id_producto = db.Column(db.Integer, primary_key=True)

    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(300))
    imagen = db.Column(db.String(255))
    categoria = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), nullable=False)
