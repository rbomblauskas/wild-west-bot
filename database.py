import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import datetime
from typing import Tuple
from translations import translate

# Use a service account.
cred = credentials.Certificate('mif-renginys-firebase-adminsdk-ld2k1-dbbfebe5f1.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client() # Maybe we will need to use async client

def get_user_by_name(name: str):
    user_ref = db.collection('users').where(filter=FieldFilter('dc_username', '==', name)).limit(1).get()
    if not user_ref:
        return None
    user_doc = user_ref[0]
    user_data = user_doc.to_dict()
    return user_data

def add_gold(sender: str, receiver: str, amount: int, reason: str, user_language: str) -> Tuple[bool, str]:
    try:
        if amount <= 0:
            return (False, translate(user_language, 'invalid_amount'))
        user_ref = db.collection('users').where(filter=FieldFilter('dc_username', '==', receiver)).limit(1).get()
        if not user_ref:
            return (False, translate(user_language, 'no_such_user', name=receiver))

        transaction = db.transaction()
        user_doc_ref = user_ref[0].reference

        @firestore.transactional
        def update_in_transaction(transaction, user_doc_ref):
            snapshot = user_doc_ref.get(transaction=transaction)
            new_balance = snapshot.get("gold") + amount
            transaction.update(user_doc_ref, {"gold": new_balance})
            return (True, new_balance)


        ok, new_balance = update_in_transaction(transaction, user_doc_ref)
        
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
        doc_ref.set(data)
        return (True, new_balance)
    except Exception as e:
        return (False, str(e))
    
def remove_gold(sender: str, receiver: str, amount: int, reason: str, user_language: str, transaction_type="remove") -> Tuple[bool, str]:
    try:
        if amount <= 0:
            return (False, translate(user_language, 'invalid_amount'))
        user_ref = db.collection('users').where(filter=FieldFilter('dc_username', '==', receiver)).limit(1).get()
        if not user_ref:
            return (False, translate(user_language, 'no_such_user', name=receiver))

        transaction = db.transaction()
        user_doc_ref = user_ref[0].reference

        @firestore.transactional
        def update_in_transaction(transaction, user_doc_ref):
            snapshot = user_doc_ref.get(transaction=transaction)
            new_balance = snapshot.get("gold") - amount
            if new_balance < 0:
                return(False, translate(user_language, 'insufficient_funds'))
            transaction.update(user_doc_ref, {"gold": new_balance})
            return (True, new_balance)

        ok, new_balance = update_in_transaction(transaction, user_doc_ref)
        
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
        doc_ref.set(data)
        return (True, new_balance)
    except Exception as e:
        return (False, str(e))

def is_user_registered(dc_username: str) -> bool:
    
    user_ref = db.collection('users').where(filter=FieldFilter('dc_username', '==', dc_username)).limit(1).get()
    return len(user_ref) > 0

def register_user(name: str, dc_username: str, language: str) -> Tuple[bool, str]:

    doc_ref = db.collection("users").document()
    timestamp = datetime.datetime.now()
    data = {
        "dc_username": dc_username,
        "gold": 0,
        "language": language,
        "name": name,
        "registration_date": timestamp
    }
    doc_ref.set(data)
    
    return (True, '')

def is_authorized(dc_username: str) -> bool:
    user_ref = db.collection('admins').where(filter=FieldFilter('dc_username', '==', dc_username)).limit(1).get()
    if user_ref:
        return True
    return False

def get_all_users():
    users_ref = db.collection('users').stream()
    return [user_doc.to_dict() for user_doc in users_ref]

def get_user_language(dc_username: str) -> str:
    user_ref = db.collection('users').where(filter=FieldFilter('dc_username', '==', dc_username)).limit(1).get()
    
    if not user_ref:
        return 'en'  
    
    user_doc = user_ref[0]
    user_data = user_doc.to_dict()
    language = user_data.get('language', 'en') 
    return language

def get_user_transactions(dc_username: str):
    transactions_ref = db.collection('transactions').where(filter=FieldFilter('receiver', '==', dc_username)).get()
    return [transaction.to_dict() for transaction in transactions_ref]

def add_moderator_to_db(member_id: str, dc_username: str) -> None:
    new_admin_ref = db.collection('admins').document(str(member_id))
    new_admin_ref.set({'dc_username': dc_username})
    
def can_user_afford_item(dc_username: str, item_price: int) -> bool:
    user_data = get_user_by_name(dc_username)
    if not user_data:
        return False
    user_gold = user_data.get("gold", 0)
    return user_gold >= item_price

def buy_item(sender: str, receiver: str, item_price: int, item_name: str, user_language: str) -> Tuple[bool, str]:
    purchase_reason = translate(user_language, 'purchase_reason', item=item_name)
    success, message = remove_gold(sender=sender, receiver=receiver, amount=item_price, reason=purchase_reason, user_language=user_language, transaction_type="purchase")
    
    return success, message

    
    


