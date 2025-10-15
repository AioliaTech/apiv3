"""
Parser específico para Revendai (revendai.com.br)
"""
from .base_parser import BaseParser
from typing import Dict, List, Any
import re

class RevendaiParser(BaseParser):
    """Parser para dados do Revendai"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do Revendai"""
        url = url.lower()
        return "revendai.com.br" in url
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do Revendai"""
        veiculos = data.get("veiculos", [])
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = v.get("modelo")
            versao_veiculo = v.get("versao")
            opcionais_veiculo = v.get("opcionais") or ""
            
            tipo_veiculo = v.get("tipo", "").lower()
            is_moto = tipo_veiculo == "moto" or "motocicleta" in tipo_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
                tipo_final = "moto"
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = v.get("cilindrada")
                tipo_final = tipo_veiculo
            
            id_original = v.get("id", "")
            numeros = re.findall(r'\d', id_original)
            id_final = ''.join(numeros[:5]) if len(numeros) >= 5 else ''.join(numeros)
            
            parsed = self.normalize_vehicle({
                "id": id_final,
                "tipo": tipo_final,
                "versao": v.get("versao"),
                "marca": v.get("marca"),
                "modelo": modelo_veiculo,
                "ano": v.get("ano"),
                "ano_fabricacao": v.get("ano_fabricacao"),
                "km": v.get("km"),
                "cor": v.get("cor"),
                "combustivel": v.get("combustivel"),
                "cambio": v.get("cambio"),
                "motor": v.get("motor"),
                "portas": v.get("portas"),
                "categoria": v.get("categoria") or categoria_final,
                "cilindrada": cilindrada_final,
                "preco": v.get("preco"),
                "opcionais": opcionais_veiculo,
                "fotos": v.get("fotos", [])
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
