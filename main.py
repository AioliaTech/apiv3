from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from unidecode import unidecode
from rapidfuzz import fuzz
from apscheduler.schedulers.background import BackgroundScheduler
from xml_fetcher import fetch_and_convert_xml
from vehicle_mappings import MAPEAMENTO_CATEGORIAS, MAPEAMENTO_MOTOS
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

app = FastAPI()

# Arquivo para armazenar status da última atualização
STATUS_FILE = "last_update_status.json"

# Configuração de prioridades para fallback (do menos importante para o mais importante)
FALLBACK_PRIORITY = [
    "motor",         # Primeiro a ser removido
    "portas",
    "cor",           
    "combustivel",
    "opcionais",
    "cambio",
    "KmMax",
    "AnoMax",
    "modelo",
    "marca",
    "categoria"         # Mais importante (nunca remove sozinho)
]

@dataclass
class SearchResult:
    """Resultado de uma busca com informações de fallback"""
    vehicles: List[Dict[str, Any]]
    total_found: int
    fallback_info: Dict[str, Any]
    removed_filters: List[str]

class VehicleSearchEngine:
    """Engine de busca de veículos com sistema de fallback inteligente"""
    
    def __init__(self):
        self.exact_fields = ["tipo", "marca", "cambio", "motor", "portas"]

    def _any_csv_value_matches(self, raw_val: str, field_val: str, vehicle_type: str, word_matcher):
        """
        Faz OR entre valores CSV (ex.: "MT,XJ6" → ["MT","XJ6"]).
        word_matcher: função (words:list[str], field_val:str, vehicle_type:str) -> (bool, reason)
        """
        if not raw_val:
            return False
        for val in self.split_multi_value(raw_val):  # "preto,prata escuro" -> ["preto","prata escuro"]
            words = val.split()                      # "prata escuro" -> ["prata","escuro"]
            ok, _ = word_matcher(words, field_val, vehicle_type)
            if ok:
                return True
        return False
        
    def normalize_text(self, text: str) -> str:
        """Normaliza texto para comparação"""
        if not text:
            return ""
        return unidecode(str(text)).lower().replace("-", "").replace(" ", "").strip()
    
    def convert_price(self, price_str: Any) -> Optional[float]:
        """Converte string de preço para float"""
        if not price_str:
            return None
        try:
            # Se já é um número (float/int), retorna diretamente
            if isinstance(price_str, (int, float)):
                return float(price_str)
            
            # Se é string, limpa e converte
            cleaned = str(price_str).replace(",", "").replace("R$", "").replace(".", "").strip()
            return float(cleaned) / 100 if len(cleaned) > 2 else float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def convert_year(self, year_str: Any) -> Optional[int]:
        """Converte string de ano para int"""
        if not year_str:
            return None
        try:
            cleaned = str(year_str).strip().replace('\n', '').replace('\r', '').replace(' ', '')
            return int(cleaned)
        except (ValueError, TypeError):
            return None
    
    def convert_km(self, km_str: Any) -> Optional[int]:
        """Converte string de km para int"""
        if not km_str:
            return None
        try:
            cleaned = str(km_str).replace(".", "").replace(",", "").strip()
            return int(cleaned)
        except (ValueError, TypeError):
            return None
    
    def convert_cc(self, cc_str: Any) -> Optional[float]:
        """Converte string de cilindrada para float"""
        if not cc_str:
            return None
        try:
            # Se já é um número (float/int), retorna diretamente
            if isinstance(cc_str, (int, float)):
                return float(cc_str)
            
            # Se é string, limpa e converte
            cleaned = str(cc_str).replace(",", ".").replace("L", "").replace("l", "").strip()
            # Se o valor for menor que 10, provavelmente está em litros (ex: 1.0, 2.0)
            # Converte para CC multiplicando por 1000
            value = float(cleaned)
            if value < 10:
                return value * 1000
            return value
        except (ValueError, TypeError):
            return None
    
    def get_max_value_from_range_param(self, param_value: str) -> str:
        """Extrai o maior valor de parâmetros de range que podem ter múltiplos valores"""
        if not param_value:
            return param_value
        
        # Se tem vírgula, pega o maior valor
        if ',' in param_value:
            try:
                values = [float(v.strip()) for v in param_value.split(',') if v.strip()]
                if values:
                    return str(max(values))
            except (ValueError, TypeError):
                pass
        
        return param_value
    
    def find_category_by_model(self, model: str) -> Optional[str]:
        """Encontra categoria baseada no modelo usando mapeamento"""
        if not model:
            return None
            
        # Normaliza o modelo para busca
        normalized_model = self.normalize_text(model)
        
        # Busca em motos primeiro (mapeamento mais específico)
        if normalized_model in MAPEAMENTO_MOTOS:
            _, category = MAPEAMENTO_MOTOS[normalized_model]
            return category
        
        # Busca parcial em motos - verifica se alguma palavra do modelo está no mapeamento
        model_words = normalized_model.split()
        for word in model_words:
            if len(word) >= 3 and word in MAPEAMENTO_MOTOS:
                _, category = MAPEAMENTO_MOTOS[word]
                return category
        
        # Busca por substring em motos - verifica se o modelo contém alguma chave do mapeamento
        for key, (_, category) in MAPEAMENTO_MOTOS.items():
            if key in normalized_model or normalized_model in key:
                return category
        
        # Se não encontrou em motos, busca em carros
        # Busca exata primeiro
        if normalized_model in MAPEAMENTO_CATEGORIAS:
            return MAPEAMENTO_CATEGORIAS[normalized_model]
        
        # Busca parcial - verifica se alguma palavra do modelo está no mapeamento
        for word in model_words:
            if len(word) >= 3 and word in MAPEAMENTO_CATEGORIAS:
                return MAPEAMENTO_CATEGORIAS[word]
        
        # Busca por substring - verifica se o modelo contém alguma chave do mapeamento
        for key, category in MAPEAMENTO_CATEGORIAS.items():
            if key in normalized_model or normalized_model in key:
                return category
        
        return None
    
    def exact_match(self, query_words: List[str], field_content: str) -> Tuple[bool, str]:
        """Busca exata: todas as palavras devem estar presentes (substring)"""
        if not query_words or not field_content:
            return False, "empty_input"
            
        normalized_content = self.normalize_text(field_content)
        
        for word in query_words:
            normalized_word = self.normalize_text(word)
            if len(normalized_word) < 2:
                continue
                
            # Deve estar presente como substring
            if normalized_word not in normalized_content:
                return False, f"exact_miss: '{normalized_word}' não encontrado"
        
        return True, f"exact_match: todas as palavras encontradas"
    
    def _fuzzy_match_all_words(self, query_words: List[str], field_content: str, fuzzy_threshold: int) -> Tuple[bool, str]:
        """Para motos: TODAS as palavras da query devem ter match"""
        normalized_content = self.normalize_text(field_content)
        matched_words = []
        match_details = []
        
        for word in query_words:
            normalized_word = self.normalize_text(word)
            if len(normalized_word) < 2:
                continue
                
            word_matched = False
            
            # Match exato (substring)
            if normalized_word in normalized_content:
                matched_words.append(normalized_word)
                match_details.append(f"exact:{normalized_word}")
                word_matched = True
            
            # Match no início da palavra
            elif not word_matched:
                content_words = normalized_content.split()
                for content_word in content_words:
                    if content_word.startswith(normalized_word):
                        matched_words.append(normalized_word)
                        match_details.append(f"starts_with:{normalized_word}")
                        word_matched = True
                        break
            
            # Substring match
            elif not word_matched and len(normalized_word) >= 3:
                content_words = normalized_content.split()
                for content_word in content_words:
                    if normalized_word in content_word:
                        matched_words.append(normalized_word)
                        match_details.append(f"substring:{normalized_word}>{content_word}")
                        word_matched = True
                        break
            
            # Fuzzy match como último recurso
            elif not word_matched and len(normalized_word) >= 3:
                partial_score = fuzz.partial_ratio(normalized_content, normalized_word)
                ratio_score = fuzz.ratio(normalized_content, normalized_word)
                max_score = max(partial_score, ratio_score)
                
                if max_score >= fuzzy_threshold:
                    matched_words.append(normalized_word)
                    match_details.append(f"fuzzy:{normalized_word}({max_score})")
                    word_matched = True
            
            # Se alguma palavra não teve match, falha para motos
            if not word_matched:
                return False, f"moto_strict: palavra '{normalized_word}' não encontrada"
        
        # Todas as palavras tiveram match
        if len(matched_words) >= len([w for w in query_words if len(self.normalize_text(w)) >= 2]):
            return True, f"moto_all_match: {', '.join(match_details)}"
        
        return False, "moto_strict: nem todas as palavras encontradas"
    
    def _fuzzy_match_any_word(self, query_words: List[str], field_content: str, fuzzy_threshold: int) -> Tuple[bool, str]:
        """Para carros: mantém a lógica original (qualquer palavra basta)"""
        normalized_content = self.normalize_text(field_content)
        
        for word in query_words:
            normalized_word = self.normalize_text(word)
            if len(normalized_word) < 2:
                continue
                
            # Match exato (substring)
            if normalized_word in normalized_content:
                return True, f"exact_match: {normalized_word}"
            
            # Match no início da palavra
            content_words = normalized_content.split()
            for content_word in content_words:
                if content_word.startswith(normalized_word):
                    return True, f"starts_with_match: {normalized_word}"
                    
            # Match fuzzy para palavras com 3+ caracteres
            if len(normalized_word) >= 3:
                # Substring match
                for content_word in content_words:
                    if normalized_word in content_word:
                        return True, f"substring_match: {normalized_word} in {content_word}"
                
                # Fuzzy matching tradicional
                partial_score = fuzz.partial_ratio(normalized_content, normalized_word)
                ratio_score = fuzz.ratio(normalized_content, normalized_word)
                max_score = max(partial_score, ratio_score)
                
                if max_score >= fuzzy_threshold:
                    return True, f"fuzzy_match: {max_score} (threshold: {fuzzy_threshold})"
        
        return False, "no_match"
    
    def fuzzy_match(self, query_words: List[str], field_content: str, vehicle_type: str = None) -> Tuple[bool, str]:
        """Verifica se há match fuzzy entre as palavras da query e o conteúdo do campo"""
        if not query_words or not field_content:
            return False, "empty_input"
        
        # Define o threshold baseado no tipo do veículo
        fuzzy_threshold = 98 if vehicle_type == "moto" else 90
        
        # Para motos: exige que TODAS as palavras façam match
        # Para outros veículos: mantém a lógica original (qualquer palavra)
        if vehicle_type == "moto":
            return self._fuzzy_match_all_words(query_words, field_content, fuzzy_threshold)
        else:
            return self._fuzzy_match_any_word(query_words, field_content, fuzzy_threshold)
    
    def model_match(self, query_words: List[str], field_content: str, vehicle_type: str = None) -> Tuple[bool, str]:
        """Busca em três níveis: Exato → Fuzzy → Falha"""
        
        # NÍVEL 1: Busca exata
        exact_result, exact_reason = self.exact_match(query_words, field_content)
        if exact_result:
            return True, f"EXACT: {exact_reason}"
        
        # NÍVEL 2: Busca fuzzy
        fuzzy_result, fuzzy_reason = self.fuzzy_match(query_words, field_content, vehicle_type)
        if fuzzy_result:
            return True, f"FUZZY: {fuzzy_reason}"
        
        # NÍVEL 3: Falha (vai para fallback)
        return False, f"NO_MATCH: exact({exact_reason}) + fuzzy({fuzzy_reason})"
    
    def model_exists_in_database(self, vehicles: List[Dict], model_query: str) -> bool:
        """Verifica se um modelo existe no banco usando busca em três níveis"""
        if not model_query:
            return False
            
        query_words = model_query.split()
        
        for vehicle in vehicles:
            vehicle_type = vehicle.get("tipo", "")
            
            # Verifica nos campos de modelo, titulo e versao
            for field in ["modelo", "titulo", "versao"]:
                field_value = str(vehicle.get(field, ""))
                if field_value:
                    is_match, _ = self.model_match(query_words, field_value, vehicle_type)
                    if is_match:
                        return True
        return False
    
    def split_multi_value(self, value: str) -> List[str]:
        """Divide valores múltiplos separados por vírgula"""
        if not value:
            return []
        return [v.strip() for v in str(value).split(',') if v.strip()]
    
    def apply_filters(self, vehicles: List[Dict], filters: Dict[str, str]) -> List[Dict]:
        """Aplica filtros aos veículos (CSV -> OR por valor)"""
        if not filters:
            return vehicles

        filtered_vehicles = list(vehicles)

        for filter_key, filter_value in filters.items():
            if not filter_value or not filtered_vehicles:
                continue

            if filter_key == "modelo":
                def matches(v):
                    vt = v.get("tipo", "")
                    # tenta em modelo, título e versão (OR entre campos)
                    for field in ["modelo", "titulo", "versao"]:
                        fv = str(v.get(field, ""))
                        if self._any_csv_value_matches(filter_value, fv, vt, self.model_match):
                            return True
                    return False
                filtered_vehicles = [v for v in filtered_vehicles if matches(v)]

            elif filter_key in ["cor", "categoria", "opcionais", "combustivel"]:
                def matches(v):
                    vt = v.get("tipo", "")
                    fv = str(v.get(filter_key, ""))
                    return self._any_csv_value_matches(filter_value, fv, vt, self.fuzzy_match)
                filtered_vehicles = [v for v in filtered_vehicles if matches(v)]

            elif filter_key in self.exact_fields:  # tipo, marca, cambio, motor, portas
                normalized_vals = [self.normalize_text(v) for v in self.split_multi_value(filter_value)]
                filtered_vehicles = [
                    v for v in filtered_vehicles
                    if self.normalize_text(str(v.get(filter_key, ""))) in normalized_vals
                ]

        return filtered_vehicles

    
    def apply_range_filters(self, vehicles: List[Dict], valormax: Optional[str], 
                          anomax: Optional[str], kmmax: Optional[str], ccmax: Optional[str]) -> List[Dict]:
        """Aplica filtros de faixa"""
        filtered_vehicles = list(vehicles)
        
        # Filtro de valor máximo - sem expansão, ranqueia por proximidade
        if valormax:
            try:
                target_price = float(valormax)
                # Não aplica filtro de teto aqui, apenas prepara para ranqueamento
            except ValueError:
                pass
        
        # Filtro de ano máximo - como teto (não ranqueia)
        if anomax:
            try:
                max_year = int(anomax)
                filtered_vehicles = [
                    v for v in filtered_vehicles
                    if self.convert_year(v.get("ano")) is not None and
                    self.convert_year(v.get("ano")) <= max_year
                ]
            except ValueError:
                pass
        
        # Filtro de km máximo - como teto (não ranqueia)
        if kmmax:
            try:
                max_km = int(kmmax)
                filtered_vehicles = [
                    v for v in filtered_vehicles
                    if self.convert_km(v.get("km")) is not None and
                    self.convert_km(v.get("km")) <= max_km
                ]
            except ValueError:
                pass
        
        # Filtro de cilindrada - sem teto, ranqueia por proximidade
        if ccmax:
            try:
                target_cc = float(ccmax)
                # Converte para CC se necessário (valores < 10 são assumidos como litros)
                if target_cc < 10:
                    target_cc *= 1000
                # Não aplica filtro de teto aqui, apenas prepara para ranqueamento
            except ValueError:
                pass
        
        return filtered_vehicles
    
    def sort_vehicles(self, vehicles: List[Dict], valormax: Optional[str], 
                     anomax: Optional[str], kmmax: Optional[str], ccmax: Optional[str]) -> List[Dict]:
        """Ordena veículos baseado nos filtros aplicados"""
        if not vehicles:
            return vehicles
        
        # Prioridade 1: Se tem CcMax, ordena por proximidade da cilindrada
        if ccmax:
            try:
                target_cc = float(ccmax)
                # Converte para CC se necessário (valores < 10 são assumidos como litros)
                if target_cc < 10:
                    target_cc *= 1000
                    
                return sorted(vehicles, key=lambda v: 
                    abs((self.convert_cc(v.get("cilindrada")) or 0) - target_cc))
            except ValueError:
                pass
        
        # Prioridade 2: Se tem ValorMax, ordena por proximidade do valor
        if valormax:
            try:
                target_price = float(valormax)
                return sorted(vehicles, key=lambda v: 
                    abs((self.convert_price(v.get("preco")) or 0) - target_price))
            except ValueError:
                pass
        
        # Prioridade 3: Se tem KmMax, ordena por KM crescente
        if kmmax:
            return sorted(vehicles, key=lambda v: self.convert_km(v.get("km")) or float('inf'))
        
        # Prioridade 4: Se tem AnoMax, ordena por ano decrescente (mais novos primeiro)
        if anomax:
            return sorted(vehicles, key=lambda v: self.convert_year(v.get("ano")) or 0, reverse=True)
        
        # Ordenação padrão: por preço decrescente
        return sorted(vehicles, key=lambda v: self.convert_price(v.get("preco")) or 0, reverse=True)
    
    def search_with_fallback(self, vehicles: List[Dict], filters: Dict[str, str],
                            valormax: Optional[str], anomax: Optional[str], kmmax: Optional[str],
                            ccmax: Optional[str], excluded_ids: set) -> SearchResult:
        """Executa busca com fallback progressivo seguindo FALLBACK_PRIORITY"""
        
        # Primeira tentativa: busca normal
        filtered_vehicles = self.apply_filters(vehicles, filters)
        filtered_vehicles = self.apply_range_filters(filtered_vehicles, valormax, anomax, kmmax, ccmax)
        
        if excluded_ids:
            filtered_vehicles = [
                v for v in filtered_vehicles
                if str(v.get("id")) not in excluded_ids
            ]
        
        if filtered_vehicles:
            sorted_vehicles = self.sort_vehicles(filtered_vehicles, valormax, anomax, kmmax, ccmax)
            return SearchResult(
                vehicles=sorted_vehicles[:6],
                total_found=len(sorted_vehicles),
                fallback_info={},
                removed_filters=[]
            )
        
        # Se não encontrou, inicia fallback
        current_filters = dict(filters)
        removed_filters = []
        current_valormax = valormax
        current_anomax = anomax
        current_kmmax = kmmax
        current_ccmax = ccmax
        
        for filter_to_remove in FALLBACK_PRIORITY:
            if filter_to_remove == "KmMax" and current_kmmax:
                test_vehicles = self.apply_filters(vehicles, current_filters)
                vehicles_within_km_limit = [
                    v for v in test_vehicles
                    if self.convert_km(v.get("km")) is not None and
                    self.convert_km(v.get("km")) <= int(current_kmmax)
                ]
                
                if not vehicles_within_km_limit:
                    current_kmmax = None
                    removed_filters.append("KmMax")
                else:
                    continue
                    
            elif filter_to_remove == "AnoMax" and current_anomax:
                test_vehicles = self.apply_filters(vehicles, current_filters)
                vehicles_within_year_limit = [
                    v for v in test_vehicles
                    if self.convert_year(v.get("ano")) is not None and
                    self.convert_year(v.get("ano")) <= int(current_anomax)
                ]
                
                if not vehicles_within_year_limit:
                    current_anomax = None
                    removed_filters.append("AnoMax")
                else:
                    continue
                    
            elif filter_to_remove == "modelo" and filter_to_remove in current_filters:
                model_value = current_filters["modelo"]
                
                # Quando for a vez do modelo, converte imediatamente para categoria
                if "categoria" not in current_filters or not current_filters["categoria"]:
                    mapped_category = self.find_category_by_model(model_value)
                    if mapped_category:
                        current_filters = {k: v for k, v in current_filters.items() if k != "modelo"}
                        current_filters["categoria"] = mapped_category
                        removed_filters.append(f"modelo({model_value})->categoria({mapped_category})")
                        
                        filtered_vehicles = self.apply_filters(vehicles, current_filters)
                        filtered_vehicles = self.apply_range_filters(filtered_vehicles, current_valormax, current_anomax, current_kmmax, current_ccmax)
                        
                        if excluded_ids:
                            filtered_vehicles = [v for v in filtered_vehicles if str(v.get("id")) not in excluded_ids]
                        
                        if filtered_vehicles:
                            sorted_vehicles = self.sort_vehicles(filtered_vehicles, current_valormax, current_anomax, current_kmmax, current_ccmax)
                            return SearchResult(
                                vehicles=sorted_vehicles[:6],
                                total_found=len(sorted_vehicles),
                                fallback_info={"fallback": {"removed_filters": removed_filters}},
                                removed_filters=removed_filters
                            )
                    else:
                        # Se não mapeia, remove modelo normal
                        current_filters = {k: v for k, v in current_filters.items() if k != "modelo"}
                        removed_filters.append(f"modelo({model_value})")
                else:
                    # Se já tem categoria, remove modelo normal
                    current_filters = {k: v for k, v in current_filters.items() if k != "modelo"}
                    removed_filters.append(f"modelo({model_value})")
                    
            elif filter_to_remove in current_filters:
                # Remove filtro comum
                current_filters = {k: v for k, v in current_filters.items() if k != filter_to_remove}
                removed_filters.append(filter_to_remove)
            else:
                continue
            
            # Testa busca após remoção
            filtered_vehicles = self.apply_filters(vehicles, current_filters)
            filtered_vehicles = self.apply_range_filters(filtered_vehicles, current_valormax, current_anomax, current_kmmax, current_ccmax)
            
            if excluded_ids:
                filtered_vehicles = [
                    v for v in filtered_vehicles
                    if str(v.get("id")) not in excluded_ids
                ]
            
            if filtered_vehicles:
                sorted_vehicles = self.sort_vehicles(filtered_vehicles, current_valormax, current_anomax, current_kmmax, current_ccmax)
                return SearchResult(
                    vehicles=sorted_vehicles[:6],
                    total_found=len(sorted_vehicles),
                    fallback_info={"fallback": {"removed_filters": removed_filters}},
                    removed_filters=removed_filters
                )
        
        # Nenhum resultado
        return SearchResult(
            vehicles=[],
            total_found=0,
            fallback_info={},
            removed_filters=removed_filters
        )

# Instância global do motor de busca
search_engine = VehicleSearchEngine()

def save_update_status(success: bool, message: str = "", vehicle_count: int = 0):
    """Salva o status da última atualização"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "message": message,
        "vehicle_count": vehicle_count
    }
    
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar status: {e}")

def get_update_status() -> Dict:
    """Recupera o status da última atualização"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Erro ao ler status: {e}")
    
    return {
        "timestamp": None,
        "success": False,
        "message": "Nenhuma atualização registrada",
        "vehicle_count": 0
    }

def wrapped_fetch_and_convert_xml():
    """Wrapper para fetch_and_convert_xml com logging de status"""
    try:
        print("Iniciando atualização dos dados...")
        fetch_and_convert_xml()
        
        # Verifica quantos veículos foram carregados
        vehicle_count = 0
        if os.path.exists("data.json"):
            try:
                with open("data.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    vehicle_count = len(data.get("veiculos", []))
            except:
                pass
        
        save_update_status(True, "Dados atualizados com sucesso", vehicle_count)
        print(f"Atualização concluída: {vehicle_count} veículos carregados")
        
    except Exception as e:
        error_message = f"Erro na atualização: {str(e)}"
        save_update_status(False, error_message)
        print(error_message)

@app.on_event("startup")
def schedule_tasks():
    """Agenda tarefas de atualização de dados"""
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")
    
    # Executa a cada 2 horas
    scheduler.add_job(wrapped_fetch_and_convert_xml, "interval", hours=2)
    
    scheduler.start()
    wrapped_fetch_and_convert_xml()  # Executa uma vez na inicialização

@app.get("/list")
def list_vehicles(request: Request):
    """Endpoint que lista todos os veículos organizados por categoria"""
    
    # Verifica se o arquivo de dados existe
    if not os.path.exists("data.json"):
        return JSONResponse(
            content={"error": "Nenhum dado disponível"},
            status_code=404
        )
    
    # Carrega os dados
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        vehicles = data.get("veiculos", [])
        if not isinstance(vehicles, list):
            raise ValueError("Formato inválido: 'veiculos' deve ser uma lista")
            
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        return JSONResponse(
            content={"error": f"Erro ao carregar dados: {str(e)}"},
            status_code=500
        )
    
    # Extrai parâmetros de filtro da query
    query_params = dict(request.query_params)
    filter_categoria = query_params.get("categoria")
    filter_tipo = query_params.get("tipo")
    
    # Aplica filtros se especificados
    filtered_vehicles = vehicles
    
    if filter_categoria:
        filtered_vehicles = [
            v for v in filtered_vehicles 
            if v.get("categoria") and filter_categoria.lower() in v.get("categoria", "").lower()
        ]
    
    if filter_tipo:
        filtered_vehicles = [
            v for v in filtered_vehicles 
            if v.get("tipo") and filter_tipo.lower() in v.get("tipo", "").lower()
        ]
    
    # Organiza veículos por categoria
    categorized_vehicles = {}
    nao_mapeados = []
    
    for vehicle in filtered_vehicles:
        categoria = vehicle.get("categoria")
        
        # Se não tem categoria, vai para "não mapeados"
        if not categoria or categoria in ["", "None", None]:
            nao_mapeados.append(_format_vehicle(vehicle))
            continue
        
        # Cria a categoria se não existe
        if categoria not in categorized_vehicles:
            categorized_vehicles[categoria] = []
        
        # Formata o veículo baseado no tipo
        formatted_vehicle = _format_vehicle(vehicle)
        categorized_vehicles[categoria].append(formatted_vehicle)
    
    # Monta resposta final ordenando por categoria
    result = {}
    
    # Adiciona categorias ordenadas alfabeticamente
    for categoria in sorted(categorized_vehicles.keys()):
        result[categoria] = categorized_vehicles[categoria]
    
    # Adiciona não mapeados no final se houver
    if nao_mapeados:
        result["NÃO MAPEADOS"] = nao_mapeados
    
    return JSONResponse(content=result)

def _format_vehicle(vehicle: Dict) -> str:
    """Formata um veículo conforme especificado"""
    tipo = vehicle.get("tipo", "").lower()
    
    # Função auxiliar para tratar valores None/vazios
    def safe_value(value):
        if value is None or value == "":
            return ""
        return str(value)
    
    # Se for moto: id,tipo,marca,modelo,versao,cor,ano,km,combustivel,cambio,cilindrada,portas,preco
    if "moto" in tipo:
        return ",".join([
            safe_value(vehicle.get("id")),
            safe_value(vehicle.get("tipo")),
            safe_value(vehicle.get("marca")),
            safe_value(vehicle.get("modelo")),
            safe_value(vehicle.get("versao")),
            safe_value(vehicle.get("cor")),
            safe_value(vehicle.get("ano")),
            safe_value(vehicle.get("km")),
            safe_value(vehicle.get("combustivel")),
            safe_value(vehicle.get("cilindrada")),
            safe_value(vehicle.get("preco"))
        ])
    
    # Se for carro: id,tipo,marca,modelo,versao,cor,ano,km,combustivel,cambio,motor,portas,preco
    else:
        return ",".join([
            safe_value(vehicle.get("id")),
            safe_value(vehicle.get("tipo")),
            safe_value(vehicle.get("marca")),
            safe_value(vehicle.get("modelo")),
            safe_value(vehicle.get("versao")),
            safe_value(vehicle.get("cor")),
            safe_value(vehicle.get("ano")),
            safe_value(vehicle.get("km")),
            safe_value(vehicle.get("combustivel")),
            safe_value(vehicle.get("cambio")),
            safe_value(vehicle.get("motor")),
            safe_value(vehicle.get("portas")),
            safe_value(vehicle.get("preco"))
        ])

@app.get("/api/data")
def get_data(request: Request):
    """Endpoint principal para busca de veículos"""
    
    # Verifica se o arquivo de dados existe
    if not os.path.exists("data.json"):
        return JSONResponse(
            content={
                "error": "Nenhum dado disponível",
                "resultados": [],
                "total_encontrado": 0
            },
            status_code=404
        )
    
    # Carrega os dados
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        vehicles = data.get("veiculos", [])
        if not isinstance(vehicles, list):
            raise ValueError("Formato inválido: 'veiculos' deve ser uma lista")
            
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        return JSONResponse(
            content={
                "error": f"Erro ao carregar dados: {str(e)}",
                "resultados": [],
                "total_encontrado": 0
            },
            status_code=500
        )
    
    # Extrai parâmetros da query
    query_params = dict(request.query_params)
    
    # Parâmetros especiais - aplica "pegar maior valor" para campos de range
    valormax = search_engine.get_max_value_from_range_param(query_params.pop("ValorMax", None))
    anomax = search_engine.get_max_value_from_range_param(query_params.pop("AnoMax", None))
    kmmax = search_engine.get_max_value_from_range_param(query_params.pop("KmMax", None))
    ccmax = search_engine.get_max_value_from_range_param(query_params.pop("CcMax", None))
    simples = query_params.pop("simples", None)
    excluir = query_params.pop("excluir", None)
    
    # Parâmetro especial para busca por ID
    id_param = query_params.pop("id", None)
    
    # Filtros principais
    filters = {
        "tipo": query_params.get("tipo"),
        "modelo": query_params.get("modelo"),
        "categoria": query_params.get("categoria"),
        "cambio": query_params.get("cambio"),
        "opcionais": query_params.get("opcionais"),
        "marca": query_params.get("marca"),
        "cor": query_params.get("cor"),
        "combustivel": query_params.get("combustivel"),
        "motor": query_params.get("motor"),
        "portas": query_params.get("portas")
    }
    
    # Remove filtros vazios
    filters = {k: v for k, v in filters.items() if v}
    
    # BUSCA POR ID ESPECÍFICO - tem prioridade sobre tudo
    if id_param:
        vehicle_found = None
        for vehicle in vehicles:
            if str(vehicle.get("id")) == str(id_param):
                vehicle_found = vehicle
                break
        
        if vehicle_found:
            # Aplica modo simples se solicitado - CORRIGIDO
            if simples == "1":
                fotos = vehicle_found.get("fotos")
                if isinstance(fotos, list) and len(fotos) > 0:
                    # Estrutura simples ["foto1", "foto2", ...] - seu caso
                    if isinstance(fotos[0], str):
                        vehicle_found["fotos"] = [fotos[0]]  # Mantém só a primeira foto
                    # Estrutura aninhada [["foto1", "foto2", ...]]
                    elif isinstance(fotos[0], list) and len(fotos[0]) > 0:
                        vehicle_found["fotos"] = [[fotos[0][0]]]  # Mantém estrutura aninhada
                    else:
                        vehicle_found["fotos"] = []
                else:
                    vehicle_found["fotos"] = []
            
            # Remove opcionais se não foi pesquisado por opcionais OU por ID
            if "opcionais" not in filters and not id_param and "opcionais" in vehicle_found:
                del vehicle_found["opcionais"]
            
            return JSONResponse(content={
                "resultados": [vehicle_found],
                "total_encontrado": 1,
                "info": f"Veículo encontrado por ID: {id_param}"
            })
        else:
            return JSONResponse(content={
                "resultados": [],
                "total_encontrado": 0,
                "error": f"Veículo com ID {id_param} não encontrado"
            })
    
    # Verifica se há filtros de busca reais (exclui parâmetros especiais)
    has_search_filters = bool(filters) or valormax or anomax or kmmax or ccmax
    
    # Processa IDs a excluir
    excluded_ids = set()
    if excluir:
        excluded_ids = set(e.strip() for e in excluir.split(",") if e.strip())
    
    # Se não há filtros de busca, retorna todo o estoque
    if not has_search_filters:
        all_vehicles = list(vehicles)
        
        # Remove IDs excluídos se especificado
        if excluded_ids:
            all_vehicles = [
                v for v in all_vehicles
                if str(v.get("id")) not in excluded_ids
            ]
        
        # Ordena por preço decrescente (padrão)
        sorted_vehicles = sorted(all_vehicles, key=lambda v: search_engine.convert_price(v.get("preco")) or 0, reverse=True)
        
        # Aplica modo simples se solicitado - CORRIGIDO
        if simples == "1":
            for vehicle in sorted_vehicles:
                fotos = vehicle.get("fotos")
                if isinstance(fotos, list) and len(fotos) > 0:
                    # Estrutura simples ["foto1", "foto2", ...] - seu caso
                    if isinstance(fotos[0], str):
                        vehicle["fotos"] = [fotos[0]]  # Mantém só a primeira foto
                    # Estrutura aninhada [["foto1", "foto2", ...]]
                    elif isinstance(fotos[0], list) and len(fotos[0]) > 0:
                        vehicle["fotos"] = [[fotos[0][0]]]  # Mantém estrutura aninhada
                    else:
                        vehicle["fotos"] = []
                else:
                    vehicle["fotos"] = []
        
        # Remove opcionais se não foi pesquisado por opcionais OU por ID
        if "opcionais" not in filters and not id_param:
            for vehicle in sorted_vehicles:
                if "opcionais" in vehicle:
                    del vehicle["opcionais"]
        
        return JSONResponse(content={
            "resultados": sorted_vehicles,
            "total_encontrado": len(sorted_vehicles),
            "info": "Exibindo todo o estoque disponível"
        })
    
    # Executa a busca com fallback
    result = search_engine.search_with_fallback(
        vehicles, filters, valormax, anomax, kmmax, ccmax, excluded_ids
    )
    
    # Aplica modo simples se solicitado - CORRIGIDO
    if simples == "1" and result.vehicles:
        for vehicle in result.vehicles:
            fotos = vehicle.get("fotos")
            if isinstance(fotos, list) and len(fotos) > 0:
                # Estrutura simples ["foto1", "foto2", ...] - seu caso
                if isinstance(fotos[0], str):
                    vehicle["fotos"] = [fotos[0]]  # Mantém só a primeira foto
                # Estrutura aninhada [["foto1", "foto2", ...]]
                elif isinstance(fotos[0], list) and len(fotos[0]) > 0:
                    vehicle["fotos"] = [[fotos[0][0]]]  # Mantém estrutura aninhada
                else:
                    vehicle["fotos"] = []
            else:
                vehicle["fotos"] = []
    
    # Remove opcionais se não foi pesquisado por opcionais OU por ID
    if "opcionais" not in filters and not id_param and result.vehicles:
        for vehicle in result.vehicles:
            if "opcionais" in vehicle:
                del vehicle["opcionais"]
    
    # Monta resposta
    response_data = {
        "resultados": result.vehicles,
        "total_encontrado": result.total_found
    }
    
    # Adiciona informações de fallback apenas se houver filtros removidos
    if result.fallback_info:
        response_data.update(result.fallback_info)
    
    # Mensagem especial se não encontrou nada
    if result.total_found == 0:
        response_data["instrucao_ia"] = (
            "Não encontramos veículos com os parâmetros informados "
            "e também não encontramos opções próximas."
        )
    
    return JSONResponse(content=response_data)

@app.get("/api/health")
def health_check():
    """Endpoint de verificação de saúde"""
    return {"status": "healthy", "timestamp": "2025-07-13"}

@app.get("/api/status")
def get_status():
    """Endpoint para verificar status da última atualização dos dados"""
    status = get_update_status()
    
    # Informações adicionais sobre os arquivos
    data_file_exists = os.path.exists("data.json")
    data_file_size = 0
    data_file_modified = None
    
    if data_file_exists:
        try:
            stat = os.stat("data.json")
            data_file_size = stat.st_size
            data_file_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except:
            pass
    
    return {
        "last_update": status,
        "data_file": {
            "exists": data_file_exists,
            "size_bytes": data_file_size,
            "modified_at": data_file_modified
        },
        "current_time": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
