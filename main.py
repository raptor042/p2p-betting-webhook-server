from flask import Flask, request
from dotenv import load_dotenv
import boto3

from db.db import connect_db
from db.users import get_user, update_user
from db.transactions import get_transaction, update_transaction
from controllers.index import loadKeyPair, decrypt_data

import logging
import os

logging.basicConfig(format="%(asctime)s - %(message)s")
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

app = Flask(__name__)
db = None
client = None

@ app.route("/", methods = ["GET"])
def publish():
    response = client.publish(PhoneNumber="+2348089672675", Message="Hello from OddZ")
    print(f"Sent an SMS with MessageId : {response['MessageId']}")

    return f"Sent an SMS with MessageId : {response['MessageId']}"

@ app.route("/transfer", methods = ["GET", "POST"])
def transfer():
    payload = request.get_json()

    if payload["event.type"] == "Transfer" and payload["event"] == "transfer.completed":
        transaction = get_transaction(db=db, query={"id" : payload["data"]["id"]})
        print(transaction)

        user = get_user(db=db, query={"username" : transaction["user"]})
        _balance = float(user["balance"])
        balance = _balance - float(transaction["amount"])
        key = loadKeyPair()
        phone_no = decrypt_data(data=user["phone"], key=key[1])
        print(user, "{:.2f}".format(balance), phone_no)

        if payload["data"]["status"] == "SUCCESSFUL":
            _user = update_user(db=db, query={ "username" : transaction["user"] }, value={"$set" : {"balance" : "{:.2f}".format(balance)}})
            _transaction = update_transaction(db=db, query={"id" : payload["data"]["id"]}, value={"$set" : {"completed" : True}})
            _transaction = update_transaction(db=db, query={"id" : payload["data"]["id"]}, value={"$set" : {"status" : "SUCCESSFUL"}})
            print(_user, _transaction)
        elif payload["data"]["status"] == "FAILED":
            _transaction = update_transaction(db=db, query={"id" : payload["data"]["id"]}, value={"$set" : {"completed" : True}})
            _transaction = update_transaction(db=db, query={"id" : payload["data"]["id"]}, value={"$set" : {"status" : "SUCCESSFUL"}})
            print(_transaction)

def main() -> None:
    global db
    db = connect_db(uri=MONGO_URI)
    print(f"Connected to the Database with the Cluster URL : {MONGO_URI}")

    global client
    client = boto3.client("sns", aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    print(f"Connected to AWS Service : {client}")

    app.run(debug = True)

if __name__ == "__main__":
    main()