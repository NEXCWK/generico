# Relatório Semanal Nex

Automação que gera e envia, toda segunda-feira às 13h (horário de Brasília),
um relatório semanal de performance comercial (Leads, Oportunidades, Vendas,
Investimento em Ads e ROAS) por linha de produto, em HTML com a identidade
visual do Nex, anexado a um e-mail para `felipe@nex.work`.

## Status

Em construção. O template HTML e a lógica de agregação/comparação já estão
prontos e testados com dados fictícios (veja `scripts/render_preview.py`).
As integrações reais (Reportei, painel de vendas, envio de e-mail) dependem
de credenciais que ainda precisam ser configuradas — veja abaixo.

## Período do relatório

Segunda-feira 13h01 até a segunda-feira seguinte 12h30 (horário de Brasília).
Enviado no mesmo dia (segunda, data final do período) às 13h.

## Linhas de produto cobertas

- Escritórios Privativos (soma dos dois funis/campanhas, um por unidade)
- Compartilhados
- Salas de Reunião
- Escritório Virtual

Qualquer outra linha/produto encontrada nas plataformas de origem é ignorada.
Funis do CRM e campanhas do Google Ads são agrupados por linha usando
similaridade de nome (ex: "Escritório Privativo - Unidade A" e "Escritório
Privativo - Unidade B" viram uma única linha "Escritórios Privativos").

## Estrutura

```
templates/report.html.j2       Template do relatório (Nex design system)
scripts/weekly_report/
  constants.py                 Linhas de produto e labels das métricas
  formatting.py                Formatação pt-BR (moeda, %, inteiros)
  report_builder.py            Agregação, comparativos (WoW e D2M), ROAS
  render.py                    Renderização Jinja2 -> HTML
scripts/render_preview.py      Gera uma prévia com dados fictícios
```

## Variáveis de ambiente necessárias (a configurar)

| Variável | Descrição |
|---|---|
| `REPORTEI_API_TOKEN` | Token de API do Reportei (RD Marketing, RD CRM, Google Ads) |
| `NEXPAINEL_EMAIL` | Login do painel `nexpainel.lovable.app` |
| `NEXPAINEL_PASSWORD` | Senha do painel `nexpainel.lovable.app` |
| `GMAIL_SENDER_ADDRESS` | Endereço @nex.work que envia o relatório |
| `GMAIL_APP_PASSWORD` | App Password do Gmail/Workspace para esse endereço |
| `REPORT_RECIPIENTS` | Destinatários do relatório, separados por vírgula (default: `felipe@nex.work, bruna@nexcoworking.com.br`) |

Essas variáveis devem ser configuradas como **Environment Variables no
ambiente do Claude Code Remote** usado por esta automação (não em um
arquivo `.env` local, que não persiste entre execuções agendadas).

## Rodando a prévia (sem credenciais)

```bash
pip install -r requirements.txt
python scripts/render_preview.py scripts/preview_output.html
```
