"""
================================================================================
gerar_dados.py — Análise Inteligente de Qualidade Têxtil
================================================================================
Gera o dataset sintético de inspeções de malha (inspecoes_malha.csv).

Os dados NÃO são puramente aleatórios: contêm padrões de negócio propositais,
para que a EDA (etapa 2) e as consultas SQL (etapa 3) tenham problemas reais
para encontrar — exatamente como acontece com dado de produção de verdade.

Padrões inseridos:
  P1) Fornecedor B tem taxa de defeito visual muito acima da média,
      concentrada em "Furos" — sugere problema de manuseio/máquina.
  P2) Malha 100% Algodão tem maior variabilidade de gramatura e reprova
      mais por sair da faixa técnica — fibra natural = processo menos
      estável (não é "culpa" de um fornecedor específico).
  P3) Cores escuras (Preto, Azul Marinho, Grafite) concentram mais
      "Diferença de Tonalidade" — problema clássico de tingimento.
  P4) No último trimestre (out-dez) a taxa de reprovação sobe — simula o
      gargalo da produção acelerada para atender à demanda de fim de ano.
  P5) Fornecedor E é o mais confiável — funciona como "benchmark".

Ao final, o script injeta uma dose pequena e realista de sujeira nos dados
(duplicatas, nulos, outlier de digitação, inconsistência de texto), porque
dado de fábrica raramente chega limpo — e a etapa de EDA precisa ter esse
trabalho de verificação para fazer sentido.

Saída: inspecoes_malha.csv (5.000 linhas)
================================================================================
"""

import random

import numpy as np
import pandas as pd
from faker import Faker

# ------------------------------------------------------------------------
# 0. Configuração e reprodutibilidade
# ------------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker("pt_BR")
Faker.seed(SEED)

N_FINAL = 5_000
DATA_INICIO = pd.Timestamp("2024-01-01").date()
DATA_FIM = pd.Timestamp("2024-12-31").date()

# ------------------------------------------------------------------------
# 1. Domínios de valores (o "de-para" do negócio)
# ------------------------------------------------------------------------
FORNECEDORES = ["Fornecedor A", "Fornecedor B", "Fornecedor C", "Fornecedor D", "Fornecedor E"]
PESO_FORNECEDORES = [0.24, 0.19, 0.21, 0.20, 0.16]  # participação de cada um no volume comprado

TIPOS_MALHA = ["Algodão", "Poliéster", "Viscose", "PV", "Ribana"]
PESO_TIPOS_MALHA = [0.32, 0.22, 0.16, 0.18, 0.12]

CORES = ["Branco", "Preto", "Cinza Mescla", "Azul Marinho", "Vermelho",
         "Verde Musgo", "Amarelo", "Rosa Claro", "Bege", "Grafite"]
CORES_ESCURAS = {"Preto", "Azul Marinho", "Grafite"}

DEFEITOS_POSSIVEIS = ["Furos", "Manchas", "Falha de Tecelagem",
                       "Fio Puxado", "Diferença de Tonalidade", "Ourela Danificada"]

# Faixa técnica "ideal" de gramatura (g/m²) por tipo de malha
FAIXA_GRAMATURA = {
    "Algodão":   (160, 180),
    "Poliéster": (140, 160),
    "Viscose":   (150, 170),
    "PV":        (155, 175),
    "Ribana":    (205, 230),
}
TOLERANCIA_GRAMATURA = 0.05   # 5% de tolerância além da faixa ideal
LIMITE_TORCAO = 6.0           # % máximo de torção/espiralidade aceitável


# ------------------------------------------------------------------------
# 2. Funções de geração de cada campo
# ------------------------------------------------------------------------
def gerar_gramatura(tipo_malha: str) -> float:
    """Amostra a gramatura (g/m²) a partir de uma normal centrada na faixa
    ideal do tipo de malha. Algodão recebe desvio-padrão bem maior de
    propósito (fibra natural = processo menos estável) — padrão P2."""
    baixo, alto = FAIXA_GRAMATURA[tipo_malha]
    media = (baixo + alto) / 2
    fator_desvio = 0.42 if tipo_malha == "Algodão" else 0.24
    desvio = (alto - baixo) * fator_desvio
    valor = np.random.normal(media, desvio)
    return round(max(valor, 60.0), 1)


def gerar_torcao() -> float:
    """Torção/espiralidade em %, medida em teste de lavagem padrão."""
    return round(max(np.random.normal(loc=3.2, scale=1.6), 0.0), 2)


def escolher_defeito(fornecedor: str, cor: str) -> str:
    """Sorteia o defeito visual, com viés por fornecedor (P1) e por cor (P3)."""
    if fornecedor == "Fornecedor B":
        pesos = [0.50, 0.12, 0.10, 0.10, 0.10, 0.08]   # forte viés -> Furos
    elif cor in CORES_ESCURAS:
        pesos = [0.10, 0.12, 0.10, 0.10, 0.48, 0.10]   # forte viés -> Tonalidade
    else:
        pesos = [0.20, 0.20, 0.18, 0.16, 0.16, 0.10]
    return random.choices(DEFEITOS_POSSIVEIS, weights=pesos, k=1)[0]


def gerar_linha(indice: int) -> dict:
    data_inspecao = fake.date_between(start_date=DATA_INICIO, end_date=DATA_FIM)
    fornecedor = random.choices(FORNECEDORES, weights=PESO_FORNECEDORES, k=1)[0]
    tipo_malha = random.choices(TIPOS_MALHA, weights=PESO_TIPOS_MALHA, k=1)[0]
    cor = random.choice(CORES)

    gramatura = gerar_gramatura(tipo_malha)
    torcao = gerar_torcao()

    baixo, alto = FAIXA_GRAMATURA[tipo_malha]
    margem = (alto - baixo) * TOLERANCIA_GRAMATURA
    gramatura_fora_padrao = gramatura < (baixo - margem) or gramatura > (alto + margem)
    torcao_fora_padrao = torcao > LIMITE_TORCAO

    # probabilidade-base de defeito visual, ajustada por fornecedor (P1, P5)
    prob_defeito = 0.10
    if fornecedor == "Fornecedor B":
        prob_defeito = 0.38
    elif fornecedor == "Fornecedor E":
        prob_defeito = 0.05

    tem_defeito_visual = random.random() < prob_defeito
    defeito = escolher_defeito(fornecedor, cor) if tem_defeito_visual else "Nenhum"

    reprovado = tem_defeito_visual or gramatura_fora_padrao or torcao_fora_padrao

    # P4 — gargalo de produção no último trimestre
    if data_inspecao.month in (10, 11, 12) and not reprovado:
        if random.random() < 0.09:
            reprovado = True
            defeito = "Falha de Tecelagem"

    status = "Reprovado" if reprovado else "Aprovado"
    lote = f"LT{data_inspecao.strftime('%y%m')}-{indice:05d}"

    return {
        "Data": data_inspecao,
        "Fornecedor": fornecedor,
        "Lote": lote,
        "Tipo de Malha": tipo_malha,
        "Cor": cor,
        "Gramatura": gramatura,
        "Torção": torcao,
        "Defeito": defeito,
        "Status": status,
    }


# ------------------------------------------------------------------------
# 3. Monta o dataset base
# ------------------------------------------------------------------------
N_DUPLICATAS = int(N_FINAL * 0.004)   # ~0,4% de linhas duplicadas de propósito
N_BASE = N_FINAL - N_DUPLICATAS

registros = [gerar_linha(i + 1) for i in range(N_BASE)]
df = pd.DataFrame(registros)

# ------------------------------------------------------------------------
# 4. Injeta "sujeira" realista (dado de fábrica nunca chega 100% limpo)
# ------------------------------------------------------------------------
# 4.1 Duplicatas — erro clássico de dupla digitação (repete o MESMO lote)
duplicatas = df.sample(n=N_DUPLICATAS, random_state=SEED)
df = pd.concat([df, duplicatas], ignore_index=True)

# 4.2 Nulos em campos de medição — falha de instrumento/sensor
idx_nulos_gramatura = df.sample(frac=0.01, random_state=SEED).index
df.loc[idx_nulos_gramatura, "Gramatura"] = np.nan

idx_nulos_torcao = df.sample(frac=0.01, random_state=SEED + 3).index
df.loc[idx_nulos_torcao, "Torção"] = np.nan

# 4.3 Outlier de digitação — vírgula decimal esquecida (165.0 -> 1650)
idx_outliers = df.sample(n=6, random_state=SEED + 1).index
df.loc[idx_outliers, "Gramatura"] = (df.loc[idx_outliers, "Gramatura"] * 10).round(1)

# 4.4 Inconsistência de texto — digitação manual em outro turno
idx_minusculo = df.sample(frac=0.01, random_state=SEED + 2).index
df.loc[idx_minusculo, "Fornecedor"] = df.loc[idx_minusculo, "Fornecedor"].str.lower()

# ------------------------------------------------------------------------
# 5. Ordena por data (como um export cronológico do sistema) e salva
# ------------------------------------------------------------------------
df = df.sort_values("Data", kind="stable").reset_index(drop=True)
df["Data"] = pd.to_datetime(df["Data"]).dt.strftime("%Y-%m-%d")

df.to_csv("inspecoes_malha.csv", index=False, encoding="utf-8-sig")

print(f"Arquivo gerado com {len(df)} linhas -> inspecoes_malha.csv")
print(f"Duplicatas propositais: {N_DUPLICATAS}")
print(f"Nulos propositais: ~{len(idx_nulos_gramatura)} em Gramatura, ~{len(idx_nulos_torcao)} em Torção")
print(f"Outliers propositais: {len(idx_outliers)}")
