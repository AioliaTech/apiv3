"""Parser para dados do Carburgo (XML)"""

from .base_parser import BaseParser
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

class CarburgoParser(BaseParser):
    """Parser para dados do Carburgo (XML)"""

    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados XML do Carburgo"""
        if not url:
            return False
        return "citroenpremiere.com.br" in url.lower()

    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados XML do Carburgo"""
        if isinstance(data, dict):
            # Assume data is parsed XML dict
            estoque = data.get('estoque')
            if not estoque:
                return []
            
            carros = estoque.get('carro')
            if not carros:
                return []
                
            if not isinstance(carros, list):
                carros = [carros]
                
            vehicles = []
            for carro in carros:
                if not isinstance(carro, dict):
                    continue
                
                placa = str(carro.get("placa") or "")
                modelo = str(carro.get("modelo") or "").strip()
                versao = modelo
                marca = carro.get("marca") or None
                
                km_text = str(carro.get("km") or "")
                km = int(km_text) if km_text.isdigit() else None
                
                ano_text = str(carro.get("ano_modelo") or carro.get("ano") or "")
                ano = int(ano_text) if ano_text.isdigit() else None
                
                ano_fab_text = str(carro.get("ano_fabricacao") or "")
                ano_fab = int(ano_fab_text) if ano_fab_text.isdigit() else None
                
                portas_text = str(carro.get("portas") or "")
                portas = int(portas_text) if portas_text.isdigit() else None
                
                combustivel = carro.get("combustivel")
                cambio = carro.get("cambio")
                
                cilindradas_text = str(carro.get("cilindradas") or "")
                cilindrada = int(cilindradas_text) if cilindradas_text.isdigit() else None
                
                preco_text = str(carro.get("preco") or "")
                preco = self.converter_preco(preco_text)
                
                cor = carro.get("cor")
                descricao = carro.get("descricao")
                url_item = carro.get("url")
                unidade = carro.get("unidade")

                fotos = []
                imagem = str(carro.get("imagem") or "")
                if imagem:
                    fotos.append(imagem.strip())
                    
                fotos_node = carro.get("fotos")
                if isinstance(fotos_node, dict) and "foto" in fotos_node:
                    foto_list = fotos_node["foto"]
                    if isinstance(foto_list, list):
                        for foto in foto_list:
                            if foto:
                                fotos.append(str(foto).strip())
                    elif isinstance(foto_list, str):
                        fotos.append(foto_list.strip())
                    elif foto_list:
                        fotos.append(str(foto_list).strip())

                tipo_tag = str(carro.get("tipo") or "")
                is_moto = "moto" in tipo_tag.lower()
                tipo_final = "moto" if is_moto else "carro"
                categoria = tipo_tag if is_moto else None

                parsed = self.normalize_vehicle({
                    "id": "".join(d for i, d in enumerate(placa) if i in [1, 2, 3, 5, 6]),
                    "tipo": tipo_final,
                    "titulo": None,
                    "versao": versao,
                    "marca": marca,
                    "modelo": modelo,
                    "ano": ano,
                    "ano_fabricacao": ano_fab,
                    "km": km,
                    "cor": cor,
                    "combustivel": combustivel,
                    "cambio": cambio,
                    "motor": None,
                    "portas": portas,
                    "categoria": categoria,
                    "cilindrada": cilindrada,
                    "preco": preco,
                    "opcionais": None,
                    "fotos": fotos,
                    "url": url_item,
                    "unidade": unidade,
                    "descricao": descricao,
                })
                vehicles.append(parsed)
            return vehicles
        else:
            # Original XML parsing
            if not data:
                return []
            try:
                root = ET.fromstring(data)
            except (ET.ParseError, TypeError):
                return []
                
            vehicles = []
            for carro in root.findall("carro"):
                placa = carro.findtext("placa") or ""
                modelo = (carro.findtext("modelo") or "").strip()
                versao = modelo
                marca = carro.findtext("marca") or None
                
                km_text = carro.findtext("km") or ""
                km = int(km_text) if km_text.isdigit() else None
                
                ano_text = carro.findtext("ano_modelo") or carro.findtext("ano") or ""
                ano = int(ano_text) if ano_text.isdigit() else None
                
                ano_fab_text = carro.findtext("ano_fabricacao") or ""
                ano_fab = int(ano_fab_text) if ano_fab_text.isdigit() else None
                
                portas_text = carro.findtext("portas") or ""
                portas = int(portas_text) if portas_text.isdigit() else None
                
                combustivel = carro.findtext("combustivel")
                cambio = carro.findtext("cambio")
                
                cilindradas_text = carro.findtext("cilindradas") or ""
                cilindrada = int(cilindradas_text) if cilindradas_text.isdigit() else None
                
                preco_text = carro.findtext("preco") or ""
                preco = self.converter_preco(preco_text)
                
                cor = carro.findtext("cor")
                descricao = carro.findtext("descricao")
                url_item = carro.findtext("url")
                unidade = carro.findtext("unidade")

                fotos = []
                imagem = carro.findtext("imagem") or ""
                if imagem:
                    fotos.append(imagem.strip())
                fotos_node = carro.find("fotos")
                if fotos_node is not None:
                    for foto in fotos_node.findall("foto"):
                        if foto.text:
                            fotos.append(foto.text.strip())

                tipo_tag = carro.findtext("tipo") or ""
                is_moto = "moto" in tipo_tag.lower()
                tipo_final = "moto" if is_moto else "carro"
                categoria = tipo_tag if not is_moto else None

                parsed = self.normalize_vehicle({
                    "id": "".join(d for i, d in enumerate(placa) if i in [1, 2, 3, 5, 6]),
                    "tipo": tipo_final,
                    "titulo": None,
                    "versao": versao,
                    "marca": marca,
                    "modelo": modelo,
                    "ano": ano,
                    "ano_fabricacao": ano_fab,
                    "km": km,
                    "cor": cor,
                    "combustivel": combustivel,
                    "cambio": cambio,
                    "motor": None,
                    "portas": portas,
                    "categoria": categoria,
                    "cilindrada": cilindrada,
                    "preco": preco,
                    "opcionais": None,
                    "fotos": fotos,
                    "url": url_item,
                    "unidade": unidade,
                    "descricao": descricao,
                })
                vehicles.append(parsed)
            return vehicles
