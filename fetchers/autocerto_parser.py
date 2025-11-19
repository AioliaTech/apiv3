"""
Parser específico para Carburgo (citroenpremiere.com.br)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any
import re
import xml.etree.ElementTree as ET

class CarburgoParser(BaseParser):
    """Parser para dados do Carburgo"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do Carburgo"""
        return "citroenpremiere.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do Carburgo"""
        # Se vier como string XML, converte para dict
        if isinstance(data, str):
            data = self._xml_to_dict(data)
        
        # Pega lista de veículos (aceita 'veiculo' ou 'carro')
        veiculos = data.get("estoque", {}).get("veiculo") or data.get("estoque", {}).get("carro", [])
        
        if isinstance(veiculos, dict):
            veiculos = [veiculos]
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = v.get("modelo", "")
            versao_veiculo = v.get("modelo", "")  # Carburgo não tem versão separada
            opcionais_veiculo = None  # Carburgo não tem opcionais
            
            # Determina se é moto ou carro
            tipo_veiculo = v.get("tipo", "").lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                categoria_final = v.get("tipo")  # SUV, Hatch, Sedan, etc
                cilindrada_final = v.get("cilindradas")
            
            # Gera ID a partir da placa
            placa = v.get("placa", "")
            id_str = "".join(d for i, d in enumerate(placa) if i in [1, 2, 3, 5, 6]) if placa else None
            
            parsed = self.normalize_vehicle({
                "id": id_str,
                "tipo": "moto" if is_moto else "carro",
                "titulo": None,
                "versao": versao_veiculo,
                "marca": v.get("marca"),
                "modelo": modelo_veiculo,
                "ano": v.get("ano_modelo"),
                "ano_fabricacao": v.get("ano"),
                "km": v.get("km"),
                "cor": None,
                "combustivel": v.get("combustivel"),
                "cambio": v.get("cambio"),
                "motor": self._extract_motor_from_version(versao_veiculo),
                "portas": v.get("portas"),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(v.get("preco")),
                "opcionais": opcionais_veiculo,
                "fotos": self._extract_photos(v),
                "url": v.get("url"),
                "unidade": v.get("unidade"),
                "descricao": v.get("descricao")
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles

    def _xml_to_dict(self, xml_str: str) -> Dict:
        """Converte XML do Carburgo para dict"""
        try:
            root = ET.fromstring(xml_str)
            carros = []
            
            for carro in root.findall('carro'):
                carro_dict = {}
                for child in carro:
                    if child.tag == 'fotos':
                        # Extrai lista de URLs das fotos
                        fotos = [foto.text for foto in child.findall('foto') if foto.text]
                        carro_dict['fotos'] = fotos
                    else:
                        carro_dict[child.tag] = child.text
                carros.append(carro_dict)
            
            return {"estoque": {"carro": carros}}
        except Exception as e:
            print(f"[ERRO] Falha ao parsear XML do Carburgo: {e}")
            return {"estoque": {"carro": []}}
    
    def _extract_motor_from_version(self, versao: str) -> str:
        """Extrai informações do motor da versão"""
        if not versao:
            return None
        
        words = versao.strip().split()
        return words[0] if words else None
    
    def _extract_photos(self, v: Dict) -> List[str]:
        """Extrai fotos do veículo Carburgo"""
        fotos = v.get("fotos", [])
        
        # Se for lista de strings (já parseado do XML)
        if isinstance(fotos, list):
            return [foto for foto in fotos if foto]
        
        # Se for dict no formato Autocerto
        if isinstance(fotos, dict):
            fotos_lista = fotos.get("foto", [])
            if isinstance(fotos_lista, str):
                return [fotos_lista]
            if isinstance(fotos_lista, list):
                return [foto for foto in fotos_lista if foto]
        
        return []
    
    def definir_categoria_veiculo(self, modelo: str, opcionais: str) -> str:
        """Define categoria do veículo baseado no modelo e opcionais"""
        return None  # Carburgo já tem o campo 'tipo' preenchido
    
    def inferir_cilindrada_e_categoria_moto(self, modelo: str, versao: str):
        """Inferir cilindrada e categoria para motos"""
        return None, None
