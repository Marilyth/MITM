import os
import atexit


def replace_dns_server(interface_name: str = "Ethernet"):
    """
    Replaces the current DNS server with this server, running on localhost:53.
    """
    # Check if current OS is Windows.
    if os.name == "nt":
        os.system(f"netsh interface ip set dns name=\"{interface_name}\" static 127.0.0.1")
        print("DNS server replaced successfully with this server.")
    
    # Check if current OS is Linux.
    elif os.name == "posix":
        # TODO
        pass

    # Register a function to revert the DNS server when the program exits.
    atexit.register(lambda: revert_dns_server(interface_name))

def revert_dns_server(interface_name: str = "Ethernet"):
    """
    Reverts the current DNS server to the default.
    """
    # Check if current OS is Windows.
    if os.name == "nt":
        os.system(f"netsh interface ip set dns name=\"{interface_name}\" dhcp")
        print("DNS server reverted successfully to the default.")

    # Check if current OS is Linux.
    elif os.name == "posix":
        # TODO
        pass


if __name__ == "__main__":
    from dns_server import MITMDNSProxy
    from proxy_server import start

    # Start the proxy server.
    start(port=443, remote_address="https://www.google.com", ssl_proxy=True)

    # Start the DNS server, pretending google is on localhost.
    proxy = MITMDNSProxy()
    proxy.add_A_domain_replacement("www.google.com", "127.0.0.1")
    proxy.start()
    
    replace_dns_server()
    
    input("Press enter to revert DNS server.")