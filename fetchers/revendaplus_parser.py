"""
Parser específico para RevendaPlus (revendaplus.com.br)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any

class RevendaPlusParser(BaseParser):
    """Parser para dados do RevendaPlus"""

    def _safe_float(self, value: Any, default: float = None) -> float:
        """Converte valor para float de forma segura"""
        if value is None or value == "":
            return default
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            value = value.strip().upper()
            # Trata casos especiais
            if value in ["ZERO", "0", "N/A", "NAO INFORMADO", "-", ""]:
                return 0.0
            
            try:
                # Remove pontos e converte vírgula para ponto
                value = value.replace(".", "").replace(",", ".")
                return float(value)
            except (ValueError, AttributeError):
                return default
        
        return default

    def _safe_int(self, value: Any, default: int = None) -> int:
        """Converte valor para int de forma segura"""
        if value is None or value == "":
            return default
        
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            value = value.strip().upper()
            # Trata casos especiais
            if value in ["ZERO", "0", "N/A", "NAO INFORMADO", "-", ""]:
                return 0
            
            try:
                # Remove caracteres não numéricos
                value = ''.join(filter(str.isdigit, value))
                return int(value) if value else default
            except (ValueError, AttributeError):
                return default
        
        if isinstance(value, float):
            return int(value)
        
        return default

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
                cilindrada_final = self._safe_int(potencia)
                categoria_final = v.get("especie", "")
                tipo_final = "moto"
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = None
                tipo_final = v.get("tipo", "")

            # Converte km de forma segura
            km_value = self._safe_float(v.get("km"))
            
            # Converte preço de forma segura
            preco_value = self._safe_float(v.get("valor"))

            # Converte anos de forma segura
            ano_value = self._safe_int(v.get("ano_modelo"))
            ano_fab_value = self._safe_int(v.get("ano_fabricacao"))

            # Remove zeros à esquerda do ID
            codigo = v.get("codigo", "")
            id_final = self._safe_int(codigo)

            parsed = self.normalize_vehicle({
                "id": id_final,
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
                "preco": preco_value,
                "opcionais": opcionais_veiculo,
                "fotos": v.get("fotos", [])
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
