"""Gera os artefatos da v2 a partir da base original e de um cenário independente."""
import base64
import csv
import gzip
import hashlib
import json
import math
import random
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
BRUTO = RAIZ / "dados/lotes_originais.csv"
if not BRUTO.exists():
    BRUTO = RAIZ.parent / "data/inspecoes_malha.csv"
SAIDA = RAIZ / "resultado"
COMMIT = "17ddfbff434dd314004a691506a2e8d252ed43c1"
HASH = "0c1faaeef4a3c5e25840dd5848d6be33b0b282783b864dae44bbd91e5cd8149d"
CAMPOS = ("Data", "Fornecedor", "Lote", "Tipo de Malha", "Cor", "Gramatura", "Torção", "Defeito", "Status")
FORNECEDORES = tuple(f"Fornecedor {letra}" for letra in "ABCDE")
FAIXAS = {"Algodão": (160, 180), "Poliéster": (140, 160), "Viscose": (150, 170), "PV": (155, 175), "Ribana": (205, 230)}
ERROS_DECIMAIS = {
    "LT2403-04852": "1749.0", "LT2404-03472": "1562.0", "LT2406-01308": "1750.0",
    "LT2406-04061": "2243.0", "LT2406-03530": "1864.0", "LT2408-04277": "2207.0",
}
CORTE = date(2026, 10, 31)
SEMENTE = 42
FICHAS = {"SIM-200": (190, 210, 158, 162), "SIM-170": (160, 180, 148, 152)}


def numero(valor, minimo, maximo):
    if not valor:
        return None
    try:
        n = Decimal(valor)
    except InvalidOperation as erro:
        raise ValueError("número inválido") from erro
    if not n.is_finite() or not minimo <= n <= maximo:
        raise ValueError("número fora do domínio")
    return n


def limpar(arquivo):
    grupos = defaultdict(list)
    log, quarentena = [], []
    recebidas = 0
    with arquivo.open(encoding="utf-8-sig", newline="") as arq:
        leitor = csv.DictReader(arq)
        if tuple(leitor.fieldnames or []) != CAMPOS:
            raise ValueError("O cabeçalho não atende ao contrato de lotes.")
        for linha, bruto in enumerate(leitor, 2):
            recebidas += 1
            lote = bruto["Lote"]
            try:
                if None in bruto or any(v is None for v in bruto.values()):
                    raise ValueError("quantidade de colunas incorreta")
                data = date.fromisoformat(bruto["Data"])
                fornecedor = bruto["Fornecedor"].strip().title()
                tipo, status = bruto["Tipo de Malha"], bruto["Status"]
                if (
                    fornecedor not in FORNECEDORES or tipo not in FAIXAS
                    or status not in {"Aprovado", "Reprovado"} or not bruto["Cor"] or not bruto["Defeito"]
                    or not re.fullmatch(r"LT" + data.strftime("%y%m") + r"-[0-9]{5}", lote)
                ):
                    raise ValueError("chave ou campo categórico inválido")
                grama_bruta = bruto["Gramatura"]
                erro_documentado = lote in ERROS_DECIMAIS and grama_bruta == ERROS_DECIMAIS[lote]
                grama = numero(grama_bruta, 1, 3000 if erro_documentado else 400)
                torcao = numero(bruto["Torção"], 0, 100)
                if erro_documentado:
                    corrigida = grama / 10
                    log.append({"lote": lote, "linha_csv": linha, "acao": "corrigir_decimal_da_simulacao", "campo": "gramatura", "antes": str(grama), "depois": str(corrigida)})
                    grama = corrigida
                if fornecedor != bruto["Fornecedor"]:
                    log.append({"lote": lote, "linha_csv": linha, "acao": "padronizar_fornecedor", "campo": "fornecedor", "antes": bruto["Fornecedor"], "depois": fornecedor})
                registro = dict(lote=lote, data=data.isoformat(), fornecedor=fornecedor, malha=tipo,
                                cor=bruto["Cor"], gramatura=grama, torcao=torcao, defeito=bruto["Defeito"], status=status)
                grupos[lote].append((linha, registro, bruto))
            except (ValueError, TypeError) as erro:
                quarentena.append({"linha_csv": linha, "lote": lote, "motivo": str(erro), "original": bruto})

    lotes = []
    removidas = 0
    chaves_invalidas = {x["lote"] for x in quarentena if x["lote"]}
    for lote, grupo in grupos.items():
        campos = {campo: {r[campo] for _, r, _ in grupo if r[campo] is not None} for campo in grupo[0][1]}
        conflito = [campo for campo, valores in campos.items() if len(valores) > 1]
        if conflito or lote in chaves_invalidas:
            motivo = f"valores conflitantes: {', '.join(conflito)}" if conflito else "outra linha da chave em quarentena"
            quarentena.extend({"linha_csv": i, "lote": lote, "motivo": motivo, "original": b} for i, _, b in grupo)
            continue
        registro = {campo: next(iter(valores), None) for campo, valores in campos.items()}
        removidas += len(grupo) - 1
        base = grupo[0][1]
        for linha, outro, _ in grupo[1:]:
            acao = "duplicata_equivalente" if outro == base else "duplicata_com_ausencia"
            log.append({"lote": lote, "linha_csv": linha, "acao": acao, "campo": "", "antes": "", "depois": ""})
        for campo in ("gramatura", "torcao"):
            valor = registro[campo]
            if base[campo] is None and valor is not None:
                fonte = next(i for i, r, _ in grupo if r[campo] == valor)
                log.append({"lote": lote, "linha_csv": fonte, "acao": "recuperar_valor_de_duplicata", "campo": campo, "antes": "", "depois": str(valor)})
            registro[campo] = float(valor) if valor is not None else None
        registro["linhas_csv"] = " ".join(str(i) for i, _, _ in grupo)
        lotes.append(registro)
    assert recebidas == len(lotes) + removidas + len(quarentena)
    return lotes, log, quarentena, recebidas


def simular_rolos():
    rng = random.Random(SEMENTE)
    rolos = []
    for i in range(500):
        artigo = rng.choice(tuple(FICHAS))
        fornecedor = rng.choice(FORNECEDORES)
        minimo_g, maximo_g, minimo_l, maximo_l = FICHAS[artigo]
        entrada = date(2026, 10, 1) + timedelta(days=rng.randrange(31))
        proposta_revisao = entrada + timedelta(days=rng.randrange(1, 9))
        revisao = proposta_revisao if proposta_revisao <= CORTE and rng.random() > 0.1 else None
        metros = rng.randrange(70, 131)
        grama = round(rng.gauss((minimo_g + maximo_g) / 2, 8), 1) if revisao else None
        largura = rng.randrange(minimo_l - 1, maximo_l + 2) if revisao else None
        visual = rng.choice(("Barramento", "Furos", "Mancha")) if revisao and rng.random() < 0.16 else None
        desvios = []
        if revisao:
            if not minimo_g <= grama <= maximo_g:
                desvios.append("Gramatura")
            if not minimo_l <= largura <= maximo_l:
                desvios.append("Largura")
            if visual:
                desvios.append(visual)
        resultado = ("Reprovado" if desvios else "Aprovado") if revisao else None
        candidata = revisao + timedelta(days=rng.randrange(0, 4)) if resultado == "Aprovado" else None
        liberacao = candidata if candidata and candidata <= CORTE else None
        data_uso = liberacao + timedelta(days=rng.randrange(1, 7)) if liberacao else None
        consumo = rng.randint(15, metros) if data_uso and data_uso <= CORTE else 0
        saldo = metros - consumo
        rolos.append(dict(
            rolo=f"SIM-R{i+1:04d}", lote=f"SIM-{fornecedor[-1]}-{artigo[-3:]}-{i//10+1:03d}",
            fornecedor=fornecedor, artigo=artigo, revisao_ficha="01", entrada=entrada.isoformat(),
            revisao=revisao.isoformat() if revisao else None, resultado=resultado,
            gramatura=grama, largura_cm=largura, ocorrencia_visual=visual, desvios=" / ".join(desvios),
            liberacao=liberacao.isoformat() if liberacao else None, corte=data_uso.isoformat() if consumo else None,
            ordem=f"SIM-OF{i+1:04d}" if consumo else None, metros_recebidos=metros, metros_consumidos=consumo,
            metros_saldo=saldo, metros_liberados=saldo if liberacao else 0,
            metros_bloqueados=saldo if resultado == "Reprovado" else 0,
            metros_aguardando=saldo if not liberacao and resultado != "Reprovado" else 0,
        ))
    return rolos


def resumo_lotes(lotes):
    reprovados = sum(x["status"] == "Reprovado" for x in lotes)
    ausentes = sum(x["gramatura"] is None or x["torcao"] is None for x in lotes)
    gramas = [x["gramatura"] for x in lotes if x["gramatura"] is not None]
    estatistica = dict(n=len(gramas), media=statistics.mean(gramas), mediana=statistics.median(gramas),
                       desvio_amostral=statistics.stdev(gramas), minimo=min(gramas), maximo=max(gramas))
    grupos = Counter((x["fornecedor"], x["malha"], x["status"]) for x in lotes)
    peso = Counter(x["malha"] for x in lotes)
    comparacao = []
    for fornecedor in FORNECEDORES:
        por_malha = []
        for malha, n in peso.items():
            rej = grupos[fornecedor, malha, "Reprovado"]
            total = rej + grupos[fornecedor, malha, "Aprovado"]
            por_malha.append(dict(malha=malha, n=total, rej=rej, peso=n/len(lotes)))
        n = sum(g["n"] for g in por_malha)
        rej = sum(g["rej"] for g in por_malha)
        ajustada = sum(g["rej"]/g["n"]*g["peso"] for g in por_malha) if all(g["n"] for g in por_malha) else None
        comparacao.append(dict(fornecedor=fornecedor, n=n, rej=rej, ajustada=ajustada, estratos=por_malha))
    return dict(n=len(lotes), reprovados=reprovados, ausentes=ausentes, estatistica=estatistica, comparacao=comparacao)


def resumo_rolos(rolos):
    kpis = dict(n=len(rolos), revisados=sum(bool(r["revisao"]) for r in rolos),
                reprovados=sum(r["resultado"] == "Reprovado" for r in rolos))
    for campo in ("metros_recebidos", "metros_consumidos", "metros_saldo", "metros_liberados", "metros_bloqueados", "metros_aguardando"):
        kpis[campo] = sum(r[campo] for r in rolos)
    esperas = sorted((CORTE - date.fromisoformat(r["entrada"])).days for r in rolos if not r["revisao"])
    kpis["espera_revisao"] = dict(n=len(esperas), mediana=statistics.median(esperas), p90=esperas[math.ceil(len(esperas)*.9)-1])
    return kpis


def gravar_csv(destino, registros, campos=None):
    with destino.open("w", encoding="utf-8-sig", newline="") as arq:
        escritor = csv.DictWriter(arq, fieldnames=campos or list(registros[0]))
        escritor.writeheader()
        escritor.writerows(registros)


def validar_sql(lotes, rolos, resumo):
    con = sqlite3.connect(":memory:")
    con.executescript((RAIZ / "modelo.sql").read_text())
    for tabela, registros in (("lotes", lotes), ("rolos", rolos)):
        campos = list(registros[0])
        con.executemany(f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({', '.join('?' for _ in campos)})",
                        [tuple(r[c] for c in campos) for r in registros])
    assert con.execute("SELECT SUM(n), SUM(reprovados) FROM lotes_por_mes").fetchone() == (
        resumo["lotes"]["n"], resumo["lotes"]["reprovados"])
    for fornecedor, n, rej, ajustada in con.execute("SELECT * FROM fornecedores_comparados"):
        python = next(x for x in resumo["lotes"]["comparacao"] if x["fornecedor"] == fornecedor)
        assert (n, rej) == (python["n"], python["rej"])
        assert math.isclose(ajustada, python["ajustada"], rel_tol=1e-12)
    assert con.execute("SELECT * FROM estoque_no_corte").fetchone() == tuple(resumo["rolos"][k] for k in (
        "n", "revisados", "reprovados", "metros_recebidos", "metros_consumidos", "metros_saldo",
        "metros_liberados", "metros_bloqueados", "metros_aguardando"))
    con.commit()
    return con


def main():
    assert hashlib.sha256(BRUTO.read_bytes()).hexdigest() == HASH, "O CSV não corresponde ao snapshot auditado."
    lotes, log, quarentena, recebidas = limpar(BRUTO)
    rolos = simular_rolos()
    resumo = dict(lotes=resumo_lotes(lotes), rolos=resumo_rolos(rolos), auditoria=dict(
        commit=COMMIT, sha256=HASH, recebidas=recebidas, quarentena=len(quarentena), eventos=dict(Counter(x["acao"] for x in log)),
    ), data_corte=CORTE.isoformat())
    con = validar_sql(lotes, rolos, resumo)
    SAIDA.mkdir(exist_ok=True)
    gravar_csv(SAIDA / "lotes.csv", lotes)
    gravar_csv(SAIDA / "rolos_simulados.csv", rolos)
    gravar_csv(SAIDA / "log_auditoria.csv", log)
    gravar_csv(SAIDA / "quarentena.csv", [{"linha_csv": x["linha_csv"], "lote": x["lote"], "motivo": x["motivo"],
                                           "original": json.dumps(x["original"], ensure_ascii=False)} for x in quarentena],
               ["linha_csv", "lote", "motivo", "original"])
    (SAIDA / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    dados = json.dumps(dict(lotes=lotes, rolos=rolos, resumo=resumo), ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    modelo = (RAIZ / "painel.html.in").read_text(encoding="utf-8")
    (SAIDA / "dashboard.html").write_text(modelo.replace("__DADOS__", dados), encoding="utf-8")
    compactado = base64.b64encode(gzip.compress(dados.encode("utf-8"), mtime=0)).decode("ascii")
    web = modelo.replace('id="dados" type="application/json"', 'id="dados" type="application/octet-stream"').replace("__DADOS__", compactado)
    inicializacao = """(async function iniciar() {
const comprimido = Uint8Array.from(atob(document.querySelector('#dados').textContent), c => c.charCodeAt(0))
const fluxo = new Blob([comprimido]).stream().pipeThrough(new DecompressionStream('gzip'))
const {lotes, rolos, resumo} = await new Response(fluxo).json()"""
    web = web.replace("const {lotes, rolos, resumo} = JSON.parse(document.querySelector('#dados').textContent)", inicializacao)
    web = web.replace('</script>\n</body>', """})().catch(erro => {
  console.error(erro)
  const aviso = document.createElement('p')
  aviso.textContent = 'Não foi possível carregar os dados do painel neste navegador.'
  aviso.setAttribute('role', 'alert')
  document.querySelector('main').prepend(aviso)
})
</script>
</body>""")
    (SAIDA / "dashboard-web.html").write_text(web, encoding="utf-8")
    banco = SAIDA / "qualidade.sqlite3"
    temporario = banco.with_suffix(".tmp")
    temporario.unlink(missing_ok=True)
    with sqlite3.connect(temporario) as destino:
        con.backup(destino)
    temporario.replace(banco)
    print(f"Lotes: {resumo['lotes']['n']} | Rolos simulados: {resumo['rolos']['n']} | SQL e reconciliação conferidos.")


if __name__ == "__main__":
    main()
