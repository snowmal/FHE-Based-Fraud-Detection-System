"""
data_owner.py
    Acts as Alice: generate keys, encrypts original data, decrypts processed result.
"""
import sys
sys.path.append('./carol_function')
import utils
import tenseal as ts
import numpy as np
import json
import os
from google.cloud import storage
import time

BUCKET_NAME = "alice_data"

def upload_to_gcs(bucket_name, source_file, destination_blob):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    print(f"[ALICE] Uploaded {source_file} to {bucket_name}/{destination_blob}")

def download_from_gcs(bucket_name, blob_name, destination_file):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    if blob.exists():
        blob.download_to_filename(destination_file)
        print(f"[ALICE] Downloaded {blob_name} to {destination_file}")
        return True
    return False

# Prepare folders
os.makedirs("keys", exist_ok=True)
os.makedirs("inputs", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Load ALice's transaction history
with open("alice_data.json", 'r') as file:
    data = json.load(file)
transactions = np.array(data["Transactions"], dtype=np.float32)
print(f"[ALICE] Transaction vector: {transactions}")

# Create encryption context --> Generate context and keys
context = ts.context(
    ts.SCHEME_TYPE.CKKS, # use CKKS since it uses real numbers for calculations
    poly_modulus_degree=8192,
    coeff_mod_bit_sizes=[60, 40, 40, 60]
)
context.generate_galois_keys() # generate context keys
context.global_scale = 2 ** 40 # set gloabl scale

# Save keys
utils.write_data("keys/secret.txt", context.serialize(save_secret_key=True)) # extract and store secret key
utils.write_data("carol_function/keys/public.txt", context.serialize()) # store public key

# Encrypt and save transaction vector
enc_txn_vector = ts.ckks_vector(context, transactions)
utils.write_data("inputs/encrypted_transactions.txt", enc_txn_vector.serialize())

# Upload to Carol
upload_to_gcs(BUCKET_NAME, "inputs/encrypted_transactions.txt", "inputs/encrypted_transactions.txt")
upload_to_gcs("alice_data", "carol_function/keys/public.txt", "keys/public.txt")

print(f"[ALICE] Encrypted data and key uploaded. Waiting for result...")

# Acquire result from Carol
result_blob = "outputs/encrypted_score.txt"
local_result_file = "outputs/encrypted_score.txt"

# Wait for Carol to respond
for _ in range(10):
    if download_from_gcs(BUCKET_NAME, result_blob, local_result_file): 
        print("[ALICE] Decrypting result...")
        result_proto = utils.read_data(local_result_file)
        enc_result = ts.lazy_ckks_vector_from(result_proto)
        enc_result.link_context(context)
        score = int(min(max(enc_result.decrypt()[0], 0), 100))  # clamp between 0 and 100
        print(f"[ALICE] Encrypted fraud risk score decrypted: {score}")
        if 0 <= score <= 20:
            print("\tScore Range: 0-20\n\tLow-Risk: Transactions are normal. Fraud is unlikely! :)")
        elif 21 <= score <= 50:
            print("\tScore Range: 20-50\n\tSuspicious: Transactions are suspicious. Further inspection is recommended.")
        elif 51 <= score:
            print("\tScore Range: 51-100+\n\tHigh-Risk: Transactions are likely fraudulent.")
        break
    print("[ALICE] Result not ready, waiting 5s...")
    time.sleep(5)
else:
    print(f"[ALICE] Timed out waiting for result...")
    # print(f"[ALICE] Awaiting encrypted score from Carol...")

