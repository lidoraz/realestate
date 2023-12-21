from cryptography.fernet import Fernet
import base64
import os

# load_vault()



def get_new_key():
    key = Fernet.generate_key()
    key_base64 = base64.b64encode(key).decode('ascii')
    # use this for key for encrypt
    return key_base64


def encrypt(uid, key_base64=None):
    key_base64 = key_base64 or os.getenv("TELEGRAM_USERID_SALT")
    cipher_suite = Fernet(base64.b64decode(key_base64))
    buid = (uid).to_bytes(8, byteorder='big')
    encoded = cipher_suite.encrypt(buid)
    return base64.b64encode(encoded).decode('ascii')


def decrypt(base64_encoded, key_base64=None):
    key_base64 = key_base64 or os.getenv("TELEGRAM_USERID_SALT")
    cipher_suite = Fernet(base64.b64decode(key_base64))
    buid = base64.b64decode(base64_encoded)
    decoded = cipher_suite.decrypt(buid)
    uid = int.from_bytes(decoded, 'big')
    return uid


def test_crypto():
    uid = 12345
    key_base64 = get_new_key()
    b64_encrypted = encrypt(uid, key_base64)
    # print("b64_encrypted", b64_encrypted)
    b64_decrypted = decrypt(b64_encrypted, key_base64)
    # print(b64_decrypted)
    assert uid == b64_decrypted


if __name__ == '__main__':
    test_crypto()
