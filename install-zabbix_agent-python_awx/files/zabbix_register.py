#!/usr/bin/env python3
# =============================================================
# ZABBIX REGISTER - Cadastro e validação de host via API REST
# Compatível com Python 3.8+ - apenas biblioteca padrão
# Uso: zabbix_register.py <api_url> <usuario> <senha> <hostname> <ip> <group> <template> <port>
# =============================================================

import sys
import json
import time
import urllib.request
import urllib.error


# --- Funções auxiliares ---

def zabbix_request(url, method, params, auth=None):
    """Faz uma requisição à API JSON-RPC do Zabbix."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    if auth:
        payload["auth"] = auth

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode("utf-8"))
            if "error" in result:
                print(f"[ERRO] API Zabbix retornou erro: {result['error']['data']}")
                sys.exit(1)
            return result.get("result")
    except urllib.error.URLError as e:
        print(f"[ERRO] Não foi possível conectar à API do Zabbix: {e}")
        sys.exit(1)


def autenticar(url, usuario, senha):
    """Autentica na API do Zabbix via user.login e retorna o token de sessão."""
    print(f"[INFO] Autenticando na API Zabbix com usuário '{usuario}'...")
    token = zabbix_request(url, "user.login", {
        "username": usuario,
        "password": senha
    })
    print(f"[INFO] Autenticação bem sucedida.")
    return token


def logout(url, auth):
    """Encerra a sessão na API do Zabbix."""
    zabbix_request(url, "user.logout", {}, auth=auth)
    print(f"[INFO] Sessão encerrada.")


def verificar_api(url):
    """Verifica se a API do Zabbix está acessível."""
    print("[INFO] Verificando acessibilidade da API Zabbix...")
    version = zabbix_request(url, "apiinfo.version", {})
    print(f"[INFO] API Zabbix acessível - versão: {version}")


def verificar_host_existe(url, auth, hostname):
    """Verifica se o host já está cadastrado no Zabbix."""
    resultado = zabbix_request(url, "host.get", {
        "output": ["hostid", "host", "available"],
        "filter": {"host": [hostname]}
    }, auth=auth)
    return resultado[0] if resultado else None


def buscar_groupid(url, auth, group_name):
    """Busca o groupid pelo nome do grupo."""
    print(f"[INFO] Buscando grupo '{group_name}'...")
    resultado = zabbix_request(url, "hostgroup.get", {
        "output": ["groupid", "name"],
        "filter": {"name": [group_name]}
    }, auth=auth)
    if not resultado:
        print(f"[ERRO] Grupo '{group_name}' não encontrado no Zabbix.")
        sys.exit(1)
    groupid = resultado[0]["groupid"]
    print(f"[INFO] Grupo encontrado - groupid: {groupid}")
    return groupid


def buscar_templateid(url, auth, template_name):
    """Busca o templateid pelo nome do template."""
    print(f"[INFO] Buscando template '{template_name}'...")
    resultado = zabbix_request(url, "template.get", {
        "output": ["templateid", "name"],
        "filter": {"name": [template_name]}
    }, auth=auth)
    if not resultado:
        print(f"[ERRO] Template '{template_name}' não encontrado no Zabbix.")
        sys.exit(1)
    templateid = resultado[0]["templateid"]
    print(f"[INFO] Template encontrado - templateid: {templateid}")
    return templateid


def cadastrar_host(url, auth, hostname, ip, port, groupid, templateid):
    """Cadastra o host no Zabbix via API."""
    print(f"[INFO] Cadastrando host '{hostname}' no Zabbix...")
    resultado = zabbix_request(url, "host.create", {
        "host": hostname,
        "name": hostname,
        "interfaces": [
            {
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": ip,
                "dns": "",
                "port": str(port)
            }
        ],
        "groups": [{"groupid": groupid}],
        "templates": [{"templateid": templateid}],
        "description": "Instalado via Ansible AWX"
    }, auth=auth)
    hostid = resultado["hostids"][0]
    print(f"[INFO] Host criado com sucesso - hostid: {hostid}")
    return hostid


def validar_monitoramento(url, auth, hostname, tentativas=4, intervalo=10):
    """Aguarda o host ficar disponível no Zabbix após o cadastro."""
    print(f"[INFO] Aguardando Zabbix Server iniciar monitoramento de '{hostname}'...")

    for i in range(1, tentativas + 1):
        resultado = zabbix_request(url, "host.get", {
            "output": ["hostid", "host", "available"],
            "filter": {"host": [hostname]}
        }, auth=auth)

        if resultado:
            available = resultado[0].get("available", "0")
            # available: 0=unknown, 1=available, 2=unavailable
            if available == "1":
                print(f"[OK] Host '{hostname}' está disponível e sendo monitorado pelo Zabbix.")
                return True
            elif available == "2":
                print(f"[ATENCAO] Tentativa {i}/{tentativas} - Host cadastrado mas indisponível. Verifique conectividade.")
            else:
                print(f"[INFO] Tentativa {i}/{tentativas} - Aguardando Zabbix Server contactar o agente...")

        if i < tentativas:
            time.sleep(intervalo)

    print(f"[ATENCAO] Host '{hostname}' cadastrado mas status ainda não confirmado após {tentativas * intervalo}s.")
    print("[ATENCAO] Verifique manualmente na interface do Zabbix.")
    return False


# --- Main ---

def main():
    if len(sys.argv) != 9:
        print("Uso: zabbix_register.py <api_url> <usuario> <senha> <hostname> <ip> <group> <template> <port>")
        sys.exit(1)

    api_url  = sys.argv[1]
    usuario  = sys.argv[2]
    senha    = sys.argv[3]
    hostname = sys.argv[4]
    ip       = sys.argv[5]
    group    = sys.argv[6]
    template = sys.argv[7]
    port     = sys.argv[8]

    print(f"[INFO] Iniciando registro do host '{hostname}' ({ip}) no Zabbix...")
    print(f"[INFO] Grupo: {group} | Template: {template} | Porta: {port}")

    # 1. Verificar API
    verificar_api(api_url)

    # 2. Autenticar
    auth = autenticar(api_url, usuario, senha)

    # 3. Verificar se host já existe
    host_existente = verificar_host_existe(api_url, auth, hostname)
    if host_existente:
        print(f"[INFO] Host '{hostname}' já cadastrado no Zabbix (hostid: {host_existente['hostid']}). Pulando cadastro.")
        logout(api_url, auth)
        print("JA_CADASTRADO")
        sys.exit(0)

    # 4. Buscar groupid e templateid dinamicamente
    groupid    = buscar_groupid(api_url, auth, group)
    templateid = buscar_templateid(api_url, auth, template)

    # 5. Cadastrar host
    cadastrar_host(api_url, auth, hostname, ip, port, groupid, templateid)

    # 6. Validar monitoramento
    validar_monitoramento(api_url, auth, hostname)

    # 7. Logout
    logout(api_url, auth)

    print("CADASTRADO")


if __name__ == "__main__":
    main()
