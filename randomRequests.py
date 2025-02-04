import random
import time
import requests
import socket
import psutil
import argparse
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import urllib3

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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

    # Disable SSL certificate verification
    requests.packages.urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        # Make the request with SSL verification disabled
        response = session.get(website, timeout=10, headers=headers, verify=False)
        print(f"Request to {website} from IP {ip} (interface {interface_name}) returned status: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error making request to {website}: {e}")

# Main function to parse the file, randomly select a website, and make requests
def main():
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description='Send requests from a specified network interface')
    parser.add_argument('interface', help='Network interface to bind requests to (e.g., eth0, wlan0)')
    parser.add_argument('websites_file', help='File containing list of websites to request')
    parser.add_argument('--interval', type=int, default=10, help='Time interval between requests in seconds')

    args = parser.parse_args()

    # Get the list of IP addresses and their associated interfaces
    ip_to_interface = get_local_ip_addresses()

    if args.interface not in ip_to_interface.values():
        print(f"Error: Interface {args.interface} not found on this system.")
        return

    # Filter IPs that belong to the specified interface
    ip_addresses = [ip for ip, interface in ip_to_interface.items() if interface == args.interface]

    if not ip_addresses:
        print(f"No IP addresses found for the interface {args.interface}.")
        return

    print(f"Available IP addresses for {args.interface}: {ip_addresses}")

    # Load websites from the file
    websites = load_websites(args.websites_file)
    print(f"Loaded {len(websites)} websites.")

    while True:
        # Randomly select a website
        website = random.choice(websites)

        # Randomly select an IP address from the specified interface
        random_ip = random.choice(ip_addresses)

        # Make the request from the selected IP address (via its network interface)
        make_request(website, random_ip, args.interface)

        # Wait for the specified interval
        time.sleep(args.interval)

# Start the program
if __name__ == '__main__':
    main()
