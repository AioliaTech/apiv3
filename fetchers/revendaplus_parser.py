"""
Parser específico para RevendaPlus (revendaplus.com.br)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any

class RevendaPlusParser(BaseParser):
    """Parser para dados do RevendaPlus"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do RevendaPlus"""
        url = url.lower()
        return "revendaplus.com.br" in url

    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do RevendaPlus (JSON)"""
        # RevendaPlus retorna um array de veículos
        if not isinstance(data, list):
            data = [data]
        
        parsed_vehicles = []
        for v in data:
            modelo_veiculo = v.get("modelo", "")
            opcionais_veiculo = v.get("opcionais") or ""
            
            # Determina se é moto ou carro baseado no tipo
            tipo_veiculo = v.get("tipo", "").lower()
            is_moto = tipo_veiculo == "moto" or "moto" in tipo_veiculo
            
            if is_moto:
                # Para motos, usa a potência como cilindrada
                potencia = v.get("potencia")
                if isinstance(potencia, str):
                    cilindrada_final = int(potencia) if potencia else None
                else:
                    cilindrada_final = potencia
                categoria_final = v.get("especie", "")
                tipo_final = "moto"
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = None
                tipo_final = v.get("tipo", "")

            # Converte km que pode vir com ponto como separador de milhar
            km_value = v.get("km", "")
            if isinstance(km_value, str):
                km_value = float(km_value.replace(".", "").replace(",", "."))
            elif km_value:
                km_value = float(km_value)
            else:
                km_value = None
            
            # Converte preço que vem com vírgula como separador decimal
            preco_str = v.get("valor", "")
            if isinstance(preco_str, str):
                preco_str = preco_str.replace(".", "").replace(",", ".")

            # Converte ano para inteiro
            ano_value = v.get("ano_modelo")
            if isinstance(ano_value, str):
                ano_value = int(ano_value) if ano_value else None
            
            ano_fab_value = v.get("ano_fabricacao")
            if isinstance(ano_fab_value, str):
                ano_fab_value = int(ano_fab_value) if ano_fab_value else None

            parsed = self.normalize_vehicle({
                "id": v.get("codigo"),
                "tipo": tipo_final,
                "versao": v.get("modelo"),
                "marca": v.get("marca"),
                "modelo": modelo_veiculo,
                "ano": ano_value,
                "ano_fabricacao": ano_fab_value,
                "km": km_value,
                "cor": v.get("cor"),
                "combustivel": v.get("combustivel"),
                "cambio": v.get("cambio"),
                "motor": v.get("potencia"),
                "portas": None,
                "categoria": v.get("especie") or categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(preco_str),
                "opcionais": opcionais_veiculo,
                "fotos": v.get("fotos", [])
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
