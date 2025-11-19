from .base_parser import BaseParser
from typing import Dict, List, Any, Optional
import re
import os

# Mapeamento de URLs para localizações baseado nas variáveis de ambiente
URL_LOCALIZACAO_MAP = {
    os.getenv("XML_URL_1", ""): "montenegro",
    os.getenv("XML_URL_2", ""): "santa luzia",
    os.getenv("XML_URL_3", ""): "motomecânica"
}

class ComautoParser1(BaseParser):
    """Parser para dados do AGSistema"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do AGSistema"""
        # Proteção contra url None ou vazia
        if not url:
            return False
        
        url = url.lower()
        return "s3.agsistema.net" in url
    
    def _get_localizacao(self, url: str) -> str:
        """Determina a localização baseado na URL"""
        if not url:
            return ""
        
        # Busca exata no mapeamento
        localizacao = URL_LOCALIZACAO_MAP.get(url, "")
        
        # Se não encontrou no mapeamento exato, verifica se é AGSistema (fallback)
        if not localizacao and "s3.agsistema.net" in url.lower():
            return "montenegro"
        
        return localizacao
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        veiculos = data.get("veiculos", [])
        if isinstance(veiculos, dict): 
            veiculos = [veiculos]
        
        # Define a localização baseada na URL
        localizacao = self._get_localizacao(url)
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = v.get("modelo")
            versao_veiculo = v.get("versao")
            opcionais_veiculo = self._parse_opcionais(v.get("opcionais"))
            
            # Determina se é moto ou carro
            tipo_veiculo = v.get("tipo", "").lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto:
                # Para motos: usa o sistema com modelo E versão
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_veiculo, versao_veiculo
                )
            else:
                # Para carros: usa o sistema existente
                categoria_final = self.definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = None
            
            # Processa preço
            preco_data = v.get("preco", {})
            if isinstance(preco_data, dict):
                preco_final = self.converter_preco(preco_data.get("venda"))
            else:
                preco_final = self.converter_preco(preco_data)
            
            # Normaliza câmbio
            cambio_raw = str(v.get("cambio", "")).lower()
            if "manual" in cambio_raw:
                cambio_final = "manual"
            elif "automático" in cambio_raw or "automatico" in cambio_raw:
                cambio_final = "automatico"
            else:
                cambio_final = v.get("cambio")
            
            # Extrai motor da versão
            motor_match = re.search(r'\b(\d+\.\d+)\b', str(versao_veiculo or ""))
            motor_final = motor_match.group(1) if motor_match else None
            
            parsed = self.normalize_vehicle({
                "id": ''.join(d for i, d in enumerate(str(v.get("placa", ""))) if i in [1, 2, 3, 5, 6]),
                "tipo": "moto" if is_moto else ("carro" if v.get("categoria") == "Carros" else v.get("categoria")), 
                "titulo": None, 
                "versao": versao_veiculo,
                "marca": v.get("marca"), 
                "modelo": modelo_veiculo, 
                "ano": v.get("ano_modelo") or v.get("ano"),
                "ano_fabricacao": v.get("ano_fabricacao"), 
                "km": v.get("km"),
                "cor": v.get("cor"), 
                "combustivel": v.get("combustivel"), 
                "cambio": cambio_final,
                "motor": motor_final, 
                "portas": v.get("portas"), 
                "categoria": v.get("carroceria") or categoria_final,
                "cilindrada": cilindrada_final,
                "preco": preco_final,
                "opcionais": v.get("acessorios") or opcionais_veiculo,
                "localizacao": localizacao,
                "fotos": v.get("fotos", [])
            })
            parsed_vehicles.append(parsed)
        return parsed_vehicles
    
    def _parse_opcionais(self, opcionais: Any) -> str:
        """Processa opcionais para formato string"""
        if isinstance(opcionais, list): 
            return ", ".join(str(item) for item in opcionais if item)
        return str(opcionais) if opcionais else ""


class ComautoParser2(BaseParser):
    """Parser para dados do MotorLeads"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do MotorLeads"""
        # Proteção contra url None ou vazia
        if not url:
            return False
        
        url = url.lower()
        return "api.motorleads.co" in url
    
    def _get_localizacao(self, url: str) -> str:
        """Determina a localização baseado na URL"""
        if not url:
            return ""
        
        # Busca exata no mapeamento
        return URL_LOCALIZACAO_MAP.get(url, "")
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do MotorLeads"""
        items = data.get("items", {})
        results = items.get("results", [])
        
        if isinstance(results, dict):
            results = [results]
        
        # Define a localização baseada na URL
        localizacao = self._get_localizacao(url)
        
        parsed_vehicles = []
        
        for v in results:
            if not isinstance(v, dict):
                continue
            
            # Extrai modelo base (primeira palavra do brand_model)
            brand_model = v.get("brand_model", "")
            modelo_final = brand_model.split()[0] if brand_model else ""
            
            # Versão completa
            versao_veiculo = v.get("brand_model_version", "")
            
            # Processa opcionais
            opcionais_processados = self._parse_attr_list(v.get("attr_list", ""))
            
            # Determina se é moto ou carro
            category = v.get("category", "").upper()
            segment = v.get("segment", "").upper()
            is_moto = category == "MOTO" or category == "MOTOCICLETA"
            
            if is_moto:
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                    modelo_final, versao_veiculo
                )
                tipo_final = "moto"
            else:
                # Tenta mapear segment primeiro, depois fallback para definir_categoria_veiculo
                categoria_final = self._map_segment_to_category(segment)
                if not categoria_final:
                    categoria_final = self.definir_categoria_veiculo(modelo_final, opcionais_processados)
                cilindrada_final = None
                tipo_final = "carro"
            
            # Extrai motor da versão
            motor_info = self._extract_motor_info(versao_veiculo)
            
            # Processa câmbio
            transmission = v.get("transmission", "").lower()
            cambio_final = None
            if "automático" in transmission or "automatico" in transmission:
                cambio_final = "automatico"
            elif "manual" in transmission:
                cambio_final = "manual"
            else:
                cambio_final = transmission if transmission else None
            
            # Processa fotos da galeria
            fotos_list = self._extract_photos_motorleads(v.get("gallery", []))
            
            # Ano (year_model tem prioridade sobre year_build)
            ano_final = v.get("year_model") or v.get("year_build")
            
            parsed = self.normalize_vehicle({
                "id": ''.join(d for i, d in enumerate(str(v.get("reference", ""))) if i in [1, 2, 3, 5, 6]),
                "tipo": tipo_final,
                "titulo": v.get("title"),
                "versao": self._clean_version(versao_veiculo),
                "marca": v.get("brand"),
                "modelo": modelo_final,
                "ano": ano_final,
                "ano_fabricacao": v.get("year_build"),
                "km": v.get("odometer"),
                "cor": v.get("color"),
                "combustivel": v.get("fuel"),
                "cambio": cambio_final,
                "motor": motor_info,
                "portas": v.get("door"),
                "categoria": categoria_final or segment,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(v.get("price")),
                "opcionais": opcionais_processados,
                "localizacao": localizacao,
                "fotos": fotos_list
            })
            
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _parse_attr_list(self, attr_list: str) -> str:
        """Processa a lista de atributos do MotorLeads"""
        if not attr_list:
            return ""
        
        # attr_list pode vir como string separada por vírgulas ou como lista
        if isinstance(attr_list, str):
            # Remove caracteres extras e normaliza
            attrs = [attr.strip() for attr in attr_list.split(',') if attr.strip()]
            return ", ".join(attrs)
        elif isinstance(attr_list, list):
            return ", ".join(str(item) for item in attr_list if item)
        
        return str(attr_list) if attr_list else ""
    
    def _map_segment_to_category(self, segment: str) -> Optional[str]:
        """Mapeia segment do MotorLeads para nossas categorias"""
        if not segment:
            return None
        
        segment_lower = segment.lower()
        
        mapping = {
            "sedan": "Sedan",
            "hatch": "Hatch",
            "hatchback": "Hatch",
            "suv": "SUV",
            "pickup": "Caminhonete",
            "picape": "Caminhonete",
            "van": "Minivan",
            "minivan": "Minivan",
            "conversivel": "Conversível",
            "coupe": "Conversível",
            "cupê": "Conversível"
        }
        
        return mapping.get(segment_lower, None)
    
    def _clean_version(self, versao: str) -> Optional[str]:
        """Limpa a versão removendo informações técnicas redundantes"""
        if not versao:
            return None
        
        # Remove padrões técnicos comuns
        versao_limpa = re.sub(
            r'\b(\d+\.\d+|16V|TB|Flex|Aut\.|Manual|4p|2p)\b', 
            '', 
            versao, 
            flags=re.IGNORECASE
        )
        versao_limpa = re.sub(r'\s+', ' ', versao_limpa).strip()
        
        return versao_limpa if versao_limpa else None
    
    def _extract_motor_info(self, versao: str) -> Optional[str]:
        """Extrai informações do motor da versão"""
        if not versao:
            return None
        
        # Busca padrão de cilindrada (ex: 1.4, 2.0, 1.6)
        motor_match = re.search(r'\b(\d+\.\d+)\b', versao)
        return motor_match.group(1) if motor_match else None
    
    def _extract_photos_motorleads(self, gallery: List) -> List[str]:
        """Extrai fotos da galeria do MotorLeads"""
        if not gallery or not isinstance(gallery, list):
            return []
        
        fotos = []
        for item in gallery:
            if isinstance(item, str):
                fotos.append(item.strip())
            elif isinstance(item, dict):
                # Procura por chaves comuns de URL
                url = item.get("url") or item.get("src") or item.get("link")
                if url:
                    fotos.append(str(url).strip())
        
        return fotos
