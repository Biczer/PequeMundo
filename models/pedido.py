from extensions import db


class Pedido(db.Model):

    __tablename__ = 'pedido'


    id_usuario = db.Column(
        db.Integer,
        primary_key=True
    )


    cliente = db.Column(
        db.String(100),
        nullable=False
    )


    cliente_email = db.Column(
        db.String(100),
        nullable=True
    )


    total = db.Column(
        db.Float,
        nullable=False
    )


    estado = db.Column(
        db.String(30),
        nullable=False,
        default='Pendiente'
    )


    vendedor_id = db.Column(
        db.Integer,
        db.ForeignKey('usuarios.id_usuario'),
        nullable=True
    )


    mp_preference_id = db.Column(
        db.String(200),
        nullable=True
    )


    mp_payment_id = db.Column(
        db.String(200),
        nullable=True
    )


    mp_status = db.Column(
        db.String(50),
        nullable=True
    )


    items_json = db.Column(
        db.Text,
        nullable=True
    )


    vendedor = db.relationship(
        'Usuario',
        backref='pedidos_vendedor',
        foreign_keys=[vendedor_id]
    )
