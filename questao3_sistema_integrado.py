
import json
import os
from datetime import datetime

FICHEIRO = "sistema_integrado.json"

UNIDADES_INICIAIS = [
    "Hospital Geral do Uíge",
    "Hospital Municipal de Negage",
    "Hospital Municipal de Maquela do Zombo",
    "Centro de Saúde de Sanza Pombo",
    "Centro de Saúde de Songo",
]


def carregar():
    if os.path.exists(FICHEIRO):
        with open(FICHEIRO, encoding="utf-8") as f:
            return json.load(f)
    return {
        "unidades": UNIDADES_INICIAIS[:],
        "pacientes": {},       # id -> dados
        "consultas": [],       # registos clínicos de todas as unidades
        "transferencias": [],  # pedidos de referenciamento
        "contador_paciente": 0,
        "contador_transf": 0,
    }


def guardar(db):
    with open(FICHEIRO, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def ler_texto(msg, obrigatorio=True):
    while True:
        t = input(msg).strip()
        if t or not obrigatorio:
            return t
        print("  Campo obrigatório.")


def escolher_unidade(db, msg="Escolha a unidade"):
    for i, u in enumerate(db["unidades"], 1):
        print(f" {i} - {u}")
    while True:
        try:
            n = int(input(f"{msg}: "))
            if 1 <= n <= len(db["unidades"]):
                return db["unidades"][n - 1]
        except ValueError:
            pass
        print("  Opção inválida.")


def obter_paciente(db):
    pid = input("ID do paciente (ex.: P-00001): ").strip().upper()
    p = db["pacientes"].get(pid)
    if not p:
        print("  Paciente não encontrado em nenhuma unidade.")
    return p


def registar_paciente(db, unidade):
    print("\n--- Registo de Paciente (partilhado por todas as unidades) ---")
    nome = ler_texto("Nome completo: ")
    nasc = ler_texto("Data de nascimento (dd/mm/aaaa): ")
    try:
        datetime.strptime(nasc, "%d/%m/%Y")
    except ValueError:
        print("  Data inválida.")
        return
    # evita duplicados entre unidades
    for p in db["pacientes"].values():
        if p["nome"].lower() == nome.lower() and p["nascimento"] == nasc:
            print(f"  Paciente já existe no sistema: {p['id']} (registado em {p['unidade_origem']}).")
            return
    genero = ler_texto("Género (M/F): ").upper()[:1]
    contacto = ler_texto("Contacto: ", obrigatorio=False)
    db["contador_paciente"] += 1
    pid = f"P-{db['contador_paciente']:05d}"
    db["pacientes"][pid] = {
        "id": pid, "nome": nome, "nascimento": nasc, "genero": genero,
        "contacto": contacto, "unidade_origem": unidade, "registado_em": agora(),
    }
    guardar(db)
    print(f"Paciente registado com ID {pid}. Disponível para todas as unidades.")


def registar_consulta(db, unidade):
    p = obter_paciente(db)
    if not p:
        return
    print(f"Paciente: {p['nome']} | Unidade atual: {unidade}")
    db["consultas"].append({
        "paciente": p["id"], "unidade": unidade, "data": agora(),
        "motivo": ler_texto("Motivo: "),
        "diagnostico": ler_texto("Diagnóstico: "),
        "tratamento": ler_texto("Tratamento: ", obrigatorio=False),
        "profissional": ler_texto("Profissional responsável: "),
    })
    guardar(db)
    print("Consulta registada e partilhada com a rede.")


def ver_historico(db, unidade):
    p = obter_paciente(db)
    if not p:
        return
    print(f"\n--- Histórico integrado: {p['nome']} ({p['id']}) ---")
    regs = [c for c in db["consultas"] if c["paciente"] == p["id"]]
    if not regs:
        print("Sem registos clínicos.")
    for c in regs:
        origem = "(esta unidade)" if c["unidade"] == unidade else ""
        print(f"- {c['data']} | {c['unidade']} {origem}")
        print(f"  Motivo: {c['motivo']} | Diagnóstico: {c['diagnostico']}")
        if c["tratamento"]:
            print(f"  Tratamento: {c['tratamento']}")
        print(f"  Profissional: {c['profissional']}")


def pedir_transferencia(db, unidade):
    p = obter_paciente(db)
    if not p:
        return
    print("Unidade de destino:")
    destino = escolher_unidade(db, "Destino")
    if destino == unidade:
        print("  O destino não pode ser a unidade atual.")
        return
    db["contador_transf"] += 1
    db["transferencias"].append({
        "id": db["contador_transf"], "paciente": p["id"], "origem": unidade,
        "destino": destino, "motivo": ler_texto("Motivo da transferência: "),
        "estado": "Pendente", "data": agora(),
    })
    guardar(db)
    print(f"Pedido n.º {db['contador_transf']} enviado para {destino}.")


def gerir_transferencias(db, unidade):
    pend = [t for t in db["transferencias"] if t["destino"] == unidade and t["estado"] == "Pendente"]
    if not pend:
        print("Sem transferências pendentes para esta unidade.")
        return
    for t in pend:
        nome = db["pacientes"][t["paciente"]]["nome"]
        print(f"#{t['id']} | {nome} | de {t['origem']} | {t['motivo']} | {t['data']}")
    try:
        tid = int(input("N.º do pedido a tratar (0 para voltar): "))
    except ValueError:
        return
    for t in pend:
        if t["id"] == tid:
            r = input("Aceitar (a) ou Recusar (r)? ").strip().lower()
            t["estado"] = "Aceite" if r == "a" else "Recusada"
            guardar(db)
            print(f"Pedido {tid}: {t['estado']}.")
            return
    print("Pedido não encontrado.")


def relatorio(db, _unidade):
    print("\n--- Relatório Provincial ---")
    print(f"Pacientes registados: {len(db['pacientes'])}")
    print(f"Consultas totais    : {len(db['consultas'])}")
    for u in db["unidades"]:
        n = sum(1 for c in db["consultas"] if c["unidade"] == u)
        print(f"  {u}: {n} consulta(s)")
    for est in ("Pendente", "Aceite", "Recusada"):
        print(f"Transferências {est.lower()}s: {sum(1 for t in db['transferencias'] if t['estado'] == est)}")


def main():
    db = carregar()
    print("===== SISTEMA INTEGRADO DE INFORMAÇÃO - SAÚDE UÍGE =====")
    print("Selecione a unidade onde está a trabalhar:")
    unidade = escolher_unidade(db)
    acoes = {
        "1": ("Registar paciente", registar_paciente),
        "2": ("Registar consulta", registar_consulta),
        "3": ("Ver histórico clínico integrado", ver_historico),
        "4": ("Pedir transferência para outra unidade", pedir_transferencia),
        "5": ("Tratar transferências recebidas", gerir_transferencias),
        "6": ("Relatório provincial", relatorio),
    }
    while True:
        print(f"\n--- {unidade} ---")
        for k, (t, _) in acoes.items():
            print(f" {k} - {t}")
        print(" 0 - Sair")
        op = input("Opção: ").strip()
        if op == "0":
            break
        if op in acoes:
            acoes[op][1](db, unidade)
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
