"""Junta os JSONs por processo em um unico fila_do_dia.json.

Uso:  python gerar_fila.py PASTA_DOS_JSONS [-o fila_do_dia.json]
A pagina de analise aceita este arquivo direto em "Importar JSON".
"""
import argparse, json, sys
from datetime import datetime
from pathlib import Path


def carregar(pasta: Path):
    itens, erros = [], []
    for f in sorted(pasta.glob("PMF_*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if not d.get("processo", {}).get("numero") or "linhas" not in d:
                raise ValueError("faltam processo.numero ou linhas")
            itens.append(d)
        except Exception as e:  # um arquivo ruim nao derruba a fila
            erros.append(f"{f.name}: {e}")
    return itens, erros


def ordem(d):
    # mais simples primeiro (menos partes e elos); empate pelo numero do processo
    c = d.get("complexidade", {})
    return (c.get("partes", 0) + c.get("elos_cadeia", 0), c.get("paginas", 0), d["processo"]["numero"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta", type=Path)
    ap.add_argument("-o", "--saida", type=Path, default=None)
    a = ap.parse_args()
    itens, erros = carregar(a.pasta)
    itens.sort(key=ordem)
    saida = a.saida or a.pasta / "fila_do_dia.json"
    pacote = {"versao_checklist": "v2", "gerado_em": datetime.now().isoformat(timespec="seconds"),
              "total": len(itens), "processos": itens}
    tmp = saida.with_suffix(".tmp")
    tmp.write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(saida)  # gravacao atomica: ninguem le arquivo pela metade
    print(f"{len(itens)} processos em {saida}")
    for e in erros:
        print("IGNORADO:", e, file=sys.stderr)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
