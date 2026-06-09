#!/usr/bin/env python3
# =============================================================
# ZABBIX DEREGISTER - Remoção de host via API REST
# Compatível com Python 3.8+ - apenas biblioteca padrão
# =============================================================

import sys
import json
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
    """Autentica na API do Zabbix via user.login."""
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


def buscar_host(url, auth, hostname):
    """Busca o hostid pelo hostname."""
    print(f"[INFO] Buscando host '{hostname}' no Zabbix...")
    resultado = zabbix_request(url, "host.get", {
        "output": ["hostid", "host"],
        "filter": {"host": [hostname]}
    }, auth=auth)
    return resultado[0] if resultado else None


def remover_host(url, auth, hostid, hostname):
    """Remove o host do Zabbix via API."""
    print(f"[INFO] Removendo host '{hostname}' (hostid: {hostid}) do Zabbix...")
    zabbix_request(url, "host.delete", [hostid], auth=auth)
    print(f"[OK] Host '{hostname}' removido com sucesso do Zabbix.")


# --- Main ---

def main():
    api_url  = sys.argv[1]
    usuario  = sys.argv[2]
    senha    = sys.argv[3]
    hostname = sys.argv[4]

    print(f"[INFO] Iniciando downgrade do host '{hostname}' no Zabbix...")

    # 1. Verificar API
    verificar_api(api_url)

    # 2. Autenticar
    auth = autenticar(api_url, usuario, senha)

    # 3. Buscar host
    host = buscar_host(api_url, auth, hostname)
    if not host:
        print(f"[INFO] Host '{hostname}' não encontrado no Zabbix. Nada a remover.")
        logout(api_url, auth)
        print("NAO_ENCONTRADO")
        sys.exit(0)

    # 4. Remover host
    remover_host(api_url, auth, host["hostid"], hostname)

    # 5. Logout
    logout(api_url, auth)

    print("REMOVIDO")


if __name__ == "__main__":
    main()