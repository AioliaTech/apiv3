"""
Parser específico para RevendaPro (revendapro.com.br)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any
import re

class RevendaproParser(BaseParser):
    """Parser para dados do RevendaPro"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do RevendaPro"""
        return "revendapro.com.br" in url.lower()

    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do RevendaPro"""
        # Pega direto do nó <CargaVeiculos><Veiculo>
        ads = data["CargaVeiculos"]["Veiculo"]

        # Garante que seja lista
        if isinstance(ads, dict):
            ads = [ads]
        
        parsed_vehicles = []
        for v in ads:
            modelo_veiculo = v.get("Modelo")
            versao_veiculo = v.get("Versao")
            opcionais_veiculo = v.get("Equipamentos") or ""
            
            # Determina se é moto ou carro
            categoria_veiculo = v.get("Tipo", "").lower()
            is_moto = categoria_veiculo == "motocicleta" or "moto" in categoria_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = None

            parsed = self.normalize_vehicle({
                "id": v.get("Codigo"), 
                "tipo": v.get("Tipo"), 
                "titulo": v.get(""), 
                "versao": v.get("Versao"),
                "marca": v.get("Marca"), 
                "modelo": v.get("Modelo"), 
                "ano": v.get("AnoModelo"),
                "ano_fabricacao": v.get("AnoFabr"), 
                "km": v.get("km"), 
                "cor": v.get("Cor"),
                "combustivel": v.get("Combustivel"), 
                "cambio": v.get("Cambio"), 
                "motor": self._extract_motor_from_version(v.get("Versao")),
                "portas": v.get("Portas"), 
                "categoria": categoria_final,
                "cilindrada": cilindrada_final, 
                "preco": self.converter_preco(v.get("Preco")),
                "opcionais": opcionais_veiculo, 
                "fotos": self._extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_motor_from_version(self, versao: str) -> str:
        """Extrai informações do motor da versão"""
        if not versao:
            return ""
        
        # Pega a primeira palavra da versão que geralmente é o motor
        words = versao.strip().split()
        return words[0] if words else ""
    
    def _extract_photos(self, v: Dict[str, Any]) -> List[str]:
        """Extrai fotos do veículo RevendaPro"""
        fotos = v.get("Fotos")
        if not fotos:
            return []

        # Caso 1: Fotos vem como dict {"foto": "..."} ou {"foto": ["...", "..."]}
        if isinstance(fotos, dict):
            images = fotos.get("foto")
            if isinstance(images, str):
                return [images]
            if isinstance(images, list):
                return [img for img in images if isinstance(img, str)]
            return []

        # Caso 2: Fotos vem como string única "<Fotos> url1 ; url2 ... </Fotos>"
        if isinstance(fotos, str):
            s = re.sub(r"</?\s*fotos?\s*>", "", fotos, flags=re.IGNORECASE).strip()
            urls = [u.strip() for u in re.split(r"[;\n]+", s) if u.strip()]
            return urls

        return []
