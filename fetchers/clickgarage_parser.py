"""
Parser específico para ClickGarage (clickgarage.com.br)
"""

from .base_parser import BaseParser
from typing import Dict, List, Any, Tuple, Optional
import re

class ClickGarageParser(BaseParser):
    """Parser para dados do ClickGarage"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do ClickGarage"""
        return "clickgarage.com.br" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do ClickGarage"""
        estoque = data.get("estoque", {})
        veiculos = estoque.get("veiculo", [])
        
        # Normaliza para lista se for um único veículo
        if isinstance(veiculos, dict):
            veiculos = [veiculos]
        
        parsed_vehicles = []
        
        for v in veiculos:
            if not isinstance(v, dict):
                continue
            
            # Extrai marca e modelo do campo composto
            marca_modelo = v.get("marca", "")
            modelo_completo = v.get("modelo", "")
            
            # Separa marca do modelo
            marca_final, modelo_final = self._extract_marca_modelo(marca_modelo, modelo_completo)
            
            # Processa opcionais
            opcionais_processados = self._parse_opcionais_clickgarage(v.get("opcionais", {}))
            
            # Determina se é moto ou carro
            tipo_veiculo = v.get("tipo", "").lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto:
                # Para motos: usa o sistema com modelo E versão
                cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(modelo_final, "")
                tipo_final = "moto"
            else:
                # Para carros: usa o sistema existente
                categoria_final = self.definir_categoria_veiculo(modelo_final, opcionais_processados)
                cilindrada_final = None
                tipo_final = "carro"
            
            # Extrai informações do motor da versão/modelo
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
                "portas": None,  # ClickGarage não fornece esse campo explicitamente
                "categoria": categoria_final,
                "cilindrada": cilindrada_final,
                "preco": self.converter_preco(v.get("preco")),
                "opcionais": opcionais_processados,
                "fotos": self._extract_photos_clickgarage(v)
            })
            
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
    
    def _extract_marca_modelo(self, marca_campo: str, modelo_completo: str) -> Tuple[str, str]:
        """
        Extrai marca e modelo dos campos compostos do ClickGarage
        Exemplo: marca="GM - Chevrolet", modelo="CRUZE Premier 1.4 16V TB Flex Aut."
        """
        # Limpa e processa o campo marca
        if marca_campo:
            # Remove prefixos como "GM - " e pega a marca principal
            marca_parts = marca_campo.split(" - ")
            marca_final = marca_parts[-1].strip() if marca_parts else marca_campo.strip()
        else:
            marca_final = ""
        
        # Extrai o modelo base (primeira palavra geralmente)
        if modelo_completo:
            modelo_words = modelo_completo.strip().split()
            modelo_final = modelo_words[0] if modelo_words else modelo_completo
        else:
            modelo_final = ""
        
        return marca_final, modelo_final
    
    def _parse_opcionais_clickgarage(self, opcionais: Dict) -> str:
        """
        Processa os opcionais do ClickGarage convertendo as chaves em texto legível
        Exemplo: <Farol-de-led>sim</Farol-de-led> -> "Farol de led"
        """
        if not isinstance(opcionais, dict):
            return ""
        
        opcionais_list = []
        
        for chave, valor in opcionais.items():
            # Só inclui se o valor for "sim"
            if str(valor).lower() == "sim":
                # Converte a chave: remove hífens, capitaliza primeira letra
                opcional_nome = chave.replace("-", " ").lower()
                # Capitaliza a primeira letra
                opcional_nome = opcional_nome.capitalize()
                opcionais_list.append(opcional_nome)
        
        return ", ".join(opcionais_list)
    
    def _extract_photos_clickgarage(self, veiculo: Dict) -> List[str]:
        """
        Extrai todas as fotos do veículo ClickGarage
        Campos: imagem_principal, foto2, foto3, ..., foto9
        """
        fotos = []
        
        # Imagem principal
        if img_principal := veiculo.get("imagem_principal"):
            fotos.append(img_principal.strip())
        
        # Fotos numeradas (foto2 até foto9, ou mais se houver)
        for i in range(2, 20):  # Verifica até foto19 por segurança
            foto_key = f"foto{i}"
            if foto_url := veiculo.get(foto_key):
                fotos.append(foto_url.strip())
        
        return fotos
    
    def _clean_version(self, modelo_completo: str) -> str:
        """
        Limpa a versão removendo informações técnicas redundantes
        """
        if not modelo_completo:
            return ""
        
        # Remove padrões técnicos comuns
        versao_limpa = re.sub(r'\b(\d+\.\d+|16V|TB|Flex|Aut\.|Manual|4p|2p)\b', '', modelo_completo, flags=re.IGNORECASE)
        # Remove espaços extras
        versao_limpa = re.sub(r'\s+', ' ', versao_limpa).strip()
        
        return versao_limpa
    
    def _extract_motor_info(self, modelo_completo: str) -> Optional[str]:
        """
        Extrai informações do motor do modelo completo
        Exemplo: "CRUZE Premier 1.4 16V TB Flex Aut." -> "1.4"
        """
        if not modelo_completo:
            return None
        
        # Busca padrão de cilindrada (ex: 1.4, 2.0, 1.6)
        motor_match = re.search(r'\b(\d+\.\d+)\b', modelo_completo)
        return motor_match.group(1) if motor_match else None
    
    def _extract_cambio_info(self, modelo_completo: str) -> Optional[str]:
        """
        Extrai informações do câmbio do modelo completo
        """
        if not modelo_completo:
            return None
        
        modelo_lower = modelo_completo.lower()
        
        if "aut" in modelo_lower:
            return "automatico"
        elif "manual" in modelo_lower:
            return "manual"
        
        return None
