import datetime
import asyncpg
import requests
import config

data_hora_atual = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

def enviar_wpp(titulo, mensagem):
    url = f"http://10.88.11.248:21465/api/{config.WPP_ROUTE}/send-message"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.WPP_TOKEN}"
    }

    payload = {
        "phone": config.WPP_FONE,
        "message": f"*_+ Med Paciente_*\n\n`{titulo}` \n {data_hora_atual} \n> {mensagem}",
        "isGroup": config.WPP_IS_GROUP
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Erro ao enviar mensagem:", e)

def gera_debug(titulo, mensagem):
    try:
        print(f"+ Med Paciente > {titulo} - {mensagem}")
        enviar_wpp(titulo, mensagem) 
    except Exception as e:
        print(f"Erro ao gerar debug: {e}")

async def db_conexao():
    try:
        connection = await asyncpg.connect(
            user=config.DB_USUARIO,
            password=config.DB_SENHA,
            database=config.DB_NOME,
            host=config.DB_ENDERECO,
            port=config.DB_PORTA,
        )
        return connection
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

async def db_notificacao_inserir(id_usuario: int, data: Notificacao):
    try:              
        connection = await db_conexao()

        query = """
            INSERT INTO notificacoes (titulo, descricao, body, id_usuario_origem, id_usuario_destino)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id;                    
        """
        result = await connection.fetch(query, data.titulo, data.descricao, data.body,
                                        id_usuario, data.id_usuario_destino)
        
        return (True, f"Notificação criada com sucesso!") if result else (False, "Erro ao criar Notificação")
    except Exception as e:
        gera_debug("Erro ao inserir Notificação",f'{data} \n> {e}')
        return str(e)
    finally:
        if connection:
            await connection.close()