# 🗺️ Mapa de Contexto — NewB Seguros

Um único arquivo de leitura rápida para qualquer agente de IA operar na NewB Seguros.

## 🏢 A Empresa
- **Nome:** NewB Seguros
- **Tipo:** Corretora de seguros (consultora estratégica)
- **Site:** https://newbseguros.com.br
- **WhatsApp comercial:** +55 11 99454-6222
- **Missão:** Proteger pessoas e empresas com soluções diferenciadas e personalizadas
- **Diferenciais:** Transparência, personalização, parceria com principais seguradoras

## 👥 Equipe e Emails
| Email | Responsável | Função |
|-------|-------------|--------|
| abm@newbseguros.com.br | ABM | — |
| adimin@newbseguros.com.br | Admin | Administração |
| barbara@newbseguros.com.br | Barbara Vieira | Consultora |
| comercial@newbseguros.com.br | Comercial | Vendas |
| contato@newbseguros.com.br | Contato | Atendimento |
| drive@newbseguros.com.br | Google Drive | Arquivos |
| faturamento@newbseguros.com.br | Faturamento | Financeiro |
| joseaugusto@newbseguros.com.br | José Augusto Pascarelli | — |
| nane@newbseguros.com.br | Nane | — |
| newbseguros@newbseguros.com.br | Newb Seguros | Principal |
| newton@newbseguros.com.br | Newton Barbosa Pascarelli | Consultor |
| rhability@newbseguros.com.br | RH ABILITY | RH |
| suporte@newbseguros.com.br | Suporte | Atendimento |
| suporte1@newbseguros.com.br | Joao Pedro | Suporte |
| suporte2@newbseguros.com.br | Gustavo Henrique | Suporte |

## 📱 WhatsApp Monitorado
| Número | Responsável | Bridge |
|--------|-------------|--------|
| Principal (bot) | Bot NewB | porta 3000 |
| +55 11 94774-6368 | Anne | porta 3001 |
| +55 11 98834-3323 | Ana | porta 3002 |
| +55 11 92782-9229 | Gustavo | porta 3003 |

**Grupo admins:** Nane - Admins (ID WhatsApp: `120363430402111272@g.us`)

## 🤖 Automações Ativas
| Cron | Horário | O que faz |
|------|---------|----------|
| Monitor Emails | 9h, 13h, 17h | Verifica 15 caixas, envia resumo no grupo |
| Export Dashboard | 9h, 13h, 17h | Exporta JSON para GitHub (dashboard) |
| Consultas Grupo | a cada 2 min | Responde perguntas no grupo WhatsApp |

## 📊 Dashboard
- **URL:** https://newbdash.com.br
- **Repo:** github.com/marcelodidier/newbseguros-dashboard
- **Login:** marcelodidier27@gmail.com
- **Dados:** JSON estáticos em `/data/*.json` atualizados 3x/dia

## 🏗️ Infraestrutura
- **Servidor:** 172.16.0.2 (IP externo: 2.25.114.18)
- **Hosting:** Hostinger (Traefik como proxy externo)
- **Email server:** email-ssl.com.br porta 993/465 (IMAP/SMTP SSL)
- **WhatsApp bridge:** Node.js (Baileys) em localhost:3000-3003
- **API:** FastAPI Python em localhost:8000 (`/opt/data/newb_api/main.py`)
- **Banco:** SQLite `/opt/data/newb_api/newb.db` + logger `/opt/data/newb_log.db`

## 📁 Arquivos Importantes
```
/opt/data/
├── newb_monitor.py      # Monitor principal emails + WhatsApp
├── newb_export.py       # Exporta JSON para GitHub
├── newb_logger.py       # Logger SQLite de emails e WhatsApp
├── newb_group_query.py  # Responde perguntas no grupo
├── newb_seen_ids.json   # Estado do monitor
├── newb_log.db          # Banco de logs
└── newb_api/
    ├── main.py          # FastAPI backend
    ├── db.py            # Schema SQLite
    └── newb.db          # Banco principal

~/.local/bin/himalaya    # Cliente IMAP
~/.config/himalaya/      # Config e senhas das caixas
```

## 📦 Produtos NewB
**Pessoas Físicas:** Auto, Vida, Residência, Saúde, Dental, Viagem, Moto, Bike, Caminhão, Equipamentos Portáteis, RC, Náutico, Fiança Locatícia, Compreensivo

**Empresas:** Empresarial, Condomínio, D&O, E&O, Riscos Cibernéticos, Garantia, Transporte, Rural, Saúde Empresarial, Vida Global, Riscos de Engenharia, Eventos

## 🔑 Classificação de Emails
- 🔴 **urgente** — palavras: urgente, urgência, imediato
- 🟡 **cotacao** — cotação, orçamento, simular, proposta, quanto custa
- 🟡 **sinistro** — sinistro, acidente, dano, acionamento
- 🟡 **contratacao** — contratar, fechar, apólice, assinar
- 🟢 **renovacao** — renovação, vencimento, vigência
- 🟢 **duvida** — dúvida, informação, como funciona
- 🟢 **cancelamento** — cancelar, desistir

## 💬 Como Responder no Grupo
Quando alguém perguntar sobre emails ou WhatsApp no grupo Nane - Admins, o agente verifica os dados e responde. Exemplos que ativam a resposta:
- 'mensagens da Anne', 'emails', 'tem cotação nova', 'status', 'resumo'
