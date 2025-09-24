"""
Parser específico para DSAutoEstoque (dsautoestoque.com) - JSON
"""
from .base_parser import BaseParser
from typing import Dict, List, Any
import json

class DSAutoEstoqueParser(BaseParser):
    """Parser para dados JSON do DSAutoEstoque"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do DSAutoEstoque"""
        return "dsautoestoque.com" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados JSON do DSAutoEstoque"""
        # Se data for string JSON, parse primeiro
        if isinstance(data, str):
            data = json.loads(data)
        
        # Extrai lista de veículos do JSON
        if "resultados" in data:
            veiculos = data["resultados"]
        elif "veiculos" in data:
            veiculos = data["veiculos"]
        elif isinstance(data, list):
            veiculos = data
        else:
            veiculos = []
        
        if isinstance(veiculos, dict):
            veiculos = [veiculos]
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = v.get("modelo")
            versao_veiculo = v.get("versao")
            observacao_veiculo = v.get("observacao", "")
            
            # Determina se é moto ou carro
            tipo_veiculo = v.get("tipoveiculo", "").lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, observacao_veiculo)
                cilindrada_final = None
            
            parsed = self.normalize_vehicle({
                "id": v.get("id"),
                "tipo": "moto" if is_moto else "carro",
                "zero_km": v.get("zerokm") == "S",
                "placa": v.get("placa"),
                "titulo": None,
                "versao": versao_veiculo,
                "marca": v.get("marca"),
                "modelo": modelo_veiculo,
                "ano": v.get("anomodelo"),
                "ano_fabricacao": v.get("anofabricacao"),
                "km": v.get("km"),
                "cor": v.get("cor"),
                "combustivel": v.get("combustivel"),
                "cambio": v.get("cambio"),
                "motor": self._extract_motor_from_version(versao_veiculo),
                "portas": v.get("portas"),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(v.get("preco")),
                "opcionais": observacao_veiculo,
                "fotos": self._extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
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
        if not fotos:
            return []
        
        if isinstance(fotos, list):
            return [foto.split("?")[0] for foto in fotos if isinstance(foto, str)]
        elif isinstance(fotos, dict) and "foto" in fotos:
            fotos_foto = fotos["foto"]
            if isinstance(fotos_foto, list):
                return [foto.split("?")[0] for foto in fotos_foto if isinstance(foto, str)]
            else:
                return [fotos_foto.split("?")[0]] if isinstance(fotos_foto, str) else []
        
        return []
