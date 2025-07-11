-- Este script é para PostgreSQL.

-- Exclui as tabelas na ordem inversa de dependência se existirem (para uma configuração limpa)
DROP TABLE IF EXISTS cobrancas_stone;
DROP TABLE IF EXISTS pedidos_stone;
DROP TABLE IF EXISTS webhooks_stone;

-- Tabela para registrar todos os webhooks recebidos para auditoria e depuração
CREATE TABLE webhooks_stone (
    id VARCHAR(255) PRIMARY KEY,      -- O ID do evento do webhook, ex: "hook_j0R8BYh0dS123RQ34"
    tipo VARCHAR(255) NOT NULL,       -- O tipo do evento, ex: "charge.paid"
    payload JSONB NOT NULL,           -- O payload completo do webhook
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    processado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para armazenar informações dos pedidos
CREATE TABLE pedidos_stone (
    id VARCHAR(255) PRIMARY KEY,      -- O ID do pedido, ex: "or_bqopZVqtEtr123F45"
    codigo VARCHAR(255),              -- O código do pedido, ex: "D3MGIQI835"
    valor INTEGER,                    -- Valor em centavos
    moeda VARCHAR(3),
    status VARCHAR(50),
    fechado BOOLEAN,
    cliente_id VARCHAR(255),
    criado_em TIMESTAMP WITH TIME ZONE,
    atualizado_em TIMESTAMP WITH TIME ZONE
);

-- Tabela para armazenar informações das cobranças, vinculadas a um pedido
CREATE TABLE cobrancas_stone (
    id VARCHAR(255) PRIMARY KEY,      -- O ID da cobrança, ex: "ch_NRPl6mouLuZ123FR4"
    pedido_id VARCHAR(255) NOT NULL REFERENCES pedidos_stone(id), -- Chave estrangeira para a tabela de pedidos
    codigo VARCHAR(255),
    valor INTEGER,                    -- Valor em centavos
    valor_pago INTEGER,
    status VARCHAR(50),
    moeda VARCHAR(3),
    metodo_pagamento VARCHAR(50),
    pago_em TIMESTAMP WITH TIME ZONE,
    criado_em TIMESTAMP WITH TIME ZONE,
    atualizado_em TIMESTAMP WITH TIME ZONE
);

-- Cria índices para buscas mais rápidas
CREATE INDEX idx_cobrancas_pedido_id ON cobrancas_stone(pedido_id);
CREATE INDEX idx_pedidos_cliente_id ON pedidos_stone(cliente_id);

-- Concede permissões se necessário (substitua 'seu_usuario' pelo seu usuário de banco de dados real)
-- GRANT ALL ON TABLE webhooks_stone, pedidos_stone, cobrancas_stone TO seu_usuario;
