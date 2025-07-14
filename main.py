from fastapi import FastAPI, HTTPException, Depends
import asyncpg
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json
import config  # Arquivo de configuração (config.py)
from datetime import datetime, timezone

# --- Modelos Pydantic para Validação do Webhook ---
# O modelo de Cliente foi removido.

class Charge(BaseModel):
    id: str
    code: Optional[str] = None
    amount: Optional[int] = None
    paid_amount: Optional[int] = None
    status: Optional[str] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    paid_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    order: Optional[Dict[str, Any]] = None

class Order(BaseModel):
    id: str
    code: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    closed: Optional[bool] = None
    # O campo 'customer' agora é um dicionário genérico para extrair o ID
    customer: Optional[Dict[str, Any]] = None
    charges: Optional[List[Charge]] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StoneWebhookData(BaseModel):
    id: str
    code: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    closed: Optional[bool] = None
    customer: Optional[Dict[str, Any]] = None
    charges: Optional[List[Charge]] = []
    paid_amount: Optional[int] = None
    payment_method: Optional[str] = None
    paid_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class StoneWebhook(BaseModel):
    id: str
    type: str
    created_at: str
    data: StoneWebhookData
    account: Dict[str, Any]

# --- Inicialização da Aplicação e Conexão com o Banco ---

app = FastAPI(
    title="Webhook Stone API",
    description="API para receber e processar webhooks da Stone.",
    version="1.1.0"
)

db_pool: Optional[asyncpg.Pool] = None

async def get_db_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = await asyncpg.create_pool(
                user=config.DB_USUARIO,
                password=config.DB_SENHA,
                database=config.DB_NOME,
                host=config.DB_ENDERECO,
                port=config.DB_PORTA,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Não foi possível conectar ao banco de dados: {e}")
    return db_pool

@app.on_event("startup")
async def startup_event():
    await get_db_pool()

@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()

# --- Funções Auxiliares ---

def parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
    if not date_string:
        return None
    try:
        if date_string.endswith('Z'):
            date_string = date_string[:-1] + '+00:00'
        return datetime.fromisoformat(date_string)
    except (ValueError, TypeError):
        try:
            return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")
        except (ValueError, TypeError):
            return None

# --- Funções de Processamento de Dados ---

# A função process_customer foi removida.

async def process_order(conn: asyncpg.Connection, order_data: StoneWebhookData):
    """Insere ou atualiza um pedido no banco de dados."""
    # Extrai o ID do cliente do dicionário, se existir
    customer_id = order_data.customer.get("id") if order_data.customer else None
    await conn.execute(
        """
        INSERT INTO pedidos_stone (id, codigo, valor, moeda, status, fechado, cliente_id, criado_em, atualizado_em)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO UPDATE SET
            codigo = EXCLUDED.codigo,
            valor = EXCLUDED.valor,
            status = EXCLUDED.status,
            fechado = EXCLUDED.fechado,
            cliente_id = EXCLUDED.cliente_id,
            atualizado_em = EXCLUDED.atualizado_em;
        """,
        order_data.id,
        order_data.code,
        order_data.amount,
        order_data.currency,
        order_data.status,
        order_data.closed,
        customer_id,
        parse_datetime(order_data.created_at),
        parse_datetime(order_data.updated_at),
    )

async def process_charge(conn: asyncpg.Connection, charge_data: Charge, order_id: Optional[str]):
    """Insere ou atualiza uma cobrança no banco de dados."""
    await conn.execute(
        """
        INSERT INTO cobrancas_stone (id, pedido_id, codigo, valor, valor_pago, status, moeda, metodo_pagamento, pago_em, criado_em, atualizado_em)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        ON CONFLICT (id) DO UPDATE SET
            pedido_id = EXCLUDED.pedido_id,
            valor_pago = EXCLUDED.valor_pago,
            status = EXCLUDED.status,
            pago_em = EXCLUDED.pago_em,
            atualizado_em = EXCLUDED.atualizado_em;
        """,
        charge_data.id,
        order_id,
        charge_data.code,
        charge_data.amount,
        charge_data.paid_amount,
        charge_data.status,
        charge_data.currency,
        charge_data.payment_method,
        parse_datetime(charge_data.paid_at),
        parse_datetime(charge_data.created_at),
        parse_datetime(charge_data.updated_at),
    )

# --- Endpoints da API ---

@app.post("/webhook/stone", status_code=200)
async def stone_webhook(webhook_data: StoneWebhook, pool: asyncpg.Pool = Depends(get_db_pool)):
    async with pool.acquire() as conn:
        async with conn.transaction():
            try:
                await conn.execute(
                    """
                    INSERT INTO webhooks_stone (id, tipo, payload, criado_em)
                    VALUES ($1, $2, $3::jsonb, $4)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    webhook_data.id,
                    webhook_data.type,
                    webhook_data.model_dump_json(),
                    parse_datetime(webhook_data.created_at),
                )

                data = webhook_data.data
                event_type = webhook_data.type

                if event_type.startswith("order."):
                    # A chamada para process_customer foi removida.
                    await process_order(conn, data)
                    
                    if data.charges:
                        for charge in data.charges:
                            await process_charge(conn, charge, order_id=data.id)

                elif event_type.startswith("charge."):
                    charge_obj = Charge(**data.model_dump())
                    order_id = charge_obj.order.get("id") if charge_obj.order else None
                    await process_charge(conn, charge_obj, order_id=order_id)

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Falha ao processar o webhook: {e}"
                )

    return {"status": "sucesso", "message": "Webhook recebido e processado."}

@app.get("/pedidos/{pedido_id}")
async def get_pedido(pedido_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    async with pool.acquire() as conn:
        order_row = await conn.fetchrow(
            "SELECT * FROM pedidos_stone WHERE id = $1", pedido_id
        )

        if not order_row:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        charges_rows = await conn.fetch(
            "SELECT * FROM cobrancas_stone WHERE pedido_id = $1", order_row['id']
        )
        
        order_dict = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in dict(order_row).items()}
        charges_list = [
            {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in dict(row).items()}
            for row in charges_rows
        ]

    return {
        "pedido": order_dict,
        "cobrancas": charges_list
    }