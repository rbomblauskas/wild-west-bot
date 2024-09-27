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
        await ctx.respond('No such user')
        return
    await ctx.respond(f'{user_data}')

@bot.slash_command(guild_ids=[1288951632200990881])
async def add_gold(ctx, name: str, amount: int, reason: str):
    if not database.is_authorized(ctx.author.name):
        await ctx.respond('User is not authorized')
        return
    success, msg = database.add_gold(ctx.author.name, name, amount, reason)
    if not success:
        await ctx.respond(msg)
        return
    await ctx.respond(f'Added {amount} gold to {name}\'s account')

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