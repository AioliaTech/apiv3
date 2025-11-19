"""
Parser específico para Carburgo (citroenpremiere.com.br)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any
import re
import xml.etree.ElementTree as ET

class CarburgoParser(BaseParser):
    """Parser para dados do Carburgo"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do Carburgo"""
        if not url:
            return False
        return "citroenpremiere.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do Carburgo"""
        if isinstance(data, str):
            data = self._xml_to_dict(data)
            if not data:
                return []

        # Validação da estrutura
        if "estoque" not in data:
            print(f"[ERRO] Estrutura 'estoque' não encontrada. Keys disponíveis: {list(data.keys())}")
            return []
        
        if "veiculo" not in data["estoque"]:
            print(f"[ERRO] Estrutura 'veiculo' não encontrada. Keys disponíveis: {list(data['estoque'].keys())}")
            return []

        veiculos = data["estoque"]["veiculo"]
        if isinstance(veiculos, dict):
            veiculos = [veiculos]

        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = v.get("modelo", "").strip()
            versao_veiculo = v.get("modelo", "").strip()  # Use modelo as versao
            opcionais_veiculo = None  # No opcionais

            # Determina se é moto ou carro
            tipo_veiculo = v.get("tipo", "").lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo

            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                categoria_final = v.get("tipo") if v.get("tipo") else None
                cilindrada_final = v.get("cilindradas")

            placa = v.get("placa", "")
            id_str = "".join(d for i, d in enumerate(placa) if i in [1, 2, 3, 5, 6]) if placa else None

            parsed = self.normalize_vehicle({
                "id": id_str,
                "tipo": "moto" if is_moto else "carro",
                "titulo": None,
                "versao": versao_veiculo,
                "marca": v.get("marca"),
                "modelo": modelo_veiculo,
                "ano": v.get("ano_modelo"),
                "ano_fabricacao": v.get("ano"),
                "km": v.get("km"),
                "cor": None,
                "combustivel": v.get("combustivel"),
                "cambio": v.get("cambio"),
                "motor": self._extract_motor_from_version(versao_veiculo),
                "portas": v.get("portas"),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(v.get("preco")),
                "opcionais": opcionais_veiculo,
                "fotos": self._extract_photos(v),
                "url": v.get("url"),
                "unidade": v.get("unidade"),
                "descricao": v.get("descricao")
            })
            parsed_vehicles.append(parsed)

        return parsed_vehicles

    def _xml_to_dict(self, xml_str: str) -> Dict:
        """Converte XML para dict similar ao Autocerto"""
        try:
            root = ET.fromstring(xml_str)
            carros = []
            
            for carro in root.findall('carro'):
                carro_dict = {}
                for child in carro:
                    if child.tag == 'fotos':
                        fotos = []
                        for foto in child.findall('foto'):
                            if foto.text:
                                fotos.append(foto.text)
                        carro_dict['fotos'] = {'foto': fotos}
                    else:
                        carro_dict[child.tag] = child.text
                carros.append(carro_dict)
            
            if not carros:
                print(f"[AVISO] Nenhum elemento <carro> encontrado no XML")
                return {}
            
            return {"estoque": {"veiculo": carros}}
        except Exception as e:
            print(f"[ERRO] Falha ao parsear XML do Carburgo: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _parse_opcionais(self, opcionais: Any) -> str:
        """Processa os opcionais do Carburgo"""
        if isinstance(opcionais, dict) and "opcional" in opcionais:
            opcional = opcionais["opcional"]
            if isinstance(opcional, list):
                return ", ".join(str(item) for item in opcional if item)
            return str(opcional) if opcional else ""
        return ""
    
    def _clean_version(self, modelo: str, versao: str) -> str:
        """Limpa a versão removendo informações técnicas redundantes"""
        if not versao:
            return modelo.strip() if modelo else None
        
        modelo_str = modelo.strip() if modelo else ""
        versao_limpa = ' '.join(re.sub(
            r'\b(\d\.\d|4x[0-4]|\d+v|diesel|flex|gasolina|manual|automático|4p)\b', 
            '', versao, flags=re.IGNORECASE
        ).split())
        
        if versao_limpa:
            return f"{modelo_str} {versao_limpa}".strip()
        else:
            return modelo_str or None
    
    def _extract_motor_from_version(self, versao: str) -> str:
        """Extrai informações do motor da versão"""
        if not versao:
            return None
        
        words = versao.strip().split()
        return words[0] if words else None
    
    def _extract_photos(self, v: Dict) -> List[str]:
        """Extrai fotos do veículo Carburgo"""
        fotos = v.get("fotos")
        if not fotos:
            return []
        
        fotos_foto = fotos.get("foto")
        if not fotos_foto:
            return []

        if isinstance(fotos_foto, dict):
            fotos_foto = [fotos_foto]

        return [img for img in fotos_foto if img]
    
    def definir_categoria_veiculo(self, modelo: str, opcionais: str) -> str:
        """Define categoria do veículo baseado no modelo e opcionais"""
        # Para Carburgo, usar o tipo como categoria
        return None  # Será definido pelo campo tipo
    
    def inferir_cilindrada_e_categoria_moto(self, modelo: str, versao: str):
        """Inferir cilindrada e categoria para motos (não aplicável para Carburgo)"""
        return None, None
