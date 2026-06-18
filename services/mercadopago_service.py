import os
import mercadopago

MP_ACCESS_TOKEN = os.environ.get(
    'MP_ACCESS_TOKEN',
    'TEST-7405494608123272-053123-046e81571c23bf9c73efb64662b94c28-585535158'
)
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)


def crear_preferencia(items_list, cliente_nombre, cliente_email, pedido_id, base_url):
    mp_items = [{
        "id": str(i['id']),
        "title": i['nombre'],
        "quantity": int(i['cantidad']),
        "unit_price": int(i['precio']),
        "currency_id": "CLP"
    } for i in items_list]

    preference_data = {
        "items": mp_items,
        "payer": {
            "name": cliente_nombre,
            "email": cliente_email or ""
        },
        "back_urls": {
            "success": f"{base_url}/mp/success",
            "failure": f"{base_url}/mp/failure",
            "pending": f"{base_url}/mp/pending",
        },
        "notification_url": f"{base_url}/mp/webhook",
        "external_reference": str(pedido_id),
        "auto_return": "all",
    }

    response = sdk.preference().create(preference_data)
    return response.get("response", {})


def obtener_pago(payment_id):
    response = sdk.payment().get(payment_id)
    return response.get("response", {})
