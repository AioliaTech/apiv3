# Adicione este endpoint no seu main.py, após os outros endpoints existentes

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
            safe_value(vehicle.get("cambio")),
            safe_value(vehicle.get("cilindrada")),
            safe_value(vehicle.get("portas")),
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
