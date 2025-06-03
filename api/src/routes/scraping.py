"""
scraping.py

Módulo responsável pela raspagem de dados do site da Embrapa

Este módulo fornece endpoints e funções referentes a raspagem de dados do site 
da Embrapa (http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_01), 
contemplando dados da vitivinicultura do estado do Rio Grande do Sul.

Aqui também será carregada a string de conexão do PostgreSQL da variável de 
ambiente POSTGRES_URL e ajustado o prefixo "postgres://" para compatibilidade 
com bibliotecas como SQLAlchemy.

Os dados extraídos são estruturados e retornados em formato JSON.

Endpoints:
    GET /scrape/content: endpoint para raspagem de dados do site da Embrapa com 
    filtros baseados nos parâmetros passados na requisição HTTP (option, year e 
    sub_option).

        Params:
            Query: 
                option: opção principal da requisição HTTP
                year: parâmetro de ano para filtrar a requisição
                sub_option: parâmetro relativo a opção principal      

        Returns:
            response: objeto JSON com os dados organizados conforme os 
            parâmetros passados na requisição HTTP ou uma mensagem de erro, 
            se a solicitação falhar.
           
    GET /scrape/content/help: endpoint auxiliar que exibe opções de parâmetros 
    válidos a serem passados na requisição HTTP e exemplos de uso da API.

        Returns:
            response: objeto JSON contendo as opções válidas de parâmetros que 
            podem ser utilizados e um exemplo de requisição HTTP para facilitar 
            o uso da API ou uma mensagem de erro, se a solicitação falhar.

    GET /scrape/salvar/<string:opcao>: endpoint para salvar os dados raspados
    do site da Embrapa em um banco de dados que servirá como "fallback" caso o
    site venha a cair.

        Params:
            Path:
                opcao: opção principal da requisição HTTP

        Returns: 
            response: objeto JSON contendo informações de salvamento do banco
            de dados ou uma mensagem de erro, se a solicitação falhar.

Functions:
    build_full_url(parameters_sent): função para construir a url completa a ser
    aplicada na requisição HTTP. Ela é definida com base nos parâmetros passados.

        Params:
            parameters_sent (dict): dicionário contendo os parâmetros já 
            validados da requisição HTTP.

        Returns:
            str: url completa formatada para a requisição HTTP.

    get_table_headers(table): função para extrair os cabeçalhos da tabela 
    principal na página raspada.

        Params:
            table (Tag): elemento html da tabela principal na página raspada. 

        Returns:
            list: lista com os cabeçalhos extraidos da tabela principal na 
            página raspada.

    get_table_footers(table): função para extrair os rodapés da tabela 
    principal na página raspada.

        Params:
            table (Tag): elemento html da tabela principal na página raspada. 

        Returns:
            list: lista com os rodapés extraidos da tabela principal na 
            página raspada.

    get_data_table(parameters_sent, table): função para extrair os dados da 
    tabela principal na página raspada. 

        Params:
            parameters_sent (dict): dicionário contendo os parâmetros já 
            validados da requisição HTTP.
            table (Tag): elemento html da tabela principal na página raspada. 

        Returns:
            list: lista com os dados extraidos da tabela principal na 
            página raspada.

    get_table_sql(parametros): função que verifica qual o tipo de opção foi
    selecionada, envia instruções SQL para o banco de dados e retorna os dados
    de acordo com os parâmetros selecionados. Chamada apenas em caso de erro
    na parte do cliente.

        Params:
            parametros (dict): faz referência ao dicionário "parameters_sent" 
            que contém os parâmetros passados na requisição HTTP.

        Returns:
            response: objeto JSON com os dados organizados conforme os 
            parâmetros passados na requisição HTTP ou uma mensagem de erro, 
            se a solicitação falhar.

    scrape_table_content(parameters_sent): função que realiza a raspagem no site. 
    Integra as outras funções definidas nesse módulo (com exceção as dos
    endpoints).

        Params:
            parameters_sent (dict): dicionário contendo os parâmetros já 
            validados da requisição HTTP.

        Returns:
            response: objeto JSON com os dados organizados conforme os 
            parâmetros passados na requisição HTTP ou uma mensagem de erro, 
            se a solicitação falhar.
"""

import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pydantic import ValidationError
from sqlalchemy import create_engine
from src.models import QueryParametersModel
from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

CONNECTION_STRING = os.environ.get('POSTGRES_URL')
if CONNECTION_STRING and CONNECTION_STRING.startswith("postgres://"):
    CONNECTION_STRING = CONNECTION_STRING.replace("postgres://", "postgresql://", 1)

scraping_bp = Blueprint('Scraping', __name__)

def build_full_url(parameters_sent) -> str:
    """
    Constrói a URL completa para a requisição HTTP do site da Embrapa.

    A URL é composta pelos parâmetros passados na requisição HTTP. Contempla a
    opção principal ("option"), o ano ("year") e, caso exista, uma sub-opção 
    ("sub_option"), transformados para o formato esperado pela API.

    Params:
        parameters_sent (dict): dicionário contendo os parâmetros já validados 
        da requisição HTTP.

    Returns:
        str: url completa a ser utilizada na requisição HTTP.
    """
    PARTIAL_URL = 'http://vitibrasil.cnpuv.embrapa.br/index.php?'
    
    full_url = PARTIAL_URL+parameters_sent['option']+'&'+parameters_sent['year']

    if parameters_sent['sub_option']:
        full_url += '&'+parameters_sent['sub_option']
   
    return full_url

def get_table_headers(table) -> list:
    """
    Extrai os cabeçalhos da tabela principal da página raspada.

    Os cabeçalhos são encontrados no elemento <thead> da tabela. 
    Os elementos foram dispostos em níveis conforme o aninhamento, 
    para facilitar a compreensão.

    Params:
        table: objeto BeautifulSoup representando a tabela principal.

    Returns:
        list: lista de strings com os nomes dos cabeçalhos da tabela.
    """
    # elemento de nível 2 - cabeçalho da tabela de produtos
    table_header = table.find('thead')

    # elemento de nível 3 - linha do cabeçalho da tabela
    header_row = table_header.find('tr')

    # elemento de nível 4 - cabeçalhos da linha
    headers = header_row.find_all('th')
    return [header.get_text(strip=True) for header in headers]

def get_table_footers(table) -> list:
    """
    Extrai os rodapés da tabela principal da página raspada.

    Os rodapés são encontrados no elemento <tfoot> da tabela.
    Os elementos foram dispostos em níveis conforme o aninhamento, 
    para facilitar a compreensão.
    
    Params:
        table: objeto BeautifulSoup representando a tabela principal.

    Returns:
        list: lista de strings com os valores dos rodapés da tabela.
    """
    # elemento de nível 2 - rodapé da tabela de produtos
    table_footer = table.find('tfoot', class_='tb_total')

    # elemento de nível 3 - linha do rodapé da tabela
    footer_row = table_footer.find('tr')

    # elemento de nível 4 - células da linha
    cells = footer_row.find_all('td')
    return [cell.get_text(strip=True) for cell in cells]

def get_data_table(parameters_sent, table) -> list:
    """
    Extrai os dados da tabela principal da página raspada com base na opção 
    selecionada. Os elementos foram dispostos em níveis conforme o aninhamento, 
    para facilitar a compreensão.

    A função analisa o corpo da tabela principal e estrutura os dados de acordo 
    com o tipo de opção informada em "original_option".

    Para as opções "producao", "processamento" e "comercializacao", os dados são 
    extraídos em formato de categorias e subcategorias.

    Para as opções "importacao" e "exportacao", os dados são organizados em 
    listas com informações de países, quantidade e preço.

    Params:
        parameters_sent (dict): dicionário com os parâmetros validados da 
        requisição HTTP.
        table: objeto BeautifulSoup que representa a tabela principal.

    Returns:
        list: lista contendo os dados extraídos da tabela, organizados conforme 
        o tipo de opção selecionada. 
        O formato da lista varia de acordo com a opção:
            lista de tuplas com categorias e subcategorias: produção, 
            processamento, comercialização.
            lista de listas com países, quantidades e preços: importação e 
            exportação.
    """
    items_dict = {}
    # Flag para navegar entre itens e sub-itens, caso aplicável na "option"
    current_category = None
    items_list = []
    
    # elemento de nível 2 - corpo da tabela de produtos
    table_body = table.find('tbody')
    
    if parameters_sent['original_option'] in \
    ['producao', 'processamento', 'comercializacao']:
        
    # elemento de nível 3 - linhas do corpo da tabela
        for row in table_body.find_all('tr'):

            # elemento de nível 4 - células das linhas 

            # items
            cells = row.find_all('td', class_='tb_item')

            if cells:
                temporary_list = [cell.get_text(strip=True) for cell in cells]

                # evita quebrar o programa, caso não haja elementos
                if len(temporary_list) >= 2:
                    product = temporary_list[0]
                    quantity = temporary_list[1]
                    current_category = f'{product} : {quantity}'
                    items_dict[current_category] = {}

            # sub-items
            cells = row.find_all('td', class_='tb_subitem')
            
            if cells:
                temporary_list = [cell.get_text(strip=True) for cell in cells]

                # evita quebrar o programa, caso não haja elementos
                if len(temporary_list) >= 2:
                    sub_product = temporary_list[0]                    
                    quantity = temporary_list[1]
                    items_dict[current_category][sub_product] = quantity

        return list(items_dict.items())
    
    if parameters_sent['original_option'] in \
    ['importacao', 'exportacao']:

        # elemento de nível 3 - linhas do corpo da tabela
        for row in table_body.find_all('tr'):

            # elemento de nível 4 - células das linhas 
            cells = row.find_all('td')

            if cells:
                temporary_list = [cell.get_text(strip=True) for cell in cells]

                # evita quebrar o programa, caso não haja elementos
                if len(temporary_list) >= 3:
                    countries = temporary_list[0]
                    quantity = temporary_list[1]
                    price = temporary_list[2]
                    items_list.append([countries, quantity, price])
        
        return items_list

def get_table_sql(parametros) -> tuple | Response:
    """
    Verifica qual a opção selecionada, faz uma consulta SQL e retorna os dados.

    Params:
        parametros (dict): faz referência ao dicionário "parameters_sent" 
        que contém os parâmetros passados na requisição HTTP.

    Returns:
        tuple | Response:
            Retorna uma tupla de listas com os valores dos dados puxados da 
            tabela com a consulta SQL ou um objeto JSON com uma mensagem de 
            erro, se a solicitação falhar.
    """
    engine = create_engine(CONNECTION_STRING)
    try: 
        # Inicializa variaveis
        dados_finais=[]

        if parametros['original_option'] in ['producao', 'comercializacao']:
            query = f'''
            SELECT 
            {parametros['original_option']}."Produto", 
            {parametros['original_option']}."Quantidade (L.)", 
            {parametros['original_option']}."Nivel", 
            {parametros['original_option']}."Categoria"
            FROM {parametros['original_option']}
            WHERE "Ano" = {parametros['original_year']}
            '''
            df = pd.read_sql(query, engine)

            for idx, row in df.head(df.shape[0]-2).iterrows():
                if idx == 0:
                    continue
                else:
                    dados_finais.append([row['Produto'],row['Quantidade (L.)'],row['Nivel'],row['Categoria']])
            return(list(df.head(1)), list(df.tail(1).iloc[0]), dados_finais)
        
        elif parametros['original_option'] in ['processamento']:
            query = f'''

            SELECT 
            {parametros['original_option']}."Produto", 
            {parametros['original_option']}."Quantidade (L.)", 
            {parametros['original_option']}."Nivel", 
            {parametros['original_option']}."Categoria"
            FROM {parametros['original_option']}
            WHERE "Ano" = {parametros['original_year']}
            '''
            if parametros['original_sub_option']:
                query += f'''AND {parametros["original_option"]}."Categoria" in ('{parametros["original_sub_option"]}')'''

            df = pd.read_sql(query, engine)

            for idx, row in df.head(df.shape[0]-2).iterrows():
                if idx == 0:
                    continue
                else:
                    dados_finais.append([row['Produto'],row['Quantidade (L.)'],row['Nivel'],row['Categoria']])
            return(list(df.head(1)), list(df.tail(1).iloc[0]), dados_finais)
        
        elif parametros['original_option'] in ['importacao', 'exportacao']:
            query = f'''

            SELECT 
            {parametros['original_option']}."Paises", 
            {parametros['original_option']}."Quantidade (Kg)", 
            {parametros['original_option']}."Valor (US$)"
            FROM {parametros['original_option']}
            WHERE "Ano" = {parametros['original_year']}

            '''
            if parametros['original_sub_option']:
                query += f'''AND {parametros["original_option"]}."Categoria" in ('{parametros["original_sub_option"]}')'''

            df = pd.read_sql(query, engine)

            for idx, row in df.head(df.shape[0]-2).iterrows():
                if idx == 0:
                    continue
                else:
                    dados_finais.append([row['Paises'],row['Quantidade (Kg)'],row['Valor (US$)']])
            return(list(df.head(1)), list(df.tail(1).iloc[0]), dados_finais)
        
    except Exception as e:
        return jsonify({"error":str(e)}), 500

def scrape_table_content(parameters_sent) -> Response:
    """
    Realiza a raspagem de dados da tabela principal da página raspada no site 
    da Embrapa com base nos parâmetros fornecidos.

    Esta função constrói a url da requisição HTTP a partir dos parâmetros 
    recebidos, realiza a requisição HTTP ao site da Embrapa, extrai e retorna 
    os dados selecionados da tabela principal encontrada na página raspada.

    Os dados retornados incluem:
        Cabeçalhos da tabela.
        Rodapés da tabela.
        Dados principais (linhas da tabela).

    Params:
        parameters_sent (dict): Dicionário com os parâmetros validados da 
        requisição HTTP.

    Returns:
        response: objeto JSON com os dados organizados conforme os parâmetros 
        passados na requisição HTTP ou uma mensagem de erro, se a solicitação 
        falhar.
    """
    full_url = build_full_url(parameters_sent) 

    # Para teste da modelagem, dos parâmetros passados na requisição HTTP, com a 
    # QueryParametersModel
    # return jsonify({"A url completa é: ":full_url})

    try:

        try:
            response = requests.get(full_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # elemento de nível 1 - tabela de produtos
            table = soup.find('table', class_='tb_base tb_dados')

            table_headers = get_table_headers(table)
            table_footers = get_table_footers(table)
            data_table = get_data_table(parameters_sent, table)
        except:
            table_headers, table_footers, data_table = get_table_sql(parameters_sent)

        return jsonify({
                f"[Parâmetros da pesquisa]":
                f"[opção={parameters_sent['original_option']}, "
                f"ano={parameters_sent['original_year']}, "
                f"sub_opção={parameters_sent['original_sub_option']}"
                " (None, se não existir)]",
                "":"",
                f"{table_headers} {table_footers}":
                data_table
                }), 200

    except Exception as e:
        return jsonify({"error":str(e)})

@scraping_bp.route('/scrape/content', methods=['GET'])
@jwt_required()
def scrap_content() -> Response:
    """
    Endpoint principal para raspagem de dados da Embrapa.
    ---
    security:
      - JWT: []
    consumes:
      - application/json
    produces:
      - application/json
    tags:
      - Scraping
    parameters:
      - in: query
        name: option
        type: string
        enum: ['producao','processamento','comercializacao','importacao','exportacao']
        required: true
      - in: query
        name: year
        type: string
        required: false
        description: Digite um ano (Ex. 2000)
      - in: query
        name: sub_option
        type: string
        required: false
        description: 
            Selecionar referente a opçao principal  \n
            \n
            processamento\n
            --viniferas, \n
            --americanas_e_hibridas, \n
            --uvas_de_mesa, \n
            --sem_classificacao \n
            \n
            importacao\n
            --vinhos_de_mesa, \n
            --espumantes, \n
            --uvas_frescas, \n
            --uvas_passas, \n
            --suco_de_uva \n
            \n
            exportacao\n
            --vinhos_de_mesa, \n
            --espumantes, \n
            --uvas_frescas, \n
            --suco_de_uva\n
    responses:
      200:
        description: Dados raspados e organizados conforme os parâmetros fornecidos.
      422:
        description: Erro de validação dos parâmetros.
      500:
        description:  Erro interno no servidor ao tentar realizar a raspagem.
    """    
    try:
        data = request.args.to_dict()
        parameters_sent = QueryParametersModel(**data).model_dump()

        return scrape_table_content(parameters_sent)
    
    except ValidationError as e:
        return jsonify({
            "error": "Validation failed",
            "details": str(e),
            "support":"/scrape/content/help",
            "example": {"option": "producao", "year": 2023}
        }), 422
    
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@scraping_bp.route('/scrape/content/help', methods=['GET'])
def scrap_content_help() -> Response:
    """
    Endpoint de auxílio para uso da API de raspagem.
    ---
    tags:
      - Scraping
    responses:
      200:
        description: Dicionário com parâmetros válidos para a requisição HTTP e exemplo de uso da API
      500:
        description: Erro interno no servidor ao tentar gerar os dados de auxílio.
    """ 
    embrapa_scraping_map = {
        "producao": {
            "parameters": {
                "year": "between 1970 and 2023"
            }
        },
        "processamento": {
            "parameters": {
                "year": "between 1970 and 2023",
                "sub_option": [
                    "viniferas",
                    "americanas_e_hibridas",
                    "uvas_de_mesa",
                    "sem_classificacao"
                ]
            }
        },
        "comercializacao": {
            "parameters": {
                "year": "between 1970 and 2023"
            }
        },
        "importacao": {
            "parameters": {
                "year": "between 1970 and 2024",
                "sub_option": [
                    "vinhos_de_mesa",
                    "espumantes",
                    "uvas_frescas",
                    "uvas_passas",
                    "suco_de_uva"
                ]
            }
        },
        "exportacao": {
            "parameters": {
                "year": "between 1970 and 2024",
                "sub_option": [
                    "vinhos_de_mesa",
                    "espumantes",
                    "uvas_frescas",
                    "suco_de_uva"
                ]
            }
        }
    }
    try:
        return jsonify({
            "help": "Esse endpoint apresenta as opções e parâmetros válidos na API.",
            "/":"",
            "example":"http://127.0.0.1:5000/scrape/content?option=producao&year=2000",
            "//":"",
            "valids options": list(embrapa_scraping_map.keys()),
            "details": embrapa_scraping_map
        }), 200
    
    except Exception as e:
        return jsonify({"error":str(e)}), 500

# Endpoint de scraping com loop de anos
@scraping_bp.route('/scrape/salvar/<string:opcao>', methods=['GET'])
@jwt_required()
def save_table_sql(opcao) -> Response:
    """
    Endpoint para salvar as tabelas no SQL para os anos de 1970 a 2023
    ---
    tags:
      - Scraping
    security:
      - JWT: []
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: path
        name: opcao
        type: string
        required: true
        description: Escolha entre as opções
        enum: [producao, processamento, comercializacao, importacao, exportacao]
    responses:
      200:
        description: Dados salvos no servidor
        schema:
          type: object
          properties:
            msg:
              type: string
            user:
              type: string
            opcao:
              type: string
            anos_processados:
              type: array
              items:
                type: integer
      400:
        description: Opção inválida
        schema:
          type: object
          properties:
            error:
              type: string
      401:
        description: Token ausente ou inválido
        schema:
          type: object
          properties:
            msg:
              type: string
      422:
        description: Erro de formato do token
        schema:
          type: object
          properties:
            msg:
              type: string
      500:
        description: Erro interno no servidor ao tentar salvar
        schema:
          type: object
          properties:
            error:
              type: string
    """
    dict_options = {
        "producao": "opcao=opt_02",
        "processamento": "opcao=opt_03",
        "comercializacao": "opcao=opt_04",
        "importacao": "opcao=opt_05",
        "exportacao": "opcao=opt_06",
    }

    # Valida a opção
    if opcao not in dict_options:
        return jsonify({
            'error': f'Opção inválida. Escolha entre: {", ".join(dict_options.keys())}'
        }), 400

    current_user = get_jwt_identity()
    anos_processados = []
    errors = []

    fg = 0
    for ano in range(1970, 2025):
        if ano != 2024:
            if opcao in ['producao', 'comercializacao']:
                try:
                # Faz a requisição para a URL
                    parameters_sent = {
                        'option': str(dict_options[opcao]), 
                        'year': f'ano={ano}', 
                        'sub_option': None, 
                        'original_option': str(opcao), 
                        'original_year': ano,
                        'original_sub_option': None
                    }

                    full_url = build_full_url(parameters_sent)
                    response = requests.get(full_url)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Inicializa variáveis
                    produtos = []
                    quantidades = []
                    niveis = []
                    categorias = []
                    current_category = None

                    # Extrai linhas do tbody
                    tbody = soup.find('tbody')

                    for row in tbody.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) < 2:
                            continue
                        produto = cells[0].text.strip()
                        quantidade = cells[1].text.strip()

                        # Determina se é item ou subitem
                        if cells[0].get('class') == ['tb_item']:
                            nivel = 'item'
                            current_category = produto
                        else:
                            nivel = 'subitem'

                        produtos.append(produto)
                        quantidades.append(quantidade)
                        niveis.append(nivel)
                        categorias.append(current_category if nivel == 'subitem' else None)

                    # Extrai total do tfoot
                    tfoot = soup.find('tfoot')
                    tfoot_row = tfoot.find('tr')
                    total_cells = tfoot_row.find_all('td')

                    total_produto = total_cells[0].text.strip()
                    total_quantidade = total_cells[1].text.strip()
                    produtos.append(total_produto)
                    quantidades.append(total_quantidade)
                    niveis.append('total')
                    categorias.append(None)

                    # Limpa quantidades
                    quantidades = [q.replace('.', '') if q != '-' else '0' for q in quantidades]

                    # Cria DataFrame
                    df = pd.DataFrame({
                        'Produto': produtos,
                        'Quantidade (L.)': quantidades,
                        'Nivel': niveis,
                        'Categoria': categorias,
                        'Ano':ano
                    })

                    engine = create_engine(CONNECTION_STRING)

                    if fg == 0:
                        df.to_sql(parameters_sent['original_option'], engine, if_exists='replace', index=False)
                        anos_processados.append(ano)
                        fg+=1
                    else:
                        df.to_sql(parameters_sent['original_option'], engine, if_exists='append', index=False)
                        anos_processados.append(ano)

                except requests.RequestException as e:
                    errors.append(f'Erro na requisição HTTP: {str(e)}')
                except Exception as e:
                    errors.append(f'Erro ao processar os dados: {str(e)}')

        elif opcao in ['processamento']:
            if ano != 2024:
                dict_sub_opt_1 = {
                    "viniferas" :"subopt_01",
                    "americanas_e_hibridas" :"subopt_01",
                    "uvas_de_mesa" :"subopt_01",
                    "sem_classificacao":"subopt_01",
                }

                for sub_opt in ['viniferas', 'americanas_e_hibridas', 'uvas_de_mesa', 'sem_classificacao']:
                    try:
                    # Faz a requisição para a URL
                        
                        parameters_sent = {
                            'option': str(dict_options[opcao]), 
                            'year': f'ano={ano}', 
                            'sub_option': f'subopcao={dict_sub_opt_1[sub_opt]}', 
                            'original_option': str(opcao), 
                            'original_year': ano,
                            'original_sub_option': sub_opt
                        }

                        full_url = build_full_url(parameters_sent)
                        response = requests.get(full_url)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Inicializa variáveis
                        produtos = []
                        quantidades = []
                        niveis = []
                        categorias = []
                        opcoes = []
                        current_category = None

                        # Extrai linhas do tbody
                        tbody = soup.find('tbody')

                        for row in tbody.find_all('tr'):
                            cells = row.find_all('td')
                            if len(cells) < 2:
                                continue
                            produto = cells[0].text.strip()
                            quantidade = cells[1].text.strip()

                            # Determina se é item ou subitem
                            if cells[0].get('class') == ['tb_item']:
                                nivel = 'item'
                                current_category = produto
                            else:
                                nivel = 'subitem'

                            produtos.append(produto)
                            quantidades.append(quantidade)
                            niveis.append(nivel)
                            categorias.append(current_category if nivel == 'subitem' else None)
                            opcoes.append(sub_opt)

                        # Extrai total do tfoot
                        tfoot = soup.find('tfoot')
                        tfoot_row = tfoot.find('tr')
                        total_cells = tfoot_row.find_all('td')

                        total_produto = total_cells[0].text.strip()
                        total_quantidade = total_cells[1].text.strip()
                        produtos.append(total_produto)
                        quantidades.append(total_quantidade)
                        niveis.append('total')
                        opcoes.append(sub_opt)
                        categorias.append(current_category if nivel == 'total' else None)

                        # Limpa quantidades
                        quantidades = [q.replace('.', '') if q != '-' else '0' for q in quantidades]

                        # Cria DataFrame
                        df = pd.DataFrame({
                            'Produto': produtos,
                            'Quantidade (L.)': quantidades,
                            'Nivel': niveis,
                            'Categoria': categorias,
                            'Opcoes':opcoes, 
                            'Ano':ano
                        })

                        engine = create_engine(CONNECTION_STRING)

                        if fg == 0:
                            df.to_sql(parameters_sent['original_option'], engine, if_exists='replace', index=False)
                            anos_processados.append([ano, sub_opt])
                            fg+=1
                        else:
                            df.to_sql(parameters_sent['original_option'], engine, if_exists='append', index=False)
                            anos_processados.append([ano, sub_opt])
                    
                    except requests.RequestException as e:
                        errors.append(f'Erro na requisição HTTP: {str(e)}')
                    except Exception as e:
                        errors.append(f'Erro ao processar os dados: {str(e)}')

        elif opcao in ['importacao', 'exportacao']:
            dict_sub_opt_2 = {
                'vinhos_de_mesa':'subopt_01',
                'espumantes':'subopt_02',
                'uvas_frescas':'subopt_03',
                'uvas_passas':'subopt_04',
                'suco_de_uva':'subopt_05'
            }

            for sub_opt in ['vinhos_de_mesa' ,'espumantes' ,'uvas_frescas' ,'uvas_passas' ,'suco_de_uva']:
                try:
                # Faz a requisição para a URL
                    
                    parameters_sent = {
                        'option': str(dict_options[opcao]), 
                        'year': f'ano={ano}', 
                        'sub_option': f'subopcao={dict_sub_opt_2[sub_opt]}', 
                        'original_option': str(opcao), 
                        'original_year': ano,
                        'original_sub_option': sub_opt
                    }

                    full_url = build_full_url(parameters_sent)
                    response = requests.get(full_url)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Inicializa variáveis
                    paises = []
                    quantidades = []
                    valores = []
                    categorias = []
                    current_category = None

                    # Extrai linhas do tbody
                    tbody = soup.find('tbody')

                    for row in tbody.find_all('tr'):
                        cells = row.find_all('td')
                        if len(cells) < 2:
                            continue
                        pais = cells[0].text.strip()
                        quantidade = cells[1].text.strip()
                        valor = cells[2].text.strip()

                        paises.append(pais)
                        quantidades.append(quantidade)
                        valores.append(valor)
                        categorias.append(sub_opt)

                    # Extrai total do tfoot
                    tfoot = soup.find('tfoot')
                    tfoot_row = tfoot.find('tr')
                    total_cells = tfoot_row.find_all('td')

                    total_quantidade = total_cells[1].text.strip()
                    total_valor = total_cells[2].text.strip()
                    quantidades.append(total_quantidade)
                    valores.append(total_valor)
                    paises.append(total_cells[0].text.strip())
                    categorias.append(sub_opt)

                    # Limpa quantidades
                    quantidades = [q.replace('.', '') if q != '-' else '0' for q in quantidades]

                    # Cria DataFrame
                    df = pd.DataFrame({
                        'Paises': paises,
                        'Quantidade (Kg)': quantidades,
                        'Valor (US$)': valores,
                        'Categoria': categorias,
                        'Ano':ano
                    })

                    engine = create_engine(CONNECTION_STRING)

                    if fg == 0:
                        df.to_sql(parameters_sent['original_option'], engine, if_exists='replace', index=False)
                        anos_processados.append([ano, sub_opt])
                        fg+=1

                    else:
                        df.to_sql(parameters_sent['original_option'], engine, if_exists='append', index=False)
                        anos_processados.append([ano, sub_opt])
                
                except requests.RequestException as e:
                    errors.append(f'Erro na requisição HTTP: {str(e)}')
                except Exception as e:
                    errors.append(f'Erro ao processar os dados: {str(e)}')

    return jsonify({
        'msg': 'Tabelas salvas com sucesso',
        'user': str(current_user).strip(),
        'opcao': opcao,
        'anos_processados': anos_processados,
        'errors': errors if errors else None
    }), 200