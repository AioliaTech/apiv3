"""
Parser específico para DSAutoEstoque (dsautoestoque.com) - VERSÃO CORRIGIDA
"""
from .base_parser import BaseParser
from typing import Dict, List, Any
import xml.etree.ElementTree as ET

class DSAutoEstoqueParser(BaseParser):
    """Parser para dados do DSAutoEstoque"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Verifica se pode processar dados do DSAutoEstoque"""
        return "dsautoestoque.com" in url.lower()
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do DSAutoEstoque"""
        try:
            # Se data for string XML, parse primeiro
            if isinstance(data, str):
                # Limpa possíveis caracteres problemáticos
                data_clean = data.strip()
                if data_clean.startswith('<?xml'):
                    # Remove declaração XML se presente para evitar problemas de encoding
                    lines = data_clean.split('\n')
                    if lines[0].startswith('<?xml'):
                        data_clean = '\n'.join(lines[1:])
                
                root = ET.fromstring(data_clean)
            else:
                root = data
                
        except ET.ParseError as e:
            print(f"Erro ao fazer parse do XML: {e}")
            print(f"Primeiros 500 caracteres do XML: {str(data)[:500]}")
            raise ValueError(f"Erro ao fazer parse do XML: {e}")
        
        parsed_vehicles = []
        
        # Debug: Verificar estrutura do XML
        print(f"Root tag: {root.tag}")
        veiculos = root.findall('.//veiculo')
        print(f"Encontrados {len(veiculos)} veículos")
        
        for v in veiculos:
            try:
                # Extrai dados básicos
                id_veiculo = self._get_text(v, 'id')
                tipo_veiculo = self._get_text(v, 'tipoveiculo')
                zero_km = self._get_text(v, 'zerokm') == 'S'
                placa = self._get_text(v, 'placa')
                marca = self._get_text(v, 'marca')
                modelo = self._get_text(v, 'modelo')
                versao = self._get_text(v, 'versao')
                ano_fabricacao = self._get_text(v, 'anofabricacao')
                ano_modelo = self._get_text(v, 'anomodelo')
                cambio = self._get_text(v, 'cambio')
                km = self._get_text(v, 'km')
                portas = self._get_text(v, 'portas')
                cor = self._get_text(v, 'cor')
                combustivel = self._get_text(v, 'combustivel')
                carroceria = self._get_text(v, 'carroceria')
                preco = self._get_text(v, 'preco')
                observacao = self._get_text(v, 'observacao')
                
                # Debug para primeiro veículo
                if len(parsed_vehicles) == 0:
                    print(f"Debug primeiro veículo:")
                    print(f"  ID: {id_veiculo}")
                    print(f"  Tipo: {tipo_veiculo}")
                    print(f"  Marca: {marca}")
                    print(f"  Modelo: {modelo}")
                    print(f"  Versão: {versao}")
                
                # Determina se é moto ou carro
                is_moto = tipo_veiculo.lower() == "moto" or "moto" in tipo_veiculo.lower()
                
                if is_moto:
                    cilindrada_final, categoria_final = self.inferir_cilindrada_e_categoria_moto(
                        modelo, versao
                    )
                    tipo_final = "moto"
                else:
                    categoria_final = self.definir_categoria_veiculo(modelo, observacao or "")
                    cilindrada_final = None
                    tipo_final = "carro"
                
                # Extrai fotos
                fotos = self._extract_photos(v)
                
                # Extrai dados da loja
                loja_elem = v.find('loja')
                loja_info = {}
                if loja_elem is not None:
                    contato_elem = loja_elem.find('contato')
                    if contato_elem is not None:
                        loja_info = {
                            'nome': self._get_text(contato_elem, 'nome'),
                            'email': self._get_text(contato_elem, 'email'),
                            'telefone': self._get_text(contato_elem, 'telefone'),
                            'site': self._get_text(contato_elem, 'site')
                        }
                
                parsed = self.normalize_vehicle({
                    "id": id_veiculo,
                    "tipo": tipo_final,
                    "zero_km": zero_km,
                    "placa": placa,
                    "versao": versao,
                    "marca": marca,
                    "modelo": modelo,
                    "ano": ano_modelo or ano_fabricacao,
                    "ano_fabricacao": ano_fabricacao,
                    "km": self._convert_km(km),
                    "cor": cor,
                    "combustivel": combustivel,
                    "cambio": cambio,
                    "motor": None,  # Não disponível no XML
                    "portas": self._convert_portas(portas),
                    "categoria": categoria_final or carroceria,
                    "cilindrada": cilindrada_final,
                    "preco": self.converter_preco(preco),
                    "opcionais": observacao or "",
                    "fotos": fotos,
                    "loja": loja_info
                })
                parsed_vehicles.append(parsed)
                
            except Exception as e:
                print(f"Erro ao processar veículo: {e}")
                continue
        
        print(f"Total de veículos processados: {len(parsed_vehicles)}")
        return parsed_vehicles
    
    def _get_text(self, element, tag_name: str) -> str:
        """Extrai texto de um elemento XML, tratando CDATA corretamente"""
        if element is None:
            return ""
        
        child = element.find(tag_name)
        if child is None:
            return ""
        
        # O Python ET já trata CDATA automaticamente
        text = child.text or ""
        return text.strip()
    
    def _extract_photos(self, v) -> List[str]:
        """Extrai fotos do veículo DSAutoEstoque"""
        fotos_elem = v.find('fotos')
        if fotos_elem is None:
            return []
        
        fotos = []
        for foto_elem in fotos_elem.findall('foto'):
            if foto_elem.text:
                # Remove parâmetros da URL após .jpg
                url = foto_elem.text.strip()
                if '.jpg' in url:
                    url = url.split('.jpg')[0] + '.jpg'
                elif '.jpeg' in url:
                    url = url.split('.jpeg')[0] + '.jpeg'
                elif '.png' in url:
                    url = url.split('.png')[0] + '.png'
                fotos.append(url)
        
        return fotos
    
    def _convert_km(self, km_str: str) -> int:
        """Converte string de KM para inteiro"""
        if not km_str:
            return 0
        
        try:
            # Remove pontos e espaços
            km_clean = km_str.replace('.', '').replace(' ', '').replace(',', '')
            return int(km_clean)
        except (ValueError, TypeError):
            return 0
    
    def _convert_portas(self, portas_str: str) -> int:
        """Converte string de portas para inteiro"""
        if not portas_str:
            return 0
        
        try:
            return int(portas_str.strip())
        except (ValueError, TypeError):
            return 0


# Função de teste para debugar o parser
def test_parser_with_sample_xml():
    """Função para testar o parser com XML de exemplo"""
    
    sample_xml = """<estoque>
<veiculo>
<id>2169492</id>
<tipoveiculo>Carro</tipoveiculo>
<zerokm>S</zerokm>
<placa>FFK1J00</placa>
<marca id="14">BMW</marca>
<modelo id="111"><![CDATA[ X3 ]]></modelo>
<versao id="589"><![CDATA[ 2.0 20I 4X4 16V ]]></versao>
<tipomotor> </tipomotor>
<anofabricacao>2015</anofabricacao>
<anomodelo>2015</anomodelo>
<cambio id="1">Automático</cambio>
<km>0</km>
<portas>4</portas>
<cor id="4">Branco</cor>
<combustivel id="6">Gasolina</combustivel>
<carroceria>SUV</carroceria>
<preco>R$ 109.000,00</preco>
<observacao><![CDATA[ BMW X3 xDrive20i 2015 - Luxo, Desempenho e Conforto em um SUV Premium! ]]></observacao>
<fotos>
<foto>https://dsae.s3.amazonaws.com/42065993000120/Fotos/FFK1J00_04.jpg?u=20250604104528</foto>
<foto>https://dsae.s3.amazonaws.com/42065993000120/Fotos/FFK1J00_03.jpg?u=20250604104528</foto>
</fotos>
<loja>
<contato>
<nome>Aprove</nome>
<email>evertoncdp@gmail.com</email>
<telefone>(48) 9996-6386</telefone>
<site>http://</site>
</contato>
</loja>
</veiculo>
</estoque>"""
    
    # Testar o parse
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(sample_xml)
        print(f"Parse bem-sucedido! Root: {root.tag}")
        
        veiculos = root.findall('.//veiculo')
        print(f"Veículos encontrados: {len(veiculos)}")
        
        if veiculos:
            v = veiculos[0]
            print(f"ID: {v.find('id').text if v.find('id') is not None else 'N/A'}")
            modelo_elem = v.find('modelo')
            print(f"Modelo: '{modelo_elem.text if modelo_elem is not None else 'N/A'}'")
            
    except Exception as e:
        print(f"Erro no teste: {e}")

if __name__ == "__main__":
    test_parser_with_sample_xml()
