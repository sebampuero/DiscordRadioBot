from discord.ext import commands
from dotenv import load_dotenv
import discord
import asyncio
import os

from radio_bot import RadioBotCommander
from logconfig.logging_config import configure_logging, get_logger
from radio_list import RadioListManager

load_dotenv()
configure_logging()
logger = get_logger("radio_discord_bot")


class RadioBot(commands.Bot):

    def __init__(self, command_prefix, description, intents):
        super().__init__(command_prefix=command_prefix, description=description, intents=intents)

    async def background_tasks(self):
        logger.info("Starting background tasks")
        rmanager = RadioListManager()
        while True:
            await rmanager.update_radio_hostname()
            await asyncio.sleep(600)
        
    async def setup_hook(self):
        self.bg_task = self.loop.create_task(self.background_tasks())

intents = discord.Intents.all()
intents.message_content = True
bot = RadioBot(command_prefix=commands.when_mentioned_or("!"),
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
    radio_bot = RadioBotCommander(bot)
    
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