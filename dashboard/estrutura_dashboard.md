# Estrutura do Dashboard — Qualidade Têxtil

Guia de montagem para Power BI ou Metabase, usando a tabela `inspecoes`
(ou o CSV tratado) como fonte. Pensado para caber numa tela só e responder,
de cara: "como estamos hoje e onde estão os riscos".

## 1. KPIs (cards de número único)

Seis cards no topo, sempre visíveis, respondendo aos filtros ativos:

| KPI | Cálculo | Por quê |
|---|---|---|
| Taxa de Reprovação Geral | Reprovados / Total × 100 | Termômetro geral de qualidade |
| Total de Inspeções | COUNT(*) | Contextualiza o volume por trás da taxa |
| Total de Lotes Reprovados | COUNT(*) WHERE status = 'Reprovado' | Número absoluto para dimensionar retrabalho |
| Gramatura Média | AVG(gramatura) | Detecta deriva de processo mesmo sem reprovação |
| Pior Fornecedor do Período | Fornecedor com maior taxa de reprovação | Aponta onde agir primeiro |
| Variação vs. Período Anterior | Taxa atual − taxa do período anterior (p.p.) | Mostra se a qualidade está melhorando ou piorando |

**Atenção ao ler o KPI "Pior Fornecedor"** com um filtro de período curto
(ex.: um mês): com poucas inspeções, um fornecedor bom pode aparecer mal
colocado por puro efeito de amostra pequena — cruze sempre com "Total de
Inspeções" daquele fornecedor antes de tirar conclusão.

## 2. Filtros (aplicados a todo o dashboard)

- **Período** (data da inspeção) — intervalo, com atalhos para "últimos 30
  dias" / "trimestre atual" / "ano"
- **Fornecedor** — múltipla escolha
- **Tipo de Malha** — múltipla escolha
- **Cor** — múltipla escolha
- **Status** — Aprovado / Reprovado

## 3. Gráficos

1. **Barra horizontal — Taxa de reprovação por fornecedor**, ordenada do
   pior para o melhor. O gráfico mais acionável do dashboard: quem aparece
   no topo é quem precisa de uma conversa de qualidade.

2. **Linha — Evolução da taxa de reprovação ao longo do tempo** (semanal
   ou mensal), com uma linha de referência/meta. Serve para flagrar
   sazonalidade (ex.: pico de fim de ano) antes que vire crônico.

3. **Pareto — Top defeitos** (barra + linha de % acumulado). Responde "se
   eu só puder atacar um problema este mês, qual é?".

4. **Tabela matriz — Fornecedor × Tipo de Malha × Defeito**, com
   drill-down. É onde o gestor confirma se um problema é do fornecedor, do
   tipo de material, ou dos dois juntos.

5. **Mapa de calor — Fornecedor × Mês**, colorido pela taxa de reprovação.
   Cruza os dois eixos de risco (quem e quando) numa visão só.

### Observação prática sobre gramatura

Nem Power BI nem Metabase trazem boxplot nativo pronto — esse é o lugar
certo do notebook para essa análise em detalhe. No dashboard, troque por
algo que a ferramenta desenha bem e carrega o mesmo sinal:

- **Power BI**: visual customizado "Box and Whisker" (AppSource, gratuito),
  ou uma tabela com Mín / Média / Máx / % fora da faixa por tipo de malha.
- **Metabase**: tabela ou barra com "% de lotes fora da faixa técnica" por
  tipo de malha — menos bonito que um boxplot, mas comunica a mesma
  decisão de negócio.

## 4. Sugestão de layout

```
┌─────────────────────────────────────────────────────────┐
│  [Taxa Reprov.] [Total Insp.] [Reprovados] [Gram. Média] │
│  [Pior Fornecedor]           [Variação vs. período]      │
├──────────────────────────────┬────────────────────────────┤
│ Taxa de reprovação            │ Evolução da taxa            │
│ por fornecedor (barra)        │ de reprovação (linha)       │
├──────────────────────────────┼────────────────────────────┤
│ Pareto de defeitos             │ Mapa de calor                │
│ (barra + % acumulado)          │ Fornecedor × Mês             │
├─────────────────────────────────────────────────────────┤
│ Tabela detalhada (drill-down): Fornecedor × Tipo × Defeito │
└─────────────────────────────────────────────────────────┘
```
