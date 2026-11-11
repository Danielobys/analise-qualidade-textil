# Análise de Qualidade Têxtil · versão 2.0

Projeto de portfólio de Daniel Correia Lemos Júnior. Duas perguntas orientam esta versão. Quanto a composição dos tipos de malha altera a comparação entre fornecedores? Como saber o que já foi revisado e o que está liberado para corte?

Acesse o [painel público da versão 2](https://danielobys.github.io/analise-qualidade-textil/v2/) ou execute o pipeline para abrir `resultado/dashboard.html` no navegador. O arquivo é autossuficiente e roda localmente. Os dados são sintéticos em todas as telas.

## O que mudou em relação à versão publicada

| Tema | Antes | Versão 2.0 |
|---|---|---|
| Unidade | Um registro por lote após limpeza | Lotes de 2024 preservados. Cenário independente com 500 rolos e datas de entrada, revisão, liberação e corte |
| Duplicatas | Primeira ocorrência por lote | Reconciliação quando os valores preenchidos concordam e quarentena se houver conflito |
| Medições | 99 lotes com gramatura ou torção ausente | 98 após recuperar a gramatura de LT2407-00394 na linha 2731 do CSV. As demais lacunas continuam nulas |
| Comparação | Taxas observadas e volume | Taxas observadas e padronizadas por tipo de malha, com pesos e contagens dos estratos |
| Distribuição | Visualizações de gramatura e evolução mensal | Média, mediana, desvio-padrão amostral e cobertura da medição por tipo. Taxas mensais com seus denominadores |
| Rastreabilidade | Consulta por lote | Consulta por lote e rolo, ficha técnica da simulação, ordem de corte, log de tratamento e reconciliação de metros |

O CSV tratado da v1 e o CSV de lotes da v2 coincidem campo a campo nos 4.980 lotes, com uma diferença de conteúdo. A medição de 222,5 g/m² foi recuperada de uma cópia compatível. A taxa global continua em 1.309 de 4.980 (26,3%).

## Resultados que podem ser reproduzidos

### Lotes de 2024

| Fornecedor sintético | Reprovados / lotes | Observada | Padronizada |
|---|---:|---:|---:|
| A | 266 / 1.178 | 22,6% | 22,5% |
| B | 447 / 956 | 46,8% | 46,6% |
| C | 233 / 1.075 | 21,7% | 21,8% |
| D | 227 / 965 | 23,5% | 23,3% |
| E | 136 / 806 | 16,9% | 17,0% |

A padronização direta calcula a taxa de cada fornecedor dentro de cada tipo de malha e pondera as taxas pelos pesos do conjunto completo de 4.980 lotes. Todos os fornecedores têm dados nos cinco tipos. A ordem das taxas permanece a mesma, com alteração máxima de cerca de 0,2 ponto percentual. Na simulação, o próximo passo para investigar a diferença entre B e os demais seria examinar os defeitos por tipo de malha e suas evidências de processo. O cálculo não isola fornecedor, cor, período, método de inspeção ou causa.

### Cenário independente de rolos

- 398 de 500 rolos revisados até 31/10/2026 (79,6% de cobertura).
- 217 dos 398 revisados foram reprovados (54,5%). Entre os 102 ainda sem revisão, a espera mediana era de 4 dias e o percentil 90, de 23 dias.
- Dos 50.035 m recebidos, 8.753 m foram consumidos. Os 41.282 m em estoque se dividem em 7.757 m liberados, 21.812 m bloqueados e 11.713 m aguardando revisão ou liberação.
- A fila identifica onde verificar prioridade. Material com aprovação registrada só fica disponível após liberação. Corte exige liberação prévia e uma ordem registrada.

## Como as ideias do livro entraram no projeto

| Seção de *A Arte de Pensar com Dados*, prova editorial v3 | Aplicação |
|---|---|
| Cap. 1, pp. 9–15 | Definição da unidade e do denominador. Comparação por estratos e padronização. A inversão descrita no livro não ocorreu neste conjunto |
| Amostra técnica, pp. 16–20 | Média, mediana e desvio-padrão amostral da gramatura por malha. Mediana e p90 da fila em dias |
| Amostra prática, pp. 21–24 | CSV de origem preservado, chave e domínios validados, log, quarentena, reconciliação e resultados reproduzíveis |
| Capítulo especial, pp. 25–31 | Ocorrência visual e medições registradas separadamente. Revisão, decisão, autorização e corte têm campos distintos. As metragens reconciliam |

## Contrato, métricas e limites

- **Lotes.** Uma linha por chave válida. O status é o já registrado em 2024. O arquivo antigo não fornece histórico por rolo nem permite inferir datas de revisão, corte ou liberação. Taxa por lote = lotes reprovados ÷ lotes no recorte. Taxa mensal = contagem reprovada ÷ total daquele mês.
- **Auditoria.** 5.000 linhas recebidas = 4.980 lotes válidos + 20 cópias reconciliadas + 0 linhas em quarentena. Foram 18 cópias equivalentes após normalização e duas com diferença de preenchimento. Recuperou-se um valor quando todas as versões preenchidas concordavam. As seis correções decimais aplicam-se aos pares lote/valor documentados no snapshot sintético. Não são regra industrial geral. O intervalo de domínio do arquivo legado é uma validação do pipeline, distinta de uma faixa de aceitação industrial.
- **Rolos.** Uma linha por rolo e somente uma revisão possível nesta simulação. Cobertura = revisados ÷ recebidos. Reprovação na revisão = reprovados ÷ revisados. Um rolo sem revisão tem resultado nulo. Sem denominador, o painel mostra um traço. Espera considera a fila ainda aberta na data de corte, com percentil de posto mais próximo.
- **Critérios didáticos.** Revisão 01 da ficha SIM-200: 190–210 g/m² e 158–162 cm. SIM-170: 160–180 g/m² e 148–152 cm. Limites inclusivos. Desvio em qualquer medida ou ocorrência visual gera reprovação na simulação.
- **Saldo.** Recebido menos consumido dá estoque físico. Saldo de rolo liberado equivale à metragem disponível nesta simulação. Reprovação e bloqueio coincidem sob a regra adotada. O cenário não cobre concessões, devoluções, descartes, reinspeções, reservas ou retrabalho.
- **Inferência.** As bases foram geradas com regras artificiais. As taxas descrevem a simulação, sem estimar desempenho real, comprovar redução de perdas ou sustentar um modelo preditivo. Para investigar previsão com dados reais, seriam necessários histórico de eventos, definição de alvo, validação temporal e controle de vazamento.

## Reproduzir

Requer Python 3.10+ com SQLite da biblioteca padrão. A pasta é independente de servidor, conta ou dependências externas.

```sh
python pipeline.py
python validar.py
```

- O pipeline lê `data/inspecoes_malha.csv` na raiz do repositório ou `dados/lotes_originais.csv` em um pacote independente. Essa entrada corresponde ao CSV bruto da [versão publicada no GitHub](https://github.com/Danielobys/analise-qualidade-textil/tree/17ddfbff434dd314004a691506a2e8d252ed43c1). O SHA-256 é conferido antes da execução.
- `pipeline.py` valida a entrada, gera os 500 rolos com semente fixa, computa os resultados e constrói as saídas. O navegador usa o snapshot que o Python embute no HTML. A saída `resultado/dashboard-web.html` compacta o snapshot para publicação e é o arquivo publicado em `docs/v2/index.html`.
- `modelo.sql` contém o esquema SQLite, as restrições e as consultas. `resultado/qualidade.sqlite3` permite consultar as tabelas e as visões `lotes_por_mes`, `fornecedores_comparados` e `estoque_no_corte`. A versão publicada usava PostgreSQL. A v2 usa SQLite para abrir e reproduzir o pacote localmente.
- `resultado/` reúne a base tratada, a simulação por rolo, a trilha de auditoria, a quarentena e o resumo em JSON.

Projeto desenvolvido com apoio de IA na revisão, implementação e validação do material de portfólio.
