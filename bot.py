import discord
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Use a service account.
cred = credentials.Certificate('mif-renginys-firebase-adminsdk-ld2k1-dbbfebe5f1.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client() # Maybe we will need to use async client

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.slash_command(guild_ids=[1288951632200990881])
async def hello(ctx):
    await ctx.respond('hi')

@bot.slash_command(guild_ids=[1288951632200990881])
async def get_user_by_name(ctx, name: str):
    user_ref = db.collection('users').where(filter=FieldFilter('dc_username', '==', name)).limit(1).get()
    if not user_ref:
        await ctx.respond('No such user')
        return
    user_doc = user_ref[0]
    user_data = user_doc.to_dict()
    await ctx.respond(f'{user_data}')

@bot.slash_command(guild_ids=[1288951632200990881])
async def add_gold(ctx, name: str, amount: int):
    user_ref = db.collection('users').where(filter=FieldFilter('dc_username', '==', name)).limit(1).get()
    if not user_ref:
        await ctx.respond('No such user')
        return
    user_doc_ref = user_ref[0].reference
    user_doc_ref.update({'gold': firestore.Increment(amount)})
    await ctx.respond(f'Added {amount} gold to {name}\'s account')


bot.run("MTI4ODk1MTgyMTkxNzg4NDQ0Ng.GJp8HR.AhbEBj7XgP5YDu_jV7ngeOM4xJilbEPMFJfQRM")