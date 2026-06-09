# 🤖 install-zabbix_agent — branch `python_awx`

Automação completa do ciclo de provisionamento do Zabbix Agent em hosts Linux,
executada via AWX como plataforma de self-service de infraestrutura.

---

## 📋 Descrição

Este repositório implementa uma role Ansible que realiza:

1. Instalação do repositório e pacote `zabbix-agent 6.0 LTS`
2. Configuração do agente via template Jinja2
3. Tratativa de firewalld, iptables e SELinux para instâncias novas
4. Habilitação e inicialização do serviço
5. Validação local do agente
6. Cadastro automático do host no Zabbix Server via API REST (Python 3)
7. Validação de monitoramento ativo pelo Zabbix Server

---

## 📂 Estrutura

```
install-zabbix_agent/
├── site.yml                          ← Playbook de entrada (configurado no AWX)
├── files/
│   └── zabbix_register.py            ← Script Python para cadastro via API REST
├── roles/
│   └── zabbix_agent/
│       ├── defaults/
│       │   └── main.yml              ← Variáveis sobrescrevíveis pelo AWX Survey
│       ├── vars/
│       │   └── main.yml              ← Variáveis fixas da infraestrutura
│       ├── tasks/
│       │   └── main.yml              ← Tasks principais da role
│       ├── templates/
│       │   └── zabbix_agentd.conf.j2 ← Template de configuração do agente
│       └── handlers/
│           └── main.yml              ← Handler de restart do serviço
└── README.md
```

---

## ✅ Sistemas Operacionais Suportados

| Sistema Operacional | Versões             |
|---------------------|---------------------|
| Oracle Linux / RHEL | 7, 8, 9             |
| Ubuntu              | 20.04, 22.04, 24.04 |
| Amazon Linux        | 2023                |

---

## ⚙️ Variáveis

### `defaults/main.yml` — sobrescrevíveis via AWX Survey

| Variável                  | Padrão                              | Descrição                    |
|---------------------------|-------------------------------------|------------------------------|
| `zabbix_agent_listenport` | `10050`                             | Porta de escuta do agente    |
| `zabbix_host_group`       | `-CDC_CLOUD`                        | Grupo de hosts no Zabbix     |
| `zabbix_template`         | `Template OS Linux by Zabbix agent` | Template vinculado ao host   |

### `vars/main.yml` — fixas da infraestrutura

| Variável                | Descrição                                 |
|-------------------------|-------------------------------------------|
| `zabbix_server_dns`     | Servidores Zabbix (Server e ServerActive) |
| `zabbix_server_primary` | Servidor primário (usado no Server=)      |
| `zabbix_api_url`        | URL da API JSON-RPC do Zabbix             |
| `zabbix_api_token`      | Token de autenticação da API              |

---

## 🚀 Fluxo de Execução

```
AWX Survey (grupo e template)
        ↓
[REPO]      Instala repositório Zabbix 6.0 LTS conforme SO detectado
        ↓
[INSTALL]   Instala pacote zabbix-agent
        ↓
[CONFIG]    Aplica zabbix_agentd.conf via Jinja2
        ↓
[FIREWALL]  Para e desabilita firewalld
        ↓
[IPTABLES]  Flush completo + política ACCEPT em todas as chains
        ↓
[SELINUX]   Coloca em modo permissive (se Enforcing)
        ↓
[SERVICE]   Habilita e inicia zabbix-agent
        ↓
[VALIDATE]  Aguarda porta 10050 + testa agente localmente
        ↓
[ZABBIX]    Script Python cadastra host + valida monitoramento via API REST
```

---

## 🖥️ AWX — Configuração do Job Template

### Survey (campos configuráveis pelo usuário)

| Campo           | Variável            | Padrão                              |
|-----------------|---------------------|-------------------------------------|
| Grupo Zabbix    | `zabbix_host_group` | `-CDC_CLOUD`                        |
| Template Zabbix | `zabbix_template`   | `Template OS Linux by Zabbix agent` |

### Pré-requisitos

- Grupo informado no Survey deve existir previamente no Zabbix
- Template informado no Survey deve existir previamente no Zabbix
- Hosts devem estar cadastrados no inventário do AWX
- Credencial SSH configurada no Job Template

---

## 🐍 Script Python — `zabbix_register.py`

Utiliza **apenas biblioteca padrão do Python 3.8+** — sem dependências externas.

Executa as seguintes etapas via API JSON-RPC do Zabbix:

1. Verifica acessibilidade da API
2. Verifica se o host já está cadastrado — evita duplicatas
3. Busca `groupid` e `templateid` dinamicamente por nome
4. Cadastra o host com interface do tipo Zabbix Agent
5. Valida disponibilidade do host (4 tentativas × 10 segundos)

---

## 📚 Referências

- [Zabbix 6.0 LTS — Documentação oficial](https://www.zabbix.com/documentation/6.0)
- [Zabbix 6.0 — API JSON-RPC](https://www.zabbix.com/documentation/6.0/en/manual/api)
- [Ansible — Documentação oficial](https://docs.ansible.com)
- [AWX 24.6.1 — Documentação oficial](https://docs.ansible.com/projects/awx/en/24.6.1)