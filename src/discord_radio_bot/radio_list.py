import aiohttp
import json
from logconfig.logging_config import get_logger

logger = get_logger("radio_discord_bot")

ALL_API_RADIO_BROWSER_HOSTNAME = "https://all.api.radio-browser.info"

selected_radio_browser_hostname = ""

async def fetch_radio_by_name(query: str):
    url = f"{selected_radio_browser_hostname}/json/stations/byname/{query}?hidebroken=true"
    logger.info(f"Fetching radio by name: {url}")
    headers = {'User-Agent': 'discord-bot-sebampuero'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url, timeout=5) as response:
            data = await response.text()
            return json.loads(data)

async def fetch_radios_by_city(offset: int, limit: int, query: str):
    url = f"{selected_radio_browser_hostname}/json/stations/bystateexact/{query}?offset={offset}&limit={limit}?hidebroken=true"
    logger.info(f"Fetching radios by city: {url}")
    headers = {'User-Agent': 'discord-bot-sebampuero'}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            data = await response.text()
            return json.loads(data)
