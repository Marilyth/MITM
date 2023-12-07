from proxy.dns_server import MITMDNSProxy
from proxy.proxy_server import start, on_response
from proxy.certificate.certificate_creator import create_domain_cert, create_root_cert, trust_root_certificate, untrust_certificate
from proxy.dns import replace_dns_server, revert_dns_server
import requests
import atexit


def revert_change():
    """
    Reverts the DNS server and certificate changes.
    """
    untrust_certificate()
    revert_dns_server()


def response_manipulator(response: requests.Response):
    """
    Manipulates the response before it is sent to the client.
    """
    # Replace all instances of "Cat" with "Dinosaur", using a regex.
    import re
    content = response.content.decode("utf-8")
    new_content = re.sub(r"([\">< ,.!?])[Cc]at(s?[\">< ,.!?])", r"\1Dinosaur\2", content)
    response._content = new_content.encode("utf-8")

    return response


if __name__ == "__main__":
    domain = "www.google.com"

    # Create certificates.
    root_cert, root_key = create_root_cert()
    domain_cert, domain_key = create_domain_cert(root_cert, root_key, domain)
    trust_root_certificate()
    atexit.register(revert_change)

    # Start the proxy server. This must happen before the DNS server is replaced.
    start(local_port=443, remote_address=f"https://{domain}", ssl_proxy=True, on_response=response_manipulator)

    # Start the DNS server, pretending google is on localhost.
    proxy = MITMDNSProxy()
    proxy.add_A_domain_replacement(f"{domain}", "127.0.0.1")
    proxy.start()
    
    # Replace the current DNS server with this server.
    replace_dns_server()

    input("Press enter to revert DNS server.")