from extensions import db
from sqlalchemy import func

productos = Producto.query.filter(
    func.lower(Producto.estado) == "activo"
).all()
