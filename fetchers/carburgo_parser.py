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
        return "citroenpremiere.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do Carburgo"""
        if isinstance(data, str):
            try:
                root = ET.fromstring(data)
                carros = root.findall('carro')
            except (ET.ParseError, TypeError):
                return []
        else:
            # Assume data is dict (parsed XML)
            estoque = data.get('estoque')
            if not estoque:
                return []
            carros = estoque.get('carro')
            if not carros:
                return []
            if isinstance(carros, dict):
                carros = [carros]
        
        parsed_vehicles = []
        for carro in carros:
            if isinstance(data, str):
                modelo_veiculo = (carro.findtext('modelo') or '').strip()
                versao_veiculo = modelo_veiculo  # No versao field, use modelo
                marca = carro.findtext('marca') or None
                ano_modelo = carro.findtext('ano_modelo')
                ano_fabricacao = carro.findtext('ano')
                km = carro.findtext('km')
                portas = carro.findtext('portas')
                combustivel = carro.findtext('combustivel')
                cambio = carro.findtext('cambio')
                cilindradas = carro.findtext('cilindradas')
                preco = carro.findtext('preco')
                cor = None  # No cor field
                opcionais_veiculo = None  # No opcionais
                fotos = self._extract_photos(carro)
                tipo = carro.findtext('tipo', '')
                placa = carro.findtext('placa', '')
                url_item = carro.findtext('url')
                unidade = carro.findtext('unidade')
                descricao = carro.findtext('descricao')
            else:
                modelo_veiculo = carro.get('modelo', '').strip()
                versao_veiculo = modelo_veiculo
                marca = carro.get('marca')
                ano_modelo = carro.get('ano_modelo')
                ano_fabricacao = carro.get('ano')
                km = carro.get('km')
                portas = carro.get('portas')
                combustivel = carro.get('combustivel')
                cambio = carro.get('cambio')
                cilindradas = carro.get('cilindradas')
                preco = carro.get('preco')
                cor = carro.get('cor')
                opcionais_veiculo = self._parse_opcionais(carro.get('opcionais'))
                fotos = self._extract_photos(carro)
                tipo = carro.get('tipo', '')
                placa = carro.get('placa', '')
                url_item = carro.get('url')
                unidade = carro.get('unidade')
                descricao = carro.get('descricao')
            
            # Convert to appropriate types
            ano = int(ano_modelo) if ano_modelo and ano_modelo.isdigit() else None
            ano_fab = int(ano_fabricacao) if ano_fabricacao and ano_fabricacao.isdigit() else None
            km_int = int(km) if km and km.isdigit() else None
            portas_int = int(portas) if portas and portas.isdigit() else None
            cilindrada = int(cilindradas) if cilindradas and cilindradas.isdigit() else None
            preco_float = self.converter_preco(preco) if preco else None
            
            # Determine tipo and categoria
            tipo_veiculo = tipo.lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo

            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                categoria_final = tipo.strip() if tipo and tipo.strip() else None
                cilindrada_final = cilindrada
            
            id_str = "".join(d for i, d in enumerate(placa) if i in [1, 2, 3, 5, 6]) if placa else None
            parsed = self.normalize_vehicle({
                "id": id_str,
                "tipo": "moto" if is_moto else "carro",
                "titulo": None,
                "versao": versao_veiculo,
                "marca": marca,
                "modelo": modelo_veiculo,
                "ano": ano,
                "ano_fabricacao": ano_fab,
                "km": km_int,
                "cor": cor,
                "combustivel": combustivel,
                "cambio": cambio,
                "motor": self._extract_motor_from_version(versao_veiculo),
                "portas": portas_int,
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": preco_float,
                "opcionais": opcionais_veiculo,
                "fotos": fotos,
                "url": url_item,
                "unidade": unidade,
                "descricao": descricao
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
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
    
    def _extract_photos(self, carro) -> List[str]:
        """Extrai fotos do veículo Carburgo"""
        fotos = []
        if hasattr(carro, 'findtext'):  # ET element
            imagem = carro.findtext('imagem')
            if imagem:
                fotos.append(imagem)
            fotos_node = carro.find('fotos')
            if fotos_node is not None:
                for foto in fotos_node.findall('foto'):
                    if foto.text:
                        fotos.append(foto.text)
        else:  # dict
            imagem = carro.get('imagem')
            if imagem:
                fotos.append(imagem)
            fotos_node = carro.get('fotos')
            if isinstance(fotos_node, dict) and 'foto' in fotos_node:
                foto_list = fotos_node['foto']
                if isinstance(foto_list, list):
                    fotos.extend(foto_list)
                elif foto_list:
                    fotos.append(str(foto_list))
        return fotos
    
    def definir_categoria_veiculo(self, modelo: str, opcionais: str) -> str:
        """Define categoria do veículo baseado no modelo e opcionais"""
        # Para Carburgo, usar o tipo como categoria
        return None  # Será definido pelo campo tipo
    
    def inferir_cilindrada_e_categoria_moto(self, modelo: str, versao: str):
        """Inferir cilindrada e categoria para motos (não aplicável para Carburgo)"""
        return None, None
