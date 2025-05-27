"""
scraping.py

Módulo responsável pela raspagem de dados do site da Embrapa

Este módulo fornece endpoints e funções referentes a raspagem de dados do site 
da Embrapa (http://vitibrasil.cnpuv.embrapa.br/index.php?opcao=opt_01), 
contemplando dados da vitivinicultura do estado do Rio Grande do Sul.

Os dados extraídos são estruturados e retornados em formato JSON.

Endpoints:
    GET /scrape/content: endpoint para raspagem de dados do site da Embrapa com 
    filtros baseados nos parâmetros passados na requisição HTTP (option, year e 
    sub_option).

        Params:
            Query: 
                option: opção principal da requisição HTTP
                year: ano da opção principal da requisição HTTP
                sub_option: sub-opção da opção principal da requisição HTTP, 
                caso aplicável

        Returns:
            response: objeto JSON com os dados organizados conforme os 
            parâmetros passados na requisição HTTP ou uma mensagem de erro, 
            se a solicitação falhar.
           
    GET /scrape/content/help: endpoint auxiliar que exibe opções de parâmetros 
    válidos a serem passados na requisição HTTP e exemplos de uso da API.

        Returns:
            response: objeto JSON contendo as opções válidas de parâmetros que 
            podem ser utilizados neste endpoint e um exemplo de requisição HTTP 
            para facilitar o uso da API ou uma mensagem de erro, se a 
            solicitação falhar.

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
from flask import Blueprint, jsonify, request, Response
import requests
from bs4 import BeautifulSoup
from src.models import QueryParametersModel
from pydantic import ValidationError

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

    try:

        response = requests.get(full_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # elemento de nível 1 - tabela de produtos
        table = soup.find('table', class_='tb_base tb_dados')

        table_headers = get_table_headers(table)
        table_footers = get_table_footers(table)
        data_table = get_data_table(parameters_sent, table)

        return jsonify({
                f"[Parâmetros da pesquisa]":
                f'[opção={parameters_sent['original_option']}, '
                f'ano={parameters_sent['original_year']}, '
                f'sub_opção={parameters_sent['original_sub_option']}'
                ' (None, se não existir)]',
                "":"",
                f"{table_headers} {table_footers}":
                data_table
                }), 200

    except Exception as e:
        return jsonify({"error":str(e)})

@scraping_bp.route('/scrape/content', methods=['GET'])
def scrap_content() -> Response:
    """
    Endpoint principal para raspagem de dados da Embrapa.
    ---
    parameters:
      - in: query
        name: option
        type: string
        required: true
        description: opção principal da requisição HTTP
      - in: query
        name: year
        type: string
        required: false
        description: ano da opção principal da requisição HTTP
      - in: query
        name: sub_option
        type: string
        required: false
        description: sub-opção da opção principal da requisição HTTP
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