import discord
from discord.ext import commands
import database
from translations import translate
import asyncio
from catalog import activities, orienteering_stops
import traceback

intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    
@bot.event
async def on_member_join(member):
    
    #await asyncio.sleep(2)
    
    channel = bot.get_channel(1295704772623601674)
    welcome_message_en = translate('en', 'welcome_message', dc_username=member.mention)
    welcome_message_lt = translate('lt', 'welcome_message', dc_username=member.mention)
    
    embed = discord.Embed(title="Welcome! // Sveiki!", color=discord.Color.gold())
    embed.add_field(name="English", value=welcome_message_en, inline=False)
    embed.add_field(name="Lietuvių", value=welcome_message_lt, inline=False)
    embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")
    embed.set_footer(text="If you are having problems registering contact the admins or moderators")
    
    await channel.send(embed=embed)
    
    view = discord.ui.View()
    english_button = discord.ui.Button(label='English', style=discord.ButtonStyle.primary)
    lithuanian_button = discord.ui.Button(label='Lietuvių', style=discord.ButtonStyle.primary)

    async def english_callback(interaction: discord.Interaction):
        if interaction.user != member:
            await interaction.response.send_message("**This button is not for you!**", ephemeral=True)
            return
        modal = NameInputModal(language='en', member=member)
        await interaction.response.send_modal(modal)

    async def lithuanian_callback(interaction: discord.Interaction):
        if interaction.user != member:
            await interaction.response.send_message("**Šis mygtukas skirtas ne tau!**", ephemeral=True)
            return
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
        await interaction.response.defer(ephemeral=True) 
        name = self.children[0].value

        if await database.is_user_registered(self.member.name):
            embed = discord.Embed(
            title=translate(self.language, 'registration'),
            description=translate(self.language, 'already_registered'),
            color=discord.Color.red() 
        )
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.assign_role()
            return

        success, msg = await database.register_user(name, self.member.name, self.language)
        
        if success:
            embed = discord.Embed(
            title=translate(self.language, 'registration'),
            description=translate(self.language, 'registration_success', name=name, dc_username=self.member.name),
            color=discord.Color.green()
        )
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.assign_role()
            await self.close_welcome_channel_and_redirect()    
        else:
            embed = discord.Embed(
            title=translate(self.language, 'registration'),
            description=translate(self.language, 'registration_error'),
            color=discord.Color.red()
        )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
    async def assign_role(self):
        if self.language == 'en':
            role_id = 1295702840240504883
        elif self.language == 'lt':
            role_id = 1295703339756949545

        role = self.member.guild.get_role(role_id)
        if role:
            await self.member.add_roles(role)

    async def close_welcome_channel_and_redirect(self):

        general_channel = self.member.guild.get_channel(1297609655261990944) 
        
        await asyncio.sleep(2)

        welcome_embed = discord.Embed(
            title=translate(self.language, 'welcome_title'),
            description=translate(self.language, 'welcome1', name=self.member.mention) +
                        translate(self.language, 'welcome2') +
                        translate(self.language, 'welcome3'),
            color=discord.Color.from_rgb(212, 184, 146) 
        )
        
        welcome_embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")
        
        await general_channel.send(embed=welcome_embed)

@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def hello(ctx):
    await ctx.respond('hi', ephemeral=True)

@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def get_user_by_name(ctx, user: discord.Option(discord.Member)):
    
    await ctx.defer(ephemeral=True)
    name = user.name
    user_language = await database.get_user_language(ctx.author.name)
    user_data = await database.get_user_by_name(name)
    
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
            color=discord.Colour.gold(),
    )
    user_embed.add_field(name=translate(user_language, 'name'), value=user_data['name'], inline=True)
    user_embed.add_field(name=translate(user_language, 'discord_username'), value=user_data['dc_username'], inline=True)
    user_embed.add_field(name=translate(user_language, 'gold'), value=user_data['gold'], inline=True)
    user_embed.add_field(name=translate(user_language, 'registration_date'), value=user_data['registration_date'].strftime('%Y-%m-%d %H:%M:%S'), inline=True)
    user_embed.add_field(name=translate(user_language, 'orienteering_team'), value=user_data['team'], inline=True)
    await ctx.followup.send(embed=user_embed, ephemeral=True)

@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def add_gold(ctx, user: discord.Option(discord.Member), amount: int, reason: discord.Option(str, choices=activities)):
    
    await ctx.defer(ephemeral=True)
    name = user.name  
    user_language = await database.get_user_language(ctx.author.name)
    
    if not await database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    success, msg = await database.add_gold(ctx.author.name, name, amount, reason, user_language)
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
#@commands.cooldown(1, 2, commands.BucketType.user)
async def remove_gold(ctx, user: discord.Option(discord.Member), amount: int, reason: str):
    
    await ctx.defer(ephemeral=True)
    name = user.name
    user_language = await database.get_user_language(ctx.author.name)
    
    if not await database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    success, msg = await database.remove_gold(ctx.author.name, name, amount, reason, user_language)
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
#@commands.cooldown(1, 2, commands.BucketType.user)
async def register_user(ctx, name: str, dc_username: str, language: str):
    
    await ctx.defer(ephemeral=True)
    
    user_language = await database.get_user_language(ctx.author.name)
    invoking_user_dc_username = ctx.author.name
    
    if not await database.is_authorized(invoking_user_dc_username): 
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
    
    if await database.is_user_registered(dc_username):
        
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
    
    success, msg = await database.register_user(name, dc_username, language)
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
    
    general_channel_id = 1297609655261990944 

    general_channel = member.guild.get_channel(general_channel_id)

    await asyncio.sleep(2)

    welcome_embed = discord.Embed(
        title=translate(language, 'welcome_title'),
        description=translate(language, 'welcome1', name=member.mention) +
                    translate(language, 'welcome2') +
                    translate(language, 'welcome3'),
        color=discord.Color.from_rgb(212, 184, 146) 
    )
    await general_channel.send(embed=welcome_embed)
    
    
@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def list_users(ctx):
    
    await ctx.defer(ephemeral=True)
    
    user_language = await database.get_user_language(ctx.author.name)
    
    if not await database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    users = await database.get_all_users()
    users = sorted(users, key=lambda x: x['gold'], reverse=True)
    
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
#@commands.cooldown(1, 2, commands.BucketType.user)
async def help(ctx):
    
    await ctx.defer(ephemeral=True)
    
    user_language = await database.get_user_language(ctx.author.name)
    invoking_user_dc_username = ctx.author.name

    help_embed = discord.Embed(
        title=translate(user_language, 'available_commands'),
        description=translate(user_language, 'here_are_commands'),
        color=discord.Colour.from_rgb(139, 69, 19),
    )

    # NON-ADMIN
    help_embed.add_field(name="/hello", value="Says hi.", inline=False)
    help_embed.add_field(name="/event", value=translate(user_language, 'event_description'))
    help_embed.add_field(name="/event_program", value=translate(user_language, 'event_program_description'), inline=False)
    help_embed.add_field(name="/get_user_by_name", value=translate(user_language, 'get_user_by_name_description'), inline=False)
    help_embed.add_field(name="/view_shop", value=translate(user_language, 'view_shop_description'), inline=False)
    help_embed.add_field(name="/balance", value=translate(user_language, 'balance_command_description'), inline=False)
    help_embed.add_field(name="/show_activities", value=translate(user_language, 'show_activities_description'), inline=False)
    help_embed.add_field(name="/create_orienteering_team", value=translate(user_language, 'create_team_description'), inline=False)
    help_embed.add_field(name="/invite_to_orienteering_team", value=translate(user_language, 'invite_team_description'), inline=False)
    help_embed.add_field(name="/join_orienteering_team", value=translate(user_language, 'join_team_description'), inline=False)
    help_embed.add_field(name="/leave_orienteering_team", value=translate(user_language, 'leave_team_description'), inline=False)
    help_embed.add_field(name="/get_team_by_name", value=translate(user_language, 'get_team_by_name_description'), inline=False)


    if await database.is_authorized(invoking_user_dc_username):
        # ADMIN
        help_embed.add_field(name="/add_gold", value=translate(user_language, 'add_gold_description'), inline=False)
        help_embed.add_field(name="/remove_gold", value=translate(user_language, 'remove_gold_description'), inline=False)
        help_embed.add_field(name="/list_users", value=translate(user_language, 'list_users_description'), inline=False)
        help_embed.add_field(name="/register_user", value=translate(user_language, 'register_user_description'), inline=False)
        help_embed.add_field(name="/get_user_transactions", value=translate(user_language, 'get_user_transactions_description'), inline=False)
        help_embed.add_field(name="/buy_item", value=translate(user_language, 'buy_item_description'), inline=False)
        help_embed.add_field(name="/complete_orienteering_stop", value=translate(user_language, 'complete_orienteering_stop_description'), inline=False)
        help_embed.add_field(name="/change_orienteering_stop", value=translate(user_language, 'change_orienteering_stop_description'), inline=False)

    help_embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")
    
    await ctx.followup.send(embed=help_embed, ephemeral=True)
    
@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def get_user_transactions(ctx, user: discord.Option(discord.Member)):
    await ctx.defer(ephemeral=True)
    dc_username = user.name
    user_language = await database.get_user_language(ctx.author.name)

    if not await database.is_authorized(ctx.author.name):
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return

    transactions = await database.get_user_transactions(dc_username)
    transactions = sorted(transactions, key=lambda x: x['timestamp'], reverse=True)
    transactions_per_page = 10
    total_transactions = len(transactions)

    if total_transactions == 0:
        await ctx.followup.send(translate(user_language, 'no_transactions', dc_username=dc_username), ephemeral=True)
        return

    num_pages = (total_transactions + transactions_per_page - 1) // transactions_per_page
    cur_page = 0

    def create_embed(page):
        start = page * transactions_per_page
        end = start + transactions_per_page
        transactions_page = transactions[start:end]

        embed = discord.Embed(
            title=translate(user_language, 'transactions_user', dc_username=dc_username, page=page + 1, num_pages=num_pages),
            color=discord.Color.blue()
        )
        for index, transaction in enumerate(transactions_page, start=start + 1):
            transaction_type = translate(user_language, 'gold_added')if transaction['transaction_type'] == "add" else translate(user_language, 'gold_removed')
            amount = abs(transaction['amount'])
            embed.add_field(
                name=f"{index}. {transaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {amount} {translate(user_language, 'gold')}",
                value=f"**{translate(user_language, 'sender')}:** {transaction['sender']}\n"
                f"**{transaction_type}:** {amount}\n"
                f"**{translate(user_language, 'reason')}:** {transaction['reason']}", inline=False
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
#@commands.cooldown(1, 2, commands.BucketType.user)
async def event(ctx):
    await ctx.defer(ephemeral=True)
    
    user_language = await database.get_user_language(ctx.author.name)
        
    embed = discord.Embed(
        title=translate(user_language, 'micius_quest'),
        description=translate(user_language, 'event1') + 
                    translate(user_language, 'event2') + 
                    translate(user_language, 'event3') + 
                    translate(user_language, 'event4'), 
        color=discord.Color.gold()
    )

    embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")
    embed.set_image(url="https://i.imgur.com/ezKiTCS.jpeg")
    embed.add_field(name=translate(user_language, 'join_quest'), value=translate(user_language, 'gather_team'), inline=False)
    embed.add_field(name=translate(user_language, 'start_earning_gold'), value=translate(user_language, 'use_command'), inline=False)
    embed.set_footer(text=translate(user_language, 'legend'))

    await ctx.followup.send(embed=embed, ephemeral=True)
    
@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def add_moderator(ctx, member: discord.Member):
    await ctx.defer(ephemeral=True)
    invoking_user_dc_username = ctx.author.name

    if not await database.is_authorized(invoking_user_dc_username):
        embed = discord.Embed(
            title="Permission Denied",
            description="You don't have permission to add moderators.",
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return
    
    if await database.is_authorized(member.name):
        embed = discord.Embed(
            title="Moderator Check",
            description=f"User **{member.mention}** is already a moderator.",
            color=discord.Color.orange()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return

    await database.add_moderator_to_db(member.id, member.name)

    MODERATOR_ROLE_ID = 1296522020078747730
    moderator_role = ctx.guild.get_role(MODERATOR_ROLE_ID)

    if moderator_role:
        await member.add_roles(moderator_role)
        
        embed = discord.Embed(
            title="Moderator Added",
            description=f"**{member.display_name}** has been successfully added as a Moderator.",
            color=discord.Color.green() 
        )
        embed.add_field(name="Assigned Role", value=moderator_role.name, inline=True)
        embed.add_field(name="Moderator ID", value=member.id, inline=True)
        embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")
        embed.set_footer(text="Action performed by: " + ctx.author.display_name)
        
        await ctx.followup.send(embed=embed, ephemeral=True)
      
    
@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def view_shop(ctx):
    user_language = await database.get_user_language(ctx.author.name)
    
    await ctx.defer(ephemeral=True)
    shop_items = await database.get_shop_items(user_language)
    translated_gold = translate(user_language, 'gold1')
    
    shop_list = "\n\n".join([f"**{item}**: {price} {translated_gold}" for item, price in shop_items.items()])
    
    embed = discord.Embed(
        title=translate(user_language, 'available_items'),
        description=shop_list,
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")
    embed.set_footer(text=translate(user_language, 'shop_footer'))
    
    await ctx.followup.send(embed=embed, ephemeral=True)
    
@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def buy_item(ctx, member: discord.Member, item: str):
    user_language = await database.get_user_language(ctx.author.name)
    await ctx.defer(ephemeral=True)

    if not await database.is_authorized(ctx.user.name):
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'user_is_not_authorized'),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return

    shop_items = await database.get_shop_items(user_language)
    
    normalized_item_name = item.lower().strip().replace("**", "")

    matching_item = next((item for item in shop_items if item.lower() == normalized_item_name), None)
    
    if matching_item is None:
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'item_not_found'),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return
    
    item_price = shop_items[matching_item]

    if not await database.is_user_registered(member.name):
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'no_such_user', name=member.name),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return

    if not await database.can_user_afford_item(member.name, item_price):
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'not_enough_gold', name=member.name, item=matching_item),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return

    success, message = await database.buy_item(sender=ctx.user.name, receiver=member.name, item_price=item_price, item_name=matching_item, user_language=user_language)
    
    if success:
        embed = discord.Embed(
            title=translate(user_language, 'success'),
            description=translate(user_language, 'purchase_successfull', name=member.name, item=matching_item, item_price=item_price),
            color=discord.Color.green()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'error'),
            color=discord.Color.red()
        )
        
        await ctx.followup.send(embed=embed, ephemeral=True)
        
@bot.slash_command(guild_ids=[1288951632200990881])     
#@commands.cooldown(1, 2, commands.BucketType.user)   
async def balance(ctx):
    user_language = await database.get_user_language(ctx.author.name)
    await ctx.defer(ephemeral=True) 

    success, user_gold = await database.get_user_balance(ctx.author.name, user_language)

    if not success:
        embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'no_such_user', name=ctx.author.name),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(
        title=translate(user_language, 'balance_title', name=ctx.author.name),
        description=translate(user_language, 'balance_description', gold=user_gold),
        color=discord.Color.gold()
    )
    await ctx.followup.send(embed=embed, ephemeral=True)
    
@bot.slash_command(guild_ids=[1288951632200990881])    
#@commands.cooldown(1, 2, commands.BucketType.user)
async def show_activities(ctx):
    
    await ctx.defer(ephemeral=True)
    user_language = await database.get_user_language(ctx.author.name)
    
    main_activities_embed = discord.Embed(
    title=translate(user_language, 'main_activities'),
    color=discord.Color.gold()
)
    main_activities_embed.add_field(name=translate(user_language, 'photo_wall'), value=translate(user_language, 'photo_wall_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'monster'), value=translate(user_language, 'monster_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'horseshoe_throw'), value=translate(user_language, 'horseshoe_throw_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'cactus'), value=translate(user_language, 'cactus_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'catching_micius'), value=translate(user_language, 'catching_micius_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'apple_bobbing'), value=translate(user_language, 'apple_bobbing_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'wild_west_duel'), value=translate(user_language, 'wild_west_duel_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'cup_pyramid_shooting'), value=translate(user_language, 'cup_pyramid_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'shoot_a_line_of_cups'), value=translate(user_language, 'line_cups_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'target_shooting'), value=translate(user_language, 'target_shooting_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'shoot_apple_from_head'), value=translate(user_language, 'apple_from_head_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'gold_searching'), value=translate(user_language, 'gold_searching_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'horse_tail'), value=translate(user_language, 'horse_tail_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'dancing'), value=translate(user_language, 'dancing_description'), inline=False)
    main_activities_embed.add_field(name=translate(user_language, 'escape_room'), value=translate(user_language, 'escape_room_description'), inline=False)
    main_activities_embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")


    await ctx.followup.send(embed=main_activities_embed, ephemeral=True)

    additional_activities_embed = discord.Embed(
        title=translate(user_language, 'additional_activities'),
        color=discord.Color.gold()
    )

    additional_activities_embed.add_field(name=translate(user_language, 'bull'), value=translate(user_language, 'bull_description'), inline=False)
    additional_activities_embed.add_field(name=translate(user_language, 'trivia'), value=translate(user_language, 'trivia_description'), inline=False)

    additional_activities_embed.add_field(name=translate(user_language, 'karaoke'), value=translate(user_language, 'karaoke_description'), inline=False)
    additional_activities_embed.add_field(name=translate(user_language, 'sack_jumping_race'), value=translate(user_language, 'sack_jumping_description'), inline=False)
    additional_activities_embed.add_field(name=translate(user_language, 'treasure_hunt'), value=translate(user_language, 'treasure_hunt_description'), inline=False)
    additional_activities_embed.add_field(name=translate(user_language, 'poker'), value=translate(user_language, 'poker_description'), inline=False)
    additional_activities_embed.add_field(name=translate(user_language, 'blackjack'), value=translate(user_language, 'blackjack_description'), inline=False)
    additional_activities_embed.add_field(name=translate(user_language, 'just_dance'), value=translate(user_language, 'just_dance_description'), inline=False)
    additional_activities_embed.add_field(name=translate(user_language, 'lecturer_interview'), value=translate(user_language, 'lecturer_interview_description'), inline=False)
    additional_activities_embed.add_field(name=translate(user_language, 'film'), value=translate(user_language, 'film_description'), inline=False)
    additional_activities_embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")


    await ctx.followup.send(embed=additional_activities_embed, ephemeral=True)

'''@bot.slash_command(guild_ids=[1288951632200990881])      
@commands.cooldown(1, 2, commands.BucketType.user)
async def redeem(ctx, key: str):
    user_language = await database.get_user_language(ctx.author.name)
    
    await ctx.defer(ephemeral=True)

    keys = await database.get_redeemable_keys()

    if key not in keys:
        error_embed = discord.Embed(
        title=translate(user_language, 'error'),
        description=translate(user_language, 'invalid_key'),
        color=discord.Color.red()
    )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return

    user = ctx.author
    user_data = await database.get_user_by_name(user.name)

    if not user_data:
        error_embed = discord.Embed(
        title=translate(user_language, 'error'),
        description=translate(user_language, 'registration_not_found'),
        color=discord.Color.red()
    )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return

    gold_amount = keys[key]

    success, message = await database.add_gold(sender=translate(user_language, 'system'), receiver=user.name, amount=gold_amount, reason=translate(user_language, 'key_activation'), user_language=user_language)

    if success:
        await database.mark_key_as_used(key, user.name)
        success_embed = discord.Embed(
        title=translate(user_language, 'success'),
        description=translate(user_language, 'successfully_redeemed', gold_amount=gold_amount) ,
        color=discord.Color.green()
        )
        await ctx.followup.send(embed=success_embed, ephemeral=True)
    else:
        error_embed = discord.Embed(
        title=translate(user_language, 'error'),
        description=translate(user_language, 'error'),
        color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)'''
        
@bot.slash_command(guild_ids=[1288951632200990881])          
#@commands.cooldown(1, 2, commands.BucketType.user)  
async def event_program(ctx):
    user_language = await database.get_user_language(ctx.author.name)
    
    await ctx.defer(ephemeral=True)
    
    embed = discord.Embed(
        title=translate(user_language, 'event_program'),
        description=translate(user_language, 'schedule'),
        color=discord.Color.gold()
    )
    
    embed.add_field(name="🕒 19:00 - 20:00", value=translate(user_language, 'registration'), inline=False)
    embed.add_field(name="🕒 20:00 - 20:15", value=translate(user_language, 'introduction'), inline=False)
    embed.add_field(name="🕒 20:15 - 22:15", value=translate(user_language, 'orienteering'), inline=False)
    embed.add_field(name="🕒 22:15 - 22:30", value=translate(user_language, 'orienteering_winners'), inline=False)
    embed.add_field(name="🕒 22:30 - 22:55", value=translate(user_language, 'after_orienteering'), inline=False)
    embed.add_field(name="🕒 22:30 - 24:00", value=translate(user_language, 'bull_activity'), inline=False)
    embed.add_field(name="🕒 21:00 - 1:00", value=translate(user_language, 'gold_shop_info'), inline=False)
    embed.add_field(name="🕒 22:30 - 1:30", value=translate(user_language, 'escape_room_info'), inline=False)
    embed.add_field(name="🕒 22:30 - 23:00", value=translate(user_language, 'sack_jumping_info'), inline=False)
    embed.add_field(name="🕒 22:30 - 23:00", value=translate(user_language, 'trivia_info'), inline=False)
    embed.add_field(name="🕒 23:00 - 00:30", value=translate(user_language, 'lecturer'), inline=False)
    embed.add_field(name="🕒 23:00 - 1:00", value=translate(user_language, 'blackjack_info'), inline=False)
    embed.add_field(name="🕒 23:00 - 1:00", value=translate(user_language, 'poker_info'), inline=False)
    embed.add_field(name="🕒 23:00 - 24:00", value=translate(user_language, 'just_dance_info'), inline=False)
    embed.add_field(name="🕒 24:00 - 1:30", value=translate(user_language, 'film_info'), inline=False)
    embed.add_field(name="🕒 24:00 - 1:30", value=translate(user_language, 'karaoke_info'), inline=False)
    embed.add_field(name="🕒 19:00 - 1:30", value=translate(user_language, 'treasure_hunt_info'), inline=False)
    embed.add_field(name="🕒 1:30", value=translate(user_language, 'end_event'), inline=False)
    

    embed.set_thumbnail(url="https://i.imgur.com/ezKiTCS.jpeg")
    
    await ctx.followup.send(embed=embed, ephemeral=True)
    
    
@bot.slash_command(guild_ids=[1288951632200990881])      
#@commands.cooldown(1, 2, commands.BucketType.user)
async def create_orienteering_team(ctx, team_name: str):
    user_language = await database.get_user_language(ctx.author.name)
    
    await ctx.defer(ephemeral=True)

    user = ctx.author
    user_data = await database.get_user_by_name(user.name)

    if not user_data:
        error_embed = discord.Embed(
        title=translate(user_language, 'error'),
        description=translate(user_language, 'registration_not_found'),
        color=discord.Color.red()
    )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    if user_data['team']:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'already_in_team'),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    success, message = await database.create_orienteering_team(user.name, team_name)
    if not success:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=message,
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    await database.assign_team(user.name, team_name, user_language)
    
        
    embed = discord.Embed(
            title=translate(user_language, "created_team_successfully"),
            color=discord.Colour.green(),
    )
    await ctx.followup.send(embed=embed, ephemeral=True)
    
    
@bot.slash_command(guild_ids=[1288951632200990881])      
#@commands.cooldown(1, 2, commands.BucketType.user)
async def join_orienteering_team(ctx, team_name: str):
    user_language = await database.get_user_language(ctx.author.name)
    
    await ctx.defer(ephemeral=True)

    user = ctx.author
    user_data = await database.get_user_by_name(user.name)

    if not user_data:
        error_embed = discord.Embed(
        title=translate(user_language, 'error'),
        description=translate(user_language, 'registration_not_found'),
        color=discord.Color.red()
    )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    if user_data['team']:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'already_in_team'),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    team = await database.get_team_by_name(team_name)
    if not team:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, translate(user_language, 'not_in_team')),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    invites = team['invites'].split(' ')
    if user.name not in invites:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, translate(user_language, 'not_invited')),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    usernames = team['usernames'].split(' ')
    if len(usernames) > 6:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'team_limit_reached'),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    await database.assign_team(user.name, team_name, user_language)
    await database.add_to_team(user.name, team_name, user_language)
    
    embed = discord.Embed(
            title=translate(user_language, "joined_team_successfully"),
            color=discord.Colour.green(),
    )
    await ctx.followup.send(embed=embed, ephemeral=True)
    
    
@bot.slash_command(guild_ids=[1288951632200990881])      
#@commands.cooldown(1, 2, commands.BucketType.user)
async def leave_orienteering_team(ctx):
    user_language = await database.get_user_language(ctx.author.name)
    
    await ctx.defer(ephemeral=True)

    user = ctx.author
    user_data = await database.get_user_by_name(user.name)

    if not user_data:
        error_embed = discord.Embed(
        title=translate(user_language, 'error'),
        description=translate(user_language, 'registration_not_found'),
        color=discord.Color.red()
    )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    if not user_data['team']:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'not_in_team'),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    
    await database.assign_team(user.name, "", user_language)
    await database.remove_from_team(user.name, user_data['team'], user_language)
    
    
    embed = discord.Embed(
            title=translate(user_language, "left_team_successfully"),
            color=discord.Colour.green(),
    )
    await ctx.followup.send(embed=embed, ephemeral=True)
    
@bot.slash_command(guild_ids=[1288951632200990881])      
#@commands.cooldown(1, 2, commands.BucketType.user)
async def invite_to_orienteering_team(ctx, dc_user: discord.Option(discord.Member)):
    dc_username = dc_user.name
    user_language = await database.get_user_language(ctx.author.name)
    
    await ctx.defer(ephemeral=True)

    user = ctx.author
    user_data = await database.get_user_by_name(user.name)

    if not user_data:
        error_embed = discord.Embed(
        title=translate(user_language, 'error'),
        description=translate(user_language, 'registration_not_found'),
        color=discord.Color.red()
    )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    if not user_data['team']:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, translate(user_language, 'not_in_team')),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    if user.name == dc_username:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'cant_invite_yourself'),
            color=discord.Color.red()
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    success, message = await database.invite_to_team(dc_username, user_data['team'], user_language)
    if not success:
        await ctx.followup.send(message, ephemeral=True)
        return
    
    embed = discord.Embed(
            title=translate(user_language, 'invited_successfully'),
            color=discord.Colour.green(),
    )
    await ctx.followup.send(embed=embed, ephemeral=True)
    
@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def get_team_by_name(ctx, team_name: str):
    
    await ctx.defer(ephemeral=True)
    
    user_language = await database.get_user_language(ctx.author.name)
    team_data = await database.get_team_by_name(team_name)
    
    if not team_data:  
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'no_such_team', name=team_name),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    team_embed = discord.Embed(
            title=translate(user_language, 'team_data'),
            color=discord.Colour.gold(),
    )
    team_embed.add_field(name=translate(user_language, 'name'), value=team_data['name'], inline=False)
    team_embed.add_field(name=translate(user_language, 'gold'), value=team_data['gold'], inline=False)
    team_embed.add_field(name=translate(user_language, 'members'), value=team_data['usernames'], inline=False)
    team_embed.add_field(name=translate(user_language, 'current_stop'), value=translate(user_language, team_data['current_stop']), inline=False)
    stops = ''
    for stop in orienteering_stops:
        stops += f'{translate(user_language, stop)} {"✅" if team_data[stop] else "❌"}\n'
    team_embed.add_field(name=translate(user_language, 'stops'), value=stops, inline=False)
    await ctx.followup.send(embed=team_embed, ephemeral=True)
    

@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def complete_orienteering_stop(ctx, team_name: str, gold_amount:int, stop: discord.Option(str, choices=orienteering_stops)):
    
    await ctx.defer(ephemeral=True)
    
    user_language = await database.get_user_language(ctx.author.name)
    
    if not await database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'user_is_not_authorized'),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    team_data = await database.get_team_by_name(team_name)
    
    if not team_data:  
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'no_such_team', name=team_name),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    if team_data[stop]:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'stop_already_completed'),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    
    
    success, msg = await database.add_gold_to_team(ctx.author.name, team_name, gold_amount, f'orienteering_{stop}', user_language)
    if not success:
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=msg,
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    usernames = team_data['usernames'].split(' ')
    for user in usernames:
        await database.add_gold(ctx.author.name, user, gold_amount, f'orienteering_{stop}', user_language)
    
    success, msg = await database.complete_orienteering_stop(team_name, stop, user_language)
    
    gold_embed = discord.Embed(
            title=translate(user_language, 'stop_completed_successfully'),
            color=discord.Colour.green(),
    )
    await ctx.followup.send(embed=gold_embed, ephemeral=True)
    
@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def change_orienteering_stop(ctx, team_name: str, stop: discord.Option(str, choices=orienteering_stops)):
    
    await ctx.defer(ephemeral=True)
    
    user_language = await database.get_user_language(ctx.author.name)
    
    if not await database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    team_data = await database.get_team_by_name(team_name)
    
    if not team_data:  
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'no_such_team', name=team_name),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    if team_data[stop]:
        error_embed = discord.Embed(
            title=translate(user_language, 'error'),
            description=translate(user_language, 'stop_already_completed'),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    
    
    success, msg = await database.change_orienteering_stop(team_name, stop, user_language)
    
    stop_embed = discord.Embed(
            title=translate(user_language, 'stop_changed_successfully'),
            color=discord.Colour.green(),
    )
    await ctx.followup.send(embed=stop_embed, ephemeral=True)
    
    
@bot.slash_command(guild_ids=[1288951632200990881])
#@commands.cooldown(1, 2, commands.BucketType.user)
async def list_teams(ctx):
    
    await ctx.defer(ephemeral=True)
    
    user_language = await database.get_user_language(ctx.author.name)
    
    if not await database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title=translate(user_language, "error"),
            description=translate(user_language, "user_is_not_authorized"),
            color=discord.Colour.red(),
        )
        await ctx.followup.send(embed=error_embed, ephemeral=True)
        return
    
    users = await database.get_all_teams()
    users = sorted(users, key=lambda x: x['gold'], reverse=True)
    
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

        embed = discord.Embed(title=translate(user_language, 'Team list', page=page + 1, num_pages=num_pages),
        color=discord.Color.blue())
        for index, user in enumerate(user_data, start=start + 1):
            embed.add_field(
                name=f"{index}. {user['name']}", 
                value=f"**{translate(user_language, 'name')}:** {user['name']}\n"
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
    
    
bot.run("MTI4ODk1MTgyMTkxNzg4NDQ0Ng.GJp8HR.AhbEBj7XgP5YDu_jV7ngeOM4xJilbEPMFJfQRM")
