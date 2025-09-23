"""
Parser específico para Autoconf
"""

from .base_parser import BaseParser
from typing import Dict, List, Any
import re

class AutoconfParser(BaseParser):
    """Parser para dados do Autoconf"""
    
    # Mapeamento de categorias específico do Autoconf
    CATEGORIA_MAPPING = {
        "conversivel/cupe": "Conversível",
        "conversível/cupê": "Conversível", 
        "picapes": "Caminhonete",
        "suv / utilitario esportivo": "SUV",
        "suv / utilitário esportivo": "SUV",
        "suv": "SUV",
        "van/utilitario": "Utilitário",
        "van/utilitário": "Utilitário",
        "wagon/perua": "Minivan",
        "perua": "Minivan"
    }
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do Autoconf"""
        return "autoconf" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do Autoconf"""
        ads = data["ADS"]["AD"]
        if isinstance(ads, dict): 
            ads = [ads]
        
        parsed_vehicles = []
        for v in ads:
            modelo_veiculo = v.get("MODEL")
            versao_veiculo = v.get("VERSION")
            opcionais_veiculo = self._parse_features(v.get("FEATURES"))
            
            # Determina se é moto ou carro - CORREÇÃO AQUI
            categoria_veiculo = v.get("CATEGORY", "")
            categoria_veiculo_lower = categoria_veiculo.lower() if categoria_veiculo else ""
            is_moto = categoria_veiculo_lower == "motos" or "moto" in categoria_veiculo_lower
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
                tipo_final = "moto"
            else:
                # Primeiro tenta inferir categoria pelo modelo/versão (como no Autocerto)
                categoria_modelo = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                
                # Se não conseguiu inferir pelo modelo, usa o campo BODY com mapeamento
                if not categoria_modelo or categoria_modelo == "Não informado":
                    body_category = v.get("BODY", "")
                    body_category_lower = body_category.lower().strip() if body_category else ""
                    categoria_final = self.CATEGORIA_MAPPING.get(body_category_lower, body_category or "Não informado")
                else:
                    categoria_final = categoria_modelo
                    
                cilindrada_final = None
                tipo_final = "carro" if categoria_veiculo_lower == "carros" else categoria_veiculo

            parsed = self.normalize_vehicle({
                "id": v.get("ID"),
                "tipo": tipo_final,
                "titulo": None,
                "versao": self._clean_version(versao_veiculo),
                "marca": v.get("MAKE"),
                "modelo": modelo_veiculo,
                "ano": v.get("YEAR"),
                "ano_fabricacao": v.get("FABRIC_YEAR"),
                "km": v.get("MILEAGE"),
                "cor": v.get("COLOR"),
                "combustivel": v.get("FUEL"),
                "cambio": v.get("gear") or v.get("GEAR"),
                "motor": v.get("MOTOR"),
                "portas": v.get("DOORS"),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(v.get("PRICE")),
                "opcionais": opcionais_veiculo,
                "fotos": self._extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _parse_features(self, features: Any) -> str:
        """Processa as features/opcionais do Autoconf"""
        if not features: 
            return ""
        
        if isinstance(features, list):
            return ", ".join(
                feat.get("FEATURE", "") if isinstance(feat, dict) else str(feat) 
                for feat in features
            )
        
        return str(features)
    
    def _clean_version(self, versao_veiculo: str) -> str:
        """Limpa a versão removendo informações técnicas redundantes"""
        if not versao_veiculo:
            return None
        
        # Remove padrões técnicos específicos do Autoconf
        versao_limpa = ' '.join(re.sub(
            r'\b(\d\.\d|4x[0-4]|\d+v|diesel|flex|aut|aut.|dies|dies.|mec.|mec|gasolina|manual|automático|4p)\b',
            '', versao_veiculo, flags=re.IGNORECASE
        ).split()).strip()
        
        return versao_limpa if versao_limpa else None
    
    def _extract_photos(self, v: Dict) -> List[str]:
        """Extrai fotos do veículo Autoconf"""
        images = v.get("IMAGES", [])
        if not images: 
            return []
    
        # Se é uma lista (múltiplos IMAGES)
        if isinstance(images, list):
            return [
                img.get("IMAGE_URL") 
                for img in images 
                if isinstance(img, dict) and img.get("IMAGE_URL")
            ]
    
        # Se é um dict único
        elif isinstance(images, dict) and images.get("IMAGE_URL"):
            return [images["IMAGE_URL"]]
        
        return []
