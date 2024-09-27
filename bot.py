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
    user_data = database.get_user_by_name(name)
    if not user_data:
        return
    gold_embed = discord.Embed(
            title="Gold added successfully",
            color=discord.Colour.green(),
    )
    gold_embed.add_field(name="User", value=user_data['dc_username'], inline=True)
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
    user_data = database.get_user_by_name(name)
    if not user_data:
        return
    gold_embed = discord.Embed(
            title="Gold removed successfully",
            color=discord.Colour.green(),
    )
    gold_embed.add_field(name="User", value=user_data['dc_username'], inline=True)
    gold_embed.add_field(name="Amount", value=amount, inline=True)
    gold_embed.add_field(name="Reason", value=reason, inline=True)
    gold_embed.add_field(name="New total gold", value=msg, inline=True)
    await ctx.respond(embed=gold_embed)

@bot.slash_command(guild_ids=[1288951632200990881])
async def register_user(ctx, name: str, dc_username: str):
    if not database.is_authorized(ctx.author.name):
        await ctx.respond('User is not authorized')
        return
    success, msg = database.register_user(name, dc_username)
    if not success:
        await ctx.respond(msg)
        return
    await ctx.respond(f'User {dc_username} sucessfully created')



bot.run("MTI4ODk1MTgyMTkxNzg4NDQ0Ng.GJp8HR.AhbEBj7XgP5YDu_jV7ngeOM4xJilbEPMFJfQRM")