CREATE TABLE lotes (
    lote TEXT PRIMARY KEY NOT NULL,
    data TEXT NOT NULL,
    fornecedor TEXT NOT NULL,
    malha TEXT NOT NULL,
    cor TEXT NOT NULL,
    gramatura REAL CHECK (gramatura > 0),
    torcao REAL CHECK (torcao BETWEEN 0 AND 100),
    defeito TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Aprovado', 'Reprovado')),
    linhas_csv TEXT NOT NULL
);

CREATE TABLE rolos (
    rolo TEXT PRIMARY KEY NOT NULL,
    lote TEXT NOT NULL,
    fornecedor TEXT NOT NULL,
    artigo TEXT NOT NULL,
    revisao_ficha TEXT NOT NULL,
    entrada TEXT NOT NULL CHECK (entrada <= '2026-10-31'),
    revisao TEXT,
    resultado TEXT,
    gramatura REAL,
    largura_cm INTEGER,
    ocorrencia_visual TEXT,
    desvios TEXT NOT NULL,
    liberacao TEXT,
    corte TEXT,
    ordem TEXT,
    metros_recebidos INTEGER NOT NULL CHECK (metros_recebidos > 0),
    metros_consumidos INTEGER NOT NULL CHECK (metros_consumidos >= 0),
    metros_saldo INTEGER NOT NULL CHECK (metros_saldo >= 0),
    metros_liberados INTEGER NOT NULL CHECK (metros_liberados >= 0),
    metros_bloqueados INTEGER NOT NULL CHECK (metros_bloqueados >= 0),
    metros_aguardando INTEGER NOT NULL CHECK (metros_aguardando >= 0),
    CHECK ((revisao IS NULL AND resultado IS NULL AND gramatura IS NULL AND largura_cm IS NULL AND ocorrencia_visual IS NULL)
        OR (revisao IS NOT NULL AND revisao BETWEEN entrada AND '2026-10-31'
            AND resultado IS NOT NULL AND resultado IN ('Aprovado', 'Reprovado')
            AND gramatura IS NOT NULL AND largura_cm IS NOT NULL)),
    CHECK (liberacao IS NULL OR (resultado IS NOT NULL AND resultado = 'Aprovado' AND liberacao BETWEEN revisao AND '2026-10-31')),
    CHECK ((corte IS NULL AND ordem IS NULL AND metros_consumidos = 0)
        OR (corte IS NOT NULL AND liberacao IS NOT NULL AND corte BETWEEN liberacao AND '2026-10-31'
            AND ordem IS NOT NULL AND metros_consumidos > 0)),
    CHECK (metros_recebidos = metros_saldo + metros_consumidos),
    CHECK (metros_saldo = metros_liberados + metros_bloqueados + metros_aguardando),
    CHECK (metros_liberados = CASE WHEN liberacao IS NOT NULL THEN metros_saldo ELSE 0 END),
    CHECK (metros_bloqueados = CASE WHEN resultado = 'Reprovado' THEN metros_saldo ELSE 0 END)
);

CREATE VIEW lotes_por_mes AS
SELECT substr(data, 1, 7) AS mes, COUNT(*) AS n,
       SUM(CASE WHEN status = 'Reprovado' THEN 1 ELSE 0 END) AS reprovados
FROM lotes GROUP BY substr(data, 1, 7);

CREATE VIEW fornecedores_comparados AS
WITH pesos AS (
    SELECT malha, 1.0 * COUNT(*) / (SELECT COUNT(*) FROM lotes) AS peso
    FROM lotes GROUP BY malha
), estratos AS (
    SELECT fornecedor, malha, COUNT(*) AS n,
           SUM(CASE WHEN status = 'Reprovado' THEN 1 ELSE 0 END) AS reprovados
    FROM lotes GROUP BY fornecedor, malha
)
SELECT e.fornecedor, SUM(n) AS n, SUM(reprovados) AS reprovados,
       CASE WHEN COUNT(*) = (SELECT COUNT(*) FROM pesos)
            THEN SUM(p.peso * e.reprovados / e.n) END AS taxa_padronizada
FROM estratos e JOIN pesos p ON p.malha = e.malha
GROUP BY e.fornecedor;

CREATE VIEW estoque_no_corte AS
SELECT COUNT(*) AS recebidos, COUNT(revisao) AS revisados,
       SUM(CASE WHEN resultado = 'Reprovado' THEN 1 ELSE 0 END) AS reprovados,
       SUM(metros_recebidos) AS metros_recebidos, SUM(metros_consumidos) AS metros_consumidos,
       SUM(metros_saldo) AS metros_saldo, SUM(metros_liberados) AS metros_liberados,
       SUM(metros_bloqueados) AS metros_bloqueados, SUM(metros_aguardando) AS metros_aguardando
FROM rolos;
