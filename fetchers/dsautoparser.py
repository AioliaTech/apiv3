"""
Parser específico para DSAutoEstoque (dsautoestoque.com)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any
import re
import xml.etree.ElementTree as ET

class DSAutoEstoqueParser(BaseParser):
    """Parser para dados do DSAutoEstoque"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do DSAutoEstoque"""
        return "dsautoestoque.com" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do DSAutoEstoque"""
        # Assume data is a string containing XML
        try:
            root = ET.fromstring(data)
        except ET.ParseError:
            return []
        
        veiculos = root.findall("veiculo")
        if not veiculos:
            return []
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = self._extract_text(v.find("modelo"))
            versao_veiculo = self._extract_text(v.find("versao"))
            opcionais_veiculo = self._parse_opcionais(v.find("opcionais"))
            
            # Determina se é moto ou carro baseado em tipoveiculo
            tipo_veiculo = self._extract_text(v.find("tipoveiculo")).lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = None
            
            parsed = self.normalize_vehicle({
                "id": self._extract_text(v.find("id")),
                "tipo": "moto" if is_moto else tipo_veiculo.capitalize(),
                "titulo": None,
                "versao": versao_veiculo,
                "marca": self._extract_text(v.find("marca")),
                "modelo": modelo_veiculo,
                "ano": self._extract_int(v.find("anomodelo")),
                "ano_fabricacao": self._extract_int(v.find("anofabricacao")),
                "km": self._extract_int(v.find("km")),
                "cor": self._extract_text(v.find("cor")),
                "combustivel": self._extract_text(v.find("combustivel")),
                "cambio": self._extract_text(v.find("cambio")),
                "motor": self._extract_motor_from_version(versao_veiculo),
                "portas": self._extract_int(v.find("portas")),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(self._extract_text(v.find("preco"))),
                "opcionais": opcionais_veiculo,
                "fotos": self._extract_photos(v.find("fotos"))
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_text(self, element) -> str:
        """Extrai texto de um elemento XML, lidando com CDATA e None"""
        if element is None:
            return ""
        text = element.text or ""
        # Remove <![CDATA[ ... ]]> se presente
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
        return text.strip()
    
    def _extract_int(self, element) -> int:
        """Extrai inteiro de um elemento XML"""
        text = self._extract_text(element)
        try:
            return int(text)
        except ValueError:
            return None
    
    def _parse_opcionais(self, opcionais_element) -> str:
        """Processa os opcionais do DSAutoEstoque"""
        if opcionais_element is None:
            return ""
        
        opcional_elements = opcionais_element.findall("opcional")
        if opcional_elements:
            opcionais = [self._extract_text(opc) for opc in opcional_elements if self._extract_text(opc)]
            return ", ".join(opcionais)
        
        # Se for vazio ou sem subelementos, retornar vazio
        return ""
    
    def _clean_version(self, modelo: str, versao: str) -> str:
        """Limpa a versão removendo informações técnicas redundantes"""
        if not versao:
            return modelo.strip() if modelo else None
        
        # Concatena modelo + versão limpa
        modelo_str = modelo.strip() if modelo else ""
        versao_limpa = ' '.join(re.sub(
            r'\b(\d\.\d|4x[0-4]|\d+v|diesel|flex|gasolina|manual|automático|4p)\b', 
            '', versao, flags=re.IGNORECASE
        ).split())
        
        if versao_limpa:
            return f"{modelo_str} {versao_limpa}".strip()
        else:
            return modelo_str or None
    
    def _extract_motor_from_version(self, versao: str) -> str:
        """Extrai informações do motor da versão"""
        if not versao:
            return None
        
        # Pega a primeira palavra da versão que geralmente é o motor
        words = versao.strip().split()
        return words[0] if words else None
    
    def _extract_photos(self, fotos_element) -> List[str]:
        """Extrai fotos do veículo DSAutoEstoque"""
        fotos = []
        if fotos_element is not None:
            foto_elements = fotos_element.findall("foto")
            for foto in foto_elements:
                url = self._extract_text(foto)
                if url:
                    # Remove query params se quiser, mas no sample não tem
                    fotos.append(url)
        return fotos
