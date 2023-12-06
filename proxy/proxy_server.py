from flask import Flask, request
import requests
from certificate.certificate_creator import create_root_cert, create_domain_cert, trust_certificate, untrust_certificate
import multiprocessing

app = Flask(__name__)
remote: str = None
app_process: multiprocessing.Process = None

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    try:
        url = f"{remote}/{path}"

        # Change host data in request headers.
        headers = dict(request.headers)
        headers['Host'] = remote.split("//")[1].split("/")[0]

        # Send request to remote server.
        response = requests.request(request.method, "http://142.250.186.164", headers=headers, data=request.get_data(), params=request.args)
        return response.content
    except requests.RequestException as e:
        return str(e), 500

def _start(local_port=5000, remote_address='https://www.google.com', ssl_proxy=True):
    global remote
    remote = remote_address

    is_ssl = remote.startswith("https://")

    if ssl_proxy and is_ssl:
        # Get the domain name of the remote address.
        domain = remote.split("//")[1].split("/")[0].split(":")[0]

        # Create self-signed certificate for the domain.
        cert, key = create_root_cert()
        create_domain_cert(cert, key, domain)
        trust_certificate()

        app.run(host=domain, port=local_port, ssl_context=(f'{domain}.crt', f'{domain}.key'))
    else:
        app.run(host='0.0.0.0', port=local_port)

def start(port=5000, remote_address='https://www.google.com', ssl_proxy=True):
    global app_process

    app_process = multiprocessing.Process(target=_start, args=(port, remote_address, ssl_proxy))
    app_process.start()

def stop():
    app_process.terminate()

if __name__ == '__main__':
    start()

    input("Press enter to stop proxy server.")