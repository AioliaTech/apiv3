"""
Parser específico para DSAutoEstoque (dsautoestoque.com)
"""
from .base_parser import BaseParser
from typing import Dict, List, Any
import xml.etree.ElementTree as ET

class DSAutoEstoqueParser(BaseParser):
    """Parser para dados do DSAutoEstoque"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do DSAutoEstoque"""
        return "dsautoestoque.com" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do DSAutoEstoque"""
        # Se data for string XML, parse primeiro
        if isinstance(data, str):
            try:
                root = ET.fromstring(data)
            except ET.ParseError as e:
                raise ValueError(f"Erro ao fazer parse do XML: {e}")
        else:
            root = data
        
        parsed_vehicles = []
        
        # Busca por todos os elementos <veiculo>
        veiculos = root.findall('.//veiculo')
        
        for v in veiculos:
            # Extrai dados básicos
            id_veiculo = self._get_text(v, 'id')
            tipo_veiculo = self._get_text(v, 'tipoveiculo')
            zero_km = self._get_text(v, 'zerokm') == 'S'
            placa = self._get_text(v, 'placa')
            marca = self._get_text(v, 'marca')
            modelo = self._get_text(v, 'modelo')
            versao = self._get_text(v, 'versao')
            ano_fabricacao = self._get_text(v, 'anofabricacao')
            ano_modelo = self._get_text(v, 'anomodelo')
            cambio = self._get_text(v, 'cambio')
            km = self._get_text(v, 'km')
            portas = self._get_text(v, 'portas')
            cor = self._get_text(v, 'cor')
            combustivel = self._get_text(v, 'combustivel')
            carroceria = self._get_text(v, 'carroceria')
            preco = self._get_text(v, 'preco')
            observacao = self._get_text(v, 'observacao')
            
            # Determina se é moto ou carro
            is_moto = tipo_veiculo.lower() == "moto" or "moto" in tipo_veiculo.lower()
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo, versao
                )
                tipo_final = "moto"
            else:
                categoria_final = self.definir_categoria_veiculo(modelo, observacao or "")
                cilindrada_final = None
                tipo_final = "carro"
            
            # Extrai fotos
            fotos = self._extract_photos(v)
            
            # Extrai dados da loja
            loja_elem = v.find('loja')
            loja_info = {}
            if loja_elem is not None:
                contato_elem = loja_elem.find('contato')
                if contato_elem is not None:
                    loja_info = {
                        'nome': self._get_text(contato_elem, 'nome'),
                        'email': self._get_text(contato_elem, 'email'),
                        'telefone': self._get_text(contato_elem, 'telefone'),
                        'site': self._get_text(contato_elem, 'site')
                    }
            
            parsed = self.normalize_vehicle({
                "id": id_veiculo,
                "tipo": tipo_final,
                "zero_km": zero_km,
                "placa": placa,
                "versao": versao,
                "marca": marca,
                "modelo": modelo,
                "ano": ano_modelo or ano_fabricacao,
                "ano_fabricacao": ano_fabricacao,
                "km": self._convert_km(km),
                "cor": cor,
                "combustivel": combustivel,
                "cambio": cambio,
                "motor": None,  # Não disponível no XML
                "portas": self._convert_portas(portas),
                "categoria": categoria_final or carroceria,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(preco),
                "opcionais": observacao or "",
                "fotos": fotos,
                "loja": loja_info
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _get_text(self, element, tag_name: str) -> str:
        """Extrai texto de um elemento XML, tratando CDATA"""
        if element is None:
            return ""
        
        child = element.find(tag_name)
        if child is None:
            return ""
        
        text = child.text or ""
        return text.strip()
    
    def _extract_photos(self, v) -> List[str]:
        """Extrai fotos do veículo DSAutoEstoque"""
        fotos_elem = v.find('fotos')
        if fotos_elem is None:
            return []
        
        fotos = []
        for foto_elem in fotos_elem.findall('foto'):
            if foto_elem.text:
                # Remove parâmetros da URL após .jpg
                url = foto_elem.text.strip()
                if '.jpg' in url:
                    url = url.split('.jpg')[0] + '.jpg'
                elif '.jpeg' in url:
                    url = url.split('.jpeg')[0] + '.jpeg'
                elif '.png' in url:
                    url = url.split('.png')[0] + '.png'
                fotos.append(url)
        
        return fotos
    
    def _convert_km(self, km_str: str) -> int:
        """Converte string de KM para inteiro"""
        if not km_str:
            return 0
        
        try:
            # Remove pontos e espaços
            km_clean = km_str.replace('.', '').replace(' ', '')
            return int(km_clean)
        except (ValueError, TypeError):
            return 0
    
    def _convert_portas(self, portas_str: str) -> int:
        """Converte string de portas para inteiro"""
        if not portas_str:
            return 0
        
        try:
            return int(portas_str)
        except (ValueError, TypeError):
            return 0
