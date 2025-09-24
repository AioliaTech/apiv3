"""
Parser específico para DSAutoEstoque (dsautoestoque.com)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any
import re

class DSAutoEstoqueParser(BaseParser):
    """Parser para dados do DSAutoEstoque"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do DSAutoEstoque"""
        return "dsautoestoque.com" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do DSAutoEstoque"""
        veiculos = data["estoque"]["veiculo"]
        if isinstance(veiculos, dict):
            veiculos = [veiculos]
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = self._extract_text(v.get("modelo"))
            versao_veiculo = self._extract_text(v.get("versao"))
            opcionais_veiculo = self._parse_opcionais(v.get("opcionais"))
            
            # Determina se é moto ou carro baseado em tipoveiculo
            tipo_veiculo = self._extract_text(v.get("tipoveiculo")).lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            # Tenta extrair categoria de "carroceria", senão usa definir_categoria_veiculo
            categoria_final = self._extract_text(v.get("carroceria"))
            if not categoria_final:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
            
            if is_moto:
                cilindrada_final, _ = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                cilindrada_final = None
            
            parsed = self.normalize_vehicle({
                "id": self._extract_text(v.get("id")),
                "tipo": "moto" if is_moto else self._extract_text(v.get("tipoveiculo")),
                "titulo": None,
                "versao": versao_veiculo,
                "marca": self._extract_text(v.get("marca")),
                "modelo": modelo_veiculo,
                "ano": self._extract_int(v.get("anomodelo")),
                "ano_fabricacao": self._extract_int(v.get("anofabricacao")),
                "km": self._extract_int(v.get("km") or v.get("quilometragem")),
                "cor": self._extract_text(v.get("cor")),
                "combustivel": self._extract_text(v.get("combustivel")),
                "cambio": self._extract_text(v.get("cambio")),
                "motor": self._extract_motor_from_version(versao_veiculo),
                "portas": self._extract_int(v.get("portas")),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(self._extract_text(v.get("preco"))),
                "opcionais": opcionais_veiculo,
                "fotos": self._extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_text(self, value: Any) -> str:
        """Extrai texto de campos que podem ser string, dict ou None"""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            # Tenta chaves comuns para texto em dicts XML-serializados
            text = value.get("#text") or value.get("$") or value.get("value") or ""
            return str(text).strip()
        return str(value or "").strip()
    
    def _extract_int(self, value: Any) -> int:
        """Extrai inteiro de campos que podem ser string, dict ou None"""
        text = self._extract_text(value)
        if text and text.isdigit():
            return int(text)
        return None
    
    def _parse_opcionais(self, opcionais: Any) -> str:
        """Processa os opcionais do DSAutoEstoque"""
        if isinstance(opcionais, dict) and "opcional" in opcionais:
            opcional = opcionais["opcional"]
            if isinstance(opcional, list):
                return ", ".join(str(item) for item in opcional if item)
            return str(opcional) if opcional else ""
        elif isinstance(opcionais, list):
            return ", ".join(str(item) for item in opcionais if item)
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
    
    def _extract_photos(self, v: Dict) -> List[str]:
        """Extrai fotos do veículo DSAutoEstoque"""
        fotos = v.get("fotos")
        if not fotos or not (fotos_foto := fotos.get("foto")):
            return []
        
        if isinstance(fotos_foto, dict):
            fotos_foto = [fotos_foto]
        
        return [
            img["url"].split("?")[0] 
            for img in fotos_foto 
            if isinstance(img, dict) and "url" in img
        ]
