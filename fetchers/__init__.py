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

__all__ = [
    'BaseParser',
    'AltimusParser',
    'AutocertoParser', 
    'AutoconfParser',
    'RevendamaisParser',
    'FronteiraParser',
    'RevendaproParser',
    'ClickGarageParser',
    'SimplesVeiculoParser',
    'BoomParser'
]
