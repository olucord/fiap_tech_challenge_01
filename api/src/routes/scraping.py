from flask import Blueprint, jsonify, request
import requests
from bs4 import BeautifulSoup
from api.src.models import QueryParametersModel
from pydantic import ValidationError

scraping_bp = Blueprint('Scraping', __name__)

def build_full_url(parameters_sent):

    PARTIAL_URL = 'http://vitibrasil.cnpuv.embrapa.br/index.php?'
    
    full_url = PARTIAL_URL+parameters_sent['option']+'&'+parameters_sent['year']

    if parameters_sent['sub_option']:
        full_url += '&'+parameters_sent['sub_option']
   
    return full_url


def get_table_headers(data_table):

    # elemento de nível 2 - cabeçalho da tabela de produtos
    table_header = data_table.find('thead')

    # elemento de nível 3 - linha do cabeçalho da tabela
    header_row = table_header.find('tr')

    # elemento de nível 4 - cabeçalhos da linha
    headers = header_row.find_all('th')
    return [header.get_text(strip=True) for header in headers]

def get_table_footers(data_table):
    
    # elemento de nível 2 - rodapé da tabela de produtos
    table_footer = data_table.find('tfoot', class_='tb_total')

    # elemento de nível 3 - linha do rodapé da tabela
    footer_row = table_footer.find('tr')

    # elemento de nível 4 - células da linha
    cells = footer_row.find_all('td')
    return [cell.get_text(strip=True) for cell in cells]

def get_data_table(parameters_sent, table):

    dict_items = {}
    # Flag para navegar entre itens e sub-itens
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
                    dict_items[current_category] = {}

            # sub-items
            cells = row.find_all('td', class_='tb_subitem')
            
            if cells:
                temporary_list = [cell.get_text(strip=True) for cell in cells]

                if len(temporary_list) >= 2:
                    sub_product = temporary_list[0]                    
                    quantity = temporary_list[1]
                    dict_items[current_category][sub_product] = quantity

        return list(dict_items.items())
    
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
    
def scrape_table_content(parameters_sent):

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
                f"[opção={parameters_sent['original_option']}, "
                f"ano={parameters_sent['original_year']}, "
                f"sub_opção={parameters_sent['original_sub_option']}"
                ' (None, se não existir)]',
                "":"",
                f"{table_headers} {table_footers}":
                data_table
                })

    except Exception as e:
        return jsonify({"error":str(e)})

@scraping_bp.route('/scrape/content', methods=['GET'])
def scrap_content():

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
    
    except ValueError as e:
        return jsonify({"error":str(e)}), 422

@scraping_bp.route('/scrape/content/help', methods=['GET'])

def get_help():
    
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

    return jsonify({
        "help": "Esse endpoint apresenta as opções e parâmetros válidos na API.",
        "/":"",
        "example":"http://127.0.0.1:5000/scrape/content?option=producao&year=2000",
        "//":"",
        "valids options": list(embrapa_scraping_map.keys()),
        "details": embrapa_scraping_map
    })
