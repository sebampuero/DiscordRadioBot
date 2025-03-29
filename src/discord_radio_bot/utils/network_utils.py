import asyncio
from functools import partial
import socket


def get_radiobrowser_base_urls(): # from https://api.radio-browser.info/
    """
    Get all base urls of all currently available radiobrowser servers

    Returns: 
    list: a list of strings

    """
    hosts = []
    # get all hosts from DNS
    ips = socket.getaddrinfo('all.api.radio-browser.info',
                             80, 0, 0, socket.IPPROTO_TCP)
    reachable_ips = []
    for ip_tupple in ips:
        ip = ip_tupple[4][0]
        try:
            socket.create_connection((ip, 443), timeout=2).close()
            reachable_ips.append(ip)
        except (socket.timeout, socket.error):
            continue  

    for ip in reachable_ips:
        # do a reverse lookup on every one of the ips to have a nice name for it
        host_addr = socket.gethostbyaddr(ip)
        # add the name to a list if not already in there
        if host_addr[0] not in hosts:
            hosts.append(host_addr[0])

    # sort list of names
    hosts.sort()
    # add "https://" in front to make it an url
    return list(map(lambda x: "https://" + x, hosts))