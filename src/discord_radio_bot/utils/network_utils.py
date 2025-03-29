import random
import socket
from logconfig.logging_config import get_logger
import asyncio
from functools import partial

logger = get_logger("radio_discord_bot")

async def get_radiobrowse_base_url(): # from https://api.radio-browser.info/
    """
    Get a base url from all available radio browser servers.

    Returns: 
    list: a list of strings

    """
    loop = asyncio.get_event_loop()
    # get all hosts from DNS
    ips = await loop.run_in_executor(None, 
                                     lambda: socket.getaddrinfo('all.api.radio-browser.info', 80, 0, 0, socket.IPPROTO_TCP))
    reachable_ips = []
    tasks = []
    for ip_tupple in ips:
        ip = ip_tupple[4][0]
        task = loop.run_in_executor(None, partial(check_connection, ip))
        tasks.append(task)
    ips = await asyncio.gather(*tasks)
    reachable_ips = [ip for ip in ips if ip is not None]

    tasks_dns_lookup = []
    for ip in reachable_ips:
        task = loop.run_in_executor(None, partial(socket.gethostbyaddr, ip))
        tasks_dns_lookup.append(task)

    resolved_ips = await asyncio.gather(*tasks_dns_lookup)

    random.shuffle(resolved_ips)
    if not resolved_ips:
        resolved_ips.append("all.api.radio-browser.info")
    # add "https://" in front to make it an url
    return list(map(lambda x: "https://" + x, resolved_ips))


def check_connection(ip: str) -> str | None:
    try:
        socket.create_connection((ip, 443), timeout=0.5).close()
        return ip
    except (socket.timeout, socket.error):
        logger.info(f"Host {ip} is not reachable")
        return None