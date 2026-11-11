#!/usr/bin/env python3
"""
NewB Seguros — API Backend (FastAPI)
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
from datetime import datetime

DB_PATH    = "/opt/data/newb_api/newb.db"
LOG_DB     = "/opt/data/newb_log.db"

app = FastAPI(title="NewB Seguros API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_list(rows):
    return [dict(r) for r in rows]

# ── Stats / Dashboard ──────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    db = get_db()
    c = db.cursor()
    stats = {
        "cotacoes": {
            "total":    c.execute("SELECT COUNT(*) FROM cotacoes").fetchone()[0],
            "aguardando":  c.execute("SELECT COUNT(*) FROM cotacoes WHERE status='aguardando'").fetchone()[0],
            "em_cotacao":  c.execute("SELECT COUNT(*) FROM cotacoes WHERE status='em_cotacao'").fetchone()[0],
            "fechado":     c.execute("SELECT COUNT(*) FROM cotacoes WHERE status='fechado'").fetchone()[0],
        },
        "renovacoes": {
            "total":    c.execute("SELECT COUNT(*) FROM renovacoes").fetchone()[0],
            "urgente":  c.execute("SELECT COUNT(*) FROM renovacoes WHERE urgencia='urgente' AND status='pendente'").fetchone()[0],
            "breve":    c.execute("SELECT COUNT(*) FROM renovacoes WHERE urgencia='breve' AND status='pendente'").fetchone()[0],
        },
        "retomadas": {
            "total":       c.execute("SELECT COUNT(*) FROM retomadas").fetchone()[0],
            "em_contato":  c.execute("SELECT COUNT(*) FROM retomadas WHERE status='em_contato'").fetchone()[0],
            "sem_contato": c.execute("SELECT COUNT(*) FROM retomadas WHERE status='sem_contato'").fetchone()[0],
        },
        "clientes": {
            "total": c.execute("SELECT COUNT(*) FROM clientes").fetchone()[0],
        },
        "emails": {
            "nao_lidos": c.execute("SELECT COUNT(*) FROM emails_monitorados WHERE lido=0").fetchone()[0],
        },
    }
    db.close()

    # Dados do logger (newb_log.db)
    try:
        log = sqlite3.connect(LOG_DB)
        log.row_factory = sqlite3.Row
        today = datetime.now().strftime("%Y-%m-%dT00:00:00")
        stats["emails"]["hoje"] = log.execute(
            "SELECT COUNT(*) FROM email_messages WHERE logged_at >= ?", (today,)
        ).fetchone()[0]
        stats["whatsapp"] = {
            "hoje": log.execute(
                "SELECT COUNT(*) FROM wa_messages WHERE logged_at >= ? AND from_me=0", (today,)
            ).fetchone()[0],
            "total": log.execute("SELECT COUNT(*) FROM wa_messages WHERE from_me=0").fetchone()[0],
        }
        log.close()
    except Exception:
        stats["whatsapp"] = {"hoje": 0, "total": 0}

    return stats

# ── Cotações ──────────────────────────────────────────────────────

@app.get("/api/cotacoes")
def list_cotacoes(
    status: Optional[str] = None,
    responsavel: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0
):
    db = get_db()
    q = "SELECT * FROM cotacoes WHERE 1=1"
    params = []
    if status:
        q += " AND status=?"; params.append(status)
    if responsavel:
        q += " AND responsavel=?"; params.append(responsavel)
    q += " ORDER BY criado_em DESC LIMIT ? OFFSET ?"
    params += [limit, offset]
    rows = rows_to_list(db.execute(q, params).fetchall())
    total = db.execute("SELECT COUNT(*) FROM cotacoes").fetchone()[0]
    db.close()
    return {"items": rows, "total": total}

class CotacaoCreate(BaseModel):
    cliente_nome: str
    tipo_seguro: str
    canal: Optional[str] = None
    valor_estimado: Optional[float] = None
    responsavel: Optional[str] = None
    observacoes: Optional[str] = None
    status: Optional[str] = "aguardando"

@app.post("/api/cotacoes", status_code=201)
def create_cotacao(data: CotacaoCreate):
    db = get_db()
    cur = db.execute("""
        INSERT INTO cotacoes (cliente_nome, tipo_seguro, canal, valor_estimado, responsavel, observacoes, status)
        VALUES (?,?,?,?,?,?,?)
    """, (data.cliente_nome, data.tipo_seguro, data.canal, data.valor_estimado,
          data.responsavel, data.observacoes, data.status))
    db.commit()
    row = dict(db.execute("SELECT * FROM cotacoes WHERE id=?", (cur.lastrowid,)).fetchone())
    db.close()
    return row

@app.patch("/api/cotacoes/{id}")
def update_cotacao(id: int, status: str):
    db = get_db()
    db.execute("UPDATE cotacoes SET status=?, atualizado_em=datetime('now','localtime') WHERE id=?", (status, id))
    db.commit()
    row = db.execute("SELECT * FROM cotacoes WHERE id=?", (id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "Cotação não encontrada")
    return dict(row)

# ── Renovações ────────────────────────────────────────────────────

@app.get("/api/renovacoes")
def list_renovacoes(
    urgencia: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200)
):
    db = get_db()
    q = "SELECT * FROM renovacoes WHERE 1=1"
    params = []
    if urgencia:
        q += " AND urgencia=?"; params.append(urgencia)
    if status:
        q += " AND status=?"; params.append(status)
    q += " ORDER BY vencimento ASC LIMIT ?"
    params.append(limit)
    rows = rows_to_list(db.execute(q, params).fetchall())
    db.close()
    return {"items": rows, "total": len(rows)}

class RenovacaoCreate(BaseModel):
    cliente_nome: str
    cliente_email: Optional[str] = None
    tipo_seguro: str
    seguradora: Optional[str] = None
    vencimento: str
    premio_anual: Optional[float] = None
    responsavel: Optional[str] = None

@app.post("/api/renovacoes", status_code=201)
def create_renovacao(data: RenovacaoCreate):
    from datetime import date
    today = date.today().isoformat()
    dias = (datetime.strptime(data.vencimento, "%Y-%m-%d").date() - date.today()).days
    urgencia = "urgente" if dias <= 7 else ("breve" if dias <= 30 else "ok")
    db = get_db()
    cur = db.execute("""
        INSERT INTO renovacoes (cliente_nome, cliente_email, tipo_seguro, seguradora, vencimento, premio_anual, responsavel, urgencia)
        VALUES (?,?,?,?,?,?,?,?)
    """, (data.cliente_nome, data.cliente_email, data.tipo_seguro, data.seguradora,
          data.vencimento, data.premio_anual, data.responsavel, urgencia))
    db.commit()
    row = dict(db.execute("SELECT * FROM renovacoes WHERE id=?", (cur.lastrowid,)).fetchone())
    db.close()
    return row

# ── Retomadas ─────────────────────────────────────────────────────

@app.get("/api/retomadas")
def list_retomadas(status: Optional[str] = None, limit: int = Query(50, le=200)):
    db = get_db()
    q = "SELECT * FROM retomadas WHERE 1=1"
    params = []
    if status:
        q += " AND status=?"; params.append(status)
    q += " ORDER BY probabilidade DESC LIMIT ?"
    params.append(limit)
    rows = rows_to_list(db.execute(q, params).fetchall())
    db.close()
    return {"items": rows, "total": len(rows)}

# ── Clientes ──────────────────────────────────────────────────────

@app.get("/api/clientes")
def list_clientes(search: Optional[str] = None, limit: int = Query(50, le=200)):
    db = get_db()
    if search:
        rows = rows_to_list(db.execute(
            "SELECT * FROM clientes WHERE nome LIKE ? OR email LIKE ? LIMIT ?",
            (f"%{search}%", f"%{search}%", limit)
        ).fetchall())
    else:
        rows = rows_to_list(db.execute("SELECT * FROM clientes ORDER BY criado_em DESC LIMIT ?", (limit,)).fetchall())
    db.close()
    return {"items": rows, "total": len(rows)}

# ── Emails ────────────────────────────────────────────────────────

@app.get("/api/emails")
def list_emails(caixa: Optional[str] = None, lido: Optional[int] = None, limit: int = Query(50, le=200)):
    db = get_db()
    q = "SELECT * FROM emails_monitorados WHERE 1=1"
    params = []
    if caixa:
        q += " AND caixa=?"; params.append(caixa)
    if lido is not None:
        q += " AND lido=?"; params.append(lido)
    q += " ORDER BY criado_em DESC LIMIT ?"
    params.append(limit)
    rows = rows_to_list(db.execute(q, params).fetchall())
    db.close()
    return {"items": rows, "total": len(rows)}

# ── Health ────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# ── Log de Emails (newb_log.db) ───────────────────────────────────

@app.get("/api/emails/log")
def list_emails_log(
    account: Optional[str] = None,
    limit: int = Query(50, le=200),
    today_only: bool = False
):
    try:
        log = sqlite3.connect(LOG_DB)
        log.row_factory = sqlite3.Row
        q = "SELECT * FROM email_messages WHERE 1=1"
        params = []
        if account:
            q += " AND account=?"; params.append(account)
        if today_only:
            q += " AND logged_at >= ?"; params.append(datetime.now().strftime("%Y-%m-%dT00:00:00"))
        q += " ORDER BY logged_at DESC LIMIT ?"
        params.append(limit)
        rows = rows_to_list(log.execute(q, params).fetchall())
        log.close()
        return {"items": rows, "total": len(rows)}
    except Exception:
        return {"items": [], "total": 0}

# ── Log de WhatsApp (newb_log.db) ─────────────────────────────────

@app.get("/api/whatsapp/log")
def list_wa_log(
    bridge: Optional[str] = None,
    limit: int = Query(50, le=200),
    today_only: bool = False
):
    try:
        log = sqlite3.connect(LOG_DB)
        log.row_factory = sqlite3.Row
        q = "SELECT * FROM wa_messages WHERE from_me=0"
        params = []
        if bridge:
            q += " AND bridge_name=?"; params.append(bridge)
        if today_only:
            q += " AND logged_at >= ?"; params.append(datetime.now().strftime("%Y-%m-%dT00:00:00"))
        q += " ORDER BY logged_at DESC LIMIT ?"
        params.append(limit)
        rows = rows_to_list(log.execute(q, params).fetchall())
        log.close()
        return {"items": rows, "total": len(rows)}
    except Exception:
        return {"items": [], "total": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
