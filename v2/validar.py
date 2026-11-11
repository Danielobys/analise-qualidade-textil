"""Verifica reconciliação, exceções de qualidade e as travas de negócio no banco."""
import csv
import sqlite3
import tempfile
from pathlib import Path

from pipeline import BRUTO, CAMPOS, limpar, resumo_lotes, resumo_rolos, simular_rolos, validar_sql


def verificar_origem():
    lotes, log, quarentena, recebidas = limpar(BRUTO)
    assert (recebidas, len(lotes), len(quarentena)) == (5000, 4980, 0)
    assert len({x["lote"] for x in lotes}) == 4980
    registro = next(x for x in lotes if x["lote"] == "LT2407-00394")
    assert registro["gramatura"] == 222.5
    assert registro["linhas_csv"] == "2717 2731"
    assert any(x["acao"] == "recuperar_valor_de_duplicata" and x["linha_csv"] == 2731 for x in log)
    return lotes


def verificar_conflitos():
    with tempfile.TemporaryDirectory() as pasta:
        p = Path(pasta) / "conflitos.csv"
        with p.open("w", encoding="utf-8", newline="") as f:
            escritor = csv.writer(f)
            escritor.writerow(CAMPOS)
            base = ["2024-01-01", "Fornecedor A", "LT2401-00001", "PV", "Preto", "160", "0", "Nenhum", "Aprovado"]
            escritor.writerow(base)
            escritor.writerow(base[:5] + ["165"] + base[6:])
            escritor.writerow(base[:2] + ["LT2401-00002"] + base[3:5] + ["450"] + base[6:])
        lotes, _, quarentena, recebidas = limpar(p)
        assert (len(lotes), len(quarentena), recebidas) == (0, 3, 3)


def rejeitar(banco, instrucao):
    try:
        with banco:
            banco.execute(instrucao)
    except sqlite3.IntegrityError:
        return
    raise AssertionError("O banco aceitou um estado proibido.")


def main():
    lotes = verificar_origem()
    verificar_conflitos()
    rolos = simular_rolos()
    resumo = {"lotes": resumo_lotes(lotes), "rolos": resumo_rolos(rolos)}
    assert (resumo["lotes"]["reprovados"], resumo["lotes"]["ausentes"]) == (1309, 98)
    assert (resumo["rolos"]["n"], resumo["rolos"]["revisados"], resumo["rolos"]["reprovados"]) == (500, 398, 217)
    con = validar_sql(lotes, rolos, resumo)
    assert con.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    rejeitar(con, "UPDATE rolos SET resultado='Reprovado' WHERE revisao IS NULL")
    rejeitar(con, "UPDATE rolos SET corte=entrada, ordem='TESTE', metros_consumidos=1, metros_saldo=metros_saldo-1, metros_bloqueados=metros_bloqueados-1 WHERE resultado='Reprovado'")
    rejeitar(con, "UPDATE rolos SET metros_saldo=metros_saldo+1")
    assert all(not r["ordem"] or r["liberacao"] <= r["corte"] for r in rolos)
    print("Regras de negócio, duplicatas, quarentena, equivalência Python/SQL e saldo verificados.")


if __name__ == "__main__":
    main()
