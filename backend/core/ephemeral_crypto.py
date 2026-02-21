import os
import json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization

class EphemeralCrypto:
    @staticmethod
    def generate_rsa_keypair():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def generate_session_key():
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def encrypt_payload(key: bytes, data: bytes) -> bytes:
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    @staticmethod
    def decrypt_payload(key: bytes, encrypted_data: bytes) -> bytes:
        aesgcm = AESGCM(key)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def wrap_metadata(public_key, metadata_dict: dict) -> str:
        data = json.dumps(metadata_dict).encode()
        wrapped = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(wrapped).decode()

    @staticmethod
    def unwrap_metadata(private_key, wrapped_b64: str) -> dict:
        wrapped = base64.b64decode(wrapped_b64)
        data = private_key.decrypt(
            wrapped,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return json.loads(data.decode())

    @staticmethod
    def wrap_metadata_hybrid(public_key, metadata_dict: dict) -> str:
        """Hybrid encryption: RSA wraps an AES key, which encrypts the large metadata."""
        aes_key = EphemeralCrypto.generate_session_key()
        data = json.dumps(metadata_dict).encode()
        encrypted_metadata = EphemeralCrypto.encrypt_payload(aes_key, data)
        
        wrapped_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        # For RSA-4096, wrapped_key is always 512 bytes
        combined = wrapped_key + encrypted_metadata
        return base64.b64encode(combined).decode()

    @staticmethod
    def unwrap_metadata_hybrid(private_key, wrapped_b64: str) -> dict:
        """Unwraps hybrid encrypted metadata."""
        combined = base64.b64decode(wrapped_b64)
        wrapped_key = combined[:512]
        encrypted_metadata = combined[512:]
        
        aes_key = private_key.decrypt(
            wrapped_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        data = EphemeralCrypto.decrypt_payload(aes_key, encrypted_metadata)
        return json.loads(data.decode())

    @staticmethod
    def hash_face(encoding_list: list) -> str:
        data = json.dumps(encoding_list).encode()
        digest = hashes.Hash(hashes.SHA256())
        digest.update(data)
        return base64.b64encode(digest.finalize()).decode()
