import requests
import xmltodict
import json
import os
import re
from datetime import datetime
from unidecode import unidecode
from typing import Dict, List, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
from vehicle_mappings import (
    MAPEAMENTO_CATEGORIAS, 
    MAPEAMENTO_MOTOS, 
    MAPEAMENTO_CILINDRADAS, 
    OPCIONAL_CHAVE_HATCH
)

# =================== CONFIGURAÇÕES GLOBAIS =======================

JSON_FILE = "data.json"

# =================== UTILS =======================

def normalizar_texto(texto: str) -> str:
    if not texto: return ""
    texto_norm = unidecode(str(texto)).lower()
    texto_norm = re.sub(r'[^a-z0-9\s]', '', texto_norm)
    texto_norm = re.sub(r'\s+', ' ', texto_norm).strip()
    return texto_norm

def definir_categoria_veiculo(modelo: str, opcionais: str = "") -> Optional[str]:
    """
    Define a categoria de um veículo usando busca EXATA no mapeamento.
    Para modelos ambíguos ("hatch,sedan"), usa os opcionais para decidir.
    """
    if not modelo: return None
    
    # Normaliza o modelo do feed para uma busca exata
    modelo_norm = normalizar_texto(modelo)
    
    # Busca pela chave exata no mapeamento
    categoria_result = MAPEAMENTO_CATEGORIAS.get(modelo_norm)
    
    # Se encontrou uma correspondência exata
    if categoria_result:
        if categoria_result == "hatch,sedan":
            opcionais_norm = normalizar_texto(opcionais)
            opcional_chave_norm = normalizar_texto(OPCIONAL_CHAVE_HATCH)
            if opcional_chave_norm in opcionais_norm:
                return "Hatch"
            else:
                return "Sedan"
        else:
            # Para todos os outros casos (SUV, Caminhonete, etc.)
            return categoria_result
            
    # Se não encontrou correspondência exata, verifica os modelos ambíguos
    # Isso é útil para casos como "Onix LTZ" corresponder a "onix"
    for modelo_ambiguo, categoria_ambigua in MAPEAMENTO_CATEGORIAS.items():
        if categoria_ambigua == "hatch,sedan":
            if normalizar_texto(modelo_ambiguo) in modelo_norm:
                opcionais_norm = normalizar_texto(opcionais)
                opcional_chave_norm = normalizar_texto(OPCIONAL_CHAVE_HATCH)
                if opcional_chave_norm in opcionais_norm:
                    return "Hatch"
                else:
                    return "Sedan"
    
    # Busca parcial para categorias não ambíguas
    for modelo_mapeado, categoria in MAPEAMENTO_CATEGORIAS.items():
        if categoria != "hatch,sedan":  # Pula os ambíguos que já foram tratados acima
            if normalizar_texto(modelo_mapeado) in modelo_norm:
                return categoria
    
    return None # Nenhuma correspondência encontrada

def inferir_cilindrada_e_categoria_moto(modelo: str, versao: str = "") -> Tuple[Optional[int], Optional[str]]:
   """
   Infere cilindrada e categoria para motocicletas baseado no modelo e versão.
   Busca primeiro no modelo, depois na versão se não encontrar.
   Retorna uma tupla (cilindrada, categoria).
   """
   def buscar_no_texto(texto: str) -> Tuple[Optional[int], Optional[str]]:
       if not texto: 
           return None, None
       
       texto_norm = normalizar_texto(texto)
       
       # Busca exata primeiro
       if texto_norm in MAPEAMENTO_MOTOS:
           cilindrada, categoria = MAPEAMENTO_MOTOS[texto_norm]
           return cilindrada, categoria
       
       # Busca por correspondência parcial - ordena por comprimento (mais específico primeiro)
       matches = []
       for modelo_mapeado, (cilindrada, categoria) in MAPEAMENTO_MOTOS.items():
           modelo_mapeado_norm = normalizar_texto(modelo_mapeado)
           
           # Verifica se o modelo mapeado está contido no texto
           if modelo_mapeado_norm in texto_norm:
               matches.append((modelo_mapeado_norm, cilindrada, categoria, len(modelo_mapeado_norm)))
           
           # Verifica também variações sem espaço (ybr150 vs ybr 150)
           modelo_sem_espaco = modelo_mapeado_norm.replace(' ', '')
           if modelo_sem_espaco in texto_norm:
               matches.append((modelo_sem_espaco, cilindrada, categoria, len(modelo_sem_espaco)))
       
       # Se encontrou correspondências, retorna a mais específica (maior comprimento)
       if matches:
           # Ordena por comprimento decrescente para pegar a correspondência mais específica
           matches.sort(key=lambda x: x[3], reverse=True)
           _, cilindrada, categoria, _ = matches[0]
           return cilindrada, categoria
       
       return None, None
   
   # Busca primeiro no modelo
   cilindrada, categoria = buscar_no_texto(modelo)
   
   # Se não encontrou e tem versão, busca na versão
   if not cilindrada and versao:
       cilindrada, categoria = buscar_no_texto(versao)
   
   # TERCEIRA TENTATIVA: modelo + versao como frase completa
   if not cilindrada and versao:
       cilindrada, categoria = buscar_no_texto(f"{modelo} {versao}")
   
   return cilindrada, categoria

def inferir_cilindrada(modelo: str, versao: str = "") -> Optional[int]:
    """Função legada para compatibilidade - retorna apenas cilindrada"""
    cilindrada, _ = inferir_cilindrada_e_categoria_moto(modelo, versao)
    return cilindrada

def converter_preco(valor: Any) -> float:
    if not valor: return 0.0
    try:
        if isinstance(valor, (int, float)): return float(valor)
        valor_str = str(valor)
        valor_str = re.sub(r'[^\d,.]', '', valor_str).replace(',', '.')
        parts = valor_str.split('.')
        if len(parts) > 2: valor_str = ''.join(parts[:-1]) + '.' + parts[-1]
        return float(valor_str) if valor_str else 0.0
    except (ValueError, TypeError): return 0.0

def safe_get(data: Dict, keys: Union[str, List[str]], default: Any = None) -> Any:
    if isinstance(keys, str): keys = [keys]
    for key in keys:
        if isinstance(data, dict) and key in data and data[key] is not None:
            return data[key]
    return default

def flatten_list(data: Any) -> List[Dict]:
    if not data: return []
    if isinstance(data, list):
        result = []
        for item in data:
            if isinstance(item, dict): result.append(item)
            elif isinstance(item, list): result.extend(flatten_list(item))
        return result
    elif isinstance(data, dict): return [data]
    return []

def normalize_fotos(fotos_data: Any) -> List[str]:
    """
    Normaliza diferentes estruturas de fotos para uma lista simples de URLs.
    
    Entrada aceitas:
    - Lista simples de URLs: ["url1", "url2"]  
    - Lista aninhada: [["url1", "url2"], ["url3"]]
    - Lista de objetos: [{"url": "url1"}, {"IMAGE_URL": "url2"}]
    - Objeto único: {"url": "url1"}
    - String única: "url1"
    
    Retorna sempre: ["url1", "url2", "url3"]
    """
    if not fotos_data:
        return []
    
    result = []
    
    def extract_url_from_item(item):
        """Extrai URL de um item que pode ser string, dict ou outro tipo"""
        if isinstance(item, str):
            return item.strip()
        elif isinstance(item, dict):
            # Tenta várias chaves possíveis para URL
            for key in ["url", "URL", "src", "IMAGE_URL", "path", "link", "href"]:
                if key in item and item[key]:
                    url = str(item[key]).strip()
                    # Remove parâmetros de query se houver
                    return url.split("?")[0] if "?" in url else url
        return None
    
    def process_item(item):
        """Processa um item que pode ser string, lista ou dict"""
        if isinstance(item, str):
            url = extract_url_from_item(item)
            if url:
                result.append(url)
        elif isinstance(item, list):
            # Lista aninhada - processa cada subitem
            for subitem in item:
                process_item(subitem)
        elif isinstance(item, dict):
            url = extract_url_from_item(item)
            if url:
                result.append(url)
    
    # Processa a estrutura principal
    if isinstance(fotos_data, list):
        for item in fotos_data:
            process_item(item)
    else:
        process_item(fotos_data)
    
    # Remove duplicatas e URLs vazias, mantém a ordem
    seen = set()
    normalized = []
    for url in result:
        if url and url not in seen:
            seen.add(url)
            normalized.append(url)
    
    return normalized

# =================== PARSERS =======================

class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, data: Any, url: str) -> bool: pass
    
    @abstractmethod
    def parse(self, data: Any, url: str) -> List[Dict]: pass
    
    def normalize_vehicle(self, vehicle: Dict) -> Dict:
        # Aplica normalização nas fotos antes de retornar
        fotos = vehicle.get("fotos", [])
        vehicle["fotos"] = normalize_fotos(fotos)
        
        return {
            "id": vehicle.get("id"), "tipo": vehicle.get("tipo"), "titulo": vehicle.get("titulo"),
            "versao": vehicle.get("versao"), "marca": vehicle.get("marca"), "modelo": vehicle.get("modelo"),
            "ano": vehicle.get("ano"), "ano_fabricacao": vehicle.get("ano_fabricacao"), "km": vehicle.get("km"),
            "cor": vehicle.get("cor"), "combustivel": vehicle.get("combustivel"), "cambio": vehicle.get("cambio"),
            "motor": vehicle.get("motor"), "portas": vehicle.get("portas"), "categoria": vehicle.get("categoria"),
            "cilindrada": vehicle.get("cilindrada"), "preco": vehicle.get("preco", 0.0),
            "opcionais": vehicle.get("opcionais", ""), "fotos": vehicle.get("fotos", [])
        }

class AltimusParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool: 
        return "altimus.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]: 
        veiculos = data.get("veiculos", []) 
        if isinstance(veiculos, dict): veiculos = [veiculos]
        
        parsed_vehicles = [] 
        for v in veiculos: 
            modelo_veiculo = v.get("modelo") 
            versao_veiculo = v.get("versao") 
            opcionais_veiculo = self._parse_opcionais(v.get("opcionais"))
            
            # Determina se é moto ou carro 
            tipo_veiculo = v.get("tipo", "").lower() 
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto: 
                # Para motos: usa o novo sistema com modelo E versão 
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_veiculo, versao_veiculo) 
            else: 
                # Para carros: usa o sistema existente 
                categoria_final = definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo) 
                cilindrada_final = v.get("cilindrada") or inferir_cilindrada(modelo_veiculo, versao_veiculo)
            
            parsed = self.normalize_vehicle({ 
                "id": v.get("id"), 
                "tipo": "eletrico" if v.get("tipo") in ["Bicicleta", "Patinete Elétrico"] else ("moto" if is_moto else ("carro" if v.get("tipo") == "Carro/Camioneta" else v.get("tipo"))), 
                "titulo": None, "versao": versao_veiculo, 
                "marca": v.get("marca"), "modelo": modelo_veiculo, "ano": v.get("anoModelo") or v.get("ano"), 
                "ano_fabricacao": v.get("anoFabricacao") or v.get("ano_fabricacao"), "km": v.get("km"), 
                "cor": v.get("cor"), "combustivel": v.get("combustivel"), 
                "cambio": "manual" if "manual" in str(v.get("cambio", "")).lower() else ("automatico" if "automático" in str(v.get("cambio", "")).lower() else v.get("cambio")), 
                "motor": re.search(r'\b(\d+\.\d+)\b', str(versao_veiculo or "")).group(1) if re.search(r'\b(\d+\.\d+)\b', str(versao_veiculo or "")) else None, 
                "portas": v.get("portas"), "categoria": categoria_final or v.get("categoria"), 
                "cilindrada": cilindrada_final, 
                "preco": converter_preco(v.get("valorVenda") or v.get("preco")), 
                "opcionais": opcionais_veiculo, "fotos": v.get("fotos", []) 
            }) 
            parsed_vehicles.append(parsed) 
        return parsed_vehicles
    
    def _parse_opcionais(self, opcionais: Any) -> str: 
        if isinstance(opcionais, list): return ", ".join(str(item) for item in opcionais if item) 
        return str(opcionais) if opcionais else ""

class AutocertoParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool: 
        return "autocerto.com" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        veiculos = data["estoque"]["veiculo"]
        if isinstance(veiculos, dict): veiculos = [veiculos]
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = v.get("modelo")
            versao_veiculo = v.get("versao")
            opcionais_veiculo = self._parse_opcionais(v.get("opcionais"))
            
            # Determina se é moto ou carro
            tipo_veiculo = v.get("tipoveiculo", "").lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_veiculo, versao_veiculo)
            else:
                categoria_final = definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = inferir_cilindrada(modelo_veiculo, versao_veiculo)

            parsed = self.normalize_vehicle({
                "id": v.get("idveiculo"), 
                "tipo": "moto" if is_moto else v.get("tipoveiculo"), 
                "titulo": None, 
                "versao": ((v.get('modelo', '').strip() + ' ' + ' '.join(re.sub(r'\b(\d\.\d|4x[0-4]|\d+v|diesel|flex|gasolina|manual|automático|4p)\b', '', v.get('versao', ''), flags=re.IGNORECASE).split())).strip()) if v.get("versao") else (v.get("modelo", "").strip() or None),
                "marca": v.get("marca"), "modelo": modelo_veiculo, "ano": v.get("anomodelo"), "ano_fabricacao": None,
                "km": v.get("quilometragem"), "cor": v.get("cor"), "combustivel": v.get("combustivel"),
                "cambio": v.get("cambio"), 
                "motor": v.get("versao", "").strip().split()[0] if v.get("versao") else None, 
                "portas": v.get("numeroportas"), "categoria": categoria_final,
                "cilindrada": cilindrada_final, "preco": converter_preco(v.get("preco")),
                "opcionais": opcionais_veiculo, "fotos": self.extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        return parsed_vehicles

    def _parse_opcionais(self, opcionais: Any) -> str:
        if isinstance(opcionais, dict) and "opcional" in opcionais:
            opcional = opcionais["opcional"]
            if isinstance(opcional, list): return ", ".join(str(item) for item in opcional if item)
            return str(opcional) if opcional else ""
        return ""
    
    def extract_photos(self, v: Dict) -> List[str]:
        fotos = v.get("fotos")
        if not fotos or not (fotos_foto := fotos.get("foto")): return []
        if isinstance(fotos_foto, dict): fotos_foto = [fotos_foto]
        return [img["url"].split("?")[0] for img in fotos_foto if isinstance(img, dict) and "url" in img]

class AutoconfParser(BaseParser):
    # Mapeamento de categorias específico do Autoconf
    CATEGORIA_MAPPING = {
        "conversivel/cupe": "Conversível",
        "conversível/cupê": "Conversível", 
        "picapes": "Caminhonete",
        "suv / utilitario esportivo": "SUV",
        "suv / utilitário esportivo": "SUV",
        "suv": "SUV",
        "van/utilitario": "Utilitário",
        "van/utilitário": "Utilitário",
        "wagon/perua": "Minivan",
        "perua": "Minivan"
    }
    
    def can_parse(self, data: Any, url: str) -> bool:
        return "autoconf" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        ads = data["ADS"]["AD"]
        if isinstance(ads, dict): ads = [ads]
        
        parsed_vehicles = []
        for v in ads:
            modelo_veiculo = v.get("MODEL")
            versao_veiculo = v.get("VERSION")
            opcionais_veiculo = self._parse_features(v.get("FEATURES"))
            
            # Determina se é moto ou carro
            categoria_veiculo = v.get("CATEGORY", "").lower()
            is_moto = categoria_veiculo == "motos" or "moto" in categoria_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_veiculo, versao_veiculo)
                tipo_final = "moto"
            else:
                # Para carros, usa SEMPRE o campo BODY e aplica o mapeamento específico
                body_category = v.get("BODY", "").lower().strip()
                categoria_final = self.CATEGORIA_MAPPING.get(body_category, v.get("BODY"))
                
                cilindrada_final = inferir_cilindrada(modelo_veiculo, versao_veiculo)
                tipo_final = "carro" if categoria_veiculo == "carros" else categoria_veiculo

            parsed = self.normalize_vehicle({
                "id": v.get("ID"), 
                "tipo": tipo_final,
                "titulo": None, 
                "versao": (' '.join(re.sub(r'\b(\d\.\d|4x[0-4]|\d+v|diesel|flex|aut|aut.|dies|dies.|mec.|mec|gasolina|manual|automático|4p)\b', '', versao_veiculo or '', flags=re.IGNORECASE).split()).strip()) if versao_veiculo else None,
                "marca": v.get("MAKE"), "modelo": modelo_veiculo, "ano": v.get("YEAR"), "ano_fabricacao": v.get("FABRIC_YEAR"),
                "km": v.get("MILEAGE"), "cor": v.get("COLOR"), "combustivel": v.get("FUEL"),
                "cambio": v.get("gear") or v.get("GEAR"), "motor": v.get("MOTOR"), "portas": v.get("DOORS"),
                "categoria": categoria_final, 
                "cilindrada": cilindrada_final,
                "preco": converter_preco(v.get("PRICE")), "opcionais": opcionais_veiculo, "fotos": self.extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        return parsed_vehicles
    
    def _parse_features(self, features: Any) -> str:
        if not features: return ""
        if isinstance(features, list):
            return ", ".join(feat.get("FEATURE", "") if isinstance(feat, dict) else str(feat) for feat in features)
        return str(features)
    
    def extract_photos(self, v: Dict) -> List[str]:
        images = v.get("IMAGES", [])
        if not images: return []
    
        # Se é uma lista (múltiplos IMAGES)
        if isinstance(images, list):
            return [img.get("IMAGE_URL") for img in images if isinstance(img, dict) and img.get("IMAGE_URL")]
    
        # Se é um dict único
        elif isinstance(images, dict) and images.get("IMAGE_URL"):
            return [images["IMAGE_URL"]]
        
        return []

class RevendamaisParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool:
        return "revendamais.com.br" in url.lower()

    def parse(self, data: Any, url: str) -> List[Dict]:
        ads = data["ADS"]["AD"]
        if isinstance(ads, dict): ads = [ads]
        
        parsed_vehicles = []
        for v in ads:
            modelo_veiculo = v.get("MODEL")
            versao_veiculo = v.get("VERSION")
            opcionais_veiculo = v.get("ACCESSORIES") or ""
            
            # Determina se é moto ou carro
            categoria_veiculo = v.get("CATEGORY", "").lower()
            is_moto = categoria_veiculo == "motocicleta" or "moto" in categoria_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_veiculo, versao_veiculo)
                tipo_final = "moto"
            else:
                categoria_final = definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = inferir_cilindrada(modelo_veiculo, versao_veiculo)
                tipo_final = v.get("CATEGORY")

            parsed = self.normalize_vehicle({
                "id": v.get("ID"), "tipo": tipo_final, "titulo": v.get("TITLE"), "versao": versao_veiculo,
                "marca": v.get("MAKE"), "modelo": modelo_veiculo, "ano": v.get("YEAR"),
                "ano_fabricacao": v.get("FABRIC_YEAR"), "km": v.get("MILEAGE"), "cor": v.get("COLOR"),
                "combustivel": v.get("FUEL"), "cambio": v.get("GEAR"), "motor": v.get("MOTOR"),
                "portas": v.get("DOORS"), "categoria": categoria_final or v.get("BODY_TYPE"),
                "cilindrada": cilindrada_final, "preco": converter_preco(v.get("PRICE")),
                "opcionais": opcionais_veiculo, "fotos": self.extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        return parsed_vehicles
    
    def extract_photos(self, v: Dict) -> List[str]:
        images = v.get("IMAGES", [])
        if not images: return []
        
        if isinstance(images, list):
            return [img.get("IMAGE_URL") for img in images if isinstance(img, dict) and img.get("IMAGE_URL")]
        elif isinstance(images, dict) and images.get("IMAGE_URL"):
            return [images["IMAGE_URL"]]
        
        return []

class FronteiraParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool:
        return "fronteiraveiculos.com" in url.lower()

    def parse(self, data: Any, url: str) -> List[Dict]:
        ads = data["estoque"]["veiculo"]
        if isinstance(ads, dict): ads = [ads]
        
        parsed_vehicles = []
        for v in ads:
            modelo_veiculo = v.get("modelo")
            versao_veiculo = v.get("titulo")
            opcionais_veiculo = v.get("opcionais") or ""
            
            # Determina se é moto ou carro
            categoria_veiculo = v.get("CATEGORY", "").lower()
            is_moto = categoria_veiculo == "motocicleta" or "moto" in categoria_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_veiculo, versao_veiculo)
                tipo_final = "moto"
            else:
                categoria_final = definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = inferir_cilindrada(modelo_veiculo, versao_veiculo)
                tipo_final = 'carro'

            parsed = self.normalize_vehicle({
                "id": v.get("id"), "tipo": tipo_final, "titulo": v.get("titulo"), "versao": versao_veiculo,
                "marca": v.get("marca"), "modelo": modelo_veiculo, "ano": v.get("ano"),
                "ano_fabricacao": v.get("FABRIC_YEAR"), "km": v.get("km"), "cor": v.get("cor"),
                "combustivel": v.get("combustivel"), "cambio": v.get("cambio"), "motor": v.get("motor"),
                "portas": v.get("DOORS"), "categoria": categoria_final or v.get("BODY_TYPE"),
                "cilindrada": cilindrada_final, "preco": converter_preco(v.get("preco")),
                "opcionais": opcionais_veiculo, "fotos": self.extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        return parsed_vehicles
    
    def extract_photos(self, v: Dict) -> List[str]:
        fotos = v.get("fotos", {})
        if not fotos: return []

        images = fotos.get("foto")
        if not images: return []

        if isinstance(images, str): return [images]
        if isinstance(images, list): return [img for img in images if isinstance(img, str)]
        return []

class RevendaproParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool:
        return "revendapro.com.br" in url.lower()

    def parse(self, data: Any, url: str) -> List[Dict]:
        ads = data["CargaVeiculos"]["Veiculo"]
        if isinstance(ads, dict): ads = [ads]
        
        parsed_vehicles = []
        for v in ads:
            modelo_veiculo = v.get("Modelo")
            versao_veiculo = v.get("Versao")
            opcionais_veiculo = v.get("Equipamentos") or ""
            
            # Determina se é moto ou carro
            categoria_veiculo = v.get("Tipo", "").lower()
            is_moto = categoria_veiculo == "motocicleta" or "moto" in categoria_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_veiculo, versao_veiculo)
            else:
                categoria_final = definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = inferir_cilindrada(modelo_veiculo, versao_veiculo)

            parsed = self.normalize_vehicle({
                "id": v.get("Codigo"), "tipo": v.get("Tipo"), "titulo": v.get(""), "versao": v.get("Versao"),
                "marca": v.get("Marca"), "modelo": v.get("Modelo"), "ano": v.get("AnoModelo"),
                "ano_fabricacao": v.get("AnoFabr"), "km": v.get("km"), "cor": v.get("Cor"),
                "combustivel": v.get("Combustivel"), "cambio": v.get("Cambio"), 
                "motor": (v.get("Versao") or "").split()[0] if v.get("Versao") else "",
                "portas": v.get("Portas"), "categoria": categoria_final,
                "cilindrada": cilindrada_final, "preco": converter_preco(v.get("Preco")),
                "opcionais": opcionais_veiculo, "fotos": self.extract_photos(v)
            })
            parsed_vehicles.append(parsed)
        return parsed_vehicles
    
    def extract_photos(self, v: Dict[str, Any]) -> List[str]:
        fotos = v.get("Fotos")
        if not fotos: return []

        if isinstance(fotos, dict):
            images = fotos.get("foto")
            if isinstance(images, str):
                return [images]
            if isinstance(images, list):
                return [img for img in images if isinstance(img, str)]
            return []

        if isinstance(fotos, str):
            s = re.sub(r"</?\s*fotos?\s*>", "", fotos, flags=re.IGNORECASE).strip()
            urls = [u.strip() for u in re.split(r"[;\n]+", s) if u.strip()]
            return urls

        return []

class ClickGarageParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool:
        return "clickgarage.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        estoque = data.get("estoque", {})
        veiculos = estoque.get("veiculo", [])
        
        if isinstance(veiculos, dict):
            veiculos = [veiculos]
        
        parsed_vehicles = []
        
        for v in veiculos:
            if not isinstance(v, dict):
                continue
            
            marca_modelo = v.get("marca", "")
            modelo_completo = v.get("modelo", "")
            
            marca_final, modelo_final = self._extract_marca_modelo(marca_modelo, modelo_completo)
            opcionais_processados = self._parse_opcionais_clickgarage(v.get("opcionais", {}))
            
            tipo_veiculo = v.get("tipo", "").lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto:
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_final, "")
                tipo_final = "moto"
            else:
                categoria_final = definir_categoria_veiculo(modelo_final, opcionais_processados)
                cilindrada_final = inferir_cilindrada(modelo_final, "")
                tipo_final = "carro"
            
            motor_info = self._extract_motor_info(modelo_completo)
            
            parsed = self.normalize_vehicle({
                "id": v.get("placa")[::-1] if v.get("placa") else v.get("id"),
                "tipo": tipo_final,
                "titulo": v.get("titulo"),
                "versao": self._clean_version(modelo_completo),
                "marca": marca_final,
                "modelo": modelo_final,
                "ano": v.get("anomod") or v.get("ano"),
                "ano_fabricacao": v.get("anofab"),
                "km": v.get("km"),
                "cor": v.get("cor"),
                "combustivel": v.get("combustivel"),
                "cambio": self._extract_cambio_info(modelo_completo),
                "motor": motor_info,
                "portas": None,
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": converter_preco(v.get("preco")),
                "opcionais": opcionais_processados,
                "fotos": self._extract_photos_clickgarage(v)
            })
            
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_marca_modelo(self, marca_campo: str, modelo_completo: str) -> Tuple[str, str]:
        if marca_campo:
            marca_parts = marca_campo.split(" - ")
            marca_final = marca_parts[-1].strip() if marca_parts else marca_campo.strip()
        else:
            marca_final = ""
        
        if modelo_completo:
            modelo_words = modelo_completo.strip().split()
            modelo_final = modelo_words[0] if modelo_words else modelo_completo
        else:
            modelo_final = ""
        
        return marca_final, modelo_final
    
    def _parse_opcionais_clickgarage(self, opcionais: Dict) -> str:
        if not isinstance(opcionais, dict):
            return ""
        
        opcionais_list = []
        
        for chave, valor in opcionais.items():
            if str(valor).lower() == "sim":
                opcional_nome = chave.replace("-", " ").lower()
                opcional_nome = opcional_nome.capitalize()
                opcionais_list.append(opcional_nome)
        
        return ", ".join(opcionais_list)
    
    def _extract_photos_clickgarage(self, veiculo: Dict) -> List[str]:
        fotos = []
        
        if img_principal := veiculo.get("imagem_principal"):
            fotos.append(img_principal.strip())
        
        for i in range(2, 20):
            foto_key = f"foto{i}"
            if foto_url := veiculo.get(foto_key):
                fotos.append(foto_url.strip())
        
        return fotos
    
    def _clean_version(self, modelo_completo: str) -> str:
        if not modelo_completo:
            return ""
        
        versao_limpa = re.sub(r'\b(\d+\.\d+|16V|TB|Flex|Aut\.|Manual|4p|2p)\b', '', modelo_completo, flags=re.IGNORECASE)
        versao_limpa = re.sub(r'\s+', ' ', versao_limpa).strip()
        
        return versao_limpa
    
    def _extract_motor_info(self, modelo_completo: str) -> Optional[str]:
        if not modelo_completo:
            return None
        
        motor_match = re.search(r'\b(\d+\.\d+)\b', modelo_completo)
        return motor_match.group(1) if motor_match else None
    
    def _extract_cambio_info(self, modelo_completo: str) -> Optional[str]:
        if not modelo_completo:
            return None
        
        modelo_lower = modelo_completo.lower()
        
        if "aut" in modelo_lower:
            return "automatico"
        elif "manual" in modelo_lower:
            return "manual"
        
        return None

class SimplesVeiculoParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool:
        return "simplesveiculo.com.br" in url.lower()
    
    def _fetch_price_from_secondary_source(self, vehicle_id: str) -> Optional[float]:
        try:
            xml_url_2 = os.environ.get('XML_URL_2')
            if not xml_url_2:
                return None
                
            response = requests.get(xml_url_2, timeout=30)
            response.raise_for_status()
            
            price_data = response.json()
            
            for vehicle in price_data:
                if str(vehicle.get("id")) == str(vehicle_id):
                    valor = vehicle.get("valor")
                    if valor:
                        return converter_preco(valor)
            
            return None
            
        except Exception as e:
            print(f"Erro ao buscar preço da fonte secundária: {e}")
            return None
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        listings = data.get("listings", {})
        veiculos = listings.get("listing", [])
        
        if isinstance(veiculos, dict):
            veiculos = [veiculos]
        
        parsed_vehicles = []
        
        for v in veiculos:
            if not isinstance(v, dict):
                continue
            
            vehicle_id = v.get("vehicle_id")
            titulo = v.get("title", "")
            modelo_completo = v.get("model", "")
            marca = v.get("make", "")
            
            modelo_final = self._extract_modelo_base(modelo_completo, marca)
            km_final = self._extract_mileage(v.get("mileage", {}))
            
            vehicle_type = v.get("vehicle_type", "").lower()
            is_moto = vehicle_type == "motorcycle" or "moto" in vehicle_type
            
            if is_moto:
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_final, modelo_completo)
                tipo_final = "moto"
            else:
                categoria_final = definir_categoria_veiculo(modelo_final, "")
                cilindrada_final = inferir_cilindrada(modelo_final, modelo_completo)
                tipo_final = "carro"
            
            motor_info = self._extract_motor_info(modelo_completo)
            combustivel_final = self._map_fuel_type(v.get("fuel_type", ""))
            cambio_final = self._map_transmission(v.get("transmission", ""))
            
            preco_secundario = self._fetch_price_from_secondary_source(vehicle_id)
            preco_final = preco_secundario if preco_secundario is not None else converter_preco(v.get("price"))
            
            parsed = self.normalize_vehicle({
                "id": vehicle_id,
                "tipo": tipo_final,
                "titulo": titulo,
                "versao": self._clean_version(modelo_completo, marca),
                "marca": marca,
                "modelo": modelo_final,
                "ano": self._safe_int(v.get("year")),
                "ano_fabricacao": None,
                "km": km_final,
                "cor": self._normalize_color(v.get("exterior_color", "")),
                "combustivel": combustivel_final,
                "cambio": cambio_final,
                "motor": motor_info,
                "portas": None,
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": preco_final,
                "opcionais": v.get("description"),
                "fotos": self._extract_photos_simples(v)
            })
            
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_modelo_base(self, modelo_completo: str, marca: str) -> str:
        if not modelo_completo:
            return ""
        
        modelo_sem_marca = modelo_completo
        if marca and modelo_completo.upper().startswith(marca.upper()):
            modelo_sem_marca = modelo_completo[len(marca):].strip()
        
        palavras = modelo_sem_marca.strip().split()
        if palavras:
            return palavras[0]
        
        return modelo_completo.strip()
    
    def _extract_mileage(self, mileage_data: Dict) -> Optional[int]:
        if not isinstance(mileage_data, dict):
            return None
        
        value = mileage_data.get("value")
        if value:
            try:
                return int(float(str(value).replace(",", "").replace(".", "")))
            except (ValueError, TypeError):
                return None
        
        return None
    
    def _map_fuel_type(self, fuel_type: str) -> Optional[str]:
        if not fuel_type:
            return None
        
        fuel_lower = fuel_type.lower()
        
        mapping = {
            "gasoline": "gasolina",
            "ethanol": "etanol", 
            "flex": "flex",
            "diesel": "diesel",
            "electric": "elétrico",
            "hybrid": "híbrido"
        }
        
        return mapping.get(fuel_lower, fuel_type.lower())
    
    def _map_transmission(self, transmission: str) -> Optional[str]:
        if not transmission:
            return None
        
        trans_lower = transmission.lower()
        
        if "manual" in trans_lower:
            return "manual"
        elif "automatic" in trans_lower or "auto" in trans_lower:
            return "automatico"
        
        return transmission.lower()
    
    def _extract_photos_simples(self, veiculo: Dict) -> List[str]:
        fotos = []
        
        image_data = veiculo.get("image")
        
        if not image_data:
            return fotos
        
        if isinstance(image_data, list):
            for img in image_data:
                if isinstance(img, dict) and "url" in img:
                    url = str(img["url"]).strip()
                    if url and url != "https://app.simplesveiculo.com.br/":
                        fotos.append(url)
                elif isinstance(img, str) and img.strip():
                    if img.strip() != "https://app.simplesveiculo.com.br/":
                        fotos.append(img.strip())
        
        elif isinstance(image_data, dict):
            if "url" in image_data:
                url = str(image_data["url"]).strip()
                if url and url != "https://app.simplesveiculo.com.br/":
                    fotos.append(url)
        
        elif isinstance(image_data, str) and image_data.strip():
            if image_data.strip() != "https://app.simplesveiculo.com.br/":
                fotos.append(image_data.strip())
        
        return fotos
    
    def _clean_version(self, modelo_completo: str, marca: str) -> Optional[str]:
        if not modelo_completo:
            return None
        
        versao = modelo_completo
        
        if marca and versao.upper().startswith(marca.upper()):
            versao = versao[len(marca):].strip()
        
        palavras = versao.split()
        if len(palavras) > 1:
            versao = " ".join(palavras[1:])
        else:
            return None
        
        return versao.strip() if versao.strip() else None
    
    def _extract_motor_info(self, modelo_completo: str) -> Optional[str]:
        if not modelo_completo:
            return None
        
        motor_match = re.search(r'\b(\d+\.\d+)\b', modelo_completo)
        return motor_match.group(1) if motor_match else None
    
    def _normalize_color(self, color: str) -> Optional[str]:
        if not color:
            return None
        
        return color.strip().lower().capitalize()
    
    def _safe_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

class BoomParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool: 
        return "boomsistemas.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        veiculos = []
        if isinstance(data, list): veiculos = flatten_list(data)
        elif isinstance(data, dict):
            for key in ['veiculos', 'vehicles', 'data', 'items', 'results', 'content']:
                if key in data: veiculos = flatten_list(data[key]); break
            if not veiculos and self._looks_like_vehicle(data): veiculos = [data]
        
        parsed_vehicles = []
        for v in veiculos:
            if not isinstance(v, dict): continue
            
            modelo_veiculo = safe_get(v, ["modelo", "model", "nome", "MODEL"])
            versao_veiculo = safe_get(v, ["versao", "version", "variant", "VERSION"])
            opcionais_veiculo = self._parse_opcionais(safe_get(v, ["opcionais", "options", "extras", "features", "FEATURES"]))
            
            tipo_veiculo = safe_get(v, ["tipo", "type", "categoria_veiculo", "CATEGORY", "vehicle_type"]) or ""
            is_moto = any(termo in str(tipo_veiculo).lower() for termo in ["moto", "motocicleta", "motorcycle", "bike"])
            
            if is_moto:
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_veiculo, versao_veiculo)
                tipo_final = "moto"
            else:
                categoria_final = definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = safe_get(v, ["cilindrada", "displacement", "engine_size"]) or inferir_cilindrada(modelo_veiculo, versao_veiculo)
                tipo_final = tipo_veiculo or "carro"

            parsed = self.normalize_vehicle({
                "id": safe_get(v, ["id", "ID", "codigo", "cod"]), 
                "tipo": tipo_final,
                "titulo": safe_get(v, ["titulo", "title", "TITLE"]), 
                "versao": versao_veiculo,
                "marca": safe_get(v, ["marca", "brand", "fabricante", "MAKE"]), 
                "modelo": modelo_veiculo,
                "ano": safe_get(v, ["ano_mod", "anoModelo", "ano", "year_model", "ano_modelo", "YEAR"]),
                "ano_fabricacao": safe_get(v, ["ano_fab", "anoFabricacao", "ano_fabricacao", "year_manufacture", "FABRIC_YEAR"]),
                "km": safe_get(v, ["km", "quilometragem", "mileage", "kilometers", "MILEAGE"]), 
                "cor": safe_get(v, ["cor", "color", "colour", "COLOR"]),
                "combustivel": safe_get(v, ["combustivel", "fuel", "fuel_type", "FUEL"]), 
                "cambio": safe_get(v, ["cambio", "transmission", "gear", "GEAR"]),
                "motor": safe_get(v, ["motor", "engine", "motorization", "MOTOR"]), 
                "portas": safe_get(v, ["portas", "doors", "num_doors", "DOORS"]),
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": converter_preco(safe_get(v, ["valor", "valorVenda", "preco", "price", "value", "PRICE"])),
                "opcionais": opcionais_veiculo, "fotos": self._parse_fotos(v)
            })
            parsed_vehicles.append(parsed)
        return parsed_vehicles
    
    def _looks_like_vehicle(self, data: Dict) -> bool: 
        return any(field in data for field in ['modelo', 'model', 'marca', 'brand', 'preco', 'price', 'ano', 'year'])
    
    def _parse_opcionais(self, opcionais: Any) -> str:
        if not opcionais: return ""
        if isinstance(opcionais, list):
            if all(isinstance(i, dict) for i in opcionais):
                return ", ".join(name for item in opcionais if (name := safe_get(item, ["nome", "name", "descricao", "description", "FEATURE"])))
            return ", ".join(str(item) for item in opcionais if item)
        return str(opcionais)
    
    def _parse_fotos(self, v: Dict) -> List[str]:
        fotos_data = safe_get(v, ["galeria", "fotos", "photos", "images", "gallery", "IMAGES"], [])
        if not isinstance(fotos_data, list): fotos_data = [fotos_data] if fotos_data else []
        
        result = []
        for foto in fotos_data:
            if isinstance(foto, str): result.append(foto)
            elif isinstance(foto, dict):
                if url := safe_get(foto, ["url", "URL", "src", "IMAGE_URL", "path"]):
                    result.append(url)
        return result

# =================== SISTEMA PRINCIPAL =======================

class UnifiedVehicleFetcher:
    def __init__(self):
        self.parsers = [
            AltimusParser(),
            FronteiraParser(),
            ClickGarageParser(), 
            AutocertoParser(), 
            RevendamaisParser(), 
            AutoconfParser(), 
            SimplesVeiculoParser(),
            RevendaproParser(),
            BoomParser()
        ]
        print("[INFO] Sistema unificado iniciado - seleção de parser baseada na URL")
    
    def get_urls(self) -> List[str]: 
        return list({val for var, val in os.environ.items() if var.startswith("XML_URL") and val})
    
    def detect_format(self, content: bytes, url: str) -> tuple[Any, str]:
        content_str = content.decode('utf-8', errors='ignore')
        try: return json.loads(content_str), "json"
        except json.JSONDecodeError:
            try: return xmltodict.parse(content_str), "xml"
            except Exception: raise ValueError(f"Formato não reconhecido para URL: {url}")
    
    def select_parser(self, data: Any, url: str) -> Optional['BaseParser']:
        for parser in self.parsers:
            if parser.can_parse(data, url):
                print(f"[INFO] Parser selecionado por URL: {parser.__class__.__name__}")
                return parser
        
        print(f"[AVISO] Nenhum parser específico encontrado para URL: {url}")
        print(f"[INFO] Tentando parser genérico BoomParser como fallback...")
        
        boom_parser = BoomParser()
        if boom_parser.can_parse(data, url):
            print(f"[INFO] Usando BoomParser como fallback")
            return boom_parser
        
        return None
    
    def process_url(self, url: str) -> List[Dict]:
        print(f"[INFO] Processando URL: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data, format_type = self.detect_format(response.content, url)
            print(f"[INFO] Formato detectado: {format_type}")
            
            parser = self.select_parser(data, url)
            if parser:
                return parser.parse(data, url)
            else:
                print(f"[ERRO] Nenhum parser adequado encontrado para URL: {url}")
                return []
                
        except requests.RequestException as e: 
            print(f"[ERRO] Erro de requisição para URL {url}: {e}")
            return []
        except Exception as e: 
            print(f"[ERRO] Erro crítico ao processar URL {url}: {e}")
            return []
    
    def fetch_all(self) -> Dict:
        urls = self.get_urls()
        if not urls:
            print("[AVISO] Nenhuma variável de ambiente 'XML_URL' foi encontrada.")
            return {}
        
        print(f"[INFO] {len(urls)} URL(s) encontrada(s) para processar")
        all_vehicles = [vehicle for url in urls for vehicle in self.process_url(url)]
        
        stats = self._generate_stats(all_vehicles)
        
        result = {
            "veiculos": all_vehicles, 
            "_updated_at": datetime.now().isoformat(), 
            "_total_count": len(all_vehicles), 
            "_sources_processed": len(urls),
            "_statistics": stats
        }
        
        try:
            with open(JSON_FILE, "w", encoding="utf-8") as f: 
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n[OK] Arquivo {JSON_FILE} salvo com sucesso!")
        except Exception as e: 
            print(f"[ERRO] Erro ao salvar arquivo JSON: {e}")
        
        print(f"[OK] Total de veículos processados: {len(all_vehicles)}")
        self._print_stats(stats)
        return result
    
    def _generate_stats(self, vehicles: List[Dict]) -> Dict:
        stats = {
            "por_tipo": {},
            "motos_por_categoria": {},
            "carros_por_categoria": {},
            "top_marcas": {},
            "cilindradas_motos": {},
            "parsers_utilizados": {}
        }
        
        for vehicle in vehicles:
            tipo = vehicle.get("tipo", "indefinido")
            stats["por_tipo"][tipo] = stats["por_tipo"].get(tipo, 0) + 1
            
            categoria = vehicle.get("categoria", "indefinido")
            if tipo and "moto" in str(tipo).lower():
                stats["motos_por_categoria"][categoria] = stats["motos_por_categoria"].get(categoria, 0) + 1
                
                cilindrada = vehicle.get("cilindrada")
                if cilindrada:
                    range_key = self._get_cilindrada_range(cilindrada)
                    stats["cilindradas_motos"][range_key] = stats["cilindradas_motos"].get(range_key, 0) + 1
            else:
                stats["carros_por_categoria"][categoria] = stats["carros_por_categoria"].get(categoria, 0) + 1
            
            marca = vehicle.get("marca", "indefinido")
            stats["top_marcas"][marca] = stats["top_marcas"].get(marca, 0) + 1
        
        return stats
    
    def _get_cilindrada_range(self, cilindrada: int) -> str:
        if cilindrada <= 125:
            return "até 125cc"
        elif cilindrada <= 250:
            return "126cc - 250cc"
        elif cilindrada <= 500:
            return "251cc - 500cc"
        elif cilindrada <= 1000:
            return "501cc - 1000cc"
        else:
            return "acima de 1000cc"
    
    def _print_stats(self, stats: Dict):
        print(f"\n{'='*60}\nESTATÍSTICAS DO PROCESSAMENTO\n{'='*60}")
        
        print(f"\n📊 Distribuição por Tipo:")
        for tipo, count in sorted(stats["por_tipo"].items(), key=lambda x: x[1], reverse=True):
            print(f"  • {tipo}: {count}")
        
        if stats["motos_por_categoria"]:
            print(f"\n🏍️  Motos por Categoria:")
            for categoria, count in sorted(stats["motos_por_categoria"].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {categoria}: {count}")
        
        if stats["carros_por_categoria"]:
            print(f"\n🚗 Carros por Categoria:")
            for categoria, count in sorted(stats["carros_por_categoria"].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  • {categoria}: {count}")
        
        if stats["cilindradas_motos"]:
            print(f"\n🔧 Cilindradas das Motos:")
            for faixa, count in sorted(stats["cilindradas_motos"].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {faixa}: {count}")
        
        print(f"\n🏭 Top 5 Marcas:")
        for marca, count in sorted(stats["top_marcas"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {marca}: {count}")

# =================== FUNÇÃO PARA IMPORTAÇÃO =======================

def fetch_and_convert_xml():
    """Função de alto nível para ser importada por outros módulos."""
    fetcher = UnifiedVehicleFetcher()
    return fetcher.fetch_all()

# =================== EXECUÇÃO PRINCIPAL (SE RODADO DIRETAMENTE) =======================

if __name__ == "__main__":
    result = fetch_and_convert_xml()
    
    if result and 'veiculos' in result:
        total = result.get('_total_count', 0)
        print(f"\n{'='*50}\nRESUMO DO PROCESSAMENTO\n{'='*50}")
        print(f"Total de veículos: {total}")
        print(f"Atualizado em: {result.get('_updated_at', 'N/A')}")
        print(f"Fontes processadas: {result.get('_sources_processed', 0)}")
        
        if total > 0:
            print(f"\nExemplo dos primeiros 5 veículos:")
            for i, v in enumerate(result['veiculos'][:5], 1):
                tipo = v.get('tipo', 'N/A')
                categoria = v.get('categoria', 'N/A')
                cilindrada = v.get('cilindrada', '')
                cilindrada_str = f" - {cilindrada}cc" if cilindrada else ""
                print(f"{i}. {v.get('marca', 'N/A')} {v.get('modelo', 'N/A')} ({tipo}/{categoria}{cilindrada_str}) {v.get('ano', 'N/A')} - R$ {v.get('preco', 0.0):,.2f}")
            
            motos = [v for v in result['veiculos'] if v.get('tipo') and 'moto' in str(v.get('tipo')).lower()]
            if motos:
                print(f"\nExemplos de motos categorizadas:")
                for i, moto in enumerate(motos[:3], 1):
                    print(f"{i}. {moto.get('marca', 'N/A')} {moto.get('modelo', 'N/A')} - {moto.get('categoria', 'N/A')} - {moto.get('cilindrada', 'N/A')}cc")
            
            print(f"\nExemplos de fotos normalizadas:")
            vehicles_with_photos = [v for v in result['veiculos'] if v.get('fotos')][:3]
            for i, vehicle in enumerate(vehicles_with_photos, 1):
                fotos = vehicle.get('fotos', [])
                print(f"{i}. {vehicle.get('marca', 'N/A')} {vehicle.get('modelo', 'N/A')} - {len(fotos)} foto(s)")
                if fotos:
                    print(f"   Primeira foto: {fotos[0]}")
                    if len(fotos) > 1:
                        print(f"   Tipo da estrutura: Lista simples com {len(fotos)} URLs")
