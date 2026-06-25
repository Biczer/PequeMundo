import os
import mercadopago


MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")


if not MP_ACCESS_TOKEN:
    raise Exception(
        "Falta configurar MP_ACCESS_TOKEN en variables de entorno"
    )


sdk = mercadopago.SDK(MP_ACCESS_TOKEN)



def crear_preferencia(items_list, cliente_nombre, cliente_email, pedido_id, base_url):


    mp_items = []


    for i in items_list:

        mp_items.append({

            "id": str(i.get("id_producto")),

            "title": i.get("nombre"),

            "quantity": int(i.get("cantidad", 1)),

            "unit_price": int(i.get("precio", 0)),

            "currency_id": "CLP"

        })



    preference_data = {


        "items": mp_items,


        "payer": {

            "name": cliente_nombre,

            "email": cliente_email or ""

        },


        "back_urls": {


            "success": f"{base_url}/mp/success",

            "failure": f"{base_url}/mp/failure",

            "pending": f"{base_url}/mp/pending"

        },


        "notification_url": f"{base_url}/mp/webhook",


        "external_reference": str(pedido_id),


        "auto_return": "approved"

    }



    response = sdk.preference().create(
        preference_data
    )


    return response.get(
        "response",
        {}
    )




def obtener_pago(payment_id):


    response = sdk.payment().get(
        payment_id
    )


    return response.get(
        "response",
        {}
    )
