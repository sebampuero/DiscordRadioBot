import random
import socket
from logconfig.logging_config import get_logger
import asyncio
from functools import partial

logger = get_logger("radio_discord_bot")


async def get_radiobrowse_base_hostname():  # from https://api.radio-browser.info/
    """
    Get the base hostname for radio-browser.info
    This function will return a list of IP addresses that are reachable
    and have a DNS entry. The list is shuffled to avoid overloading
    a single IP address.

    Returns:
        list: A list of IP addresses that are reachable and have a DNS entry.
    """
    loop = asyncio.get_event_loop()
    # get all hosts from DNS
    ips = await loop.run_in_executor(
        None,
        lambda: socket.getaddrinfo(
            "all.api.radio-browser.info", 80, 0, 0, socket.IPPROTO_TCP
        ),
    )
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
    logger.info(f"Resolved IPs for radio: {resolved_ips}")
    hosts = [ip[0] for ip in resolved_ips]
    random.shuffle(hosts)
    return hosts


def check_connection(ip: str) -> str | None:
    try:
        socket.create_connection((ip, 443), timeout=2).close()
        return ip
    except (socket.timeout, socket.error):
        logger.info(f"Host {ip} is not reachable")
        return None
