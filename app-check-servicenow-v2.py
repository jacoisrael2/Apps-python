import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime, timedelta
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

def login_servicenow(driver):
    """Função para acessar o ServiceNow"""
    try:
        # URL do ServiceNow Petrobras
        driver.get("https://petrobras.service-now.com")
        return True
    except Exception as e:
        print(f"Erro ao acessar ServiceNow: {str(e)}")
        return False

def check_tickets(driver):
    """Função para verificar tickets SCTASK não atribuídos"""
    try:
        # Navega para a lista de tarefas em aberto dos grupos
        driver.get("https://petrobras.service-now.com/now/nav/ui/classic/params/target/task_list.do%3Fsysparm_userpref_module%3Db257f48f1be1ad5418feab853a4bcbae%26sysparm_view%3DITSMTasks%26sysparm_query%3Dactive%253Dtrue%255Eassignment_groupDYNAMICd6435e965f510100a9ad2572f2b47744%255Esys_class_name%253Dincident%255EORsys_class_name%253Dincident_task%255EORsys_class_name%253Dsc_req_item%255EORsys_class_name%253Dsc_task%255EORsys_class_name%253Dchange_request%255EORsys_class_name%253Dchange_task%255EORsys_class_name%253Dproblem%255EORsys_class_name%253Dproblem_task%255EORsys_class_name%253Dcmdb_multisource_recomp_task%255EORsys_class_name%253Dcmdb_multisource_recomp_task%255EORsys_class_name%253Dstale_ci_remediation%255EEQ")
        
        # Aguarda carregamento da tabela de tickets
        ticket_table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "list_table"))
        )
        
        # Encontra tickets SCTASK não atribuídos
        tickets = ticket_table.find_elements(By.TAG_NAME, "tr")
        
        for ticket in tickets[1:]:  # Ignora cabeçalho
            try:
                # Obtém informações do ticket
                created_time = ticket.find_element(By.CSS_SELECTOR, "td.vt").text
                ticket_number = ticket.find_element(By.CSS_SELECTOR, "a.linked").text
                
                # Verifica se é um SCTASK
                if not ticket_number.startswith("SCTASK"):
                    continue
                    
                # Verifica se está atribuído
                assigned_to = ticket.find_element(By.CSS_SELECTOR, "td[name='assigned_to']").text
                if assigned_to.strip():
                    continue
                
                # Converte string de data/hora para objeto datetime
                created_dt = datetime.strptime(created_time, "%Y-%m-%d %H:%M:%S")
                
                # Verifica se passou mais de 20 minutos
                if datetime.now() - created_dt > timedelta(minutes=20):
                    assign_ticket(driver, ticket_number)
            
            except Exception as e:
                print(f"Erro ao processar ticket: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Erro ao verificar tickets: {str(e)}")

def assign_ticket(driver, ticket_number):
    """Função para atribuir SCTASK para si mesmo"""
    try:
        # Abre o ticket
        driver.get(f"https://petrobras.service-now.com/sc_task.do?sysparm_query=number={ticket_number}")
        
        # Aguarda carregamento do formulário
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "sc_task.form_header"))
        )
        
        # Define grupo de atribuição
        group_field = driver.find_element(By.ID, "sys_display.sc_task.assignment_group")
        group_field.clear()
        group_field.send_keys("N3-SUPORTE-LAN-CPD")
        
        # Atribui para si mesmo
        assigned_to = driver.find_element(By.ID, "sys_display.sc_task.assigned_to")
        assigned_to.clear()
        assigned_to.send_keys("Israel Andrade Pinheiro")
        
        # Salva alterações
        driver.find_element(By.ID, "sysverb_update").click()
        
        print(f"SCTASK {ticket_number} atribuído com sucesso!")
        
    except Exception as e:
        print(f"Erro ao atribuir SCTASK {ticket_number}: {str(e)}")

def main():
    # Configuração do Firefox WebDriver
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    
    # Login no ServiceNow usando credenciais salvas
    if not login_servicenow(driver):
        driver.quit()
        return
    
    try:
        # Loop principal
        while True:
            check_tickets(driver)
            print("Verificação concluída. Aguardando próximo ciclo...")
            time.sleep(300)  # Aguarda 5 minutos antes da próxima verificação
            
    except KeyboardInterrupt:
        print("\nPrograma encerrado pelo usuário")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
