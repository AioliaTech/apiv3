"""
Parser específico para DSAutoEstoque com DEBUG DETALHADO
"""
from .base_parser import BaseParser
from typing import Dict, List, Any
import xml.etree.ElementTree as ET
import traceback

class DSAutoEstoqueParser(BaseParser):
    """Parser para dados do DSAutoEstoque com debug detalhado"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do DSAutoEstoque"""
        result = "dsautoestoque.com" in url.lower()
        print(f"[DEBUG] can_parse - URL: {url}, Pode processar: {result}")
        return result
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do DSAutoEstoque com debug detalhado"""
        print(f"[DEBUG] Iniciando parse - Tipo do data: {type(data)}")
        
        try:
            # Debug inicial dos dados
            if isinstance(data, str):
                print(f"[DEBUG] Data é string - Tamanho: {len(data)} chars")
                print(f"[DEBUG] Primeiros 200 chars: {data[:200]}")
                print(f"[DEBUG] Últimos 200 chars: {data[-200:]}")
                
                # Limpa possíveis caracteres problemáticos
                data_clean = data.strip()
                
                # Remove BOM se presente
                if data_clean.startswith('\ufeff'):
                    data_clean = data_clean[1:]
                    print("[DEBUG] Removido BOM")
                
                # Remove declaração XML problemática
                if data_clean.startswith('<?xml'):
                    lines = data_clean.split('\n')
                    if lines[0].startswith('<?xml'):
                        data_clean = '\n'.join(lines[1:])
                        print("[DEBUG] Removida declaração XML")
                
                print(f"[DEBUG] Tentando parse XML...")
                root = ET.fromstring(data_clean)
                print(f"[DEBUG] Parse XML bem-sucedido!")
                
            else:
                print(f"[DEBUG] Data não é string, usando diretamente")
                root = data
                
        except ET.ParseError as e:
            print(f"[ERROR] Erro ao fazer parse do XML: {e}")
            print(f"[ERROR] Linha do erro: {e.lineno if hasattr(e, 'lineno') else 'N/A'}")
            print(f"[ERROR] Posição do erro: {e.offset if hasattr(e, 'offset') else 'N/A'}")
            
            # Tenta identificar o problema
            if isinstance(data, str):
                lines = data.split('\n')
                print(f"[ERROR] Total de linhas no XML: {len(lines)}")
                if hasattr(e, 'lineno') and e.lineno <= len(lines):
                    error_line = lines[e.lineno - 1] if e.lineno > 0 else "Linha não encontrada"
                    print(f"[ERROR] Linha com erro: {error_line}")
            
            raise ValueError(f"Erro ao fazer parse do XML: {e}")
        
        except Exception as e:
            print(f"[ERROR] Erro inesperado no parse: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            raise
        
        # Debug da estrutura do XML
        print(f"[DEBUG] Root tag: {root.tag}")
        print(f"[DEBUG] Root attrib: {root.attrib}")
        print(f"[DEBUG] Filhos diretos do root: {[child.tag for child in root]}")
        
        # Busca veículos de diferentes formas
        veiculos_direct = root.findall('veiculo')
        veiculos_recursive = root.findall('.//veiculo')
        
        print(f"[DEBUG] Veículos encontrados (busca direta): {len(veiculos_direct)}")
        print(f"[DEBUG] Veículos encontrados (busca recursiva): {len(veiculos_recursive)}")
        
        veiculos = veiculos_recursive if veiculos_recursive else veiculos_direct
        
        if len(veiculos) == 0:
            # Debug mais profundo se não encontrar veículos
            print("[DEBUG] Nenhum veículo encontrado! Investigando estrutura...")
            
            def print_xml_structure(element, level=0):
                indent = "  " * level
                print(f"{indent}{element.tag}: '{element.text.strip() if element.text else ''}' {element.attrib}")
                for child in element:
                    print_xml_structure(child, level + 1)
                    if level < 3:  # Limita profundidade para não poluir muito
                        continue
            
            print_xml_structure(root)
            
            return []
        
        parsed_vehicles = []
        
        for i, v in enumerate(veiculos):
            try:
                print(f"[DEBUG] Processando veículo {i+1}/{len(veiculos)}")
                
                # Extrai dados básicos com debug
                id_veiculo = self._get_text_debug(v, 'id', f"Veículo {i+1}")
                tipo_veiculo = self._get_text_debug(v, 'tipoveiculo', f"Veículo {i+1}")
                zero_km = self._get_text(v, 'zerokm') == 'S'
                placa = self._get_text_debug(v, 'placa', f"Veículo {i+1}")
                marca = self._get_text_debug(v, 'marca', f"Veículo {i+1}")
                modelo = self._get_text_debug(v, 'modelo', f"Veículo {i+1}")
                versao = self._get_text_debug(v, 'versao', f"Veículo {i+1}")
                
                # Só faz debug detalhado do primeiro veículo
                if i == 0:
                    ano_fabricacao = self._get_text_debug(v, 'anofabricacao', f"Veículo {i+1}")
                    ano_modelo = self._get_text_debug(v, 'anomodelo', f"Veículo {i+1}")
                    cambio = self._get_text_debug(v, 'cambio', f"Veículo {i+1}")
                    km = self._get_text_debug(v, 'km', f"Veículo {i+1}")
                    portas = self._get_text_debug(v, 'portas', f"Veículo {i+1}")
                    cor = self._get_text_debug(v, 'cor', f"Veículo {i+1}")
                    combustivel = self._get_text_debug(v, 'combustivel', f"Veículo {i+1}")
                    carroceria = self._get_text_debug(v, 'carroceria', f"Veículo {i+1}")
                    preco = self._get_text_debug(v, 'preco', f"Veículo {i+1}")
                    observacao = self._get_text_debug(v, 'observacao', f"Veículo {i+1}")
                else:
                    # Para os outros, usa versão sem debug
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
                
                print(f"[DEBUG] Veículo {i+1} - É moto: {is_moto}")
                
                if is_moto:
                    try:
                        cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                            modelo, versao
                        )
                        tipo_final = "moto"
                    except Exception as e:
                        print(f"[WARNING] Erro ao inferir cilindrada/categoria moto: {e}")
                        cilindrada_final = None
                        categoria_final = "moto"
                        tipo_final = "moto"
                else:
                    try:
                        categoria_final = self.definir_categoria_veiculo(modelo, observacao or "")
                        cilindrada_final = None
                        tipo_final = "carro"
                    except Exception as e:
                        print(f"[WARNING] Erro ao definir categoria veículo: {e}")
                        categoria_final = carroceria or "sedan"
                        cilindrada_final = None
                        tipo_final = "carro"
                
                # Extrai fotos
                fotos = self._extract_photos_debug(v, f"Veículo {i+1}")
                
                # Extrai dados da loja
                loja_info = self._extract_loja_debug(v, f"Veículo {i+1}")
                
                # Converte valores
                km_converted = self._convert_km(km)
                portas_converted = self._convert_portas(portas)
                
                try:
                    preco_converted = self.converter_preco(preco)
                except Exception as e:
                    print(f"[WARNING] Erro ao converter preço '{preco}': {e}")
                    preco_converted = 0.0
                
                # Cria objeto normalizado
                vehicle_data = {
                    "id": id_veiculo,
                    "tipo": tipo_final,
                    "zero_km": zero_km,
                    "placa": placa,
                    "versao": versao,
                    "marca": marca,
                    "modelo": modelo,
                    "ano": ano_modelo or ano_fabricacao,
                    "ano_fabricacao": ano_fabricacao,
                    "km": km_converted,
                    "cor": cor,
                    "combustivel": combustivel,
                    "cambio": cambio,
                    "motor": None,  # Não disponível no XML
                    "portas": portas_converted,
                    "categoria": categoria_final or carroceria,
                    "cilindrada": cilindrada_final,
                    "preco": preco_converted,
                    "opcionais": observacao or "",
                    "fotos": fotos,
                    "loja": loja_info
                }
                
                print(f"[DEBUG] Dados do veículo {i+1} antes da normalização: {vehicle_data}")
                
                try:
                    parsed = self.normalize_vehicle(vehicle_data)
                    parsed_vehicles.append(parsed)
                    print(f"[DEBUG] Veículo {i+1} processado com sucesso")
                except Exception as e:
                    print(f"[ERROR] Erro ao normalizar veículo {i+1}: {e}")
                    print(f"[ERROR] Dados: {vehicle_data}")
                    continue
                
            except Exception as e:
                print(f"[ERROR] Erro ao processar veículo {i+1}: {e}")
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                continue
        
        print(f"[DEBUG] Total de veículos processados: {len(parsed_vehicles)}")
        return parsed_vehicles
    
    def _get_text_debug(self, element, tag_name: str, context: str) -> str:
        """Versão com debug do _get_text"""
        result = self._get_text(element, tag_name)
        print(f"[DEBUG] {context} - {tag_name}: '{result}'")
        return result
    
    def _get_text(self, element, tag_name: str) -> str:
        """Extrai texto de um elemento XML, tratando CDATA corretamente"""
        if element is None:
            return ""
        
        child = element.find(tag_name)
        if child is None:
            return ""
        
        # O Python ET já trata CDATA automaticamente
        text = child.text or ""
        return text.strip()
    
    def _extract_photos_debug(self, v, context: str) -> List[str]:
        """Extrai fotos com debug"""
        fotos_elem = v.find('fotos')
        if fotos_elem is None:
            print(f"[DEBUG] {context} - Nenhum elemento 'fotos' encontrado")
            return []
        
        fotos = []
        foto_elements = fotos_elem.findall('foto')
        print(f"[DEBUG] {context} - Encontrados {len(foto_elements)} elementos 'foto'")
        
        for foto_elem in foto_elements:
            if foto_elem.text:
                # Remove parâmetros da URL após extensão
                url = foto_elem.text.strip()
                if '.jpg' in url:
                    url = url.split('.jpg')[0] + '.jpg'
                elif '.jpeg' in url:
                    url = url.split('.jpeg')[0] + '.jpeg'
                elif '.png' in url:
                    url = url.split('.png')[0] + '.png'
                fotos.append(url)
        
        print(f"[DEBUG] {context} - Total de fotos extraídas: {len(fotos)}")
        return fotos
    
    def _extract_loja_debug(self, v, context: str) -> Dict[str, str]:
        """Extrai dados da loja com debug"""
        loja_elem = v.find('loja')
        if loja_elem is None:
            print(f"[DEBUG] {context} - Nenhum elemento 'loja' encontrado")
            return {}
        
        contato_elem = loja_elem.find('contato')
        if contato_elem is None:
            print(f"[DEBUG] {context} - Nenhum elemento 'contato' em 'loja' encontrado")
            return {}
        
        loja_info = {
            'nome': self._get_text(contato_elem, 'nome'),
            'email': self._get_text(contato_elem, 'email'),
            'telefone': self._get_text(contato_elem, 'telefone'),
            'site': self._get_text(contato_elem, 'site')
        }
        
        print(f"[DEBUG] {context} - Loja extraída: {loja_info}")
        return loja_info
    
    def _convert_km(self, km_str: str) -> int:
        """Converte string de KM para inteiro"""
        if not km_str:
            return 0
        
        try:
            # Remove pontos, espaços e vírgulas
            km_clean = km_str.replace('.', '').replace(' ', '').replace(',', '')
            return int(km_clean)
        except (ValueError, TypeError):
            return 0
    
    def _convert_portas(self, portas_str: str) -> int:
        """Converte string de portas para inteiro"""
        if not portas_str:
            return 0
        
        try:
            return int(portas_str.strip())
        except (ValueError, TypeError):
            return 0
