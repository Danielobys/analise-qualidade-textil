/* ============================================================================
   consultas_analiticas.sql — Análise Inteligente de Qualidade Têxtil
   ============================================================================
   Banco: PostgreSQL 13+
   Pipeline: staging_inspecoes (carga bruta) -> fornecedores (dimensão)
             -> inspecoes (fato, com FK para fornecedores)

   Como rodar (via psql):
     1) createdb qualidade_textil
     2) cd sql/
        psql -d qualidade_textil -f consultas_analiticas.sql
        (o \copy abaixo usa caminho relativo à pasta /sql — ajuste se rodar
        de outro lugar)
   ============================================================================ */

-- Interrompe e reverte toda a carga se houver erro. Use banco de estudo.
\set ON_ERROR_STOP on
BEGIN;
CREATE SCHEMA IF NOT EXISTS qualidade_textil;
SET search_path TO qualidade_textil;
-- Somente tabelas deste esquema; dependências externas impedem a remoção.
DROP TABLE IF EXISTS inspecoes, fornecedores, staging_inspecoes;

-- ----------------------------------------------------------------------------
-- 1) DDL — criação das tabelas
-- ----------------------------------------------------------------------------

-- Staging: espelha exatamente as colunas do CSV tratado (saída do notebook)
CREATE TABLE staging_inspecoes (
    data_inspecao   DATE,
    fornecedor      VARCHAR(50),
    lote            VARCHAR(20),
    tipo_malha      VARCHAR(30),
    cor             VARCHAR(30),
    gramatura       NUMERIC(6,1),
    torcao          NUMERIC(5,2),
    defeito         VARCHAR(50),
    status          VARCHAR(15)
);

-- Dimensão: fornecedores
CREATE TABLE fornecedores (
    id_fornecedor   SERIAL PRIMARY KEY,
    nome_fornecedor VARCHAR(50) UNIQUE NOT NULL
);

-- Fato: inspeções, com FK para fornecedores
CREATE TABLE inspecoes (
    id_inspecao     SERIAL PRIMARY KEY,
    data_inspecao   DATE NOT NULL,
    id_fornecedor   INTEGER NOT NULL REFERENCES fornecedores(id_fornecedor),
    lote            VARCHAR(20) NOT NULL UNIQUE,
    tipo_malha      VARCHAR(30) NOT NULL,
    cor             VARCHAR(30) NOT NULL,
    gramatura       NUMERIC(6,1),
    torcao          NUMERIC(5,2),
    defeito         VARCHAR(50) NOT NULL DEFAULT 'Nenhum',
    status          VARCHAR(15) NOT NULL CHECK (status IN ('Aprovado', 'Reprovado'))
);

CREATE INDEX idx_inspecoes_data       ON inspecoes(data_inspecao);
CREATE INDEX idx_inspecoes_fornecedor ON inspecoes(id_fornecedor);
CREATE INDEX idx_inspecoes_status     ON inspecoes(status);

-- ----------------------------------------------------------------------------
-- 2) Carga (ETL simples: staging -> dimensão -> fato)
-- ----------------------------------------------------------------------------

-- \copy roda no cliente (psql), então não exige permissão de arquivo no
-- servidor Postgres — mais prático que COPY para rodar localmente.
\copy staging_inspecoes (data_inspecao, fornecedor, lote, tipo_malha, cor, gramatura, torcao, defeito, status) FROM '../data/inspecoes_malha_tratada.csv' WITH (FORMAT csv, HEADER true, NULL '', ENCODING 'UTF8');

INSERT INTO fornecedores (nome_fornecedor)
SELECT DISTINCT fornecedor FROM staging_inspecoes
ON CONFLICT (nome_fornecedor) DO NOTHING;

INSERT INTO inspecoes (data_inspecao, id_fornecedor, lote, tipo_malha, cor, gramatura, torcao, defeito, status)
SELECT s.data_inspecao, f.id_fornecedor, s.lote, s.tipo_malha, s.cor, s.gramatura, s.torcao, s.defeito, s.status
FROM staging_inspecoes s
JOIN fornecedores f ON f.nome_fornecedor = s.fornecedor;

DROP TABLE staging_inspecoes;
COMMIT;

-- ----------------------------------------------------------------------------
-- 3) Consultas analíticas avançadas
-- ----------------------------------------------------------------------------

-- 3.1 Ranking dos piores fornecedores no mês mais recente da base
--     (agregação + CASE WHEN + RANK)
WITH inspecoes_mes AS (
    SELECT
        f.nome_fornecedor,
        COUNT(*) AS total_inspecoes,
        SUM(CASE WHEN i.status = 'Reprovado' THEN 1 ELSE 0 END) AS total_reprovados
    FROM inspecoes i
    JOIN fornecedores f ON f.id_fornecedor = i.id_fornecedor
    WHERE DATE_TRUNC('month', i.data_inspecao) =
          (SELECT DATE_TRUNC('month', MAX(data_inspecao)) FROM inspecoes)
    GROUP BY f.nome_fornecedor
)
SELECT
    nome_fornecedor,
    total_inspecoes,
    total_reprovados,
    ROUND(100.0 * total_reprovados / total_inspecoes, 2)                    AS taxa_reprovacao_pct,
    RANK() OVER (ORDER BY total_reprovados::NUMERIC / total_inspecoes DESC) AS posicao_pior_fornecedor
FROM inspecoes_mes
ORDER BY posicao_pior_fornecedor;


-- 3.2 Evolução semanal da taxa de reprovação, com variação vs. semana
--     anterior e média simples das 4 últimas semanas observadas (LAG, AVG OVER)
WITH taxa_semanal AS (
    SELECT
        DATE_TRUNC('week', data_inspecao)::DATE AS semana,
        COUNT(*) AS total_inspecoes,
        ROUND(100.0 * SUM(CASE WHEN status = 'Reprovado' THEN 1 ELSE 0 END) / COUNT(*), 2) AS taxa_reprovacao_pct
    FROM inspecoes
    GROUP BY DATE_TRUNC('week', data_inspecao)
)
SELECT
    semana,
    total_inspecoes,
    taxa_reprovacao_pct,
    LAG(taxa_reprovacao_pct) OVER (ORDER BY semana)                                 AS taxa_semana_anterior,
    ROUND(taxa_reprovacao_pct - LAG(taxa_reprovacao_pct) OVER (ORDER BY semana), 2) AS variacao_pontos_percentuais,
    ROUND(AVG(taxa_reprovacao_pct) OVER (
        ORDER BY semana ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ), 2)                                                                          AS media_movel_4_semanas
FROM taxa_semanal
ORDER BY semana;


-- 3.3 Presença de defeito visual entre as reprovações
--     por fornecedor, com participação percentual dentro de cada fornecedor
--     Não identifica causa raiz nem exclui causas simultâneas.
--     Ausência de defeito visual não comprova falha técnica.
--     (CASE WHEN + PARTITION BY + RANK)
WITH reprovacoes_classificadas AS (
    SELECT
        f.nome_fornecedor,
        CASE
            WHEN i.defeito <> 'Nenhum' THEN 'Com defeito visual'
            ELSE 'Sem defeito visual registrado'
        END AS motivo_reprovacao,
        COUNT(*) AS qtde
    FROM inspecoes i
    JOIN fornecedores f ON f.id_fornecedor = i.id_fornecedor
    WHERE i.status = 'Reprovado'
    GROUP BY f.nome_fornecedor, motivo_reprovacao
)
SELECT
    nome_fornecedor,
    motivo_reprovacao,
    qtde,
    SUM(qtde) OVER (PARTITION BY nome_fornecedor)                             AS total_reprovado_fornecedor,
    ROUND(100.0 * qtde / SUM(qtde) OVER (PARTITION BY nome_fornecedor), 2)    AS percentual_do_motivo,
    RANK() OVER (PARTITION BY nome_fornecedor ORDER BY qtde DESC)            AS posicao_motivo
FROM reprovacoes_classificadas
ORDER BY nome_fornecedor, posicao_motivo;
