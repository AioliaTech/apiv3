"""
Base parser class - Define a interface comum para todos os parsers de veículos
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from vehicle_mappings import (
    MAPEAMENTO_CATEGORIAS, 
    MAPEAMENTO_MOTOS, 
    OPCIONAL_CHAVE_HATCH
)
import re
from unidecode import unidecode

# Cache global para evitar recriação constante
_MAPEAMENTO_NORMALIZADO_CACHE = None

def _get_mapeamento_normalizado():
    """Função utilitária para obter mapeamento normalizado com cache global"""
    global _MAPEAMENTO_NORMALIZADO_CACHE
    if _MAPEAMENTO_NORMALIZADO_CACHE is None:
        _MAPEAMENTO_NORMALIZADO_CACHE = {}
        for chave_original, categoria in MAPEAMENTO_CATEGORIAS.items():
            # Normaliza texto igual a função normalizar_texto
            texto_norm = unidecode(str(chave_original)).lower()
            texto_norm = re.sub(r'[^a-z0-9\s]', '', texto_norm)
            texto_norm = re.sub(r'\s+', ' ', texto_norm).strip()
            _MAPEAMENTO_NORMALIZADO_CACHE[texto_norm] = categoria
    return _MAPEAMENTO_NORMALIZADO_CACHE

def definir_categoria_veiculo_global(modelo: str, opcionais: str = "") -> str:
    """
    Função global para definir categoria - pode ser usada por qualquer parser
    mesmo que não herde corretamente do BaseParser
    """
    if not modelo: 
        return None
    
    # Normaliza o modelo do feed
    texto_norm = unidecode(str(modelo)).lower()
    texto_norm = re.sub(r'[^a-z0-9\s]', '', texto_norm)
    modelo_norm = re.sub(r'\s+', ' ', texto_norm).strip()
    
    mapeamento = _get_mapeamento_normalizado()
    
    # ETAPA 1: Busca EXATA
    categoria_result = mapeamento.get(modelo_norm)
    if categoria_result:
        if categoria_result == "hatch,sedan":
            opcionais_norm = unidecode(str(opcionais)).lower() if opcionais else ""
            opcionais_norm = re.sub(r'[^a-z0-9\s]', '', opcionais_norm)
            opcionais_norm = re.sub(r'\s+', ' ', opcionais_norm).strip()
            
            opcional_chave_norm = unidecode(str(OPCIONAL_CHAVE_HATCH)).lower()
            opcional_chave_norm = re.sub(r'[^a-z0-9\s]', '', opcional_chave_norm)
            opcional_chave_norm = re.sub(r'\s+', ' ', opcional_chave_norm).strip()
            
            if opcional_chave_norm in opcionais_norm:
                return "Hatch"
            else:
                return "Sedan"
        else:
            return categoria_result
    
    # ETAPA 2: Busca PARCIAL por especificidade
    matches_ambiguos = []
    matches_normais = []
    
    for chave_normalizada, categoria in mapeamento.items():
        # Busca parcial melhorada
        if (chave_normalizada in modelo_norm or 
            all(palavra in modelo_norm.split() for palavra in chave_normalizada.split() if palavra)):
            
            comprimento = len(chave_normalizada)
            if categoria == "hatch,sedan":
                matches_ambiguos.append((chave_normalizada, categoria, comprimento))
            else:
                matches_normais.append((chave_normalizada, categoria, comprimento))
    
    # ETAPA 3: Processa ambíguos primeiro
    if matches_ambiguos:
        matches_ambiguos.sort(key=lambda x: x[2], reverse=True)
        
        opcionais_norm = unidecode(str(opcionais)).lower() if opcionais else ""
        opcionais_norm = re.sub(r'[^a-z0-9\s]', '', opcionais_norm)
        opcionais_norm = re.sub(r'\s+', ' ', opcionais_norm).strip()
        
        opcional_chave_norm = unidecode(str(OPCIONAL_CHAVE_HATCH)).lower()
        opcional_chave_norm = re.sub(r'[^a-z0-9\s]', '', opcional_chave_norm)
        opcional_chave_norm = re.sub(r'\s+', ' ', opcional_chave_norm).strip()
        
        if opcional_chave_norm in opcionais_norm:
            return "Hatch"
        else:
            return "Sedan"
    
    # ETAPA 4: Processa categorias normais
    if matches_normais:
        matches_normais.sort(key=lambda x: x[2], reverse=True)
        _, categoria_mais_especifica, _ = matches_normais[0]
        return categoria_mais_especifica
    
    return None

class BaseParser(ABC):
    """Classe base abstrata para todos os parsers de veículos"""
    
    @property
    def mapeamento_normalizado(self):
        """Lazy loading do mapeamento normalizado - funciona mesmo sem __init__"""
        return _get_mapeamento_normalizado()
    
    @abstractmethod
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se este parser pode processar os dados da URL fornecida"""
        pass
    
    @abstractmethod
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa os dados e retorna lista de veículos normalizados"""
        pass
    
    def normalize_vehicle(self, vehicle: Dict) -> Dict:
        """Normaliza um veículo para o formato padrão"""
        # Aplica normalização nas fotos antes de retornar
        fotos = vehicle.get("fotos", [])
        vehicle["fotos"] = self.normalize_fotos(fotos)
        
        return {
            "id": vehicle.get("id"), 
            "tipo": vehicle.get("tipo"), 
            "titulo": vehicle.get("titulo"),
            "versao": vehicle.get("versao"), 
            "marca": vehicle.get("marca"), 
            "modelo": vehicle.get("modelo"),
            "ano": vehicle.get("ano"), 
            "ano_fabricacao": vehicle.get("ano_fabricacao"), 
            "km": vehicle.get("km"),
            "cor": vehicle.get("cor"), 
            "combustivel": vehicle.get("combustivel"), 
            "cambio": vehicle.get("cambio"),
            "motor": vehicle.get("motor"), 
            "portas": vehicle.get("portas"), 
            "categoria": vehicle.get("categoria"),
            "cilindrada": vehicle.get("cilindrada"), 
            "preco": vehicle.get("preco", 0.0),
            "opcionais": vehicle.get("opcionais", ""), 
            "fotos": vehicle.get("fotos", [])
        }
    
    def normalize_fotos(self, fotos_data: Any) -> List[str]:
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
    
    def normalizar_texto(self, texto: str) -> str:
        """Normaliza texto para comparação"""
        if not texto: 
            return ""
        texto_norm = unidecode(str(texto)).lower()
        texto_norm = re.sub(r'[^a-z0-9\s]', '', texto_norm)
        texto_norm = re.sub(r'\s+', ' ', texto_norm).strip()
        return texto_norm
    
# Normaliza o modelo do feed para uma busca exata
        modelo_norm = self.normalizar_texto(modelo)
        
        # ETAPA 1: Busca pela chave EXATA no mapeamento normalizado
        categoria_result = self.mapeamento_normalizado.get(modelo_norm)
        
        # Se encontrou uma correspondência exata
        if categoria_result:
            if categoria_result == "hatch,sedan":
                opcionais_norm = self.normalizar_texto(opcionais)
                opcional_chave_norm = self.normalizar_texto(OPCIONAL_CHAVE_HATCH)
                if opcional_chave_norm in opcionais_norm:
                    return "Hatch"
                else:
                    return "Sedan"
            else:
                # Para todos os outros casos (SUV, Caminhonete, etc.)
                return categoria_result
        
        # ETAPA 2: Se não encontrou exata, busca PARCIAL ordenada por ESPECIFICIDADE
        # Coleta todas as correspondências parciais com seus comprimentos
        matches_ambiguos = []  # Para modelos hatch,sedan
        matches_normais = []   # Para outras categorias
        
        for chave_normalizada, categoria in self.mapeamento_normalizado.items():
            # Busca parcial: verifica se a chave está contida no modelo OU se o modelo contém as palavras da chave
            if (chave_normalizada in modelo_norm or 
                all(palavra in modelo_norm.split() for palavra in chave_normalizada.split() if palavra)):
                comprimento = len(chave_normalizada)
                
                if categoria == "hatch,sedan":
                    matches_ambiguos.append((chave_normalizada, categoria, comprimento))
                else:
                    matches_normais.append((chave_normalizada, categoria, comprimento))
        
        # ETAPA 3: Processa modelos ambíguos primeiro (ordenados por especificidade)
        if matches_ambiguos:
            # Ordena por comprimento decrescente (mais específico primeiro)
            matches_ambiguos.sort(key=lambda x: x[2], reverse=True)
            # Pega o mais específico
            chave_mais_especifica, _, _ = matches_ambiguos[0]
            
            opcionais_norm = self.normalizar_texto(opcionais)
            opcional_chave_norm = self.normalizar_texto(OPCIONAL_CHAVE_HATCH)
            if opcional_chave_norm in opcionais_norm:
                return "Hatch"
            else:
                return "Sedan"
        
        # ETAPA 4: Se não tem ambíguos, processa categorias normais (ordenadas por especificidade)
        if matches_normais:
            # Ordena por comprimento decrescente (mais específico primeiro)
            matches_normais.sort(key=lambda x: x[2], reverse=True)
            # Retorna a categoria da correspondência mais específica
            _, categoria_mais_especifica, _ = matches_normais[0]
            return categoria_mais_especifica
        
        return None # Nenhuma correspondência encontrada
    
    def inferir_cilindrada_e_categoria_moto(self, modelo: str, versao: str = ""):
        """
        Infere cilindrada e categoria para motocicletas baseado no modelo e versão.
        Busca primeiro no modelo, depois na versão se não encontrar.
        Retorna uma tupla (cilindrada, categoria).
        """
        def buscar_no_texto(texto: str):
            if not texto: 
                return None, None
            
            texto_norm = self.normalizar_texto(texto)
            
            # Busca exata primeiro
            if texto_norm in MAPEAMENTO_MOTOS:
                cilindrada, categoria = MAPEAMENTO_MOTOS[texto_norm]
                return cilindrada, categoria
            
            # Busca por correspondência parcial - ordena por comprimento (mais específico primeiro)
            matches = []
            for modelo_mapeado, (cilindrada, categoria) in MAPEAMENTO_MOTOS.items():
                modelo_mapeado_norm = self.normalizar_texto(modelo_mapeado)
                
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
    
    def converter_preco(self, valor: Any) -> float:
        """Converte string de preço para float"""
        if not valor: 
            return 0.0
        try:
            if isinstance(valor, (int, float)): 
                return float(valor)
            valor_str = str(valor)
            valor_str = re.sub(r'[^\d,.]', '', valor_str).replace(',', '.')
            parts = valor_str.split('.')
            if len(parts) > 2: 
                valor_str = ''.join(parts[:-1]) + '.' + parts[-1]
            return float(valor_str) if valor_str else 0.0
        except (ValueError, TypeError): 
            return 0.0
