import discord
import database
from translations import translate
import asyncio

intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    
@bot.event
async def on_member_join(member):
    
    await asyncio.sleep(2)
    
    channel = bot.get_channel(1295704772623601674)
    welcome_message_en = translate('en', 'welcome_message', dc_username=member.mention)
    welcome_message_lt = translate('lt', 'welcome_message', dc_username=member.mention)
    
    embed = discord.Embed(title="Welcome! // Sveiki!", color=discord.Color.blue())
    embed.add_field(name="English", value=welcome_message_en, inline=False)
    embed.add_field(name="Lietuvių", value=welcome_message_lt, inline=False)
    
    await channel.send(embed=embed)
    
    view = discord.ui.View()
    english_button = discord.ui.Button(label='English', style=discord.ButtonStyle.primary)
    lithuanian_button = discord.ui.Button(label='Lietuvių', style=discord.ButtonStyle.primary)

    async def english_callback(interaction: discord.Interaction):
        modal = NameInputModal(language='en', member=member)
        await interaction.response.send_modal(modal)

    async def lithuanian_callback(interaction: discord.Interaction):
        modal = NameInputModal(language='lt', member=member)
        await interaction.response.send_modal(modal)

    english_button.callback = english_callback
    lithuanian_button.callback = lithuanian_callback

    view.add_item(english_button)
    view.add_item(lithuanian_button)

    await channel.send(view=view) 

class NameInputModal(discord.ui.Modal):
    def __init__(self, language: str, member: discord.Member):
        self.language = language
        self.member = member
        super().__init__(title=translate(self.language, 'name_prompt'))

        self.add_item(discord.ui.InputText(
            label=translate(self.language, 'name_prompt'),
            placeholder=translate(self.language, 'name_placeholder'),
            required=True,
        ))

    async def callback(self, interaction: discord.Interaction):
        name = self.children[0].value

        if database.is_user_registered(self.member.name):
            embed = discord.Embed(
            title=translate(self.language, 'registration'),
            description=translate(self.language, 'already_registered'),
            color=discord.Color.red() 
        )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.assign_role()
            await self.close_welcome_channel_and_redirect()
            return

        success, msg = database.register_user(name, self.member.name, self.language)
        
        if success:
            embed = discord.Embed(
            title=translate(self.language, 'registration'),
            description=translate(self.language, 'registration_success', name=name, dc_username=self.member.name),
            color=discord.Color.green()
        )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.assign_role()
            await self.close_welcome_channel_and_redirect()    
        else:
            embed = discord.Embed(
            title=translate(self.language, 'registration'),
            description=translate(self.language, 'registration_error'),
            color=discord.Color.red()
        )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
    async def assign_role(self):
        if self.language == 'en':
            role_id = 1295702840240504883
        elif self.language == 'lt':
            role_id = 1295703339756949545

        role = self.member.guild.get_role(role_id)
        if role:
            await self.member.add_roles(role)

    async def close_welcome_channel_and_redirect(self):

        general_channel = self.member.guild.get_channel(1288951632200990886)

        await asyncio.sleep(2)

        welcome_embed = discord.Embed(
            title=translate(self.language, 'welcome_title'),
            description=translate(self.language, 'welcome', name=self.member.mention), 
            color=discord.Color.green() 
        )
        
        await general_channel.send(embed=welcome_embed)

@bot.slash_command(guild_ids=[1288951632200990881])
async def hello(ctx):
    await ctx.respond('hi', ephemeral=True)

@bot.slash_command(guild_ids=[1288951632200990881])
async def get_user_by_name(ctx, name: str):
    
    await ctx.defer(ephemeral=True)
    
    user_language = database.get_user_language(ctx.author.name)
    user_data = database.get_user_by_name(name)
    
    if not user_data:  
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'no_such_user', name=name),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    user_embed = discord.Embed(
            title=translate(user_language, 'user_data'),
            color=discord.Colour.blue(),
    )
    user_embed.add_field(name=translate(user_language, 'name'), value=user_data['name'], inline=True)
    user_embed.add_field(name=translate(user_language, 'discord_username'), value=user_data['dc_username'], inline=True)
    user_embed.add_field(name=translate(user_language, 'gold'), value=user_data['gold'], inline=True)
    user_embed.add_field(name=translate(user_language, 'registration_date'), value=user_data['registration_date'].strftime('%Y-%m-%d %H:%M:%S'), inline=True)
    await ctx.followup.send(embed=user_embed, ephemeral=True)

@bot.slash_command(guild_ids=[1288951632200990881])
async def add_gold(ctx, name: str, amount: int, reason: str):
    
    await ctx.defer(ephemeral=True)
    
    user_language = database.get_user_language(ctx.author.name)
    
    if not database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    success, msg = database.add_gold(ctx.author.name, name, amount, reason)
    if not success:
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=msg,
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    gold_embed = discord.Embed(
            title=translate(user_language, "gold_added_successfully"),
            color=discord.Colour.green(),
    )
    gold_embed.add_field(name=translate(user_language, 'name'), value=name, inline=True)
    gold_embed.add_field(name=translate(user_language, 'amount'), value=amount, inline=True)
    gold_embed.add_field(name=translate(user_language, 'reason'), value=reason, inline=True)
    gold_embed.add_field(name=translate(user_language, "new_total_gold"), value=msg, inline=True)
    await ctx.followup.send(embed=gold_embed, ephemeral=True)

@bot.slash_command(guild_ids=[1288951632200990881])
async def remove_gold(ctx, name: str, amount: int, reason: str):
    
    await ctx.defer(ephemeral=True)
    
    user_language = database.get_user_language(ctx.author.name)
    
    if not database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    success, msg = database.remove_gold(ctx.author.name, name, amount, reason)
    if not success:
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=msg,
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    gold_embed = discord.Embed(
            title=translate(user_language, 'gold_removed_successfully'),
            color=discord.Colour.green(),
    )
    gold_embed.add_field(name=translate(user_language, 'name'), value=name, inline=True)
    gold_embed.add_field(name=translate(user_language, 'amount'), value=amount, inline=True)
    gold_embed.add_field(name=translate(user_language, 'reason'), value=reason, inline=True)
    gold_embed.add_field(name=translate(user_language, 'new_total_gold'), value=msg, inline=True)
    await ctx.followup.send(embed=gold_embed, ephemeral=True)

@bot.slash_command(guild_ids=[1288951632200990881])
async def register_user(ctx, name: str, dc_username: str, language: str):
    
    await ctx.defer(ephemeral=True)
    
    user_language = database.get_user_language(ctx.author.name)
    invoking_user_dc_username = ctx.author.name
    
    if not database.is_authorized(invoking_user_dc_username): 
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'user_is_not_authorized'),
            color=discord.Color.red() 
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return
    
    if language not in ['lt', 'en']:
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'invalid_language'),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return
    
    member = discord.utils.get(ctx.guild.members, name=dc_username)
    
    if member is None:
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'no_such_user', name=dc_username),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return
    
    if database.is_user_registered(dc_username):
        
        if await user_has_role(member, language):
            embed = discord.Embed(
                title=translate(user_language, 'registration'),
                description=translate(user_language, 'user_is_already_registered', dc_username=dc_username),
                color=discord.Color.red()
            )
            await ctx.followup.send(embed=embed, ephemeral=True)
            return
        else:
            await assign_role(member, language)
            embed = discord.Embed(
                title=translate(user_language, 'registration'),
                description=translate(user_language, 'role_assigned', name=dc_username),
                color=discord.Color.green()
            )
            await ctx.followup.send(embed=embed, ephemeral=True)
            return
    
    success, msg = database.register_user(name, dc_username, language)
    if not success:
        await ctx.followup.send(msg, ephemeral=True) 
        return
    embed = discord.Embed(
        title=translate(user_language, 'registration'), 
        description=translate(user_language, 'registration_success', name=name, dc_username=dc_username),
        color=discord.Color.green()
    )
    await ctx.followup.send(embed=embed, ephemeral=True)
    await assign_role(member, language)
    await close_welcome_channel_and_redirect(member, language)
    
async def user_has_role(member: discord.Member, language: str) -> bool:
    if language == 'lt':
        role_id = 1295703339756949545
    elif language == 'en':
        role_id = 1295702840240504883
    else: 
        return False

    role = member.guild.get_role(role_id)
    return role in member.roles
    
async def assign_role(member: discord.Member, language: str):
    
    verified_role_id_lt = 1295703339756949545
    verified_role_id_en = 1295702840240504883

    if language == 'lt':
        role_id = verified_role_id_lt
    else:
        role_id = verified_role_id_en

    role = member.guild.get_role(role_id)
    await member.add_roles(role)
        
async def close_welcome_channel_and_redirect(member: discord.Member, language: str):
    
    general_channel_id = 1288951632200990886 

    general_channel = member.guild.get_channel(general_channel_id)

    await asyncio.sleep(2)

    welcome_embed = discord.Embed(
        title=translate(language, 'welcome_title'),
        description=translate(language, 'welcome', name=member.mention),
        color=discord.Color.green()
    )
    
    await general_channel.send(embed=welcome_embed)
    
    
@bot.slash_command(guild_ids=[1288951632200990881])
async def list_users(ctx):
    
    await ctx.defer(ephemeral=True)
    
    user_language = database.get_user_language(ctx.author.name)
    
    if not database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    users = database.get_all_users()
    pages = 5 
    total_users = len(users)

    if total_users == 0:
        await ctx.followup.send(translate(user_language, 'no_registered_users'), ephemeral=True)
        return

    num_pages = (total_users + pages - 1) // pages
    cur_page = 0

    def create_embed(page):
        start = page * pages
        end = start + pages
        user_data = users[start:end]

        embed = discord.Embed(title=translate(user_language, 'user_list', page=page + 1, num_pages=num_pages),
        color=discord.Color.blue())
        for index, user in enumerate(user_data, start=start + 1):
            embed.add_field(
                name=f"{index}. {user['name']}", 
                value=f"**{translate(user_language, 'discord_username')}:** {user['dc_username']}\n"
                      f"**{translate(user_language, 'gold')}:** {user['gold']}", 
                inline=False
            )
        
        return embed

    message = await ctx.followup.send(embed=create_embed(cur_page), ephemeral=True)

    previous_button = discord.ui.Button(label=translate(user_language, 'previous_button'), style=discord.ButtonStyle.primary, disabled=True)
    next_button = discord.ui.Button(label=translate(user_language, 'next_button'), style=discord.ButtonStyle.primary)

    view = discord.ui.View()
    view.add_item(previous_button)
    view.add_item(next_button)

    def update_buttons():
        previous_button.disabled = cur_page == 0
        next_button.disabled = cur_page >= num_pages - 1

    update_buttons() 

    async def button_callback(interaction: discord.Interaction):
        nonlocal cur_page 
        if interaction.user != ctx.author:
            await interaction.response.send_message(translate(user_language, 'not_your_button'), ephemeral=True)
            return

        if interaction.data['custom_id'] == "next_button":
            if cur_page < num_pages - 1:
                cur_page += 1
        elif interaction.data['custom_id'] == "previous_button":
            if cur_page > 0:
                cur_page -= 1

        await message.edit(embed=create_embed(cur_page))
        update_buttons() 
        await interaction.response.edit_message(view=view) 

    previous_button.callback = button_callback
    previous_button.custom_id = "previous_button"
    next_button.callback = button_callback
    next_button.custom_id = "next_button"

    await message.edit(view=view)

@bot.slash_command(guild_ids=[1288951632200990881])    
async def help(ctx):
    
    await ctx.defer(ephemeral=True)
    
    user_language = database.get_user_language(ctx.author.name)
    invoking_user_dc_username = ctx.author.name

    help_embed = discord.Embed(
        title=translate(user_language, 'available_commands'),
        description=translate(user_language, 'here_are_commands'),
        color=discord.Colour.blue(),
    )

    # NON-ADMIN
    help_embed.add_field(name="/hello", value="Says hi.", inline=False)
    help_embed.add_field(name="/get_user_by_name", value=translate(user_language, 'get_user_by_name_description'), inline=False)

    if database.is_authorized(invoking_user_dc_username):
        # ADMIN
        help_embed.add_field(name="/add_gold", value=translate(user_language, 'add_gold_description'), inline=False)
        help_embed.add_field(name="/remove_gold", value=translate(user_language, 'remove_gold_description'), inline=False)
        help_embed.add_field(name="/list_users", value=translate(user_language, 'list_users_description'), inline=False)
        help_embed.add_field(name="/register_user", value=translate(user_language, 'register_user_description'), inline=False)

    await ctx.followup.send(embed=help_embed, ephemeral=True)


bot.run("MTI4ODk1MTgyMTkxNzg4NDQ0Ng.GJp8HR.AhbEBj7XgP5YDu_jV7ngeOM4xJilbEPMFJfQRM")