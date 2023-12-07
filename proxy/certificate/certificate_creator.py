from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
import os
import atexit
import datetime

def create_root_cert() -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    if os.path.exists("root.crt") and os.path.exists("root.key"):
        print("Root certificate already exists. Reading from file.")

        with open("root.crt", "rb") as cert_file:
            root_cert = x509.load_pem_x509_certificate(cert_file.read())

        with open("root.key", "rb") as key_file:
            root_key = serialization.load_pem_private_key(key_file.read(), password=None)

        return root_cert, root_key

    # Generate a private key
    root_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Specify the subject for the root certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'Root CA'),
    ])

    # Create a self-signed root certificate
    root_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(digital_signature=True, content_commitment=True, key_encipherment=True, data_encipherment=True, key_agreement=True, key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(root_key.public_key()),
            critical=False,
        )
        .sign(root_key, hashes.SHA256())
    )

    # Save the root certificate and private key
    with open("root.crt", "wb") as cert_file:
        cert_file.write(root_cert.public_bytes(serialization.Encoding.PEM))

    with open("root.key", "wb") as key_file:
        key_file.write(root_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    return root_cert, root_key

def create_domain_cert(root_cert, root_key, domain_name) -> tuple[x509.Certificate, rsa.RSAPrivateKey]:
    if os.path.exists(f"{domain_name}.crt") and os.path.exists(f"{domain_name}.key"):
        print(f"Certificate for {domain_name} already exists. Reading from file.")

        with open(f"{domain_name}.crt", "rb") as cert_file:
            domain_cert = x509.load_pem_x509_certificate(cert_file.read())

        with open(f"{domain_name}.key", "rb") as key_file:
            domain_key = serialization.load_pem_private_key(key_file.read(), password=None)

        return domain_cert, domain_key

    # Generate a private key for the domain certificate
    domain_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Specify the subject for the domain certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, domain_name),
    ])

    # Create a domain certificate signed by the root certificate
    san_entries = [x509.DNSName(domain_name)]
    san_extension = x509.SubjectAlternativeName(san_entries)

    domain_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(root_cert.subject)
        .public_key(domain_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(digital_signature=True,
                content_commitment=True,
                key_encipherment=True,
                data_encipherment=True,
                key_agreement=True,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH, x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]),
            critical=False,
        )
        .add_extension(
            san_extension,
            critical=False,
        )
        .sign(root_key, hashes.SHA256())
    )

    # Save the domain certificate and private key
    with open(f"{domain_name}.crt", "wb") as cert_file:
        cert_file.write(domain_cert.public_bytes(serialization.Encoding.PEM))

    with open(f"{domain_name}.key", "wb") as key_file:
        key_file.write(domain_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    return domain_cert, domain_key

def trust_root_certificate():
    # Check if current OS is Windows.
    if os.name == "nt":
        os.system(f"certutil -addstore -f root root.crt")
        print("Certificate trusted successfully.")

    # Check if current OS is Linux.
    elif os.name == "posix":
        # TODO
        pass

def untrust_certificate():
    print("Untrusting certificate...")
    
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