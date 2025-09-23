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

class BaseParser(ABC):
    """Classe base abstrata para todos os parsers de veículos"""
    
    def __init__(self):
        # Cache do mapeamento normalizado para evitar recalcular sempre
        self._mapeamento_normalizado = None
    
    @property
    def mapeamento_normalizado(self):
        """Lazy loading do mapeamento normalizado"""
        if self._mapeamento_normalizado is None:
            self._mapeamento_normalizado = {}
            for chave_original, categoria in MAPEAMENTO_CATEGORIAS.items():
                chave_normalizada = self.normalizar_texto(chave_original)
                self._mapeamento_normalizado[chave_normalizada] = categoria
        return self._mapeamento_normalizado
    
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
    
    def definir_categoria_veiculo(self, modelo: str, opcionais: str = "") -> str:
        """
        Define a categoria de um veículo usando busca EXATA no mapeamento.
        Para modelos ambíguos ("hatch,sedan"), usa os opcionais para decidir.
        CORRIGIDO: Usa mapeamento normalizado com busca por especificidade (mais longo = mais específico)
        """
        if not modelo: 
            return None
        
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
            if chave_normalizada in modelo_norm:  # Se a chave está contida no modelo
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
