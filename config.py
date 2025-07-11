import os
from dotenv import load_dotenv

load_dotenv()

WPP_TOKEN = os.getenv("WPP_TOKEN")
WPP_FONE = os.getenv("WPP_FONE")
WPP_IS_GROUP = os.getenv("WPP_IS_GROUP")
WPP_ROUTE = os.getenv("WPP_ROUTE")

DB_ENDERECO = os.getenv("DB_ENDERECO")
DB_PORTA = os.getenv("DB_PORTA")
DB_USUARIO = os.getenv("DB_USUARIO")
DB_SENHA = os.getenv("DB_SENHA")
DB_NOME = os.getenv("DB_NOME")