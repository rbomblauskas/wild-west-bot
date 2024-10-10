import discord
import database

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command(guild_ids=[1288951632200990881])
async def hello(ctx):
    await ctx.respond('hi')

@bot.slash_command(guild_ids=[1288951632200990881])
async def get_user_by_name(ctx, name: str):
    user_data = database.get_user_by_name(name)
    if not user_data:  
        error_embed = discord.Embed(
            title="Error",
            description=f"No such user {name}",
            color=discord.Colour.red(),
        )
        await ctx.respond(embed=error_embed)
        return
    
    user_embed = discord.Embed(
            title="User data",
            color=discord.Colour.blue(),
    )
    user_embed.add_field(name="Name", value=user_data['name'], inline=True)
    user_embed.add_field(name="Discord username", value=user_data['dc_username'], inline=True)
    user_embed.add_field(name="Gold", value=user_data['gold'], inline=True)
    user_embed.add_field(name="Registration date", value=user_data['registration_date'].strftime('%Y-%m-%d %H:%M:%S'), inline=True)
    await ctx.respond(embed=user_embed)

@bot.slash_command(guild_ids=[1288951632200990881])
async def add_gold(ctx, name: str, amount: int, reason: str):
    if not database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title="Error",
            description=f"User is not authorized",
            color=discord.Colour.red(),
        )
        await ctx.respond(embed=error_embed)
        return
    success, msg = database.add_gold(ctx.author.name, name, amount, reason)
    if not success:
        error_embed = discord.Embed(
            title="Error",
            description=msg,
            color=discord.Colour.red(),
        )
        await ctx.respond(embed=error_embed)
        return
    gold_embed = discord.Embed(
            title="Gold added successfully",
            color=discord.Colour.green(),
    )
    gold_embed.add_field(name="User", value=name, inline=True)
    gold_embed.add_field(name="Amount", value=amount, inline=True)
    gold_embed.add_field(name="Reason", value=reason, inline=True)
    gold_embed.add_field(name="New total gold", value=msg, inline=True)
    await ctx.respond(embed=gold_embed)

@bot.slash_command(guild_ids=[1288951632200990881])
async def remove_gold(ctx, name: str, amount: int, reason: str):
    if not database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title="Error",
            description=f"User is not authorized",
            color=discord.Colour.red(),
        )
        await ctx.respond(embed=error_embed)
        return
    success, msg = database.remove_gold(ctx.author.name, name, amount, reason)
    if not success:
        error_embed = discord.Embed(
            title="Error",
            description=msg,
            color=discord.Colour.red(),
        )
        await ctx.respond(embed=error_embed)
        return
    gold_embed = discord.Embed(
            title="Gold removed successfully",
            color=discord.Colour.green(),
    )
    gold_embed.add_field(name="User", value=name, inline=True)
    gold_embed.add_field(name="Amount", value=amount, inline=True)
    gold_embed.add_field(name="Reason", value=reason, inline=True)
    gold_embed.add_field(name="New total gold", value=msg, inline=True)
    await ctx.respond(embed=gold_embed)

@bot.slash_command(guild_ids=[1288951632200990881])
async def register_user(ctx, name: str, dc_username: str = None):
    invoking_user_dc_username = ctx.author.name
    
    if not name:
        await ctx.respond('Name must be provided.', ephemeral=True)
        return
    
    if database.is_authorized(invoking_user_dc_username):
        if not dc_username:
            await ctx.respond('As an admin, you must provide a Discord username to register.', ephemeral=True)
            return
    else:
        dc_username = invoking_user_dc_username
        if database.is_user_registered(dc_username):
            await ctx.respond(f'The Discord username **{dc_username}** is already registered. Each account can only register once.', ephemeral=True)
            return
    success, msg = database.register_user(name, dc_username)
    if not success:
        await ctx.respond(msg, ephemeral=True) 
        return

    await ctx.respond(f'User **{dc_username}** successfully created!', ephemeral=True)
    
@bot.slash_command(guild_ids=[1288951632200990881])
async def list_users(ctx):
    if not database.is_authorized(ctx.author.name):        
        error_embed = discord.Embed(
            title="Error",
            description=f"User is not authorized",
            color=discord.Colour.red(),
        )
        await ctx.respond(embed=error_embed)
        return
    
    users = database.get_all_users()
    pages = 5 
    total_users = len(users)

    if total_users == 0:
        await ctx.respond("No registered users found.", ephemeral=True)
        return

    num_pages = (total_users + pages - 1) // pages
    cur_page = 0

    def create_embed(page):
        start = page * pages
        end = start + pages
        user_data = users[start:end]

        embed = discord.Embed(title=f"User List (Page {page + 1}/{num_pages})", color=discord.Color.blue())
        for index, user in enumerate(user_data, start=start + 1):
            embed.add_field(
                name=f"{index}. {user['name']}", 
                value=f"**Discord Username:** {user['dc_username']}\n**Gold:** {user['gold']}", 
                inline=False
            )
        
        return embed

    message = await ctx.respond(embed=create_embed(cur_page), ephemeral=True)

    previous_button = discord.ui.Button(label="◀️ Previous", style=discord.ButtonStyle.primary, disabled=True)
    next_button = discord.ui.Button(label="▶️ Next", style=discord.ButtonStyle.primary)

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
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
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