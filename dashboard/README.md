# Dashboard de qualidade têxtil

Aplicação web local com snapshot de 4.980 inspeções sintéticas de 2024. Não é um arquivo Power BI.

## Executar

Na raiz do projeto:

```bash
python -m http.server 4173 --bind 127.0.0.1 --directory dashboard/app/dist
```

Abra http://127.0.0.1:4173. Não abra o index.html diretamente: o carregamento do JSON precisa de HTTP.

## Medidas

- Taxa: reprovados / total do recorte. Sem registros, taxa indisponível.
- Lotes com medição ausente: gramatura ou torção nula; cada lote contado uma vez.
- Pareto: apenas defeitos visuais diferentes de Nenhum. Frequência e percentual acumulado em gráficos lado a lado.
- Gramatura fora da faixa: calculada entre medições preenchidas, com as faixas e tolerância do gerador.
- Todos os gráficos e tabelas compartilham os filtros globais. Busca nas tabelas afeta apenas a tabela correspondente.
- Não foi incluída média de gramatura geral: misturar especificações de malhas distintas pode ocultar diferenças. O indicador foi substituído por fora da faixa por malha e cobertura de medições.
- Não há comparação automática com período anterior nem meta de negócio inventada. A evolução mensal mostra as taxas observadas na simulação.

## Código e dados

Interface em app/src/content/dashboard/DashboardContent.jsx e textile.css. Snapshot e definições em app/src/data.json. Fonte original: data/inspecoes_malha_tratada.csv, relativa à raiz do projeto.

A pasta app/dist contém a versão compilada e os dados necessários para executar sem Node ou bibliotecas externas. Para recompilar a interface no Codex, usar o build da skill Data, conforme app/AGENTS.md. O repositório inclui os fontes; a reprodução do build usa o runtime Data do Codex. Para apenas executar ou hospedar, Python ou qualquer servidor estático basta.

Consulte ../PUBLICAR.md para publicação no GitHub Pages e atualização da pasta docs. O dashboard trabalha com cópia estática da base: mudar o CSV exige regenerar app/src/data.json e recompilar. Sem atualização automática ou gravação na fonte.
