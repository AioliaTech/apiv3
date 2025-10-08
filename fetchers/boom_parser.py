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
        
        print(f"DEBUG - Tipo recebido: {type(data)}")
        print(f"DEBUG - Primeiros 200 chars: {str(data)[:200]}")
        
        # Se recebeu string XML, converte para dict
        if isinstance(data, (str, bytes)):
            data = self._parse_xml(data)
        
        print(f"DEBUG - Após parse, tipo: {type(data)}")
        print(f"DEBUG - Keys: {data.keys() if isinstance(data, dict) else 'N/A'}")
        
        veiculos = []
        
        if isinstance(data, dict):
            print(f"DEBUG - Conteúdo do dict: {data}")
            
            if 'veiculo' in data:
                print("DEBUG - Encontrou 'veiculo'")
                veiculo_data = data['veiculo']
                print(f"DEBUG - Tipo veiculo_data: {type(veiculo_data)}")
                
                if isinstance(veiculo_data, list):
                    veiculos = veiculo_data
                    print(f"DEBUG - É lista com {len(veiculos)} items")
                else:
                    veiculos = [veiculo_data]
                    print("DEBUG - Transformou em lista")
        
        print(f"DEBUG - Total veiculos: {len(veiculos)}")
        
        if veiculos:
            print(f"DEBUG - Primeiro veiculo: {veiculos[0]}")
        
        parsed_vehicles = []
        for i, v in enumerate(veiculos):
            print(f"DEBUG - Processando veiculo {i}: {type(v)}")
            
            if not isinstance(v, dict):
                print(f"DEBUG - Veiculo {i} não é dict, pulando")
                continue
            
            print(f"DEBUG - Veiculo {i} keys: {v.keys()}")
            
            modelo_veiculo = v.get('modelo')
            tipo_veiculo = v.get('tipo', 'carro')
            
            # Verifica se é moto
            is_moto = 'moto' in str(tipo_veiculo).lower()
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, None
                )
                tipo_final = "moto"
            else:
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, "")
                cilindrada_final = None
                tipo_final = tipo_veiculo
            
            # Processa fotos da galeria
            fotos = []
            galeria = v.get('galeria')
            if galeria and isinstance(galeria, dict) and 'item' in galeria:
                items = galeria['item']
                if isinstance(items, list):
                    fotos = [item for item in items if item]
                elif items:
                    fotos = [items]
            
            parsed = self.normalize_vehicle({
                "id": v.get('id'),
                "tipo": tipo_final,
                "titulo": v.get('titulo'),
                "versao": None,
                "marca": v.get('marca'),
                "modelo": v.get('modelo'),
                "ano": v.get('ano_mod'),
                "ano_fabricacao": v.get('ano_fab'),
                "km": v.get('km'),
                "cor": v.get('cor'),
                "combustivel": v.get('combustivel'),
                "cambio": v.get('cambio'),
                "motor": v.get('motor'),
                "portas": v.get('portas'),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(v.get('valor')),
                "opcionais": "",
                "fotos": fotos
            })
            parsed_vehicles.append(parsed)
        
        print(f"DEBUG - Total parsed: {len(parsed_vehicles)}")
        return parsed_vehicles
    
    def _parse_xml(self, xml_data: Union[str, bytes]) -> Dict:
        """Converte XML em dicionário"""
        try:
            if isinstance(xml_data, bytes):
                xml_data = xml_data.decode('utf-8')
            
            root = ET.fromstring(xml_data)
            print(f"DEBUG XML - Root tag: {root.tag}")
            print(f"DEBUG XML - Root children: {[child.tag for child in root]}")
            
            result = self._element_to_dict(root)
            print(f"DEBUG XML - Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
            
            return result
        except Exception as e:
            print(f"Erro ao parsear XML: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _element_to_dict(self, element: ET.Element) -> Any:
        """Converte um elemento XML recursivamente em dicionário"""
        children = list(element)
        
        if not children:
            # Elemento folha
            text = element.text
            if text is not None:
                text = text.strip()
                return text if text else None
            return None
        
        # Tem filhos
        result = {}
        for child in children:
            child_data = self._element_to_dict(child)
            
            if child.tag in result:
                # Já existe - transforma em lista
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
