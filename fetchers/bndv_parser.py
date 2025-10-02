"""
Parser específico para BNDV (Sistema de Lojistas)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any
import json

class BndvParser(BaseParser):
    """Parser para dados do BNDV"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do BNDV"""
        # Verifica se é BNDV pela URL ou estrutura dos dados
        if "bndv" in url.lower() or "sistema.lojistas" in url.lower():
            return True
        
        # Verifica pela estrutura do JSON
        if isinstance(data, dict) and "vehiclesBy" in data:
            return True
        
        return False
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do BNDV"""
        veiculos = data.get("vehiclesBy", [])
        
        if not isinstance(veiculos, list):
            veiculos = [veiculos]
        
        parsed_vehicles = []
        for v in veiculos:
            # Extrai dados básicos
            marca = v.get("markName")
            modelo = v.get("modelName")
            versao = v.get("versionName")
            ano = v.get("year")
            
            # Processa opcionais
            opcionais_veiculo = self._parse_opcionais(v.get("itemJs"))
            
            # Processa fotos
            fotos = self._parse_fotos(v.get("pictureJs"))
            
            # Determina categoria (assumindo que é sempre carro, já que não tem campo tipo)
            categoria_final = self.definir_categoria_veiculo(modelo, opcionais_veiculo)
            
            # Extrai motor da versão
            motor = self._extract_motor_from_version(versao)
            
            parsed = self.normalize_vehicle({
                "id": v.get("vehicleExternalKey"),
                "tipo": "carro",  # Padrão para carros
                "titulo": None,
                "versao": versao,
                "marca": marca,
                "modelo": modelo,
                "ano": ano,
                "ano_fabricacao": None,
                "km": v.get("km"),
                "cor": v.get("color"),
                "combustivel": v.get("fuelName"),
                "cambio": v.get("transmissionName"),
                "motor": motor,
                "portas": None,  # Não disponível no JSON
                "categoria": categoria_final,
                "cilindrada": None,
                "preco": v.get("saleValue"),  # Já vem como número
                "opcionais": opcionais_veiculo,
                "fotos": fotos,
                "placa": v.get("plate"),
                "placa_final": v.get("finalPlate"),
                "subcategoria": v.get("subCategoryName"),
                "tipo_veiculo": v.get("vehicleTypeName"),
                "data_cadastro": v.get("registrationDate"),
                "lojista": self._parse_customer(v.get("Customer"))
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _parse_opcionais(self, item_js: str) -> str:
        """Processa os opcionais do BNDV (vem como JSON string)"""
        if not item_js:
            return ""
        
        try:
            items = json.loads(item_js)
            if isinstance(items, list):
                return ", ".join(item.get("value", "") for item in items if item.get("value"))
            return ""
        except (json.JSONDecodeError, AttributeError):
            return ""
    
    def _parse_fotos(self, picture_js: str) -> List[str]:
        """Extrai fotos do veículo BNDV (vem como JSON string)"""
        if not picture_js:
            return []
        
        try:
            pictures = json.loads(picture_js)
            if isinstance(pictures, list):
                # Ordena colocando a foto principal primeiro
                pictures_sorted = sorted(
                    pictures, 
                    key=lambda x: x.get("Principal", "false") != "true"
                )
                return [pic.get("Link", "") for pic in pictures_sorted if pic.get("Link")]
            return []
        except (json.JSONDecodeError, AttributeError):
            return []
    
    def _extract_motor_from_version(self, versao: str) -> str:
        """Extrai informações do motor da versão"""
        if not versao:
            return None
        
        # Procura por padrões como "1.0", "1.5", "2.0", etc.
        import re
        match = re.search(r'\b(\d\.\d)\b', versao)
        if match:
            return match.group(1)
        
        return None
    
    def _parse_customer(self, customer: Dict) -> Dict:
        """Processa informações do lojista"""
        if not customer:
            return {}
        
        contact_info = {}
        try:
            contact_str = customer.get("contact", "{}")
            contact_info = json.loads(contact_str)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return {
            "nome": customer.get("name"),
            "site": customer.get("site"),
            "cnpj": customer.get("cnpj"),
            "telefone": contact_info.get("contact"),
            "whatsapp": contact_info.get("whatsapp"),
            "email": contact_info.get("email"),
            "customer_key": customer.get("customerKey")
        }
