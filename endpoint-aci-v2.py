# Importação das bibliotecas necessárias
import requests
import json
import pandas as pd
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

# Desabilita avisos de SSL não verificado
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def login_apic(apic_ip, username, password):
    """Função para autenticar no APIC e obter token
    
    Args:
        apic_ip (str): Endereço IP do APIC
        username (str): Nome de usuário para autenticação
        password (str): Senha do usuário
        
    Returns:
        str: Token de autenticação se sucesso, None se falha
    """
    login_url = f"https://{apic_ip}/api/aaaLogin.json"
    login_data = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password
            }
        }
    }
    
    try:
        response = requests.post(login_url, json=login_data, verify=False)
        response.raise_for_status()
        token = response.json()['imdata'][0]['aaaLogin']['attributes']['token']
        print("Login realizado com sucesso!")
        return token
    except Exception as e:
        print(f"Erro ao fazer login no APIC: {str(e)}")
        return None

def get_all_endpoints(apic_ip, token):
    """Função para coletar informações de todos os endpoints
    
    Args:
        apic_ip (str): Endereço IP do APIC
        token (str): Token de autenticação
        
    Returns:
        list: Lista com informações de todos os endpoints
    """
    endpoint_url = f"https://{apic_ip}/api/node/class/fvCEp.json"
    
    headers = {
        "Cookie": f"APIC-Cookie={token}"
    }
    
    try:
        response = requests.get(endpoint_url, headers=headers, verify=False)
        response.raise_for_status()
        print("Coleta de endpoints realizada com sucesso!")
        return response.json()['imdata']
    except Exception as e:
        print(f"Erro ao coletar endpoints: {str(e)}")
        return None

def parse_endpoint_data(endpoints):
    """Função para extrair dados relevantes dos endpoints
    
    Args:
        endpoints (list): Lista de endpoints do ACI
        
    Returns:
        list: Lista de dicionários com dados formatados
    """
    parsed_data = []
    
    for ep in endpoints:
        ep_info = ep['fvCEp']['attributes']
        parsed_data.append({
            'IP': ep_info.get('ip', 'N/A'),
            'MAC': ep_info.get('mac', 'N/A'),
            'Interface': ep_info.get('ifId', 'N/A'),
            'Encap': ep_info.get('encap', 'N/A'),
            'EPG': ep_info.get('epgDn', 'N/A').split('/')[-1],
            'Tenant': ep_info.get('dn', 'N/A').split('/')[1],
            'VRF': ep_info.get('vrfDn', 'N/A').split('/')[-1],
            'Status': ep_info.get('lcC', 'N/A')
        })
    print(f"Total de endpoints processados: {len(parsed_data)}")
    return parsed_data

def export_to_excel(data, filename=None):
    """Função para exportar dados para Excel
    
    Args:
        data (list): Lista de dicionários com dados dos endpoints
        filename (str): Nome do arquivo Excel (opcional)
    """
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"aci_endpoints_{timestamp}.xlsx"
    
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"\nDados exportados com sucesso para {filename}")

def main():
    """Função principal que coordena o fluxo do programa"""
    apic_ip = input("Digite o IP do APIC: ")
    username = input("Digite o usuário: ")
    password = input("Digite a senha: ")
    print("\nConectando ao APIC...")
    token = login_apic(apic_ip, username, password)
    if not token:
        print("Falha na autenticação")
        return
    print("Coletando informações dos endpoints...")
    endpoints = get_all_endpoints(apic_ip, token)
    if not endpoints:
        print("Não foi possível coletar informações dos endpoints")
        return
    print("Processando dados...")
    endpoint_data = parse_endpoint_data(endpoints)
    print(f"\nTotal de endpoints encontrados: {len(endpoint_data)}")
    export_to_excel(endpoint_data)

if __name__ == "__main__":
    main()
