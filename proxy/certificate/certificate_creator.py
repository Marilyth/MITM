import OpenSSL
from OpenSSL import crypto
import os
import atexit


def create_root_cert():
    # Create a key pair
    root_key = crypto.PKey()
    root_key.generate_key(crypto.TYPE_RSA, 2048)

    # Create a self-signed root certificate
    root_cert = crypto.X509()
    root_cert.get_subject().CN = "Root CA"
    root_cert.set_serial_number(1000)
    root_cert.gmtime_adj_notBefore(0)
    root_cert.gmtime_adj_notAfter(3650 * 24 * 60 * 60)  # 10 years validity
    root_cert.set_issuer(root_cert.get_subject())
    root_cert.set_pubkey(root_key)
    root_cert.sign(root_key, "sha256")

    # Save the root certificate and private key
    with open("root.crt", "wb") as cert_file:
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, root_cert))

    with open("root.key", "wb") as key_file:
        key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, root_key))

    return root_cert, root_key

def create_domain_cert(root_cert, root_key, domain_name):
    # Create a key pair for the domain certificate
    domain_key = crypto.PKey()
    domain_key.generate_key(crypto.TYPE_RSA, 2048)

    # Create a certificate signing request (CSR) for the domain
    domain_csr = crypto.X509Req()
    domain_csr.get_subject().CN = domain_name
    domain_csr.set_pubkey(domain_key)
    domain_csr.sign(domain_key, "sha256")

    # Create a domain certificate signed by the root certificate
    domain_cert = crypto.X509()
    domain_cert.set_serial_number(1001)
    domain_cert.gmtime_adj_notBefore(0)
    domain_cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 1 year validity
    domain_cert.set_issuer(root_cert.get_subject())
    domain_cert.set_subject(domain_csr.get_subject())
    domain_cert.set_pubkey(domain_csr.get_pubkey())
    domain_cert.sign(root_key, "sha256")

    # Save the domain certificate and private key
    with open(f"{domain_name}.crt", "wb") as cert_file:
        cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, domain_cert))

    with open(f"{domain_name}.key", "wb") as key_file:
        key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, domain_key))

    return domain_cert, domain_key

def trust_certificate():
    # Check if current OS is Windows.
    if os.name == "nt":
        os.system(f"certutil -addstore -f root root.crt")
        print("Certificate trusted successfully.")

    # Check if current OS is Linux.
    elif os.name == "posix":
        # TODO
        pass

    atexit.register(untrust_certificate)


def untrust_certificate():
    # Check if current OS is Windows.
    if os.name == "nt":
        os.system(f"certutil -delstore -f root root.crt")
        print("Certificate untrusted successfully.")

    # Check if current OS is Linux.
    elif os.name == "posix":
        # TODO
        pass


if __name__ == "__main__":
    # Create a root certificate
    root_cert, root_key = create_root_cert()

    # Create a domain certificate signed by the root certificate
    domain_name = "www.google.com"  # Replace with your domain name
    domain_cert, domain_key = create_domain_cert(root_cert, root_key, domain_name)