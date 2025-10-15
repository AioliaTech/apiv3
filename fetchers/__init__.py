"""
Fetchers package - Parsers individuais para cada fornecedor de dados de veículos
"""
from .base_parser import BaseParser
from .altimus_parser import AltimusParser
from .autocerto_parser import AutocertoParser
from .autoconf_parser import AutoconfParser
from .revendamais_parser import RevendamaisParser
from .fronteira_parser import FronteiraParser
from .revendapro_parser import RevendaproParser
from .clickgarage_parser import ClickGarageParser
from .simplesveiculo_parser import SimplesVeiculoParser
from .boom_parser import BoomParser
from .dsautoparser import DSAutoEstoqueParser  # Nome correto do arquivo
from .vitorioso_wordpress_parser import WordPressParser
from .bndv_parser import BndvParser
from .revendai_parser. import RevendaiParser

__all__ = [
    'RevendaiParser',
    'BaseParser',
    'AltimusParser',
    'AutocertoParser', 
    'AutoconfParser',
    'RevendamaisParser',
    'FronteiraParser',
    'RevendaproParser',
    'ClickGarageParser',
    'SimplesVeiculoParser',
    'BoomParser',
    'DSAutoEstoqueParser',
    'BndvParser',# Adicionado na lista __all__
    'WordPressParser'  # Corrigido - estava faltando
]
