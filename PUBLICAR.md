# Publicar e atualizar o portfólio

## O que cada link faz

O repositório no GitHub mostra código, notebook, dados e documentação. O GitHub Pages abre o dashboard no navegador, sem instalar nada. O endereço 127.0.0.1 funciona somente no computador que está executando o servidor.

## Publicação inicial

1. Entre no GitHub e crie um repositório público chamado analise-qualidade-textil.
2. Envie o conteúdo desta pasta, mantendo README.md na raiz e as subpastas intactas. Não envie somente o ZIP. Para muitas pastas, use GitHub Desktop: clone o repositório, copie os arquivos para a pasta clonada, revise a lista em Changes, faça Commit e Push origin.
3. No repositório, abra Settings > Pages. Em Source, escolha Deploy from a branch; em Branch, main e /docs; clique Save.
4. Aguarde o processo em Actions terminar. Volte a Pages e abra Visit site. Confirme que aparecem 4.980 lotes e 26,3% sem filtros.
5. Adicione o endereço exibido pelo GitHub Pages ao campo Website de About no repositório e ao currículo.

A pasta docs já contém o dashboard compilado e o arquivo de dados. Não é necessário instalar Node ou executar o notebook para hospedar essa versão.

Referência: [configurar a origem de publicação do GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Atualizações

- Documentação: altere o arquivo, confira a diferença e faça Commit + Push no GitHub Desktop.
- Interface: altere apenas o conteúdo autorizado em dashboard/app, recompile pelo runtime Data do Codex conforme AGENTS.md e execute `python scripts/preparar_site.py` na raiz. Confira o dashboard, faça Commit + Push. O Pages atualizará a pasta docs.
- Dados: atualize o CSV pelo notebook, atualize o snapshot com a mesma transformação documentada, recompile e execute o preparador. O verificador rejeita divergências entre CSV, snapshot e compilado.
- Alterações de filtros feitas durante uma visita não alteram os CSVs nem salvam uma nova versão do repositório.

## Apresentar em uma entrevista

Explique o problema de inspeção, a diferença entre duplicata exata e por lote, por que nulos não viraram zero e como a taxa muda com os filtros. Mostre os volumes junto das taxas. Reconheça que os dados são sintéticos e que os padrões foram inseridos no gerador. A experiência profissional é em qualidade têxtil; a análise de dados é um projeto de portfólio.

Texto para currículo:

“Análise de qualidade têxtil: estudo com 5.000 registros sintéticos, limpeza em Python/pandas, análise exploratória, consultas PostgreSQL e dashboard interativo para comparar fornecedores e padrões de reprovação.”
