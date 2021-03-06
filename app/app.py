from chalice import Chalice, Response
import http.client
import json
import os
import time

app = Chalice(app_name='app')

#
# Step 1: Get Client credentials, see doc here
# https://shopify.dev/tutorials/authenticate-with-oauth#step-1-get-client-credentials
#
@app.route('/')
def index():

    request = app.current_request
    params = request.query_params

    # Debug helper, uncomment the following
    # return request.to_dict()

    if not params:
        return Response(
            body="STATUS OK",
            status_code=200,
            headers={
                'Content-Type': 'text/plain'
            }
        )

    url = request.context.get('path')
    shop = params.get('shop')
    hmac = params.get('hmac')
    timestamp = params.get('timestamp')
    api_key = os.getenv('SHOPIFY_API_KEY')
    base_url = os.getenv('AWS_API_BASE_URL')
    scopes = "read_orders,read_customers"
    redirect_uri = f"{base_url}confirm/install"
    nonce = time.time()

    #
    # Step 2: Ask for permission, see doc here
    # https://shopify.dev/tutorials/authenticate-with-oauth#step-2-ask-for-permission
    #
    if hmac and shop:
        url = f"https://{shop}/admin/oauth/authorize?client_id={api_key}&scope={scopes}&redirect_uri={redirect_uri}&state={nonce}"
        return Response(
            status_code=301,
            body='',
            headers={'Location': url}
        )

    body = f"<pre>{request.method}\n url={url}\n shop={shop}\n timestamp={timestamp}\n hmac={hmac}\n</pre>"
    return Response(
        body=body,
        status_code=200,
        headers={
            'Content-Type': 'text/html'
        }
    )

#
# Step 3: Confirm installation, see doc here
# https://shopify.dev/tutorials/authenticate-with-oauth#step-3-confirm-installation
#
@app.route('/confirm/install')
def confirmInstall():

    request = app.current_request
    params = request.query_params

    # debug helper, uncomment the following
    # return request.to_dict()

    if not params:
        return Response(
            body="INVALID REQUEST",
            status_code=500,
            headers={
                'Content-Type': 'text/plain'
            }
        )

    shop = params.get('shop')
    authorization_code = params.get('code')
    hmac = params.get('hmac')
    timestamp = params.get('timestamp')
    state = params.get('state')
    api_key = os.getenv('SHOPIFY_API_KEY')
    api_secret = os.getenv('SHOPIFY_API_SECRET')

    # TODO verify hmac

    # Get Access Token by making a post request to Shopify
    conn = http.client.HTTPSConnection(shop)
    conn.request(
        'POST',
        f"https://{shop}/admin/oauth/access_token",
        json.dumps({
            'client_id': api_key,
            'client_secret': api_secret,
            'code': authorization_code
        }),
        {
            'Content-type': 'application/json'
        }
    )

    response = conn.getresponse()
    content = response.read().decode()

    # Response content should look something like this
    # {
    #     "code": "XXXXXXXXXXXXXXXXXXXXXXXXX",
    #     "hmac": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    #     "shop": "XXXXXXXXX.myshopify.com",
    #     "state": "1593318793.829355",
    #     "timestamp": "1593318794"
    # }

    if response.status != 200:
        return Response(
            body=content,
            status_code=response.status,
            headers={
                'Content-Type': 'text/plain'
            }
        )

    # In a real app you want to save this token somewhere for making Shopify api calls
    decoded = json.loads(content)
    return Response(
        body=decoded.get('access_token'),
        status_code=response.status,
        headers={
            'Content-Type': 'text/plain'
        }
    )
