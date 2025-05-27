"""
query_params_model.py

Define e valida os parâmetros de consulta passados nas requisições HTTP da API. 

Este módulo contém o modelo de dados que valida e transforma os parâmetros 
fornecidos pelo usuário nas chamadas à API. Utiliza Pydantic para assegurar a 
consistência e formato dos dados antes de serem processados pela aplicação.

Classes:
    QueryParametersModel: Valida, transforma e gera os parâmetros utilizados nas 
    requisições HTTP da API.
"""

from pydantic import BaseModel, model_validator, computed_field
from typing import Optional
    
class QueryParametersModel(BaseModel):
    """
    Esta classe apresenta o modelo que será utilizado para validar os parâmetros
    passados pelo usuário na requisição HTTP, transformando-os para formatos 
    esperados pela API. Também armazena os parâmetros originais fornecidos em 
    atributos privados que não são passados diretamente, mas gerados 
    posteriormente para rastreabilidade, sendo acessados através de campos 
    computados.

    Foi definido um atributo "model_config" como um dicionário contendo um par 
    chave-valor "{'extra':'forbid'}", impedindo a inclusão de parâmetros não 
    definidos no modelo.
    
    Attrs:
        option (str): obrigatório. Deve ser uma das opções permitidas na 
        requisição HTTP ("producao", "importacao", etc). 
        year (Optional[str]): o ano da opção para a requisição HTTP. Pode ser 
        definido ou recebe um valor padrão. Deve estar em um intervalo 
        aceitável, conforme a "option" escolhida.
        sub_option (Optional[str]): a sub-opção da opção escolhida para a 
        requisição HTTP, caso aplicável. Pode ser definida ou recebe um valor 
        padrão e é validada ou inferida conforme a "option" escolhida. 
        _original_option (Optional[str]): preserva o valor de "option" antes da 
        transformação.
        _original_year (Optional[str]): preserva o valor de "year" antes da 
        transformação.
        _original_sub_option (Optional[str]): preserva o valor de "sub_option" 
        antes da transformação.
        model_config (dict): impede a passagem de parâmetross extras na 
        requisição HTTP, permitindo apenas os presentes no modelo dessa classe.
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
        Valida e transforma o atributo "option", gerando "_original_option" 

        O valor de "option" é obrigatório e deve ser uma das seguintes opções:
        "producao", "processamento", "comercializacao", "importacao" ou 
        "exportacao". 

        Se for válido, o valor de "option" é transformado para o formato 
        esperado pela API e o valor original é armazenado em um atributo 
        privado, o "_original_option", para fins de rastreamento.

        Raises:
            ValueError: se o valor de "option" não estiver entre os valores 
            permitidos.

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
        Define um campo computado, permitindo o acesso a um atributo privado. 
        
        Este método torna acessível, como se fosse um atributo comum, o valor 
        armazenado em "_original_option" que, por sua vez, preserva o valor de
        "option" antes da transformação, para fins de rastreamento.
        
        Returns:
            Optional[str]: O valor original de "option" ou None, se não definido.
        """
        return self._original_option
    
    @model_validator(mode='after')
    def validate_and_transform_year(self) -> 'QueryParametersModel':
        """
        Valida e transforma o parâmetro "year", gerando "_original_year"

        O valor de "year" não é obrigatório. Se não for informado será definido 
        um valor padrão. Caso seja passado, precisa estar no intervalo permitido,
        que depende da "option" escolhida. 
		
        Se for válido, o valor de "year" é transformado para o formato esperado
        pela API e o valor original é armazenado em um atributo privado, o 
        "_original_year", para fins de rastreamento. 
		
        Raises:
            ValueError: se o valor de "year" está fora do intervalo permitido 
            para a opção escolhida.

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
        Define um campo computado, permitindo o acesso a um atributo privado. 
        
        Este método torna acessível, como se fosse um atributo comum, o valor 
        armazenado em "_original_year" que, por sua vez, preserva o valor de
        "year" antes da transformação, para fins de rastreamento.
        
        Returns:
            Optional[str]: O valor original de "year" ou None, se não definido.
        """
        return self._original_year
    
    @model_validator(mode='after')
    def validate_and_set_sub_option(self) -> 'QueryParametersModel':
        """
        Valida e transforma o parâmetro "sub_option", gerando 
        "_original_sub_option" 

        O valor de "sub_option" não é obrigatório. Se não for informado e a 
        "option" selecionada exigir uma sub-opção, será definido um valor padrão.
        Caso seja passado, precisa estar entre os valores permitidos, que 
        dependem da "option" escolhida.
		
        Se for válido, o valor de "sub_option" é transformado para o formato 
        esperado pela API e o valor original é armazenado em um atributo privado,
        o "_original_sub_option", para fins de rastreamento. 
	
		Raises:
			ValueError: se a combinação for inválida ou se "sub_option" for 
            usado indevidamente.
		
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
        Define um campo computado, permitindo o acesso a um atributo privado. 
        
        Este método torna acessível, como se fosse um atributo comum, o valor 
        armazenado em "_original_sub_option" que, por sua vez, preserva o valor 
        de "sub_option" antes da transformação, para fins de rastreamento.
        
        Returns:
            Optional[str]: O valor original de "sub_option" ou None, se não 
            definido.
        """
        return self._original_sub_option