#!/usr/bin/env python3
"""
NewB Seguros — Inicialização do Banco de Dados SQLite
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "/opt/data/newb_api/newb.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Clientes ──────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nome        TEXT NOT NULL,
        email       TEXT,
        telefone    TEXT,
        cpf_cnpj    TEXT,
        tipo        TEXT DEFAULT 'PF',  -- PF ou PJ
        canal       TEXT,               -- site, whatsapp, email, indicacao
        responsavel TEXT,
        status      TEXT DEFAULT 'ativo',
        observacoes TEXT,
        criado_em   TEXT DEFAULT (datetime('now','localtime')),
        atualizado_em TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Cotações ──────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS cotacoes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id      INTEGER REFERENCES clientes(id),
        cliente_nome    TEXT,
        tipo_seguro     TEXT NOT NULL,
        seguradora      TEXT,
        canal           TEXT,
        valor_estimado  REAL,
        valor_proposta  REAL,
        status          TEXT DEFAULT 'aguardando',
        -- aguardando | em_cotacao | proposta_enviada | fechado | perdido
        responsavel     TEXT,
        origem          TEXT,  -- email, whatsapp, site
        observacoes     TEXT,
        criado_em       TEXT DEFAULT (datetime('now','localtime')),
        atualizado_em   TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Renovações ────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS renovacoes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id      INTEGER REFERENCES clientes(id),
        cliente_nome    TEXT NOT NULL,
        cliente_email   TEXT,
        tipo_seguro     TEXT NOT NULL,
        seguradora      TEXT,
        vencimento      TEXT NOT NULL,
        premio_anual    REAL,
        responsavel     TEXT,
        status          TEXT DEFAULT 'pendente',
        -- pendente | em_negociacao | renovado | cancelado
        urgencia        TEXT DEFAULT 'ok',  -- urgente | breve | ok
        observacoes     TEXT,
        criado_em       TEXT DEFAULT (datetime('now','localtime')),
        atualizado_em   TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Retomadas ─────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS retomadas (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id      INTEGER REFERENCES clientes(id),
        cliente_nome    TEXT NOT NULL,
        cliente_email   TEXT,
        ultimo_seguro   TEXT,
        venceu_em       TEXT,
        motivo_saida    TEXT,
        -- preco_alto | concorrente | mudanca | encerrou_atividade | outro
        ultimo_contato  TEXT,
        probabilidade   INTEGER DEFAULT 50,  -- 0-100%
        status          TEXT DEFAULT 'sem_contato',
        -- sem_contato | em_contato | perdido | recuperado
        responsavel     TEXT,
        observacoes     TEXT,
        criado_em       TEXT DEFAULT (datetime('now','localtime')),
        atualizado_em   TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Emails Monitorados ────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS emails_monitorados (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        caixa       TEXT NOT NULL,       -- abm, barbara, comercial, etc.
        email_id    TEXT,                -- ID no servidor IMAP
        assunto     TEXT,
        remetente   TEXT,
        data        TEXT,
        tags        TEXT,                -- cotacao, sinistro, etc. (JSON)
        prioridade  TEXT DEFAULT 'verde',
        lido        INTEGER DEFAULT 0,
        acao_tomada TEXT,
        criado_em   TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Mensagens WhatsApp ────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_mensagens (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        numero      TEXT NOT NULL,       -- Anne, Ana, Gustavo
        remetente   TEXT,
        telefone    TEXT,
        mensagem    TEXT,
        tipo        TEXT DEFAULT 'dm',   -- dm | grupo
        tags        TEXT,                -- JSON
        prioridade  TEXT DEFAULT 'verde',
        respondido  INTEGER DEFAULT 0,
        criado_em   TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Índices para performance ──────────────────────────────────
    c.execute("CREATE INDEX IF NOT EXISTS idx_cotacoes_status ON cotacoes(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_renovacoes_vencimento ON renovacoes(vencimento)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_retomadas_status ON retomadas(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_emails_caixa ON emails_monitorados(caixa)")

    conn.commit()

    # ── Dados de exemplo ──────────────────────────────────────────
    # Verifica se já tem dados
    count = c.execute("SELECT COUNT(*) FROM cotacoes").fetchone()[0]
    if count == 0:
        seed_data(c)
        conn.commit()
        print("✅ Dados de exemplo inseridos")

    conn.close()
    print(f"✅ Banco criado: {DB_PATH}")
    return DB_PATH

def seed_data(c):
    # Clientes exemplo
    clientes = [
        ("Carlos Ferreira", "carlos@empresa.com.br", "(11) 99999-1111", None, "PF", "site", "Barbara"),
        ("Mariana Souza", "mari@gmail.com", "(11) 99999-2222", None, "PF", "whatsapp", "Newton"),
        ("Construtora RB Ltda", "adm@construtorb.com.br", "(11) 3333-4444", "12.345.678/0001-90", "PJ", "indicacao", "Newton"),
        ("Fernanda Lima", "fe.lima@hotmail.com", "(11) 99999-3333", None, "PF", "site", "Barbara"),
        ("Loja Moda Fácil", "gerencia@modafacil.com.br", "(11) 3333-5555", "98.765.432/0001-10", "PJ", "indicacao", "Comercial"),
        ("Juliana Pereira", "ju.pereira@gmail.com", "(11) 99999-4444", None, "PF", "site", "Barbara"),
        ("Paulo Rodrigues", "paulo.r@empresa.com.br", "(11) 99999-5555", None, "PF", "email", "Newton"),
        ("Beatriz Costa", "beatrizcosta@gmail.com", "(11) 99999-6666", None, "PF", "whatsapp", "Barbara"),
    ]
    c.executemany("""INSERT INTO clientes (nome, email, telefone, cpf_cnpj, tipo, canal, responsavel)
                     VALUES (?,?,?,?,?,?,?)""", clientes)

    # Cotações
    cotacoes = [
        (1, "Carlos Ferreira", "Auto", "Porto Seguro", "site", 3800, None, "aguardando", "Barbara"),
        (2, "Mariana Souza", "Vida", "SulAmérica", "whatsapp", 2800, None, "em_cotacao", "Newton"),
        (3, "Construtora RB Ltda", "Empresarial", "Zurich", "indicacao", 18500, None, "em_cotacao", "Newton"),
        (4, "Fernanda Lima", "Residência", "Bradesco Seguros", "site", 1200, None, "proposta_enviada", "Barbara"),
        (5, "Loja Moda Fácil", "Empresarial", None, "indicacao", 12000, None, "aguardando", "Comercial"),
        (6, "Juliana Pereira", "Auto", None, "site", 3200, None, "aguardando", "Barbara"),
    ]
    c.executemany("""INSERT INTO cotacoes (cliente_id, cliente_nome, tipo_seguro, seguradora, canal, valor_estimado, valor_proposta, status, responsavel)
                     VALUES (?,?,?,?,?,?,?,?,?)""", cotacoes)

    # Renovações
    renovacoes = [
        ("Carlos Ferreira", "carlos@empresa.com.br", "Auto", "Porto Seguro", "2026-11-14", 4200, "Barbara", "pendente", "urgente"),
        ("Mariana Souza", "mari@gmail.com", "Vida", "SulAmérica", "2026-11-16", 2800, "Newton", "pendente", "urgente"),
        ("Construtora RB Ltda", "adm@construtorb.com.br", "Empresarial", "Zurich", "2026-11-17", 18500, "Newton", "em_negociacao", "urgente"),
        ("Fernanda Lima", "fe.lima@hotmail.com", "Residência", "Bradesco Seguros", "2026-11-30", 1200, "Barbara", "pendente", "breve"),
        ("Beatriz Costa", "beatrizcosta@gmail.com", "Auto", "Allianz", "2026-12-05", 3100, "Barbara", "pendente", "breve"),
    ]
    c.executemany("""INSERT INTO renovacoes (cliente_nome, cliente_email, tipo_seguro, seguradora, vencimento, premio_anual, responsavel, status, urgencia)
                     VALUES (?,?,?,?,?,?,?,?,?)""", renovacoes)

    # Retomadas
    retomadas = [
        ("Paulo Rodrigues", "paulo.r@empresa.com.br", "Auto", "2026-02-01", "preco_alto", "2026-11-03", 72, "em_contato", "Newton"),
        ("Beatriz Costa", "beatrizcosta@gmail.com", "Residência", "2026-01-15", "mudanca", "2026-10-28", 58, "em_contato", "Barbara"),
        ("Diego Martins", "diegomartins@outlook.com", "Vida", "2026-04-01", "preco_alto", None, 25, "sem_contato", "Newton"),
    ]
    c.executemany("""INSERT INTO retomadas (cliente_nome, cliente_email, ultimo_seguro, venceu_em, motivo_saida, ultimo_contato, probabilidade, status, responsavel)
                     VALUES (?,?,?,?,?,?,?,?,?)""", retomadas)

if __name__ == "__main__":
    init_db()
