"""
Parser específico para WordPress/WooCommerce de veículos
"""
from .base_parser import BaseParser
from typing import Dict, List, Any, Optional, Tuple
import re

class WordPressParser(BaseParser):
    """Parser para dados do WordPress/WooCommerce de veículos"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do WordPress"""
        if not isinstance(data, dict):
            return False
        
        # Verifica estruturas típicas do WordPress
        if "data" in data and isinstance(data["data"], dict):
            post_data = data["data"]
            if "post" in post_data:
                return True
        
        if "post" in data:
            return True
            
        return False
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do WordPress"""
        posts = self._extract_posts(data)
        parsed_vehicles = []
        
        for post in posts:
            if not isinstance(post, dict):
                continue
            
            # Debug apenas para o primeiro post
            if len(parsed_vehicles) == 0:
                print(f"[DEBUG] Campos disponíveis no XML:")
                for key in sorted(post.keys()):
                    value = post[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + "..."
                    print(f"  {key}: {value}")
                print()
            
            # Extrai dados básicos
            marca = self._safe_get_post_field(post, ["Marca", "marca", "_marca"])
            modelo = self._safe_get_post_field(post, ["Modelo", "modelo", "_modelo"])
            versao = self._safe_get_post_field(post, ["Verso", "versao", "_versao", "Version"])
            carroceria = self._safe_get_post_field(post, ["_carroceria", "carroceria", "Carroceria"])
            opcionais = self._safe_get_post_field(post, ["Opcionais", "opcionais", "_opcionais"])
            
            # Campos específicos
            cor = self._safe_get_post_field(post, ["Cores", "cor", "_cor", "Color"])
            ano_campo = self._safe_get_post_field(post, ["_ano", "ano", "Ano", "Year"])
            km = self._safe_get_post_field(post, ["_quilometragem", "quilometragem", "KM", "km"])
            combustivel = self._safe_get_post_field(post, ["_combustivel", "combustivel", "Combustivel"])
            cambio = self._safe_get_post_field(post, ["_cambio", "cambio", "Cambio"])
            preco = self._safe_get_post_field(post, ["_valor", "valor", "preco", "Preco", "Price"])
            
            # Processa anos
            ano_fabricacao, ano_modelo = self._extract_anos(ano_campo)
            
            # Determina categoria
            categoria_final = self.definir_categoria_veiculo(modelo, opcionais)
            
            # Extrai motor
            motor_info = self._extract_motor_info(versao or "")
            
            # Processa fotos
            fotos = self._extract_photos(post)
            
            # Monta veículo
            parsed = self.normalize_vehicle({
                "id": self._safe_get_post_field(post, ["ID", "id", "_id"]),
                "tipo": "carro",
                "versao": self._clean_version(versao or ""),
                "marca": marca,
                "modelo": modelo,
                "ano": ano_modelo,
                "ano_fabricacao": ano_fabricacao,
                "km": km,
                "cor": cor,
                "combustivel": combustivel,
                "cambio": cambio,
                "motor": motor_info,
                "portas": None,
                "categoria": categoria_final,
                "cilindrada": None,
                "preco": self.converter_preco(preco),
                "opcionais": opcionais or "",
                "fotos": fotos
            })
            
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_posts(self, data: Dict) -> List[Dict]:
        """Extrai posts da estrutura do WordPress"""
        posts = []
        
        if "data" in data and isinstance(data["data"], dict):
            post_data = data["data"]
            if "post" in post_data:
                post_content = post_data["post"]
                if isinstance(post_content, list):
                    posts.extend(post_content)
                elif isinstance(post_content, dict):
                    posts.append(post_content)
        
        elif "post" in data:
            post_content = data["post"]
            if isinstance(post_content, list):
                posts.extend(post_content)
            elif isinstance(post_content, dict):
                posts.append(post_content)
        
        # Fallback: procura por qualquer chave que contenha "post"
        if not posts:
            for key, value in data.items():
                if "post" in key.lower() and isinstance(value, (dict, list)):
                    if isinstance(value, list):
                        posts.extend(value)
                    else:
                        posts.append(value)
        
        return posts
    
    def _safe_get_post_field(self, post: Dict, fields: List[str]) -> Optional[str]:
        """Extrai campo do post com fallbacks e limpeza de CDATA"""
        for field in fields:
            if field in post and post[field] is not None:
                value = post[field]
                
                # Remove CDATA se presente
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                if value is not None:
                    str_value = str(value).strip()
                    return str_value if str_value else None
        return None
    
    def _extract_anos(self, ano_campo: str) -> Tuple[Optional[str], Optional[str]]:
        """Extrai ano de fabricação e modelo do campo de ano"""
        if not ano_campo:
            return None, None
        
        # Formato "fabricação/modelo"
        if "/" in ano_campo:
            partes = ano_campo.split("/")
            if len(partes) == 2:
                ano_fabricacao = partes[0].strip()
                ano_modelo = partes[1].strip()
                return ano_fabricacao, ano_modelo
        
        # Apenas um ano
        ano_limpo = ano_campo.strip()
        return ano_limpo, ano_limpo
    
    def _extract_photos(self, post: Dict) -> List[str]:
        """Extrai fotos do veículo WordPress"""
        # Campos prioritários para fotos
        foto_fields_priority = [
            "_galeria",
            "ImageURL", 
            "ImageFeatured",
        ]
        
        # Tenta campos prioritários primeiro
        for field in foto_fields_priority:
            if field in post and post[field]:
                value = post[field]
                
                # Remove CDATA se presente
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                fotos_normalizadas = self._normalize_fotos(value)
                
                if fotos_normalizadas:
                    print(f"[DEBUG] Usando campo '{field}' para fotos: {len(fotos_normalizadas)} foto(s)")
                    return fotos_normalizadas
        
        # Campos alternativos
        outros_campos = ["galeria", "_imagens", "imagens", "fotos", "_fotos", "images", "_images"]
        for field in outros_campos:
            if field in post and post[field]:
                value = post[field]
                
                # Remove CDATA se presente
                if isinstance(value, str) and value.startswith('<![CDATA['):
                    value = value.replace('<![CDATA[', '').replace(']]>', '').strip()
                
                fotos_normalizadas = self._normalize_fotos(value)
                if fotos_normalizadas:
                    print(f"[DEBUG] Usando campo alternativo '{field}' para fotos: {len(fotos_normalizadas)} foto(s)")
                    return fotos_normalizadas
        
        print(f"[DEBUG] Nenhuma foto encontrada para este veículo")
        return []
    
    def _normalize_fotos(self, fotos_data: Any) -> List[str]:
        """Normaliza diferentes estruturas de fotos para uma lista simples de URLs"""
        if not fotos_data:
            return []
        
        result = []
        
        def extract_url_from_item(item):
            if isinstance(item, str):
                url = item.strip()
                if not url:
                    return []
                
                # URLs separadas por pipe ou vírgula
                if "|" in url:
                    return [u.strip() for u in url.split("|") if u.strip()]
                elif "," in url:
                    urls = [u.strip() for u in url.split(",") if u.strip()]
                    valid_urls = []
                    for u in urls:
                        if ("http" in u or u.startswith("/")) and len(u) > 10:
                            valid_urls.append(u)
                    return valid_urls
                else:
                    return [url] if url else []
                    
            elif isinstance(item, dict):
                # Procura por chaves comuns de URL
                for key in ["url", "URL", "src", "IMAGE_URL", "path", "link", "href"]:
                    if key in item and item[key]:
                        url = str(item[key]).strip()
                        clean_url = url.split("?")[0] if "?" in url else url
                        return [clean_url] if clean_url else []
            return []
        
        def process_item(item):
            if isinstance(item, str):
                urls = extract_url_from_item(item)
                result.extend(urls)
            elif isinstance(item, list):
                for subitem in item:
                    process_item(subitem)
            elif isinstance(item, dict):
                urls = extract_url_from_item(item)
                result.extend(urls)
        
        if isinstance(fotos_data, list):
            for item in fotos_data:
                process_item(item)
        else:
            process_item(fotos_data)
        
        # Remove duplicatas
        seen = set()
        normalized = []
        for url in result:
            if url and url not in seen and url.strip() and len(url) > 10:
                seen.add(url)
                normalized.append(url.strip())
        
        # Ordena por número se possível
        def extract_number(url):
            pattern = r'-(\d+)\.(?:avif|jpg|jpeg|png|webp)$'
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return int(match.group(1))
            return 999999
        
        normalized.sort(key=extract_number)
        return normalized
    
    def _extract_motor_info(self, versao: str) -> Optional[str]:
        """Extrai informação do motor da versão"""
        if not versao:
            return None
        
        motor_match = re.search(r'\b(\d+\.\d+)\b', versao)
        return motor_match.group(1) if motor_match else None
    
    def _clean_version(self, versao: str) -> str:
        """Limpa a versão removendo informações técnicas redundantes"""
        if not versao:
            return ""
        
        # Remove informações técnicas comuns
        versao_limpa = re.sub(r'\b(\d+\.\d+|16V|TB|Flex|Aut\.|Manual|4p|2p)\b', '', versao, flags=re.IGNORECASE)
        versao_limpa = re.sub(r'\s+', ' ', versao_limpa).strip()
        
        return versao_limpa
