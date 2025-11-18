"""Parser para dados do Carburgo (XML)"""

from .base_parser import BaseParser
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

class CarburgoParser(BaseParser):
    """Parser para dados do Carburgo (XML)"""

    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados XML do Carburgo"""
        print(f"DEBUG: can_parse called for {url}")
        print(f"DEBUG: data type: {type(data)}")
        if isinstance(data, dict):
            print(f"DEBUG: data keys: {list(data.keys())}")
            if 'estoque' in data:
                xml_data = data['estoque']
            else:
                return False
        else:
            xml_data = data
        
        if not xml_data:
            return False
        try:
            root = ET.fromstring(xml_data)
        except (ET.ParseError, TypeError) as e:
            print(f"DEBUG: can_parse error: {e}")
            return False
        return root.tag == "estoque"

    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados XML do Carburgo"""
        print(f"DEBUG: Type of data: {type(data)}")
        print(f"DEBUG: Data: {repr(data)}")
        if isinstance(data, dict) and 'estoque' in data:
            xml_data = data['estoque']
        else:
            xml_data = data
        root = ET.fromstring(xml_data)
        vehicles: List[Dict] = []
        for carro in root.findall("carro"):
            placa = carro.findtext("placa", default="")
            modelo = carro.findtext("modelo", default="").strip()
            versao = modelo
            marca = carro.findtext("marca", default=None)
            km_text = carro.findtext("km", default="")
            km = int(km_text) if km_text.isdigit() else None
            ano_text = carro.findtext("ano_modelo") or carro.findtext("ano")
            ano = int(ano_text) if ano_text and ano_text.isdigit() else None
            ano_fab_text = carro.findtext("ano_fabricacao", default=None)
            ano_fab = int(ano_fab_text) if ano_fab_text and ano_fab_text.isdigit() else None
            portas_text = carro.findtext("portas", default="")
            portas = int(portas_text) if portas_text.isdigit() else None
            combustivel = carro.findtext("combustivel", default=None)
            cambio = carro.findtext("cambio", default=None)
            cilindradas_text = carro.findtext("cilindradas", default="")
            cilindrada = int(cilindradas_text) if cilindradas_text.isdigit() else None
            preco_text = carro.findtext("preco", default="")
            preco = self.converter_preco(preco_text)
            cor = carro.findtext("cor", default=None)
            descricao = carro.findtext("descricao", default=None)
            url_item = carro.findtext("url", default=None)
            unidade = carro.findtext("unidade", default=None)

            fotos: List[str] = []
            imagem = carro.findtext("imagem", default="")
            if imagem:
                fotos.append(imagem.strip())
            fotos_node = carro.find("fotos")
            if fotos_node is not None:
                for foto in fotos_node.findall("foto"):
                    if foto.text:
                        fotos.append(foto.text.strip())

            tipo_tag = carro.findtext("tipo", default="")
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
