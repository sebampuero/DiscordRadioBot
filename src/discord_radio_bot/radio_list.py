import aiohttp
import json
from logconfig.logging_config import get_logger
from utils.network_utils import get_radiobrowse_base_url

logger = get_logger("radio_discord_bot")

async def fetch_radio_by_name(query: str):
    radio_hostname_list = await get_radiobrowse_base_url()
    url = f"{radio_hostname_list[0]}/json/stations/byname/{query}?hidebroken=true"
    logger.info(f"Fetching radio by name: {url}")
    headers = {'User-Agent': 'discord-bot-sebampuero'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=2) as response:
            data = await response.text()
            return json.loads(data)

async def fetch_radios_by_city(offset: int, limit: int, query: str):
    radio_hostname_list = await get_radiobrowse_base_url()
    url = f"{radio_hostname_list[0]}/json/stations/bystateexact/{query}?offset={offset}&limit={limit}?hidebroken=true"
    logger.info(f"Fetching radios by city: {url}")
    headers = {'User-Agent': 'discord-bot-sebampuero'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=2) as response:
            data = await response.text()
            return json.loads(data)
