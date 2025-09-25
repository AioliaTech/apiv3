"""
Parser específico para Altimus (altimus.com.br)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any
import re

class AltimusParser(BaseParser):
    """Parser para dados do Altimus"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do Altimus"""
        return "altimus.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do Altimus"""
        veiculos = data.get("veiculos", [])
        if isinstance(veiculos, dict):
            veiculos = [veiculos]
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = v.get("modelo")
            versao_veiculo = v.get("versao")
            opcionais_veiculo = self._parse_opcionais(v.get("opcionais"))
            combustivel_veiculo = v.get("combustivel")
            
            # Determina se é moto ou carro - CORREÇÃO PARA EVITAR ERRO DE None
            tipo_veiculo = v.get("tipo", "")
            tipo_veiculo_lower = tipo_veiculo.lower() if tipo_veiculo else ""
            is_moto = "moto" in tipo_veiculo_lower or "motocicleta" in tipo_veiculo_lower
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = None
            
            # Determina o tipo final do veículo
            tipo_final = self._determine_tipo(tipo_veiculo, is_moto)
            
            # NOVA REGRA: Se tipo for 'moto' ou 'eletrico' e combustível for 'Elétrico', categoria = "Scooter Eletrica"
            if (tipo_final in ['moto', 'eletrico'] and 
                combustivel_veiculo and 
                str(combustivel_veiculo).lower() == 'elétrico'):
                categoria_final = "Scooter Eletrica"
            
            parsed = self.normalize_vehicle({
                "id": v.get("id"),
                "tipo": tipo_final,
                "titulo": None,
                "versao": versao_veiculo,
                "marca": v.get("marca"),
                "modelo": modelo_veiculo,
                "ano": v.get("anoModelo") or v.get("ano"),
                "ano_fabricacao": v.get("anoFabricacao") or v.get("ano_fabricacao"),
                "km": v.get("km"),
                "cor": v.get("cor"),
                "combustivel": combustivel_veiculo,
                "cambio": self._normalize_cambio(v.get("cambio")),
                "motor": self._extract_motor_from_version(versao_veiculo),
                "portas": v.get("portas"),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(v.get("valorVenda") or v.get("preco")),
                "opcionais": opcionais_veiculo,
                "fotos": v.get("fotos", [])
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _parse_opcionais(self, opcionais: Any) -> str:
        """Processa os opcionais do Altimus"""
        if isinstance(opcionais, list):
            return ", ".join(str(item) for item in opcionais if item)
        return str(opcionais) if opcionais else ""
    
    def _determine_tipo(self, tipo_original: str, is_moto: bool) -> str:
        """Determina o tipo final do veículo"""
        if not tipo_original:
            return "carro" if not is_moto else "moto"
            
        if tipo_original in ["Bicicleta", "Patinete Elétrico"]:
            return "eletrico"
        elif is_moto:
            return "moto"
        elif tipo_original == "Carro/Camioneta":
            return "carro"
        else:
            return tipo_original.lower()
    
    def _normalize_cambio(self, cambio: str) -> str:
        """Normaliza informações de câmbio"""
        if not cambio:
            return cambio
        
        cambio_str = str(cambio).lower()
        if "manual" in cambio_str:
            return "manual"
        elif "automático" in cambio_str or "automatico" in cambio_str:
            return "automatico"
        else:
            return cambio
    
    def _extract_motor_from_version(self, versao: str) -> str:
        """Extrai informações do motor da versão"""
        if not versao:
            return None
        
        # Busca padrão de cilindrada (ex: 1.4, 2.0, 1.6)
        motor_match = re.search(r'\b(\d+\.\d+)\b', str(versao))
        return motor_match.group(1) if motor_match else None
