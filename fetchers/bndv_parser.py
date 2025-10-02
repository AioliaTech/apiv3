def parse(self, data: Any, url: str) -> List[Dict]:
    """Processa dados do BNDV"""
    veiculos = data.get("vehiclesBy", [])
    
    if not isinstance(veiculos, list):
        veiculos = [veiculos]
    
    parsed_vehicles = []
    for v in veiculos:
        # Extrai dados básicos
        marca = v.get("markName")
        modelo = v.get("modelName")
        versao = v.get("versionName")
        ano = v.get("year")
        
        # Processa opcionais
        opcionais_veiculo = self._parse_opcionais(v.get("itemJs"))
        
        # Processa fotos
        fotos = self._parse_fotos(v.get("pictureJs"))
        
        # Determina categoria (assumindo que é sempre carro, já que não tem campo tipo)
        categoria_final = self.definir_categoria_veiculo(modelo, opcionais_veiculo)
        
        # Extrai motor da versão
        motor = self._extract_motor_from_version(versao)
        
        # Usa a placa ao contrário como ID
        placa = v.get("plate")
        vehicle_id = placa[::-1] if placa else None
        
        parsed = self.normalize_vehicle({
            "id": vehicle_id,
            "tipo": "carro",  # Padrão para carros
            "titulo": None,
            "versao": versao,
            "marca": marca,
            "modelo": modelo,
            "ano": ano,
            "ano_fabricacao": None,
            "km": v.get("km"),
            "cor": v.get("color"),
            "combustivel": v.get("fuelName"),
            "cambio": v.get("transmissionName"),
            "motor": motor,
            "portas": None,  # Não disponível no JSON
            "categoria": categoria_final,
            "cilindrada": None,
            "preco": v.get("saleValue"),  # Já vem como número
            "opcionais": opcionais_veiculo,
            "fotos": fotos,
            "placa": v.get("plate"),
            "placa_final": v.get("finalPlate"),
            "subcategoria": v.get("subCategoryName"),
            "tipo_veiculo": v.get("vehicleTypeName"),
            "data_cadastro": v.get("registrationDate"),
            "lojista": self._parse_customer(v.get("Customer"))
        })
        parsed_vehicles.append(parsed)
    
    return parsed_vehicles
