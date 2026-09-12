"""Gera uma chave Fernet para BACKUP_ENCRYPTION_KEY.

Execute uma vez em máquina confiável e salve a saída diretamente como secret.
Não coloque a chave em Git, README, print ou mensagem pública.
"""
from cryptography.fernet import Fernet

print(Fernet.generate_key().decode("ascii"))
