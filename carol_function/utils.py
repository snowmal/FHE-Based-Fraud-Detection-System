"""
utils.py
    Utility fruntions for reading/writing encrypted data using base64 encoding.
    https://www.youtube.com/watch?v=2qkCLaeD7pA
"""

import base64
def write_data(filename:str, data:bytes):
    """
        Encode bytes data into based64 and write encrypted data into file.
    """
    with open(filename, 'wb') as file:
        file.write(base64.b64encode(data))

def read_data(filename:str) -> bytes:
    """
        Read base64 data from encrypted file and convert it to bytes.
    """
    with open(filename, 'rb') as file:
        return base64.b64decode(file.read())
