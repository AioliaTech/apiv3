"""
Parser específico para DSAutoEstoque (dsautoestoque.com) - JSON
"""
from .base_parser import BaseParser
from typing import Dict, List, Any
import json

class DSAutoEstoqueParser(BaseParser):
    """Parser para dados JSON do DSAutoEstoque"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do DSAutoEstoque"""
        return "dsautoestoque.com" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados JSON do DSAutoEstoque"""
        print(f"[DEBUG] Tipo original do data: {type(data)}")
        print(f"[DEBUG] Data (primeiros 200 chars): {str(data)[:200]}")
        
        # Se data for string JSON, parse primeiro
        if isinstance(data, str):
            try:
                data = json.loads(data)
                print(f"[DEBUG] Após JSON parse - Tipo: {type(data)}")
                print(f"[DEBUG] Chaves disponíveis: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
            except json.JSONDecodeError as e:
                print(f"[ERROR] Erro ao fazer parse do JSON: {e}")
                print(f"[ERROR] Data que causou erro: {str(data)[:500]}")
                return []
        
        # Verifica se data é None ou vazio
        if not data:
            print("[DEBUG] Data está vazio")
            return []
        
        parsed_vehicles = []
        
        # Busca pelos veículos no JSON
        veiculos = []
        
        if isinstance(data, dict):
            if 'veiculos' in data:
                veiculos = data['veiculos']
            elif 'estoque' in data:
                veiculos = data['estoque']
            elif 'veiculo' in data:
                veiculos = data['veiculo'] if isinstance(data['veiculo'], list) else [data['veiculo']]
            else:
                # Se for um dict com uma única chave, pega o valor
                if len(data.keys()) == 1:
                    key = list(data.keys())[0]
                    if isinstance(data[key], list):
                        veiculos = data[key]
        
        elif isinstance(data, list):
            veiculos = data
        
        for v in veiculos:
            # Verifica se v é dict antes de usar .get()
            if not isinstance(v, dict):
                continue
                
            # Extrai dados básicos
            id_veiculo = str(v.get('id', ''))
            tipo_veiculo = v.get('tipoveiculo', '')
            zero_km = v.get('zerokm', '') == 'S'
            placa = v.get('placa', '')
            marca = v.get('marca', '')
            modelo = v.get('modelo', '')
            versao = v.get('versao', '')
            ano_fabricacao = v.get('anofabricacao', '')
            ano_modelo = v.get('anomodelo', '')
            cambio = v.get('cambio', '')
            km = v.get('km', '0')
            portas = v.get('portas', '0')
            cor = v.get('cor', '')
            combustivel = v.get('combustivel', '')
            carroceria = v.get('carroceria', '')
            preco = v.get('preco', '')
            observacao = v.get('observacao', '')
            
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
            loja_info = {}
            if 'loja' in v and v['loja']:
                loja = v['loja']
                if 'contato' in loja and loja['contato']:
                    contato = loja['contato']
                    loja_info = {
                        'nome': contato.get('nome', ''),
                        'email': contato.get('email', ''),
                        'telefone': contato.get('telefone', ''),
                        'site': contato.get('site', '')
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
                "motor": None,
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
    
    def _extract_photos(self, v) -> List[str]:
        """Extrai fotos do veículo"""
        if 'fotos' not in v or not v['fotos']:
            return []
        
        fotos = []
        foto_list = v['fotos']
        
        if isinstance(foto_list, list):
            for foto in foto_list:
                if isinstance(foto, str):
                    url = foto.strip()
                elif isinstance(foto, dict) and 'url' in foto:
                    url = foto['url'].strip()
                else:
                    continue
                    
                # Remove parâmetros da URL após extensão
                if '.jpg' in url:
                    url = url.split('.jpg')[0] + '.jpg'
                elif '.jpeg' in url:
                    url = url.split('.jpeg')[0] + '.jpeg'
                elif '.png' in url:
                    url = url.split('.png')[0] + '.png'
                fotos.append(url)
        
        return fotos
    
    def _convert_km(self, km_str: str) -> int:
        """Converte string/int de KM para inteiro"""
        if not km_str:
            return 0
        
        try:
            if isinstance(km_str, int):
                return km_str
            km_clean = str(km_str).replace('.', '').replace(' ', '').replace(',', '')
            return int(km_clean)
        except (ValueError, TypeError):
            return 0
    
    def _convert_portas(self, portas_str: str) -> int:
        """Converte string/int de portas para inteiro"""
        if not portas_str:
            return 0
        
        try:
            return int(portas_str)
        except (ValueError, TypeError):
            return 0
