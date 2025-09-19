"""
Parser específico para Fronteira Veículos (fronteiraveiculos.com)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any

class FronteiraParser(BaseParser):
    """Parser para dados da Fronteira Veículos"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados da Fronteira"""
        return "fronteiraveiculos.com" in url.lower()

    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados da Fronteira"""
        # Pega direto do nó <estoque><veiculo>
        ads = data["estoque"]["veiculo"]

        # Garante que seja lista
        if isinstance(ads, dict):
            ads = [ads]
        
        parsed_vehicles = []
        for v in ads:
            modelo_veiculo = v.get("modelo")
            versao_veiculo = v.get("titulo")
            opcionais_veiculo = v.get("opcionais") or ""
            
            # Determina se é moto ou carro
            categoria_veiculo = v.get("CATEGORY", "").lower()
            is_moto = categoria_veiculo == "motocicleta" or "moto" in categoria_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
                tipo_final = "moto"
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = None
                tipo_final = 'carro'

            parsed = self.normalize_vehicle({
                "id": v.get("id"), 
                "tipo": tipo_final, 
                "titulo": v.get("titulo"), 
                "versao": versao_veiculo,
                "marca": v.get("marca"), 
                "modelo": modelo_veiculo, 
                "ano": v.get("ano"),
                "ano_fabricacao": v.get("FABRIC_YEAR"), 
                "km": v.get("km"), 
                "cor": v.get("cor"),
                "combustivel": v.get("combustivel"), 
                "cambio": v.get("cambio"), 
                "motor": v.get("motor"),
                "portas": v.get("DOORS"), 
                "categoria": categoria_final or v.get("BODY_TYPE"),
                "cilindrada": cilindrada_final, 
                "preco": self.converter_preco(v.get("preco")),
                "opcionais": opcionais_veiculo, 
                "fotos": self._extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_photos(self, v: Dict) -> List[str]:
        """Extrai fotos do veículo Fronteira"""
        fotos = v.get("fotos", {})
        if not fotos:
            return []

        images = fotos.get("foto")
        if not images:
            return []

        # Se só uma foto (string)
        if isinstance(images, str):
            return [images]

        # Se várias fotos (lista de strings)
        if isinstance(images, list):
            return [img for img in images if isinstance(img, str)]

        return []
