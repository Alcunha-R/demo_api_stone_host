DROP TABLE IF EXISTS cobrancas_stone;
DROP TABLE IF EXISTS pedidos_stone;
DROP TABLE IF EXISTS webhooks_stone;

-- Tabela para registrar todos os webhooks recebidos para auditoria e depuração
CREATE TABLE webhooks_stone (
    id VARCHAR(255) PRIMARY KEY,     
    tipo VARCHAR(255) NOT NULL,       
    payload JSONB NOT NULL,          
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    processado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para armazenar informações dos pedidos
CREATE TABLE pedidos_stone (
    id VARCHAR(255) PRIMARY KEY,     
    codigo VARCHAR(255),             
    valor INTEGER,                  
    moeda VARCHAR(3),
    status VARCHAR(50),
    fechado BOOLEAN,
    cliente_id VARCHAR(255),
    criado_em TIMESTAMP WITH TIME ZONE,
    atualizado_em TIMESTAMP WITH TIME ZONE
);

-- Tabela para armazenar informações das cobranças, vinculadas a um pedido
CREATE TABLE cobrancas_stone (
    id VARCHAR(255) PRIMARY KEY,     
    pedido_id VARCHAR(255) NOT NULL,
    codigo VARCHAR(255),
    valor INTEGER,                  
    valor_pago INTEGER,
    status VARCHAR(50),
    moeda VARCHAR(3),
    metodo_pagamento VARCHAR(50),
    pago_em TIMESTAMP WITH TIME ZONE,
    criado_em TIMESTAMP WITH TIME ZONE,
    atualizado_em TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_cobrancas_pedido_id ON cobrancas_stone(pedido_id);
CREATE INDEX idx_pedidos_cliente_id ON pedidos_stone(cliente_id);