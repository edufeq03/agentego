import base64
import os

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-key-fallback-for-agente-academia")

def encrypt_key(plain_text: str) -> str:
    """Criptografa uma chave usando XOR simétrico com a JWT_SECRET e encode em Base64."""
    if not plain_text:
        return ""
    # XOR com a chave secreta repetida
    key = SECRET_KEY.encode('utf-8')
    data = plain_text.encode('utf-8')
    encrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_key(cipher_text: str) -> str:
    """Decriptografa uma chave criptografada com XOR simétrico."""
    if not cipher_text:
        return ""
    try:
        key = SECRET_KEY.encode('utf-8')
        data = base64.b64decode(cipher_text.encode('utf-8'))
        decrypted = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        return decrypted.decode('utf-8')
    except Exception:
        return ""
