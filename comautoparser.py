class AltimusParser(BaseParser):
    def can_parse(self, data: Any, url: str) -> bool: return isinstance(data, dict) and "veiculos" in data
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        veiculos = data.get("veiculos", [])
        if isinstance(veiculos, dict): veiculos = [veiculos]
        
        parsed_vehicles = []
        for v in veiculos:
            modelo_veiculo = v.get("modelo")
            versao_veiculo = v.get("versao")
            opcionais_veiculo = self._parse_opcionais(v.get("opcionais"))
            
            # Determina se é moto ou carro
            tipo_veiculo = v.get("tipo", "").lower()
            is_moto = "moto" in tipo_veiculo or "motocicleta" in tipo_veiculo
            
            if is_moto:
                # Para motos: usa o novo sistema com modelo E versão
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_veiculo, versao_veiculo)
            else:
                # Para carros: usa o sistema existente
                categoria_final = definir_categoria_veiculo(modelo_veiculo, opcionais_veiculo)
                cilindrada_final = v.get("cilindrada") or inferir_cilindrada(modelo_veiculo, versao_veiculo)
            
            parsed = self.normalize_vehicle({
                "id": ''.join(d for i, d in enumerate(str(v.get("placa", ""))) if i in [1, 2, 3, 5, 6]),
                "tipo": "moto" if is_moto else ("carro" if v.get("categoria") == "Carros" else v.get("categoria")), 
                "titulo": None, "versao": versao_veiculo,
                "marca": v.get("marca"), "modelo": modelo_veiculo, "ano": v.get("ano_modelo") or v.get("ano"),
                "ano_fabricacao": v.get("ano_fabricacao") or v.get("ano_fabricacao"), "km": v.get("km"),
                "cor": v.get("cor"), "combustivel": v.get("combustivel"), 
                "cambio": "manual" if "manual" in str(v.get("cambio", "")).lower() else ("automatico" if "automático" in str(v.get("cambio", "")).lower() else v.get("cambio")),
                "motor": re.search(r'\b(\d+\.\d+)\b', str(versao_veiculo or "")).group(1) if re.search(r'\b(\d+\.\d+)\b', str(versao_veiculo or "")) else None, 
                "portas": v.get("portas"), "categoria": v.get("carroceria"),
                "cilindrada": cilindrada_final,
                "preco": converter_preco(v.get("preco", {}).get("venda")),
                "opcionais": v.get("acessorios"), "fotos": v.get("fotos", [])
            })
            parsed_vehicles.append(parsed)
        return parsed_vehicles
    
    def _parse_opcionais(self, opcionais: Any) -> str:
        if isinstance(opcionais, list): return ", ".join(str(item) for item in opcionais if item)
        return str(opcionais) if opcionais else ""

class MotorLeadsParser(BaseParser):
    """Parser para estrutura MotorLeads (XML_URL_2 e XML_URL_3)"""
    
    def can_parse(self, data: Any, url: str) -> bool:
        """Identifica estrutura MotorLeads"""
        if not isinstance(data, dict):
            return False
        
        # Verifica estrutura MotorLeads: tem "items" com "results"
        if "items" in data:
            items = data["items"]
            if isinstance(items, dict) and "results" in items:
                return True
        
        return False
    
    def parse(self, data: Any, url: str) -> List[Dict]:
        """Processa dados do MotorLeads"""
        items = data.get("items", {})
        results = items.get("results", [])
        
        if isinstance(results, dict):
            results = [results]
        
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
                cilindrada_final, categoria_final = inferir_cilindrada_e_categoria_moto(modelo_final, versao_veiculo)
                tipo_final = "moto"
            else:
                # Tenta mapear segment primeiro, depois fallback para definir_categoria_veiculo
                categoria_final = self._map_segment_to_category(segment)
                if not categoria_final:
                    categoria_final = definir_categoria_veiculo(modelo_final, opcionais_processados)
                cilindrada_final = inferir_cilindrada(modelo_final, versao_veiculo)
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
                "preco": converter_preco(v.get("price")),
                "opcionais": opcionais_processados,
                "fotos": fotos_list
            })
            
            parsed_vehicles.append(parsed)
        
        return parsed_vehicles
