import json
from flask import Blueprint, request, redirect, url_for, session, flash, jsonify
from extensions import db
from models import Producto, Pedido
from services.mercadopago_service import sdk

mp_bp = Blueprint('mp', __name__)


def _actualizar_pedido_desde_pago(payment_id, external_ref, status_fallback=None):
    if not external_ref:
        return
    try:
        pedido = db.session.get(Pedido, int(external_ref))
    except (ValueError, TypeError):
        return
    if not pedido:
        return

    status = status_fallback
    if payment_id:
        try:
            payment_info = sdk.payment().get(payment_id)
            payment = payment_info.get("response", {})
            status = payment.get("status", status_fallback)
            payment_id = str(payment.get("id", payment_id))
        except Exception:
            pass

    if payment_id:
        pedido.mp_payment_id = str(payment_id)
    if status:
        pedido.mp_status = status

    if status == 'approved' and pedido.estado != 'Pagado':
        pedido.estado = 'Pagado'
        if pedido.items_json:
            try:
                for item in json.loads(pedido.items_json):
                    prod = db.session.get(Producto, item['id'])
                    if prod:
                        prod.stock = max(0, prod.stock - item['cantidad'])
                        if prod.stock == 0:
                            prod.estado = 'Agotado'
            except Exception:
                pass
    elif status == 'rejected':
        pedido.estado = 'Rechazado'
    elif status == 'pending':
        pedido.estado = 'Pendiente'

    db.session.commit()


@mp_bp.route('/mp/success')
def mp_success():
    payment_id = request.args.get('payment_id')
    external_ref = request.args.get('external_reference')
    status = request.args.get('status')
    _actualizar_pedido_desde_pago(payment_id, external_ref, status_fallback=status or 'approved')
    flash('¡Pago realizado con éxito!', 'success')
    rol = session.get('rol')
    if rol in ('Vendedor', 'Admin'):
        return redirect(url_for('vendedor.vendedor_pedidos'))
    return redirect(url_for('pedidos.mis_pedidos'))


@mp_bp.route('/mp/failure')
def mp_failure():
    payment_id = request.args.get('payment_id')
    external_ref = request.args.get('external_reference')
    status = request.args.get('status')
    _actualizar_pedido_desde_pago(payment_id, external_ref, status_fallback=status or 'rejected')
    flash('El pago fue rechazado. Intenta nuevamente.', 'danger')
    rol = session.get('rol')
    if rol in ('Vendedor', 'Admin'):
        return redirect(url_for('vendedor.vendedor_pedidos'))
    return redirect(url_for('publico.catalogo'))


@mp_bp.route('/mp/pending')
def mp_pending():
    payment_id = request.args.get('payment_id')
    external_ref = request.args.get('external_reference')
    status = request.args.get('status')
    _actualizar_pedido_desde_pago(payment_id, external_ref, status_fallback=status or 'pending')
    flash('Pago pendiente de confirmación.', 'warning')
    rol = session.get('rol')
    if rol in ('Vendedor', 'Admin'):
        return redirect(url_for('vendedor.vendedor_pedidos'))
    return redirect(url_for('pedidos.mis_pedidos'))


@mp_bp.route('/mp/webhook', methods=['POST'])
def mp_webhook():
    data = request.get_json(silent=True) or {}
    topic = data.get('type') or request.args.get('topic')
    if topic == 'payment':
        payment_id = data.get('data', {}).get('id') or request.args.get('id')
        if payment_id:
            try:
                payment_info = sdk.payment().get(payment_id)
                payment = payment_info.get("response", {})
                external_ref = payment.get("external_reference")
                status = payment.get("status")
                _actualizar_pedido_desde_pago(str(payment_id), external_ref, status_fallback=status)
            except Exception:
                pass
    return jsonify({"status": "ok"}), 200
