import random
from discord.ext import commands
from dotenv import load_dotenv
import discord
import asyncio
import os

from utils.network_utils import get_radiobrowser_base_urls
from radio_bot import RadioBot
from logconfig.logging_config import configure_logging, get_logger
import radio_list

load_dotenv()
configure_logging()
logger = get_logger("radio_discord_bot")

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    description='Radio bot',
    intents=intents,
)

@bot.event
async def on_ready():
    logger.info("Bot is ready and logged in")

async def main():
    token = os.getenv("TOKEN")
    if token is None:
        logger.error("Discord TOKEN not found in environment variables")
        return

    logger.info("Initializing radio bot")
    radio_bot = RadioBot(bot)
    
    logger.info("Checking if radio browser ips are reachable...")
    urls = get_radiobrowser_base_urls()
    if urls: #TODO: add background job that checks if the urls are reachable and update selected url?
        random.shuffle(urls)
        radio_list.selected_radio_browser_hostname = urls[0]
        logger.info(f"Using {radio_list.selected_radio_browser_hostname} as radio browser hostname")
    else:
        logger.warn(f"No reachable radio browser IPs found! Using default {radio_list.ALL_API_RADIO_BROWSER_HOSTNAME}")
        logger.warn("This may not work!")
        radio_list.selected_radio_browser_hostname = radio_list.ALL_API_RADIO_BROWSER_HOSTNAME
    async with bot:
        await bot.add_cog(radio_bot)
        logger.info("Starting bot")
        await bot.start(token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except discord.LoginFailure:
        logger.error("Invalid token provided")
    except discord.HTTPException as e:
        logger.error(f"HTTP error occurred: {e}")
    except Exception as e:
        logger.exception("Unexpected error occurred", exc_info=e)