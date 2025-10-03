"""
Parser específico para Revendamais (revendamais.com.br)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any

class RevendamaisParser(BaseParser):
    """Parser para dados do Revendamais"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do Revendamais"""
        return "revendamais.com.br" in url.lower()

    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do Revendamais"""
        ads = data["ADS"]["AD"]
        if isinstance(ads, dict): 
            ads = [ads]
        
        parsed_vehicles = []
        for v in ads:
            modelo_veiculo = v.get("MODEL")
            versao_veiculo = v.get("VERSION")
            opcionais_veiculo = v.get("ACCESSORIES") or ""
            
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
                tipo_final = v.get("CATEGORY")

            parsed = self.normalize_vehicle({
                "id": v.get("ID"), 
                "tipo": tipo_final, 
                "versao": v.get("TITLE"),
                "marca": v.get("MAKE"), 
                "modelo": modelo_veiculo, 
                "ano": v.get("YEAR"),
                "ano_fabricacao": v.get("FABRIC_YEAR"), 
                "km": v.get("MILEAGE"), 
                "cor": v.get("COLOR"),
                "combustivel": v.get("FUEL"), 
                "cambio": v.get("GEAR"), 
                "motor": v.get("MOTOR"),
                "portas": v.get("DOORS"), 
                "categoria": v.get("BODY_TYPE") or categoria_final,
                "cilindrada": cilindrada_final, 
                "preco": self.converter_preco(v.get("PRICE")),
                "opcionais": opcionais_veiculo, 
                "fotos": self._extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_photos(self, v: Dict) -> List[str]:
        """Extrai fotos do veículo Revendamais"""
        images = v.get("IMAGES", [])
        if not images: 
            return []
        
        if isinstance(images, list):
            return [
                img.get("IMAGE_URL") 
                for img in images 
                if isinstance(img, dict) and img.get("IMAGE_URL")
            ]
        elif isinstance(images, dict) and images.get("IMAGE_URL"):
            return [images["IMAGE_URL"]]
        
        return []
