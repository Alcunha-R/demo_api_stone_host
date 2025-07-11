from fastapi import FastAPI, HTTPException
import asyncpg
from pydantic import BaseModel
from typing import Dict, Any
import json
import config
from datetime import datetime

app = FastAPI()

db_pool = None

# Helper function to parse date strings
def parse_datetime(date_string: str) -> datetime:
    if not date_string:
        return None

    # Sanitize the date string
    if date_string.endswith('ZZ'):
        date_string = date_string[:-1]

    try:
        # Truncate to 6 microsecond digits before parsing
        if '.' in date_string:
            parts = date_string.split('.')
            # Ensure the fractional part is not empty
            if len(parts) > 1 and parts[1]:
                # Remove the 'Z' before truncating
                if parts[1].endswith('Z'):
                    fractional = parts[1][:-1]
                else:
                    fractional = parts[1]
                
                fractional = fractional[:6]
                date_string = parts[0] + '.' + fractional + 'Z'

        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
    except (ValueError, TypeError):
        # Fallback for other formats if needed
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f%z"):
            try:
                return datetime.strptime(date_string, fmt)
            except (ValueError, TypeError):
                continue
    raise ValueError(f"Unable to parse date: {date_string}")

async def get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            user=config.DB_USUARIO,
            password=config.DB_SENHA,
            database=config.DB_NOME,
            host=config.DB_ENDERECO,
            port=config.DB_PORTA,
        )
    return db_pool

@app.on_event("startup")
async def startup():
    await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

class StoneWebhook(BaseModel):
    id: str
    account: Dict[str, Any]
    type: str
    created_at: str
    data: Dict[str, Any]

@app.post("/webhook/stone")
async def stone_webhook(webhook_data: StoneWebhook):
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            try:
                await connection.execute(
                    """
                    INSERT INTO webhooks_stone (id, tipo, payload, criado_em)
                    VALUES ($1, $2, $3::jsonb, $4)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    webhook_data.id,
                    webhook_data.type,
                    json.dumps(webhook_data.dict()),
                    parse_datetime(webhook_data.created_at),
                )

                order_data = webhook_data.data.get("order")
                if order_data:
                    await connection.execute(
                        """
                        INSERT INTO pedidos_stone (id, codigo, valor, moeda, status, fechado, cliente_id, criado_em, atualizado_em)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (id) DO UPDATE SET
                            codigo = EXCLUDED.codigo,
                            valor = EXCLUDED.valor,
                            status = EXCLUDED.status,
                            fechado = EXCLUDED.fechado,
                            atualizado_em = EXCLUDED.atualizado_em;
                        """,
                        order_data.get("id"),
                        order_data.get("code"),
                        order_data.get("amount"),
                        order_data.get("currency"),
                        order_data.get("status"),
                        order_data.get("closed"),
                        order_data.get("customer_id"),
                        parse_datetime(order_data.get("created_at")),
                        parse_datetime(order_data.get("updated_at")),
                    )

                if webhook_data.type.startswith("charge."):
                    charge_data = webhook_data.data
                    await connection.execute(
                        """
                        INSERT INTO cobrancas_stone (id, pedido_id, codigo, valor, valor_pago, status, moeda, metodo_pagamento, pago_em, criado_em, atualizado_em)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (id) DO UPDATE SET
                            valor_pago = EXCLUDED.valor_pago,
                            status = EXCLUDED.status,
                            pago_em = EXCLUDED.pago_em,
                            atualizado_em = EXCLUDED.atualizado_em;
                        """,
                        charge_data.get("id"),
                        order_data.get("id") if order_data else None,
                        charge_data.get("code"),
                        charge_data.get("amount"),
                        charge_data.get("paid_amount"),
                        charge_data.get("status"),
                        charge_data.get("currency"),
                        charge_data.get("payment_method"),
                        parse_datetime(charge_data.get("paid_at")),
                        parse_datetime(charge_data.get("created_at")),
                        parse_datetime(charge_data.get("updated_at")),
                    )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Falha ao processar e armazenar o webhook: {e}")

    return {"status": "sucesso", "message": "Webhook processado com sucesso"}

@app.get("/pedidos/{pedido_id}")
async def get_pedido(pedido_id: str):
    pool = await get_db_pool()
    async with pool.acquire() as connection:
        order_row = await connection.fetchrow(
            "SELECT * FROM pedidos_stone WHERE id = $1", pedido_id
        )

        if not order_row:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")

        charges_rows = await connection.fetch(
            "SELECT * FROM cobrancas_stone WHERE pedido_id = $1", order_row['id']
        )

    return {
        "pedido": dict(order_row),
        "cobrancas": [dict(row) for row in charges_rows]
    }