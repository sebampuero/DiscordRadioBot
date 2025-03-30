import aiohttp
import json
from logconfig.logging_config import get_logger
from utils.network_utils import get_radiobrowse_base_hostname

logger = get_logger("radio_discord_bot")


class RadioListManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    async def update_radio_hostname(self):
        """
        Update the radio hostname to a new URL.
        """
        radio_base_url_list = await get_radiobrowse_base_hostname()
        if len(radio_base_url_list) > 0:
            self.selected_radio_hostname = f"https://{radio_base_url_list[0]}"
        else:
            self.selected_radio_hostname = "http://10.8.0.7:9090"
            logger.warning("No radio browser servers available, using local server")
        logger.info(f"Updated radio hostname to: {self.selected_radio_hostname}")

    async def fetch_all_radios_by_name(self, query: str):
        url = f"{self.selected_radio_hostname}/json/stations/byname/{query}?hidebroken=true"
        logger.info(f"Fetching all radios by name: {url}")
        headers = {"User-Agent": "discord-bot-sebampuero"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=4) as response:
                data = await response.text()
                return json.loads(data)

    async def fetch_all_radios_by_city(self, query: str):
        url = f"{self.selected_radio_hostname}/json/stations/bystateexact/{query}?hidebroken=true"
        logger.info(f"Fetching all radios by city: {url}")
        headers = {"User-Agent": "discord-bot-sebampuero"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=4) as response:
                data = await response.text()
                return json.loads(data)

    async def fetch_radio_by_name(self, offset: int, limit: int, query: str):
        url = f"{self.selected_radio_hostname}/json/stations/byname/{query}?offset={offset}&limit={limit}&hidebroken=true"
        logger.info(
            f"Fetching radio by name: {url} with offset {offset} and limit {limit}"
        )
        headers = {"User-Agent": "discord-bot-sebampuero"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=4) as response:
                data = await response.text()
                return json.loads(data)

    async def fetch_radios_by_city(self, offset: int, limit: int, query: str):
        url = f"{self.selected_radio_hostname}/json/stations/bystateexact/{query}?offset={offset}&limit={limit}&hidebroken=true"
        logger.info(
            f"Fetching radios by city: {url} with offset {offset} and limit {limit}"
        )
        headers = {"User-Agent": "discord-bot-sebampuero"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=4) as response:
                data = await response.text()
                return json.loads(data)
