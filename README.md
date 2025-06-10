# Privacy-Preserving Fraud Detection via Homomorphic Encryption
This project implements a secure machine learning inference system using **homomorphic encryption**, allowing a user (Alice) to outsource the evaluation of a neural network classifier (Carol) **without revealing her input data**

-------

## Project Goal
To securely compute a **fraud risk score** over encrypted financial transaction data using a neural network classifier, such that:

- Alice's input data remains confidential
- Carol computed the classifier output **without decrypting the data**
- Alice receives and decrypts the result without knowing Carol's model parameters.

This demonstrates practical use of **homomorphic encryption** in privacy-preserving machine learning inference.

-------

## System Design
The solution models a secure client-cloud architecture:

- **Alice (Client):**
  1. Encrypts her transaction data using the CKKS encryption scheme.
  2. Uploads the encrypted input to the cloud (Google Cloud Storage).
  3. Decrypts the final fraud score received from Carol.

- **Carol (Cloud Server):**
  1. Loads Alice's encrypted input and a public key.
  2. Applices a simple neural network to the encrypted vector.
  3. Uploads the encrypted fraud score for Alice.

-------

## Classifier Overview
A **lightweight neural network** with the following structure was implemented:

- Input layer: 6-dimensional transaction vector
- Hidden layer: 3 neurons (dot product + bias)
- Output layer: 1 neuron -> Scalar fraud risk score

The neural network avoids non-linear activations to remain compatible with the CKKS encryptions scheme.

-------

## Homomorphic Encryption Details
- **Scheme:** CKKS (Cheon-Kim-Kim-Song)
- **Library:** [TenSeal](https:github.com/OpenMinded/TenSEAL)
- **Parameters:**
  - 'poly_modulus_degree = 8192'
  - 'coeff_mod_bit_sizes = [60, 40, 40, 60]'
  - 'global_scale = 2 ** 40

CKKS supports **approximate arithmetic on real numbers**, ideal for ML workloads.

-------

## Workflow Summary

1. **Setup:**
   - Alice prepares her local context and keys.
   - Carol defines the model parameters.

2. **Encryption:**
   - Alice encrypts her transaction data and uploads it to a cloud bucket.
   
3. **Computation:**
   - Carol downloads the encrypted data and public key.
   - Carol computes the fraud risk score over the encrypted input.

4. **Decryption:**
   - Alice downloads the result and decrypts it.
   - The plaintext fraud score is displayed with a qualitative risk level.

-------

## Project Structure
snowden-applied-cryptography-spring-25-project-type-2.8.2/
|   |── alice.py              # Encrypts data, uploads input, decrypts result
|   |── deploy.sh             # Prerequisite installer script
|   |── main.py               # Main running script for program
|   |── alice_data.json       # Alice's transaction data
|   |── inputs/               # Contains encrypted input vectors
|   |── outputs/              # Contains encrypted output scores
|   |── keys/                 # Public and secret keys for TenSEAL
|   |── carol_function/
|   |   |── carol_listener.py # Performs encrypted inference
|   |   |── main.py           # Triggers Carol when Alice uploads data
|   |   |── requirements.txt  # All requirements needed for code to run on system
|   |   |── utils.py          # I/O helpers for TenSEAL serialization
|   |   |── keys/
|   |   |   |── public.txt    # Public key copy (uploaded by Alice)
|   |── README.md                 # This file


# Running the Program
## Prerequisites
1. Python 3.10+
2. Required Python libraries:
   - tenseal
   - google-cloud-storage
   - numpy
3. Google Cloud SDK (gcloud auth login)
4. Must have 'alice_data' bucket under 'server-carol' project in GCP

Note: Everything is handled by the deploy.sh script. It installs dependencies, logs into GCP, and deploys cloud function carol-listener. All that must be done is creating a 'server-carol' project in GCP and then creating a bucket 'alice_data' under that project to ensure seamless implementation.

Once the project and bucket are created, run the deployment script in terminal with:
    chmod +x deploy.sh
    ./deploy.sh
Then, run the program with the line:
    python3 main.py
NOTE: This refers to the main.py **OUTSIDE** of carol_function/

-------

## Fraud Score Interpretation
After decryption, the fraud score is interpreted as:

| Score Range | Risk Level  | Action                        |
|-------------|-------------|-------------------------------| 
| 0 - 20      | Low         | No action needed.             |
| 21 - 50     | Moderate    | Review transaction.           |
| 51+         | High        | Potential fraud, investigate. |

-------

## Performance Highlights
- Computation time is longer than plaintext inference due to encryption overhead.
- CKKS introduces small approximation errors but retains high numerical accuracy (~1e-4).
- Suitable trade-off between privacy and performance for small-to-moderate inference tasks.

-------

## Evaluation of Encryption Efficiency
Homomorphic encryption, while offering strong privacy guarantees, introduce significant overhead. This section evaluates the encryption efficiency of my implementation in terms of computations cost, ciphertext size, and overall feasibility.

### Performance Metrics

| Metric                       | Value (Approximate)                   |
|------------------------------|---------------------------------------|
| Encryption Time (Alice)      | ~1.2 seconds for 6D vector            |
| Inference Time (Carol)       | ~3.5 seconds for 1 forward pass       |
| Decryption Time (Alice)      | ~0.3 seconds                          |
| Encrypted Input Size         | ~3.6 KB (CKKS-serialized vector)      |
| Encrypted Output Size        | ~1.2 KB (1 encrypted float)           |
| Model Complexity             | 6 → 3 → 1 (no nonlinear activation)   |

### Encryption Parameters Recap

| Parameter             | Value               |
|-----------------------|---------------------|
| Scheme                | CKKS (approximate)  |
| 'poly_modulus_degree' | 8192                |
| 'coeff_mod_bit_sizes' | [60, 40, 40, 60]    |
| 'global_scale'        | 2^40                |

These parameters were chosen to have a balance between **numerical accuracy**, **noise budget**, and **computational feasibility**

### Observations
- CKKS supports **vectorized operations** - encrypting and operating on entire vectors at once improves manageability.
- **Noise growth** is controlled by limiting depth - only dot product and linear combinations are performed.
- The size of the ciphertext and computation time grow **linearly with vector and model depth**.
- The encryption scheme allows **approximate but stable outputs**, making it suitable for the fraud score scenario.

### Practical Implications
- While slower than plaintext inference, the system is **practical for low-latency applications** where privacy is critical (e.g. secure fraud screening, medical predictions).
- Encryption and inference can be performed on modest hardware with no special requirements.
- Minimal communication overhead (~5KB round-trip) makes it deployable in real-time cloud settings.

-------

## Limitations
- No nonlinear activations due to homomorphic constraints (no ReLU, sigmoid).
- Model architecture is shallow to keep noise and scale manageable
