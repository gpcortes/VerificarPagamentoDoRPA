from distutils.log import error
from worker import worker
from smtpmail import SMTPClient
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from docxtpl import DocxTemplate
import requests
import pandas as pd
from sqlalchemy import create_engine
import pymysql
from time import sleep
from os.path import expanduser, join
import os


#import sys
# sys.path.append(
#     'C:\\Users\\Ataualpa_roriz\\OneDrive\\CETT\\ScriptsPython\\Processos\\notify\\app')


# rpaID = 351


worker = worker()
email = SMTPClient()

def load_env():
    if os.getenv('ENV') != 'production':
        from os.path import join, dirname
        from dotenv import load_dotenv
        dotenv_path = join(dirname(__file__), 'finan.env')
        load_dotenv(dotenv_path)

    FINAN_HOST_DB = os.getenv('FINAN_HOST_DB')
    FINAN_PORT_DB = os.getenv('FINAN_PORT_DB')
    FINAN_USER_DB = os.getenv('FINAN_USER_DB')
    FINAN_PASSWD_DB = os.getenv('FINAN_PASSWD_DB')
    FINAN_DB = os.getenv('FINAN_DB')
    FINAN_FTP_HOST = os.getenv('FINAN_FTP_HOST')
    FINAN_FTP_USER = os.getenv('FINAN_FTP_USER')
    FINAN_FTP_PASSWD = os.getenv('FINAN_FTP_PASSWD')

    return FINAN_HOST_DB, FINAN_PORT_DB, FINAN_USER_DB, FINAN_PASSWD_DB, FINAN_DB, FINAN_FTP_HOST, FINAN_FTP_USER, FINAN_FTP_PASSWD

def inserir_dados_bd_protocolo(ano, hoje):
    FINAN_HOST_DB, FINAN_PORT_DB, FINAN_USER_DB, FINAN_PASSWD_DB, FINAN_DB = load_env()
    mydb = pymysql.connect(
        host=FINAN_HOST_DB,
        user=FINAN_USER_DB,
        password=FINAN_PASSWD_DB,
        database=FINAN_DB
    )

    mycursor = mydb.cursor()
    sql = "INSERT INTO finan_00_oficio_adm_cobranca (ano,data) VALUES (%s, %s)"
    val = (ano, hoje)
    mycursor.execute(sql, val)
    mydb.commit()
    n_oficio_cobranca = mycursor.lastrowid
    return n_oficio_cobranca


def get_engine():
    FINAN_HOST_DB, FINAN_PORT_DB, FINAN_USER_DB, FINAN_PASSWD_DB, FINAN_DB = load_env()
    return create_engine('mysql+pymysql://'+FINAN_USER_DB+':'+FINAN_PASSWD_DB+'@'+FINAN_HOST_DB+':'+FINAN_PORT_DB+'/'+FINAN_DB)


def enviar_email_cobranca(dias_sem_pagar):
    email.toAddresses = ["desenvolvedor1@cett.org.br"]
    email.subject = "RPA - Notificação de cobrança"
    email.htmlMessage = "O pagamento de Fulano de Tal está com {} dias de atraso".format(dias_sem_pagar)
    return email.send()


def enviar_email_rpa_pago(valor):
    email.toAddresses = ["desenvolvedor1@cett.org.br"]
    email.subject = "RPA Pago"
    email.htmlMessage = "Seu RPA no valor de {} foi pago pela fundação. Favor verificar no seu extrato".format(valor)
    return email.send()


def enviar_oficio_cobranca(dados):
    templates_dir = join(expanduser("~"), 'templates')
    doc1 = DocxTemplate(join(templates_dir, 'Oficio_Cobranca_RTVE-Cobranca_RPA.docx'))
    doc1.render(dados.iloc[0])
    outputs_dir = join(expanduser("~"), 'outputs')
    document_path = join(outputs_dir, "Oficio_Cobranca_RTVE-Cobranca_RPA_{}.docx".format(n_oficio_cobranca))
    doc1.save(document_path)
    email.toAddresses = ["desenvolvedor1@cett.org.br"]
    email.subject = "RPA - Ofício de cobrança"
    email.htmlMessage = "Segue ofício referente ao pagamento de Fulano de Tal".format(dias_sem_pagar)
    email.attachments = [document_path]
    return email.send()


def busca_dados_api_mov_rtve(cpf, valor, data_inicial, data_final):
    data = {"Login": "ATAUALPA.RORIZ", "Senha": "ATAUALPARORIZ"}

    r = requests.api.post(
        url='http://45.191.207.223:44365/api/usuario/loginAPI', json=data)

    if r.text == 'Senha Inválida':
        print('\n', 'Mensagem de erro do End Point de Login da API SAGE: ', r.text, '\n')
        return False

    headers = r.text.split(":")[1].strip()
    headers = {"login": "ATAUALPA.RORIZ", str(r.text.split(
        ":")[0].strip()): str(r.text.split(":")[1].strip())}
    login = "ATAUALPA.RORIZ"
    token = str(r.text.split(":")[1].strip())

    url = "http://45.191.207.223:44365/api/privado/movfinanceira"

    querystring = {"numconv": "376209", "login": "ATAUALPA.RORIZ",
                   "token": str(r.text.split(":")[1].strip())}

    payload = ""
    response = requests.get(
        f"http://45.191.207.223:44365/api/privado/movfinanceira_new?numconv=376209&login={login}&token={token}")

    #mov = requests.get(f'http://45.191.207.223:44365/api/privado/movfinanceira?numconv=376209&login={login}&token=')
    x = response.json()
    df = pd.DataFrame(x)
    data = [datetime.strptime(x, '%Y-%m-%dT00:00:00')
            for x in df.dataCompensacao]
    ano = [x.year for x in data]
    mes = [x.month for x in data]
    dia = [x.day for x in data]
    df['dataCompensacao'] = [datetime.strftime(x, '%Y-%m-%d') for x in data]
    df['ano'] = ano
    df['mes'] = mes
    df['dia'] = dia
    df['Rubrica'] = [x.split('-')[0].strip() for x in df.rubrica]
    df['Rubrica'] = df['Rubrica'].fillna(0)
    descricao = []
    for x in df.Rubrica:
        try:
            temp = x.split('-')[1].strip()
            descricao.append(temp)
        except:
            temp = ""
            descricao.append(temp)
    df['Descricao'] = descricao
    df['Bruto'] = -df['valorLiquido']
    df = df[['titulo', 'cgc_cpf', 'nomePessoa', 'subProjeto',
             'itemApoiado', 'valorLiquido', 'Bruto', 'dataEmissao', 'dataCompensacao',
             'listaItensPretacaoContasAdiantamentos', 'ano', 'mes', 'dia', 'Rubrica',
             'Descricao']]
    df['dataCompensacao'] = [datetime.strptime(
        x, '%Y-%m-%d') for x in df['dataCompensacao']]
    df = df.set_index('dataCompensacao')
    data_final = data_inicial + relativedelta(months=+2)
    df = df[data_inicial:data_final]
    cpf = cpf.replace(".", "").replace("-", "")
    df_ = df[(df['cgc_cpf'] == cpf) & (df['valorLiquido'] == -(valor))]
    return df_


def verifica_pagamento(rpaID):
    dados = pd.read_sql_query(
        'select * from finan_00_recibo_de_pagamento_autonomo WHERE id = '+str(rpaID), con=get_engine())
    cpf = dados.cpf.iloc[0]
    nome = dados.nome_completo[0]

    dados['valor_liquido'] = dados['valor_liquido'].str.replace('[R$ .]','').str.replace('[,]','.').astype(float)
    # dados['valor_liquido'] = float(1500)
    # data_inicial = datetime.strftime(dados.data_inicio[0], '%Y-%m-%d')
    dados['data_rpa'] = datetime.strptime(datetime.strftime(
        dados.date_time.iloc[0], '%Y-%m-%d'), '%Y-%m-%d')
    dados['prazo_pagamento'] = dados['data_rpa'].iloc[0] + \
        relativedelta(months=+2)
    buscar_pagamento = busca_dados_api_mov_rtve(
        cpf, dados['valor_liquido'].iloc[0], dados['data_rpa'].iloc[0], dados['prazo_pagamento'].iloc[0])
    lista_pagamento = list(buscar_pagamento.Bruto)
    dados['hoje'] = date.today()
    hoje = date.today()
    ano = hoje.year
    dados['n_oficio_cobranca'] = inserir_dados_bd_protocolo(ano, hoje)

    #verificar_id = pd.read_sql_query('select * from finan_00_oficio_adm_cobranca', con = get_engine())

    if lista_pagamento == []:
        dias_sem_pagar_temp = datetime.strftime(
            dados.date_time.iloc[0], '%Y-%m-%d')
        dados['dias_sem_pagar'] = abs(datetime.strptime(
            dias_sem_pagar_temp, '%Y-%m-%d') - datetime.now()).days
        dados['vencimento'] = datetime.strftime(datetime.strptime(
            dias_sem_pagar_temp, '%Y-%m-%d') + relativedelta(days=+10), '%d-%m-%Y')
        dias_sem_pagar = dados['dias_sem_pagar'].iloc[0]
        print('dias sem pagar --->', dados['dias_sem_pagar'].iloc[0])
        if dados['dias_sem_pagar'].iloc[0] > 5:
            enviar_email_cobranca(dias_sem_pagar)
            if dias_sem_pagar == 141:
                enviar_oficio_cobranca(dados)
            elif dias_sem_pagar == 20:
                enviar_oficio_cobranca(dados)
            elif dias_sem_pagar == 30:
                enviar_oficio_cobranca(dados)
        else:
            print("aguardar_pagamento")
            return False

    else:
        enviar_email_rpa_pago(valor)
        return True


if __name__ == '__main__':
    print('Worker started')
    while True:
        tasks = worker.fetch_tasks()

        for task in tasks:

            rpaID = task.variables['rpaID'].value if 'rpaID' in task.variables else None

            result = verifica_pagamento(rpaID)

            task_variables = {
                'pagamentoEfetuado': {
                    'name': 'pagamentoEfetuado',
                    'value': result,
                    'type': 'Boolean'
                }
            }

            worker.complete_task(task_id=task.id_, variables=task_variables)

        sleep(30)
