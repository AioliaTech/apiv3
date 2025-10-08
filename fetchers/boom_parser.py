"""
Parser genérico BoomParser - usado como fallback para estruturas não específicas
"""

from .base_parser import BaseParser
from typing import Dict, List, Any, Union
import xml.etree.ElementTree as ET

class BoomParser(BaseParser):
    """Parser genérico para estruturas variadas - usado como fallback"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Aceita dados de boomsistemas.com.br ou como fallback genérico"""
        return "boomsistemas.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados com estrutura genérica/variável"""
        
        # Se recebeu string XML, converte para dict
        if isinstance(data, (str, bytes)):
            data = self._parse_xml(data)
        
        veiculos = []
        
        if isinstance(data, list):
            veiculos = self._flatten_list(data)
        elif isinstance(data, dict):
            # Tenta várias chaves possíveis para encontrar os veículos
            for key in ['veiculos', 'veiculo', 'vehicles', 'data', 'items', 'results', 'content']:
                if key in data:
                    veiculos = self._flatten_list(data[key])
                    break
            
            # Se não encontrou e o próprio dict parece ser um veículo
            if not veiculos and self._looks_like_vehicle(data):
                veiculos = [data]
        
        parsed_vehicles = []
        for v in veiculos:
            if not isinstance(v, dict):
                continue
            
            modelo_veiculo = self._safe_get(v, ["modelo", "model", "nome", "MODEL"])
            versao_veiculo = self._safe_get(v, ["versao", "version", "variant", "VERSION"])
            opcionais_veiculo = self._parse_opcionais(
                self._safe_get(v, ["opcionais", "options", "extras", "features", "FEATURES"])
            )
            
            # Determina se é moto ou carro baseado em campos disponíveis
            tipo_veiculo = self._safe_get(v, ["tipo", "type", "categoria_veiculo", "CATEGORY", "vehicle_type"]) or ""
            is_moto = any(termo in str(tipo_veiculo).lower() for termo in ["moto", "motocicleta", "motorcycle", "bike"])
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
                tipo_final = "moto"
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = (
                    self._safe_get(v, ["cilindrada", "displacement", "engine_size"])
                )
                tipo_final = tipo_veiculo or "carro"
            
            parsed = self.normalize_vehicle({
                "id": self._safe_get(v, ["id", "ID", "codigo", "cod"]),
                "tipo": tipo_final,
                "titulo": self._safe_get(v, ["titulo", "title", "TITLE"]),
                "versao": versao_veiculo,
                "marca": self._safe_get(v, ["marca", "brand", "fabricante", "MAKE"]),
                "modelo": modelo_veiculo,
                "ano": self._safe_get(v, ["ano_mod", "anoModelo", "ano", "year_model", "ano_modelo", "YEAR"]),
                "ano_fabricacao": self._safe_get(v, ["ano_fab", "anoFabricacao", "ano_fabricacao", "year_manufacture", "FABRIC_YEAR"]),
                "km": self._safe_get(v, ["km", "quilometragem", "mileage", "kilometers", "MILEAGE"]),
                "cor": self._safe_get(v, ["cor", "color", "colour", "COLOR"]),
                "combustivel": self._safe_get(v, ["combustivel", "fuel", "fuel_type", "FUEL"]),
                "cambio": self._safe_get(v, ["cambio", "transmission", "gear", "GEAR"]),
                "motor": self._safe_get(v, ["motor", "engine", "motorization", "MOTOR"]),
                "portas": self._safe_get(v, ["portas", "doors", "num_doors", "DOORS"]),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(
                    self._safe_get(v, ["valor", "valorVenda", "preco", "price", "value", "PRICE"])
                ),
                "opcionais": opcionais_veiculo,
                "fotos": self._parse_fotos(v)
            })
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _parse_xml(self, xml_data: Union[str, bytes]) -> Dict:
        """Converte XML em dicionário"""
        try:
            if isinstance(xml_data, bytes):
                xml_data = xml_data.decode('utf-8')
            
            root = ET.fromstring(xml_data)
            
            # Converte o XML inteiro para dict
            return self._element_to_dict(root)
        except Exception as e:
            print(f"Erro ao parsear XML: {e}")
            return {}
    
    def _element_to_dict(self, element: ET.Element) -> Any:
        """Converte um elemento XML recursivamente em dicionário"""
        # Processa filhos
        children = list(element)
        
        if not children:
            # Elemento folha - retorna o texto ou None se vazio
            text = element.text
            if text is not None:
                text = text.strip()
                return text if text else None
            return None
        
        # Tem filhos - processa recursivamente
        result = {}
        for child in children:
            child_data = self._element_to_dict(child)
            
            # Se já existe essa chave, transforma em lista
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _safe_get(self, data: Dict, keys: Union[str, List[str]], default: Any = None) -> Any:
        """Busca valor em múltiplas chaves possíveis"""
        if not isinstance(data, dict):
            return default
            
        if isinstance(keys, str):
            keys = [keys]
        
        for key in keys:
            if key in data:
                value = data[key]
                # Retorna apenas se não for None e não for string vazia
                if value is not None and value != "":
                    return value
        return default
    
    def _flatten_list(self, data: Any) -> List[Dict]:
        """Achata listas aninhadas para encontrar veículos"""
        if not data:
            return []
        
        if isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, dict):
                    result.append(item)
                elif isinstance(item, list):
                    result.extend(self._flatten_list(item))
            return result
        elif isinstance(data, dict):
            return [data]
        
        return []
    
    def _looks_like_vehicle(self, data: Dict) -> bool:
        """Verifica se um dict parece conter dados de veículo"""
        vehicle_indicators = ['modelo', 'model', 'marca', 'brand', 'preco', 'price', 'ano', 'year', 'ano_mod', 'ano_fab']
        return any(field in data for field in vehicle_indicators)
    
    def _parse_opcionais(self, opcionais: Any) -> str:
        """Processa opcionais de formato variável"""
        if not opcionais:
            return ""
        
        if isinstance(opcionais, list):
            # Se é lista de dicts com estrutura
            if all(isinstance(i, dict) for i in opcionais):
                names = []
                for item in opcionais:
                    name = self._safe_get(item, ["nome", "name", "descricao", "description", "FEATURE"])
                    if name:
                        names.append(name)
                return ", ".join(names)
            # Se é lista simples
            return ", ".join(str(item) for item in opcionais if item)
        
        return str(opcionais)
    
    def _parse_fotos(self, v: Dict) -> List[str]:
        """Processa fotos de formato variável"""
        if not isinstance(v, dict):
            return []
            
        fotos_data = self._safe_get(v, ["galeria", "fotos", "photos", "images", "gallery", "IMAGES"])
        
        if not fotos_data:
            return []
        
        # Se galeria é um dict com 'item', pega os items
        if isinstance(fotos_data, dict) and 'item' in fotos_data:
            fotos_data = fotos_data['item']
        
        if not isinstance(fotos_data, list):
            fotos_data = [fotos_data] if fotos_data else []
        
        result = []
        for foto in fotos_data:
            if isinstance(foto, str) and foto:
                result.append(foto)
            elif isinstance(foto, dict):
                url = self._safe_get(foto, ["url", "URL", "src", "IMAGE_URL", "path"])
                if url:
                    result.append(url)
        
        return result
