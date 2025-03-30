from typing import Any, Coroutine
from discord.ext import commands
from logconfig.logging_config import get_logger
from radio_list import RadioListManager
import discord
import asyncio

logger = get_logger("radio_discord_bot")


RADIOS_PER_PAGE = 5
VOLUME = 0.1
class SelectButton(discord.ui.Button):
    def __init__(self, label: str, radio: dict, calling_cog: commands.Cog):
        super().__init__(label=label)
        self.radio  = radio
        self.cog = calling_cog
    
    async def callback(self, interaction):
        guild = self.cog.bot.get_guild(interaction.guild_id)
        member = guild.get_member_named(interaction.user.name)
        logger.info(f"Going to play: {self.radio['name']}")
        if member.voice:
            await interaction.response.edit_message(content=f"Playing: {self.radio['name']}", view=None)
            await self.cog.play_radio(self.radio['url_resolved'], member.voice.channel)
        else:
            await interaction.response.edit_message(content="You're not in a voice channel, bitch", view=None)


class NextButton(discord.ui.Button):
    def __init__(self, label: str, *, calling_cog: commands.Cog, query: str, radios_caller: Coroutine[Any, Any, None]):
        super().__init__(label=label)
        self.cog = calling_cog
        self.query = query
        self.radios_caller = radios_caller

    async def callback(self, interaction):
        self.view.update_current_page(self.view.current_page + 1)
        select_buttons = self.view.children[:RADIOS_PER_PAGE]
        radios = await self.radios_caller(self.view.current_page * RADIOS_PER_PAGE,RADIOS_PER_PAGE,self.query)
        options_txt = ""
        for i in range(0, len(radios)):
            select_buttons[i].radio = radios[i]
            select_buttons[i].calling_cog = self.cog
            select_buttons[i].label = (i+1) + RADIOS_PER_PAGE * self.view.current_page
            options_txt += f"{(i+1) + RADIOS_PER_PAGE * self.view.current_page}: {radios[i]['name']}\n"
        await interaction.response.edit_message(content=f"Radios for {self.query}:\n{options_txt}", view=self.view)



class PrevButton(discord.ui.Button):
    def __init__(self, label: str, *, calling_cog: commands.Cog, query: str, radios_caller: Coroutine[Any, Any, None]):
        super().__init__(label=label)
        self.cog = calling_cog
        self.query = query
        self.radios_caller = radios_caller
    
    async def callback(self, interaction):
        self.view.update_current_page(self.view.current_page - 1)
        select_buttons = self.view.children[:RADIOS_PER_PAGE]
        radios = await self.radios_caller(self.view.current_page * RADIOS_PER_PAGE,RADIOS_PER_PAGE,self.query)
        options_txt = ""
        for i in range(0, len(radios)):
            select_buttons[i].radio = radios[i]
            select_buttons[i].calling_cog = self.cog
            select_buttons[i].label = (i+1) + RADIOS_PER_PAGE * self.view.current_page
            options_txt += f"{(i+1) + RADIOS_PER_PAGE * self.view.current_page}: {radios[i]['name']}\n"
        await interaction.response.edit_message(content=f"Radios for {self.query}:\n{options_txt}", view=self.view)

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180, radios_callback: Coroutine[Any, Any, None], query: str):
        super().__init__(timeout=timeout)
        self.current_page = 0
        self.radios_api_callback = radios_callback
        self.total_size_of_radios = 0
        self.query = query

    def update_current_page(self, page: int):
        logger.debug(f"Updating current page to {page}")
        self.current_page = page
        if self.current_page == 0 and self.total_size_of_radios > RADIOS_PER_PAGE and not any(isinstance(item, NextButton) for item in self.children):
            self.add_item(NextButton("Next", calling_cog=self, query=self.query, radios_caller=self.radios_api_callback))
        if self.current_page > 0 and not any(isinstance(item, PrevButton) for item in self.children):
            self.add_item(PrevButton("Previous", calling_cog=self, query=self.query, radios_caller=self.radios_api_callback))
        if self.current_page == 0:
            [self.remove_item(item)  for item in self.children if isinstance(item, PrevButton)]
        if (self.current_page + 1) * RADIOS_PER_PAGE > self.total_size_of_radios:
            [self.remove_item(item) for item in self.children if isinstance(item, NextButton)]
        if (self.current_page + 1) * RADIOS_PER_PAGE < self.total_size_of_radios and not any(isinstance(item, NextButton) for item in self.children):
            self.add_item(NextButton("Next", calling_cog=self, query=self.query, radios_caller=self.radios_api_callback))

class RadioBotCommander(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.current_voice_client = None

    def disconnect(self):
        if len(self.bot.voice_clients) > 0:
            voice_client = self.bot.voice_clients[0]
            asyncio.run_coroutine_threadsafe(voice_client.disconnect(), self.bot.loop)
        self.current_voice_client = None

    async def play_radio(self, radio_url: str, voice_channel: discord.VoiceChannel):
        if not self.current_voice_client:
            voice_client = await voice_channel.connect()
            self.current_voice_client = voice_client
        self.current_voice_client.stop()
        audio_source = discord.FFmpegPCMAudio(radio_url)
        volume_adjusted_source = discord.PCMVolumeTransformer(audio_source, volume=VOLUME)
        self.current_voice_client.play(volume_adjusted_source, after=None)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel and after.channel == None and self.current_voice_client and self.current_voice_client.channel == before.channel:
            left_members = [member for member in before.channel.members if not member.bot]
            if len(left_members) == 0:
                self.disconnect()

    @commands.command(name="radio-city")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def get_radios_by_city(self, ctx: commands.Context, query: str):
        '''
        !radio-city [city] => shows all radios in this city
        '''
        if not query:
            return
        view = Buttons(radios_callback=RadioListManager().fetch_radios_by_city, query=query)
        message = await ctx.send("Fetching radios...")
        try:
            radios = await RadioListManager().fetch_radios_by_city(0,RADIOS_PER_PAGE,query)
            all_radios = await RadioListManager().fetch_all_radios_by_city(query)
            view.total_size_of_radios = len(all_radios)
        except asyncio.TimeoutError as e:   
            logger.error(f"Timeout error: {e} when fetching radios by city {query}")
            await message.edit("Having network issues, try again later gogigagagagigo")
            return
        
        options_txt = ""
        for i in range(0,len(radios)):
            btn = SelectButton(str(i+1), radios[i], self)
            view.add_item(btn)
            options_txt += f"{i+1}: {radios[i]['name']}\n"
        view.update_current_page(0)
        if len(radios) > 0:
            await message.edit(content=f"Radios for {query}:\n{options_txt}", view=view)
        else:
            await message.edit(content=f"No radios for {query}")

    @commands.command(name="radio")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def get_radio_by_name(self, ctx: commands.Context, *query: str):
        '''
        !radio [name] => shows radios with this name
        '''
        query = ' '.join(query)
        if not query:
            return
        view = Buttons(radios_callback=RadioListManager().fetch_radio_by_name, query=query)
        message = await ctx.send("Fetching radios...")
        try:
            radios = await RadioListManager().fetch_radio_by_name(0,RADIOS_PER_PAGE,query)
            all_radios = await RadioListManager().fetch_all_radios_by_name(query)
            view.total_size_of_radios = len(all_radios)
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error: {e} when fetching radios by name {query}")
            await message.edit(content="Having network issues, try again later gogigagagagigo")
            return
        options_txt = ""
        for i in range(0, len(radios)):
            btn = SelectButton(str(i+1), radios[i], self)
            view.add_item(btn)
            options_txt += f"{i+1}: {radios[i]['name']} - {radios[i]['state']},{radios[i]['country']}\n"
        view.update_current_page(0)
        if len(radios) > 0:
            await message.edit(content=f"Radios found: '{query}':\n{options_txt}", view=view)
        else:
            await message.edit(content=f"No radios with name '{query}'")

    @commands.command()
    async def stop(self, ctx: commands.Context):
        '''
        !stop => disconnects the bot
        '''
        if ctx.author.voice.channel:
            self.disconnect()
