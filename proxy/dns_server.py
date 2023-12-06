from dnslib import DNSRecord, QTYPE, A, RD
import socket
from typing import Dict
from multiprocessing import Process


class MITMDNSProxy:
    def __init__(self, local_port: int = 53, remote_dns: str = "8.8.8.8", domain_replacements: Dict[str, Dict[int, RD]] = {}):
        """
        Prepares the DNS proxy.

        Args:
            local_port (str): The local port to listen on.
            remote_dns (str, optional): The remote DNS server to use. Defaults to "
            domain_replacements (Dict[str, List[str]], optional): A dictionary of domains to replace with other values. Defaults to {}.
        """
        self.local_port = local_port
        self.remote_dns = remote_dns
        self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.local_socket.bind(("127.0.0.1", local_port))
        self.domain_replacements = domain_replacements
        self.started = False

    def add_A_domain_replacement(self, domain: str, replacement: str):
        """
        Adds a domain replacement for A records.

        Args:
            domain (str): The domain to replace.
            replacement (str): The replacement value.
        """
        if domain not in self.domain_replacements:
            self.domain_replacements[domain] = {}
        self.domain_replacements[domain][QTYPE.reverse["A"]] = A(replacement)

    def add_domain_replacement(self, domain: str, replacement: RD, qtype: int):
        """
        Adds a domain replacement for a specific query type.

        Args:
            domain (str): The domain to replace.
            replacement (RD): The replacement value.
            qtype (int, optional): The query type to replace.
        """
        if domain not in self.domain_replacements:
            self.domain_replacements[domain] = {}
        self.domain_replacements[domain][qtype] = replacement

    def start(self):
        """
        Starts the DNS proxy in a seperate thread.
        """
        if self.started:
            raise Exception("DNS proxy already started.")
        
        self.started = True
        self.proxy_process = Process(target=self._proxy)
        self.proxy_process.start()
    
    def stop(self):
        """
        Stops the DNS proxy.
        """
        self.proxy_process.terminate()

    def replace_record(self, record: DNSRecord):
        """
        Replaces the record's rdata with the replacement value if it exists, in-place.

        Args:
            record (DNSRecord): The record to replace.
        """
        name = ".".join([str(segment, 'utf-8') for segment in record.questions[0].qname.label])

        if name in self.domain_replacements:
            for rr in record.rr:
                if rr.rtype in self.domain_replacements[name]:
                    rr.rdata = self.domain_replacements[name][rr.rtype]

    def _proxy(self):
        """
        The main proxy loop. Infinitely loops and proxies DNS requests to the remote DNS server, or replaces them with the replacement values.
        """
        while True:
            try:
                data, addr = self.local_socket.recvfrom(1024)
                dns_request = DNSRecord.parse(data)

                remote_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                remote_socket.sendto(data, (self.remote_dns, 53))
                remote_data, _ = remote_socket.recvfrom(1024)
                remote_socket.close()

                dns_response = DNSRecord.parse(remote_data)
                self.replace_record(dns_response)

                self.local_socket.sendto(dns_response.pack(), addr)
                print(f"DNS query for {dns_request.questions[0].qname} from {addr[0]}")
            except Exception as e:
                print(e)

if __name__ == "__main__":
    proxy = MITMDNSProxy()
    proxy.add_A_domain_replacement("google.com", RD("127.0.0.2"))
    proxy.start()