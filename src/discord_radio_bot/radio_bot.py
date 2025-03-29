from discord.ext import commands
from logconfig.logging_config import get_logger
from radio_list import fetch_radio_by_name, fetch_radios_by_city
import discord
import asyncio

logger = get_logger("radio_discord_bot")

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
            await interaction.response.edit_message(content=f"Reproduciendo: {self.radio['name']}", view=None)
            await self.cog.play_radio(self.radio['url_resolved'], member.voice.channel)
        else:
            await interaction.response.edit_message(content="No estas en canal de voz, animal de mierda", view=None)

class NextPrevButton(discord.ui.Button):
    def __init__(self, label: str, *, calling_cog: commands.Cog, query: str, is_next_btn: bool):
        super().__init__(label=label)
        self.cog = calling_cog
        self.query = query
        self.is_next_btn = is_next_btn
    
    async def callback(self, interaction):
        if self.is_next_btn:
            self.view.current_page += 1
        else:
            self.view.current_page -= 1
        if self.view.current_page == -1:
            self.view.remove_item(self)
            await interaction.response.edit_message(view=self.view)
        select_buttons = self.view.children[:self.cog.RADIOS_PER_PAGE]
        radios = await fetch_radios_by_city(self.view.current_page * self.cog.RADIOS_PER_PAGE,self.cog.RADIOS_PER_PAGE,self.query)
        if len(radios) == 0:
            self.view.remove_item(self)
            await interaction.response.edit_message(view=self.view)
        options_txt = ""
        for i in range(0, len(radios)):
            select_buttons[i].radio = radios[i]
            select_buttons[i].calling_cog = self.cog
            select_buttons[i].label = (i+1) + self.cog.RADIOS_PER_PAGE * self.view.current_page
            options_txt += f"{(i+1) + self.cog.RADIOS_PER_PAGE * self.view.current_page}: {radios[i]['name']}\n"
        await interaction.response.edit_message(content=f"Radios para {self.query}:\n{options_txt}", view=self.view)

class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.current_page = 0

class RadioBot(commands.Cog):

    RADIOS_PER_PAGE = 5
    VOLUME = 0.1

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
        volume_adjusted_source = discord.PCMVolumeTransformer(audio_source, volume=self.VOLUME)
        self.current_voice_client.play(volume_adjusted_source, after=None)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if before.channel and after.channel == None and self.current_voice_client and self.current_voice_client.channel == before.channel:
            left_members = [member for member in before.channel.members if not member.bot]
            if len(left_members) == 0:
                self.disconnect()

    @commands.command(name="radio-ciudad")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def get_radios_by_city(self, ctx: commands.Context, query: str): #TODO: add check if user is in a voice channel
        '''
        !radio-ciudad [ciudad] => muestra todas las radios en esta ciudad
        '''
        view = Buttons()
        try:
            radios = await fetch_radios_by_city(0,self.RADIOS_PER_PAGE,query)
        except asyncio.TimeoutError as e:   
            logger.error(f"Timeout error: {e} when fetching radios by city {query}")
            await ctx.send(f"No pude buscar radios de {query}, sorry, intenta despues, ctm")
            return
        options_txt = ""
        for i in range(0,len(radios)):
            btn = SelectButton(str(i+1), radios[i], self)
            view.add_item(btn)
            options_txt += f"{i+1}: {radios[i]['name']}\n"
        view.add_item(NextPrevButton("Previo", calling_cog=self, query=query, is_next_btn=False))
        view.add_item(NextPrevButton("Siguiente", calling_cog=self, query=query, is_next_btn=True))
        if len(radios) > 0:
            await ctx.send(f"Radios para {query}:\n{options_txt}", view=view)
        else:
            await ctx.send(f"No hay radios para {query}")

    @commands.command(name="radio")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def get_radio_by_name(self, ctx: commands.Context, *query: str):
        '''
        !radio [nombre] => muestra radios con este nombre
        '''
        view = Buttons()
        query = ' '.join(query)
        try:
            radios = await fetch_radio_by_name(query)
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error: {e} when fetching radios by name {query}")
            await ctx.send(f"TU internet es una mierda, intenta despues")
            return
        options_txt = ""
        for i in range(0, len(radios)):
            btn = SelectButton(str(i+1), radios[i], self)
            view.add_item(btn)
            options_txt += f"{i+1}: {radios[i]['name']} - {radios[i]['state']},{radios[i]['country']}\n"
        if len(radios) > 0:
            await ctx.send(f"Radios con nombres parecidos a '{query}':\n{options_txt}", view=view)
        else:
            await ctx.send(f"No hay radios con nombre '{query}'")

    @commands.command()
    async def stop(self, ctx: commands.Context):
        '''
        !stop => desconecta el bot
        '''
        if ctx.author.voice.channel:
            self.disconnect()
