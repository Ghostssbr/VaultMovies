import sqlite3
from datetime import datetime, timedelta
import secrets

# Caminhos dos bancos de dados
DATABASE_API = "filmes.db"
DATABASE_MANGAS = "mangas.db"

# Função para resetar a tabela de chaves API

# Função para conectar ao banco de dados de chaves API
def get_db_connection_api():
    conn = sqlite3.connect(DATABASE_API)
    conn.row_factory = sqlite3.Row
    return conn

# Função para conectar ao banco de dados de mangás
def get_db_connection_mangas():
    conn = sqlite3.connect(DATABASE_MANGAS)
    conn.row_factory = sqlite3.Row
    return conn

# Função para gerar uma nova chave API (agora verifica se já existe uma ativa para o IP)
def gerar_chave(ip):
    conn = get_db_connection_api()
    cursor = conn.cursor()

    # Verificar se o IP já possui uma chave ativa
    cursor.execute("SELECT * FROM api_keys WHERE ip = ? AND expires_at > ?", (ip, datetime.now()))
    chave_existente = cursor.fetchone()

    if chave_existente:
        conn.close()
        return None  # Retorna None se já existir uma chave válida

    # Gerar nova chave e definir expiração para 24 horas
    chave = secrets.token_hex(16)
    expires_at = datetime.now() + timedelta(hours=24)

    cursor.execute("INSERT INTO api_keys (key, ip, expires_at) VALUES (?, ?, ?)", (chave, ip, expires_at))
    conn.commit()
    conn.close()
    
    return chave

# Função para verificar se uma chave API é válida
def verificar_chave(chave, ip):
    conn = get_db_connection_api()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_keys WHERE key = ? AND ip = ? AND expires_at > ?", (chave, ip, datetime.now()))
    chave_valida = cursor.fetchone()
    conn.close()
    return chave_valida is not None
