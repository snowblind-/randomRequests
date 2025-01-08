import random
import time
import requests
import socket
import psutil
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# Function to read the list of websites from a file
def load_websites(filename):
    with open(filename, 'r') as file:
        websites = [line.strip() for line in file.readlines()]
    return websites

# Function to get a list of all IP addresses and their associated network interfaces
def get_local_ip_addresses():
    ip_to_interface = {}
    # Iterate over network interfaces
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            # Only consider IPv4 addresses (ignoring loopback)
            if addr.family == socket.AF_INET and not addr.address.startswith('127.'):
                ip_to_interface[addr.address] = interface
    return ip_to_interface

# Custom adapter to bind the requests to a specific source IP address via its interface
class SourceIPAdapter(HTTPAdapter):
    def __init__(self, interface_name, **kwargs):
        self.interface_name = interface_name
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # Set the socket options to bind to the specified interface
        kwargs['socket_options'] = [
            (socket.SOL_SOCKET, socket.SO_BINDTODEVICE, self.interface_name.encode('utf-8'))
        ]
        return super().init_poolmanager(*args, **kwargs)

# Function to make an HTTPS request from a specific IP address (via its network interface)
def make_request(website, ip, interface_name):
    # Create a session and mount the custom adapter
    session = requests.Session()
    adapter = SourceIPAdapter(interface_name=interface_name)
    session.mount('https://', adapter)
    session.mount('http://', adapter)

    try:
        response = session.get(website, timeout=10)
        print(f"Request to {website} from IP {ip} (interface {interface_name}) returned status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error making request to {website}: {e}")

# Main function to parse the file, randomly select a website, and make requests
def main():
    websites_file = 'websites.txt'  # File containing the list of websites
    interval = 10  # Time interval (in seconds) between each request

    # Load websites from the file
    websites = load_websites(websites_file)
    print(f"Loaded {len(websites)} websites.")

    # Get the list of IP addresses and their associated interfaces
    ip_to_interface = get_local_ip_addresses()
    if not ip_to_interface:
        print("No valid IP addresses found on the system.")
        return

    print(f"Available IP addresses: {ip_to_interface}")

    while True:
        # Randomly select a website
        website = random.choice(websites)

        # Randomly select an IP address and its corresponding interface
        ip, interface_name = random.choice(list(ip_to_interface.items()))

        # Make the request from the selected IP address (via its network interface)
        make_request(website, ip, interface_name)

        # Wait for the specified interval
        time.sleep(interval)

# Start the program
if __name__ == '__main__':
    main()
