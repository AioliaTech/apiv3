import requests
import xmltodict
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Importa todos os parsers da pasta fetchers
from fetchers import (
    AltimusParser,
    AutocertoParser,
    AutoconfParser,
    RevendamaisParser, 
    FronteiraParser,
    RevendaproParser,
    ClickGarageParser,
    SimplesVeiculoParser,
    BoomParser
)

# =================== CONFIGURAÇÕES GLOBAIS =======================

JSON_FILE = "data.json"

# =================== PARSERS ADICIONAIS (que não foram migrados ainda) =======================

# Aqui você pode adicionar parsers que ainda não foram migrados para a pasta fetchers
# Mantenha temporariamente até migrar todos

class AutoconfParser:
    """Parser temporário até migrar"""
    def can_parse(self, data: Any, url: str) -> bool:
        return "autoconf" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        # Implementação simplificada - substitua pela implementação completa
        return []

class RevendamaisParser:
    """Parser temporário até migrar"""
    def can_parse(self, data: Any, url: str) -> bool:
        return "revendamais.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        # Implementação simplificada - substitua pela implementação completa
        return []

class FronteiraParser:
    """Parser temporário até migrar"""
    def can_parse(self, data: Any, url: str) -> bool:
        return "fronteiraveiculos.com" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        # Implementação simplificada - substitua pela implementação completa
        return []

class RevendaproParser:
    """Parser temporário até migrar"""
    def can_parse(self, data: Any, url: str) -> bool:
        return "revendapro.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        # Implementação simplificada - substitua pela implementação completa
        return []

class SimplesVeiculoParser:
    """Parser temporário até migrar"""
    def can_parse(self, data: Any, url: str) -> bool:
        return "simplesveiculo.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        # Implementação simplificada - substitua pela implementação completa
        return []

# =================== SISTEMA PRINCIPAL =======================

class UnifiedVehicleFetcher:
    def __init__(self):
        # Inicializa os parsers usando as classes da pasta fetchers
        self.parsers = [
            AltimusParser(),
            AutocertoParser(),
            ClickGarageParser(), 
            BoomParser(),  # BoomParser como fallback
            # Parsers temporários até migrar completamente
            AutoconfParser(),
            RevendamaisParser(),
            FronteiraParser(),
            RevendaproParser(),
            SimplesVeiculoParser()
        ]
        print("[INFO] Sistema unificado iniciado com parsers modularizados")
    
    def get_urls(self) -> List[str]: 
        """Obtém todas as URLs das variáveis de ambiente"""
        return list({val for var, val in os.environ.items() if var.startswith("XML_URL") and val})
    
    def detect_format(self, content: bytes, url: str) -> tuple[Any, str]:
        """Detecta se o conteúdo é JSON ou XML"""
        content_str = content.decode('utf-8', errors='ignore')
        try: 
            return json.loads(content_str), "json"
        except json.JSONDecodeError:
            try: 
                return xmltodict.parse(content_str), "xml"
            except Exception: 
                raise ValueError(f"Formato não reconhecido para URL: {url}")
    
    def select_parser(self, data: Any, url: str) -> Optional[object]:
        """
        Seleciona o parser apropriado baseado na URL
        """
        # Primeira prioridade: seleção baseada na URL
        for parser in self.parsers:
            if parser.can_parse(data, url):
                print(f"[INFO] Parser selecionado: {parser.__class__.__name__}")
                return parser
        
        # Se nenhum parser foi encontrado, usa BoomParser como fallback
        print(f"[AVISO] Nenhum parser específico encontrado para URL: {url}")
        print(f"[INFO] Tentando BoomParser como fallback...")
        
        boom_parser = BoomParser()
        if boom_parser.can_parse(data, url):
            print(f"[INFO] Usando BoomParser como fallback")
            return boom_parser
        
        return None
    
    def process_url(self, url: str) -> List[Dict]:
        """Processa uma URL específica"""
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
        """Executa a coleta de todas as fontes"""
        urls = self.get_urls()
        if not urls:
            print("[AVISO] Nenhuma variável de ambiente 'XML_URL' foi encontrada.")
            return {}
        
        print(f"[INFO] {len(urls)} URL(s) encontrada(s) para processar")
        all_vehicles = [vehicle for url in urls for vehicle in self.process_url(url)]
        
        # Estatísticas por tipo e categoria
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
        """Gera estatísticas dos veículos processados"""
        stats = {
            "por_tipo": {},
            "motos_por_categoria": {},
            "carros_por_categoria": {},
            "top_marcas": {},
            "cilindradas_motos": {},
            "parsers_utilizados": {}
        }
        
        for vehicle in vehicles:
            # Estatísticas por tipo
            tipo = vehicle.get("tipo", "indefinido")
            stats["por_tipo"][tipo] = stats["por_tipo"].get(tipo, 0) + 1
            
            # Estatísticas por categoria
            categoria = vehicle.get("categoria", "indefinido")
            if tipo and "moto" in str(tipo).lower():
                stats["motos_por_categoria"][categoria] = stats["motos_por_categoria"].get(categoria, 0) + 1
                
                # Cilindradas das motos
                cilindrada = vehicle.get("cilindrada")
                if cilindrada:
                    range_key = self._get_cilindrada_range(cilindrada)
                    stats["cilindradas_motos"][range_key] = stats["cilindradas_motos"].get(range_key, 0) + 1
            else:
                stats["carros_por_categoria"][categoria] = stats["carros_por_categoria"].get(categoria, 0) + 1
            
            # Top marcas
            marca = vehicle.get("marca", "indefinido")
            stats["top_marcas"][marca] = stats["top_marcas"].get(marca, 0) + 1
        
        return stats
    
    def _get_cilindrada_range(self, cilindrada: int) -> str:
        """Categoriza cilindradas em faixas"""
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
        """Imprime estatísticas formatadas"""
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
        print(f"Sistema modularizado com parsers individuais!")
        
        if total > 0:
            print(f"\nExemplo dos primeiros 5 veículos:")
            for i, v in enumerate(result['veiculos'][:5], 1):
                tipo = v.get('tipo', 'N/A')
                categoria = v.get('categoria', 'N/A')
                cilindrada = v.get('cilindrada', '')
                cilindrada_str = f" - {cilindrada}cc" if cilindrada else ""
                print(f"{i}. {v.get('marca', 'N/A')} {v.get('modelo', 'N/A')} ({tipo}/{categoria}{cilindrada_str}) {v.get('ano', 'N/A')} - R$ {v.get('preco', 0.0):,.2f}")
