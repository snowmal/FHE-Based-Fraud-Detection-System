"""
carol_listener.py
Acts as Carol: Reads encrypted data and performs computation using public context.
"""
import tenseal as ts
import utils
import numpy as np
import os
from google.cloud import storage

# Prepare folders
BUCKET_NAME = "alice_data"
INPUT_BLOB = "inputs/encrypted_transactions.txt"
OUTPUT_BLOB = "outputs/encrypted_score.txt"
PUBLIC_KEY_BLOB = "keys/public.txt"
LOCAL_INPUT = "/tmp/encrypted_transactions.txt"
LOCAL_KEY_FILE = "/tmp/public.txt"
LOCAL_OUTPUT = "/tmp/encrypted_score.txt"

def download_blob(bucket_name, blob_name, destination_file):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(destination_file)
    print(f"[CAROL] Downloaded {blob_name}.")

def upload_blob(bucket_name, source_file, destination_blob):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    print(f"[CAROL] Uploaded result to {destination_blob}.")

def process():
    print("[CAROL] Downloading public key and encrypted transactions from bucket...")
    download_blob(BUCKET_NAME, PUBLIC_KEY_BLOB, LOCAL_KEY_FILE)
    download_blob(BUCKET_NAME, INPUT_BLOB, LOCAL_INPUT)
    
    print("[CAROL] Loading public context...")
    context = ts.context_from(utils.read_data(LOCAL_KEY_FILE))

    # Load encrypted input (transaction vector)
    txn_proto = utils.read_data(LOCAL_INPUT)
    enc_txn = ts.ckks_vector_from(context, txn_proto)

    # Pretrained nerual network (6 inputs (txn) -> 3 hidden -> 1 output) 
    # Weights for hidden layer (3 neurons)
    print("[DEBUG] Reading encrypted transaction vector...")
    w1 = [ # smaller weights and biases to prevent score inflation due to encrypted math
        [0.01, 0.02, -0.03, 0.05, 0.01, -0.02],
        [-0.04, 0.03, 0.01, 0.01, 0.02, -0.01],
        [0.02, -0.02, 0.05, -0.03, 0.04, 0.01]
    ]
    b1 = [0.01, -0.01, 0.005]

    # Encode W1 rows and perform dot product for each neuron
    print("[DEBUG] Computing hidden layer outputs...")
    hidden_layer_outputs = []
    for i in range(3):
        z = enc_txn.dot(w1[i]) # homomorphic dot product
        # a = z * z # must avoid squared activation so as to not increase scale
        hidden_layer_outputs.append(z)

    # Output layer (1 neuron)
    w2 = [0.1, -0.1, 0.15]
    b2 = [0.05]

    # Compute final risk calculation score
    print("[CAROL] Computing output score...")
    weighted_terms = []
    for i in range(3):
        term = hidden_layer_outputs[i] * w2[i]
        weighted_terms.append(term)
    score = sum(weighted_terms) + b2[0]    
    # Save and upload
    utils.write_data(LOCAL_OUTPUT, score.serialize())
    upload_blob(BUCKET_NAME, LOCAL_OUTPUT, OUTPUT_BLOB)
