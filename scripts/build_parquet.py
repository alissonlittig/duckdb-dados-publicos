"""Baixa PIB dos Municipios (SIDRA 5938) + populacao estimada (6579) e grava data/municipios.parquet."""
import json, re
from pathlib import Path
here = Path(__file__).parent
V = {"37": "pib", "513": "va_agro", "517": "va_industria", "6575": "va_servicos", "525": "va_publico"}
rows = {}
for r in json.load(open(here / "pib.json", encoding="utf-8"))[1:]:
    m = re.match(r"(.*?)(?: \((\w\w)\)| - (\w\w))$", r["D1N"])
    d = rows.setdefault(r["D1C"], {"cod_ibge": int(r["D1C"]), "municipio": m.group(1), "uf": m.group(2) or m.group(3)})
    d[V[r["D2C"]]] = float(r["V"]) * 1000 if r["V"].replace(".", "").isdigit() else None  # mil reais -> reais
for r in json.load(open(here / "pop.json", encoding="utf-8"))[1:]:
    if r["D1C"] in rows:
        rows[r["D1C"]]["populacao"] = int(r["V"]) if r["V"].isdigit() else None
out = list(rows.values())
REG = {**dict.fromkeys("RO AC AM RR PA AP TO".split(), "Norte"), **dict.fromkeys("MA PI CE RN PB PE AL SE BA".split(), "Nordeste"),
       **dict.fromkeys("MG ES RJ SP".split(), "Sudeste"), **dict.fromkeys("PR SC RS".split(), "Sul"), **dict.fromkeys("MS MT GO DF".split(), "Centro-Oeste")}
for d in out: d["regiao"] = REG[d["uf"]]; d["ano"] = 2021
import pyarrow as pa, pyarrow.parquet as pq
tb = pa.Table.from_pylist(out)
tb = tb.select(["cod_ibge", "municipio", "uf", "regiao", "ano", "populacao", "pib", "va_agro", "va_industria", "va_servicos", "va_publico"])
pq.write_table(tb, here.parent / "data" / "municipios.parquet", compression="zstd")
print(len(out), "municipios;", sum(1 for d in out if d.get("pib") is None), "sem PIB")
