"""
Parser genérico BoomParser - usado como fallback para estruturas não específicas
"""

from .base_parser import BaseParser
from typing import Dict, List, Any, Union

class BoomParser(BaseParser):
    """Parser genérico para estruturas variadas - usado como fallback"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Aceita dados de boomsistemas.com.br ou como fallback genérico"""
        return "boomsistemas.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados com estrutura genérica/variável"""
        
        # Busca a lista de veículos
        veiculos = []
        
        if isinstance(data, dict):
            # Estrutura: {'veiculos': {'veiculo': [...]}}
            if 'veiculos' in data and isinstance(data['veiculos'], dict):
                veiculo_data = data['veiculos'].get('veiculo', [])
                if isinstance(veiculo_data, list):
                    veiculos = veiculo_data
                elif isinstance(veiculo_data, dict):
                    veiculos = [veiculo_data]
        
        parsed_vehicles = []
        for v in veiculos:
            if not isinstance(v, dict):
                continue
            
            modelo_veiculo = v.get('modelo')
            tipo_veiculo = v.get('tipo', 'carro')
            
            # Verifica se é moto
            is_moto = 'moto' in str(tipo_veiculo).lower()
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, None
                )
                tipo_final = "moto"
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, "")
                cilindrada_final = None
                tipo_final = tipo_veiculo
            
            # Processa fotos da galeria
            fotos = []
            galeria = v.get('galeria')
            if galeria and isinstance(galeria, dict) and 'item' in galeria:
                items = galeria['item']
                if isinstance(items, list):
                    fotos = [item for item in items if item]
                elif items:
                    fotos = [items]
            
            # Processa opcionais
            opcionais_str = ""
            opcional = v.get('opcional')
            if opcional and isinstance(opcional, dict) and 'item' in opcional:
