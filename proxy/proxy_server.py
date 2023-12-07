from flask import Flask, request
import requests
import multiprocessing
import socket
from typing import Callable

app = Flask(__name__)
remote: str = None
app_process: multiprocessing.Process = None

def on_request(request: requests.Request):
    """
    Called before a request is sent to the remote server.
    Can be used to modify the request before it is sent.
    """
    pass

def on_response(response: requests.Response):
    """
    Called before a response is sent to the client.
    Can be used to modify the response before it is sent.
    """
    pass

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    try:
        url = f"{remote}/{path}"

        # Change host data in request headers.
        headers = dict(request.headers)
        headers['Host'] = remote.split("//")[1].split("/")[0]

        # Manipulate request before sending.
        on_request(request)

        # Send request to remote server.
        response = requests.request(request.method, url, headers=headers, data=request.get_data(), params=request.args)
        on_response(response)

        return response.content
    except requests.RequestException as e:
        return str(e), 500
    
def override_dns(domain: str, ip: str):
    """
    Overrides the default DNS lookup to force a domain to resolve to a specific IP address.
    Since the DNS is being overridden for this domain, the remote server could otherwise not be reached.
    """
    # Slightly modified from
    # https://stackoverflow.com/questions/44374215/how-do-i-specify-url-resolution-in-pythons-requests-library-in-a-similar-fashio
    dns_cache = {domain: ip}

    prv_getaddrinfo = socket.getaddrinfo
    # Override default socket.getaddrinfo() and pass ip instead of host
    # if override is detected.
    def new_getaddrinfo(*args):
        if args[0] in dns_cache:
            return prv_getaddrinfo(dns_cache[args[0]], *args[1:])
        else:
            return prv_getaddrinfo(*args)

    socket.getaddrinfo = new_getaddrinfo

def _start(local_port: int, remote_address: str, domain: str, ip: str, ssl_proxy: bool, on_request_overwrite=None, on_response_overwrite=None):
    global remote
    remote = remote_address

    is_ssl = remote.startswith("https://")

    if on_request_overwrite:
        global on_request
        on_request = on_request_overwrite
    
    if on_response_overwrite:
        global on_response
        on_response = on_response_overwrite

    if ssl_proxy and is_ssl:
        # We are pretending to be the remote server, stealing its domain name.
        override_dns(domain, ip)
        app.run(host='0.0.0.0', port=local_port, ssl_context=(f'{domain}.crt', f'{domain}.key'))
    else:
        # We are a proxy to the remote server, but our address is different.
        app.run(host='0.0.0.0', port=local_port)

def start(local_port: int, remote_address: str, ssl_proxy: bool, on_request: Callable[[requests.Request], None]=None, on_response: Callable[[requests.Response], None]=None):
    global app_process

    # Get the domain name of the remote address.
    domain = remote_address.split("//")[1].split("/")[0].split(":")[0]
    ip = socket.gethostbyname(domain)

    app_process = multiprocessing.Process(target=_start, args=(local_port, remote_address, domain, ip, ssl_proxy, on_request, on_response))
    app_process.start()

def stop():
    app_process.terminate()

if __name__ == '__main__':
    start(ssl_proxy=False)
    input("Press enter to stop proxy server.")
    