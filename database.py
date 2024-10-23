import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore_async
from google.cloud.firestore_v1.base_query import FieldFilter
import datetime
from typing import Tuple
from translations import translate
from catalog import orienteering_stops

# Use a service account.
cred = credentials.Certificate('mif-renginys-firebase-adminsdk-ld2k1-dbbfebe5f1.json')
app = firebase_admin.initialize_app(cred)
db = firestore_async.client() # Maybe we will need to use async client


async def get_user_by_name(name: str):
    user_ref = await db.collection('users').where(filter=FieldFilter('dc_username', '==', name)).limit(1).get()
    if not user_ref:
        return None
    user_doc = user_ref[0]
    user_data = user_doc.to_dict()
    return user_data

async def add_gold(sender: str, receiver: str, amount: int, reason: str, user_language: str) -> Tuple[bool, str]:
    try:
        if amount <= 0:
            return (False, translate(user_language, 'invalid_amount'))
        user_ref = await db.collection('users').where(filter=FieldFilter('dc_username', '==', receiver)).limit(1).get()
        if not user_ref:
            return (False, translate(user_language, 'no_such_user', name=receiver))

        transaction = db.transaction()
        user_doc_ref = user_ref[0].reference

        @firestore_async.async_transactional
        async def update_in_transaction(transaction, user_doc_ref):
            snapshot = await user_doc_ref.get(transaction=transaction)
            new_balance = snapshot.get("gold") + amount
            transaction.update(user_doc_ref, {"gold": new_balance})
            return (True, new_balance)


        ok, new_balance = await update_in_transaction(transaction, user_doc_ref)
        
        if not ok:
            return (False, new_balance)

        doc_ref = db.collection("transactions").document()
        data = {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.datetime.now(),
            "transaction_type": "add"
        }
        await doc_ref.set(data)
        return (True, new_balance)
    except Exception as e:
        return (False, str(e))
    
async def remove_gold(sender: str, receiver: str, amount: int, reason: str, user_language: str, transaction_type="remove") -> Tuple[bool, str]:
    try:
        if amount <= 0:
            return (False, translate(user_language, 'invalid_amount'))
        user_ref = await db.collection('users').where(filter=FieldFilter('dc_username', '==', receiver)).limit(1).get()
        if not user_ref:
            return (False, translate(user_language, 'no_such_user', name=receiver))

        transaction = db.transaction()
        user_doc_ref = user_ref[0].reference

        @firestore_async.async_transactional
        async def update_in_transaction(transaction, user_doc_ref):
            snapshot = await user_doc_ref.get(transaction=transaction)
            new_balance = snapshot.get("gold") - amount
            if new_balance < 0:
                return(False, translate(user_language, 'insufficient_funds'))
            transaction.update(user_doc_ref, {"gold": new_balance})
            return (True, new_balance)

        ok, new_balance = await update_in_transaction(transaction, user_doc_ref)
        
        if not ok:
            return (False, new_balance)
        
        doc_ref = db.collection("transactions").document()
        data = {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.datetime.now(),
            "transaction_type": transaction_type,
        }
        await doc_ref.set(data)
        return (True, new_balance)
    except Exception as e:
        return (False, str(e))

async def is_user_registered(dc_username: str) -> bool:
    
    user_ref = await db.collection('users').where(filter=FieldFilter('dc_username', '==', dc_username)).limit(1).get()
    return len(user_ref) > 0

async def register_user(name: str, dc_username: str, language: str) -> Tuple[bool, str]:
    if await is_user_registered:
        return (False, '')

    doc_ref = db.collection("users").document()
    timestamp = datetime.datetime.now()
    data = {
        "dc_username": dc_username,
        "gold": 0,
        "language": language,
        "name": name,
        "registration_date": timestamp,
        "team": ""
    }
    await doc_ref.set(data)
    
    return (True, '')

async def is_authorized(dc_username: str) -> bool:
    user_ref = await db.collection('admins').where(filter=FieldFilter('dc_username', '==', dc_username)).limit(1).get()
    if user_ref:
        return True
    return False

async def get_all_users():
    users_ref = await db.collection('users').get()
    return [user_doc.to_dict() for user_doc in users_ref]

async def get_user_language(dc_username: str) -> str:
    user_ref = await db.collection('users').where(filter=FieldFilter('dc_username', '==', dc_username)).limit(1).get()
    
    if not user_ref:
        return 'en'  
    
    user_doc = user_ref[0]
    user_data = user_doc.to_dict()
    language = user_data.get('language', 'en') 
    return language

async def get_user_transactions(dc_username: str):
    transactions_ref = await db.collection('transactions').where(filter=FieldFilter('receiver', '==', dc_username)).get()
    return [transaction.to_dict() for transaction in transactions_ref]

async def add_moderator_to_db(member_id: str, dc_username: str) -> None:
    new_admin_ref = db.collection('admins').document(str(member_id))
    await new_admin_ref.set({'dc_username': dc_username})
    
async def can_user_afford_item(dc_username: str, item_price: int) -> bool:
    user_data = await get_user_by_name(dc_username)
    if not user_data:
        return False
    user_gold = user_data.get("gold", 0)
    return user_gold >= item_price

async def buy_item(sender: str, receiver: str, item_price: int, item_name: str, user_language: str) -> Tuple[bool, str]:
    purchase_reason = translate(user_language, 'purchase_reason', item=item_name)
    success, message = await remove_gold(sender=sender, receiver=receiver, amount=item_price, reason=purchase_reason, user_language=user_language, transaction_type="purchase")
    
    return success, message

async def get_shop_items(language: str) -> dict:
    return {
        
        translate(language, 'sheriff_adventure_kit'): 250,
        translate(language, 'desert_wanderer'): 450,
        translate(language, 'sand_protection'): 500,
        translate(language, 'lonely_cowboy'): 650,
        translate(language, 'wild_west_outfit'): 700,
        translate(language, 'traveler_bag'): 180,
        translate(language, 'sheriff_shirt_and_gear'): 850,
        translate(language, 'hint_qr_codes'): 30,
        translate(language, 'karaoke_song_request'): 100,
        translate(language, 'just_dance_song_request'): 100,
    }
    
async def get_user_balance(dc_username: str, user_language: str) -> Tuple[bool, int]:
    try:
        user_data = await get_user_by_name(dc_username)
        if not user_data:
            return (False, 0)
        user_gold = user_data.get("gold", 0)
        return (True, user_gold)
    except Exception as e:
        print(translate(user_language, 'error'), {e})
        return (False, 0)

async def redeemable_keys() -> dict:
    return {'kruopu-svajoniu-sultinys': 100, 'menulio-dulkes-pica': 100, 'sauletos-dienos-salotos': 100, 'paslaptingas-misko-troskinys': 100, 'vejo-puku-ravioli': 100, 'vasaros-svelnumo-desertine': 100, 'juros-bangu-kebabas': 100, 'tamsos-grotu-uogiene': 100, 'erdves-balanso-patiekalas': 100, 'nakties-svytejimo-pudingas': 100}

async def is_key_used(key: str) -> bool:
    used_key_ref = await db.collection('used_keys').where(filter=FieldFilter('key', '==', key)).limit(1).get()
    return len(used_key_ref) > 0

async def mark_key_as_used(key: str, user: str) -> None:
    await db.collection('used_keys').add({'key': key, 'user': user})

async def get_redeemable_keys() -> dict:
    keys = await redeemable_keys()
    available_keys = {}
    for key, value in keys.items():
        if not await is_key_used(key):
            available_keys[key] = value
    return available_keys


async def create_orienteering_team(leader, name):
    team_ref = await db.collection('teams').where(filter=FieldFilter('name', '==', name)).get()
    if len(team_ref) > 0:
        return (False, 'team_exists')
    
    doc_ref = db.collection("teams").document()
    data = {
        "name": name,
        "gold": 0,
        "invites": "",
        "usernames": leader,
        "current_stop": "" 
    }
    for stop in orienteering_stops:
        data[stop] = False
    await doc_ref.set(data)
    
    return (True, 'success')


async def assign_team(dc_username, name, user_language):
    try:
        user_ref = await db.collection('users').where(filter=FieldFilter('dc_username', '==', dc_username)).limit(1).get()
        if not user_ref:
            return (False, translate(user_language, 'no_such_user', name=dc_username))

        transaction = db.transaction()
        user_doc_ref = user_ref[0].reference

        @firestore_async.async_transactional
        async def update_in_transaction(transaction, user_doc_ref):
            #snapshot = await user_doc_ref.get(transaction=transaction)
            #team = snapshot.get("team")
            transaction.update(user_doc_ref, {"team": name})
            return (True, "")

        ok, message = await update_in_transaction(transaction, user_doc_ref)
        
        if not ok:
            return (False, message)
        
        return (True, message)
    except Exception as e:
        return (False, str(e))
    
async def get_team_by_name(name: str):
    user_ref = await db.collection('teams').where(filter=FieldFilter('name', '==', name)).limit(1).get()
    if not user_ref:
        return None
    user_doc = user_ref[0]
    user_data = user_doc.to_dict()
    return user_data

async def invite_to_team(dc_username, name, user_language):
    try:
        user_ref = await db.collection('teams').where(filter=FieldFilter('name', '==', name)).limit(1).get()
        if not user_ref:
            return (False, translate(user_language, 'no_such_team'))

        transaction = db.transaction()
        user_doc_ref = user_ref[0].reference

        @firestore_async.async_transactional
        async def update_in_transaction(transaction, user_doc_ref):
            snapshot = await user_doc_ref.get(transaction=transaction)
            invites = snapshot.get("invites")
            invites = invites.split(' ')
            invites.append(dc_username)
            transaction.update(user_doc_ref, {"invites": ' '.join(invites)})
            return (True, "")

        ok, message = await update_in_transaction(transaction, user_doc_ref)
        
        if not ok:
            return (False, message)
        
        return (True, message)
    except Exception as e:
        return (False, str(e))
    
    
async def add_to_team(dc_username, name, user_language):
    try:
        user_ref = await db.collection('teams').where(filter=FieldFilter('name', '==', name)).limit(1).get()
        if not user_ref:
            return (False, translate(user_language, 'no_such_team'))

        transaction = db.transaction()
        user_doc_ref = user_ref[0].reference

        @firestore_async.async_transactional
        async def update_in_transaction(transaction, user_doc_ref):
            snapshot = await user_doc_ref.get(transaction=transaction)
            usernames = snapshot.get("usernames")
            usernames = usernames.split(' ')
            usernames.append(dc_username)
            transaction.update(user_doc_ref, {"usernames": ' '.join(usernames)})
            return (True, "")

        ok, message = await update_in_transaction(transaction, user_doc_ref)
        
        if not ok:
            return (False, message)
        
        return (True, message)
    except Exception as e:
        return (False, str(e))
    
async def remove_from_team(dc_username, name, user_language):
    try:
        team_ref = await db.collection('teams').where(filter=FieldFilter('name', '==', name)).limit(1).get()
        if not team_ref:
            return (False, translate(user_language, 'no_such_team'))

        transaction = db.transaction()
        user_doc_ref = team_ref[0].reference

        @firestore_async.async_transactional
        async def update_in_transaction(transaction, user_doc_ref):
            snapshot = await user_doc_ref.get(transaction=transaction)
            usernames = snapshot.get("usernames")
            usernames = set(usernames.split(' '))
            usernames.remove(dc_username)
            usernames = list(usernames)
            transaction.update(user_doc_ref, {"usernames": ' '.join(usernames)})
            return (True, "")

        ok, message = await update_in_transaction(transaction, user_doc_ref)
        
        if not ok:
            return (False, message)
        
        return (True, message)
    except Exception as e:
        return (False, str(e))

async def add_gold_to_team(sender: str, team_name: str, amount: int, reason: str, user_language: str) -> Tuple[bool, str]:
    try:
        if amount <= 0:
            return (False, translate(user_language, 'invalid_amount'))
        user_ref = await db.collection('teams').where(filter=FieldFilter('name', '==', team_name)).limit(1).get()
        if not user_ref:
            return (False, translate(user_language, 'no_such_user', name=team_name))

        transaction = db.transaction()
        user_doc_ref = user_ref[0].reference

        @firestore_async.async_transactional
        async def update_in_transaction(transaction, user_doc_ref):
            snapshot = await user_doc_ref.get(transaction=transaction)
            new_balance = snapshot.get("gold") + amount
            transaction.update(user_doc_ref, {"gold": new_balance})
            return (True, new_balance)


        ok, new_balance = await update_in_transaction(transaction, user_doc_ref)
        
        if not ok:
            return (False, new_balance)
        
        return (True, new_balance)
    except Exception as e:
        return (False, str(e))
    
async def complete_orienteering_stop(team_name: str, stop:str, user_language: str) -> Tuple[bool, str]:        
    team_ref = await db.collection('teams').where(filter=FieldFilter('name', '==', team_name)).limit(1).get()
    if not team_ref:
        return (False, translate(user_language, 'no_such_team'))
    
    team_doc_ref = team_ref[0].reference
    await team_doc_ref.update({stop: True})
    return (True, 'success')
    


    


