"""
query_params_model.py

Define e valida os parâmetros de consulta aceitos nas requisições HTTP da API. 

Este módulo contém o modelo de dados que processa, transforma e valida os 
argumentos fornecidos pelo usuário nas chamadas à API. Utiliza Pydantic para 
assegurar a consistência e formato dos dados antes de serem processados pela 
aplicação.

Classes:
    - QueryParametersModel: Valida, transforma e gera os parâmetros utilizados 
    na API.
"""

from pydantic import BaseModel, model_validator, computed_field
from typing import Optional
    
class QueryParametersModel(BaseModel):
    """
    Valida e transforma os parâmetros "option", "year" e "sub_option" passados
    pelo usuário, convertendo-os em formatos esperados pela API. Armazena os 
    argumentos originais fornecidos pelo usuário em atributos computados que 
    não são passados diretamente, mas gerados posteriormente para rastreabili-
    dade.
    ---
    Atributos validados e transformados em argumentos da requisição HTTP:
        - option (str): deve ser uma das opções permitidas na consulta 
        ("producao", "importacao", etc). 
        - year (Optional[str]): o ano da opção para a consulta. Pode ser 
        definida ou recebe um valor padrão. Deve estar em um intervalo 
        aceitável, conforme a "option" escolhida.
        - sub_option (Optional[str]): a sub-opção da opção escolhida para a 
        consulta, caso aplicável. Pode ser definida ou recebe um valor padrão. 
        É validada ou inferida conforme a "option" escolhida. 
    Atributos computados:
        - _original_option (Optional[str]): valor de "option" antes da 
        transformação.
        - _original_year (Optional[str]): valor de "year" antes da 
        transformação.
        - _original_sub_option (Optional[str]): valor de "sub_option" antes da 
        transformação.
    Outros atributos:
        - model_config (dict): impede a passagem de argumentos extras, 
        permitindo apenas os presentes no modelo dessa classe.
    """
    option: str
    year: Optional[str] = None
    sub_option: Optional[str] = None
    
    _original_option: Optional[str] = None
    _original_year: Optional[str] = None
    _original_sub_option: Optional[str] = None

    model_config = {
        'extra':'forbid'
    }

    @model_validator(mode='after')
    def validate_and_transform_option(self) -> 'QueryParametersModel':
        """
        Valida e transforma o argumento "option" passado.

        Converte o valor de "option" para um formato interno e salva o valor 
        original em "_original_option". Lança um erro se "option" não estiver 
        entre os valores permitidos.

        Returns:
            QueryParametersModel: A própria instância modificada do modelo.
        """
        option_map = {
            'producao':'opcao=opt_02',
            'processamento':'opcao=opt_03',
            'comercializacao':'opcao=opt_04',
            'importacao':'opcao=opt_05',
            'exportacao':'opcao=opt_06',
        }

        if self.option is None or self.option not in option_map:
            raise ValueError(
                'Você precisa escolher uma opção entre (producao, ' 
                'processamento, comercializacao, importacao, exportacao)'
            )

        self._original_option = self.option
        self.option = option_map[self.option]

        return self
        
    @computed_field
    def original_option(self) -> Optional[str]:
        """
        Retorna o valor original do argumento "option", antes da transformação.

        Returns:
            Optional[str]: O valor original de "option" ou None se não definido.
        """
        return self._original_option
    
    @model_validator(mode='after')
    def validate_and_transform_year(self) -> 'QueryParametersModel':
        """
        Valida e transforma o argumento "year" com base na opção selecionada.

        Define um valor padrão se "year" não for informado. Valida se o ano 
        informado está dentro do intervalo permitido de acordo com o valor 
        original de "option". Também armazena o valor original de "year" 
        antes da transformação.

        Returns:
            QueryParametersModel: A própria instância modificada do modelo.
        """
        year_map = {
            "until_2024":['importacao', 'exportacao'],
            "until_2023":['producao', 'processamento', 'comercializacao']
        }

        if self.year is None:
            self._original_year = '2023'
            self.year = 'ano=2023'
            return self

        try:
            parsed_year = int(self.year)
        except ValueError:
            raise ValueError(
                'Você digitou um ano inválido. '
                'São aceitos apenas números inteiros.'
                ) 
                
        if self._original_option in year_map['until_2024']:
            
            if not (1970 <= parsed_year <= 2024):
                raise ValueError(
                    'O ano precisa estar no ' 
                    'intervalo entre 1970 e 2024'
                )
            
        if self._original_option in year_map['until_2023']:
                
            if not (1970 <= parsed_year <= 2023):
                raise ValueError(
                    'O ano precisa estar no ' 
                    'intervalo entre 1970 e 2023'
                )
            
        self._original_year = self.year
        self.year = 'ano='+self.year 
        
        return self  

    @computed_field
    def original_year(self) -> Optional[str]:
        """
        Retorna o valor original do argumento "year", antes da transformação.

        Returns:
            Optional[str]: O valor original de "year" ou None se não definido.
        """
        return self._original_year
    
    @model_validator(mode='after')
    def validate_and_set_sub_option(self) -> 'QueryParametersModel':
        """
        Valida e transforma o argumento "sub_option" com base na opção principal
        ("option").

        Se "sub_option" não for fornecido, define um valor padrão baseado em 
        "option". Valida se o valor informado é permitido para a opção atual. 
        Lança erro se a combinação for inválida ou se "sub_option" for usado 
        indevidamente.

        Returns:
            QueryParametersModel: A própria instância modificada do modelo.
        """
        sub_options_map = {
            'processamento': {
                'viniferas':'subopcao=subopt_01',
                'americanas_e_hibridas':'subopcao=subopt_02',
                'uvas_de_mesa':'subopcao=subopt_03',
                'sem_classificacao':'subopcao=subopt_04'
            },
            'importacao': {
                'vinhos_de_mesa':'subopcao=subopt_01',
                'espumantes':'subopcao=subopt_02',
                'uvas_frescas':'subopcao=subopt_03',
                'uvas_passas':'subopcao=subopt_04',
                'suco_de_uva':'subopcao=subopt_05'
            },
            'exportacao': {
                'vinhos_de_mesa':'subopcao=subopt_01',
                'espumantes':'subopcao=subopt_02',
                'uvas_frescas':'subopcao=subopt_03',
                'suco_de_uva':'subopcao=subopt_04'
            }
        }

        if self._original_option in sub_options_map:
            valids_sub = sub_options_map[self._original_option]

            if self.sub_option is None:

                self._original_sub_option = list(valids_sub.keys())[0]
                self.sub_option = valids_sub[self._original_sub_option]
                return self

            elif self.sub_option not in valids_sub:
                raise ValueError(
                    "Valor inválido para sub_option com option = "
                    f"'{self._original_option}'. "
                    f"Permitidos: {list(valids_sub.keys())}"
                )
            
            self._original_sub_option = self.sub_option
            self.sub_option = valids_sub[self.sub_option]
            
        else:

            if self.sub_option is not None:
                raise ValueError(
                    "sub_option não é permitido quando option="
                    f"'{self._original_option}'"
                )

        return self
    
    @computed_field
    def original_sub_option(self) -> Optional[str]:
        """
        Retorna o valor original do argumento "sub_option", antes da 
        transformação.

        Returns:
            Optional[str]: O valor original de "sub_option" ou None se não 
            definido.
        """
        return self._original_sub_option