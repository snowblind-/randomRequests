Quick python script to iterate through a list of websites and to source the request from a random IP address from those configured on the host and bound to the interface. So if you have one IP address it will source all requests from there. If you have hundreds of secondary addresses, it will randomly pick one as the source to simulate users browsing the Internet.

  Usage: python3 randomRequests.py enp0s5 websites.txt --interval 5

No warranties to whether or not this works for you.

-B
