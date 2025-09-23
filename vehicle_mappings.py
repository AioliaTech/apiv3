# =================== MAPEAMENTOS DE VEÍCULOS =======================
"""
Arquivo centralizado com mapeamentos de categorias para carros e motos.
Usado tanto pelo main.py quanto pelo xml_fetcher.py
"""

MAPEAMENTO_CATEGORIAS = {}
OPCIONAL_CHAVE_HATCH = "limpador traseiro"

# --- Listas de Modelos por Categoria ---

hatch_models = ["500", "QQ", "308", "IX35", "A 200", "a200", "joy", "gol", "uno", "palio", "celta", "march", "sandero", "i30", "golf", "fox", "up", "fit", "etios", "bravo", "punto", "208", "argo", "mobi", "c3", "picanto", "stilo", "c4 vtr", "kwid", "soul", "agile", "fusca", "a1", "new beetle", "116i", "118i", "120i", "125i", "m135i", "m140i"]
for model in hatch_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Hatch"

sedan_models = ["arrizo6", "arrizo 6", "A5", "430i", "civic", "a6", "sentra", "jetta", "voyage", "siena", "grand siena", "cobalt", "logan", "fluence", "cerato", "elantra", "virtus", "accord", "altima", "fusion", "passat", "vectra sedan", "classic", "cronos", "linea", "408", "c4 pallas", "bora", "hb20s", "lancer", "camry", "onix plus", "azera", "malibu", "318i", "320d", "320i", "328i", "330d", "330i", "335i", "520d", "528i", "530d", "530i", "535i", "540i", "550i", "740i", "750i", "c180", "c200", "c250", "c300", "e250", "e350", "m3", "m5", "s4", "classe c", "classe e", "classe s", "eqe", "eqs"]
for model in sedan_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Sedan"

hatch_sedan_models = ["320iA", "onix", "hb20", "yaris", "city", "a3", "corolla", "focus", "fiesta", "corsa", "astra", "vectra", "cruze", "clio", "megane", "206", "207", "307", "tiida", "ka", "versa", "prisma", "polo", "c4", "sonic", "série 1", "série 2", "série 3", "série 4", "série 5", "série 6", "série 7", "classe a", "cla"]
for model in hatch_sedan_models: 
    MAPEAMENTO_CATEGORIAS[model] = "hatch,sedan"

suv_models = ["RANGE ROVER SPORT", "GLK 220", "disc spt", "veracruz", "Captiva", "Discovery", "Macan", "JOURNEY", "XC90", "xc60", "tiggo", "edge", "outlander", "range rover evoque", "song plus", "duster", "ecosport", "hrv", "hr-v", "COMPASS", "compass", "renegade", "tracker", "kicks", "captur", "creta", "tucson", "santa fe", "sorento", "sportage", "pajero", "tr4", "aircross", "tiguan", "t-cross", "tcross", "rav4", "land cruiser", "cherokee", "grand cherokee", "trailblazer", "pulse", "fastback", "territory", "bronco sport", "2008", "3008", "5008", "c4 cactus", "taos", "crv", "cr-v", "corolla cross", "hilux sw4", "sw4", "pajero sport", "commander", "nivus", "equinox", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "ix", "ix1", "ix2", "ix3", "gla", "glb", "glc", "gle", "gls", "classe g", "eqa", "eqb", "eqc", "q2", "q3", "q5", "q7", "q8", "q6 e-tron", "e-tron", "q4 e-tron", "q4etron", "wrx", "xv"]
for model in suv_models: 
    MAPEAMENTO_CATEGORIAS[model] = "SUV"

caminhonete_models = ["f-350", "S-10 Pick-up", "Silverado", "F-1000", "F1000", "duster oroch", "d20", "hilux", "ranger", "S10", "S-10", "L200 Triton", "l200", "triton", "toro", "frontier", "amarok", "maverick", "ram 1500", "rampage", "f-250", "f250", "courier", "dakota", "gladiator", "hoggar"]
for model in caminhonete_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Caminhonete"

utilitario_models = ["bongo", "montana", "saveiro", "strada", "oroch", "kangoo", "partner", "doblo", "fiorino", "kombi", "doblo cargo", "berlingo", "combo", "express", "hr"]
for model in utilitario_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Utilitário"

furgao_models = ["boxer", "daily", "ducato", "expert", "jumper", "jumpy", "master", "scudo", "sprinter", "trafic", "transit", "vito"]
for model in furgao_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Furgão"

coupe_models = ["911", "718", "370z", "brz", "camaro", "challenger", "corvette", "gt86", "mustang", "r8", "rcz", "rx8", "supra", "tt", "tts", "veloster", "m2", "m4", "m8", "s5", "amg gt"]
for model in coupe_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Coupe"

conversivel_models = ["911 cabrio", "beetle cabriolet", "boxster", "eos", "miata", "mini cabrio", "slk", "z4", "série 8", "slc", "sl"]
for model in conversivel_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Conversível"

station_wagon_models = ["a4 avant", "fielder", "golf variant", "palio weekend", "parati", "quantum", "spacefox", "rs2", "rs4", "rs6"]
for model in station_wagon_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Station Wagon"

minivan_models = ["caravan", "carnival", "grand c4", "idea", "livina", "meriva", "picasso", "scenic", "sharan", "spin", "touran", "xsara picasso", "zafira", "série 2 active tourer", "classe b", "classe t", "classe r", "classe v"]
for model in minivan_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Minivan"

offroad_models = ["T4", "bandeirante", "bronco", "defender", "grand vitara", "jimny", "samurai", "troller", "wrangler"]
for model in offroad_models: 
    MAPEAMENTO_CATEGORIAS[model] = "Off-road"

# =================== MAPEAMENTOS DE MOTOCICLETAS =======================

# Mapeamento combinado: cilindrada e categoria
MAPEAMENTO_MOTOS = {
    # Street/Urbanas (commuter básicas e econômicas)
    "DK 150": (150, "street"),
    "SPEED 400": (400, "street"),
    "FAN Flex": (160, "street"),    
    "FZ15 150": (150, "street"),
    "xy 150": (150, "street"),
    "cg 150 sport": (150, "street"),
    "YS 150 FAZER": (150, "street"),
    "dk 160": (160, "street"),
    "cg 150 titan": (150, "street"),
    "cg150 titan": (150, "street"),  # Variação sem espaço
    "cg 160 titan": (160, "street"),
    "cg160 titan": (160, "street"),  # Variação sem espaço
    "cg 125": (125, "street"),
    "cg125": (125, "street"),  # Variação sem espaço
    "cg 160": (160, "street"),
    "cg160": (160, "street"),  # Variação sem espaço
    "cg 160 fan": (160, "street"),
    "cg160 fan": (160, "street"),  # Variação sem espaço
    "cg 160 start": (160, "street"),
    "cg160 start": (160, "street"),  # Variação sem espaço
    "cg 160 titan s": (160, "street"),
    "cg160 titan s": (160, "street"),  # Variação sem espaço
    "cg 125 fan ks": (125, "street"),
    "cg125 fan ks": (125, "street"),  # Variação sem espaço
    "cg150 fan": (150, "street"),
    "cg 150 fan": (150, "street"),
    "cg 150 fan esdi": (150, "street"),
    "cg150 titan": (150, "street"),
    "ybr 150": (150, "street"),
    "ybr150": (150, "street"),  # Variação sem espaço
    "ybr 125": (125, "street"),
    "ybr125": (125, "street"),  # Variação sem espaço
    "factor 125": (125, "street"),
    "factor125": (125, "street"),  # Variação sem espaço
    "factor 150": (150, "street"),
    "factor150": (150, "street"),  # Variação sem espaço
    "fz25": (250, "street"),
    "fz 25": (250, "street"),
    "fz25 fazer": (250, "street"),
    "fz 25 fazer": (250, "street"),
    "fz15 fazer": (150, "street"),
    "fz 15 fazer": (150, "street"),
    "fazer 150": (150, "street"),
    "fazer150": (150, "street"),  # Variação sem espaço
    "fazer 250": (250, "street"),
    "fazer250": (250, "street"),  # Variação sem espaço
    "ys 250": (250, "street"),
    "ys250": (250, "street"),  # Variação sem espaço
    "cb 300": (300, "street"),
    "cb300": (300, "street"),  # Variação sem espaço
    "cb twister": (300, "street"),
    "twister": (300, "street"),
    "fz6": (150, "street"),
    
    # Scooter (transmissão automática, design step-through)
    "SH 300": (300, "scooter"),
    "lead 110": (110, "scooter"),
    "biz 125": (125, "scooter"),
    "jet 50": (50, "scooter"),
    "jl 50": (50, "scooter"),
    "xy 125": (125, "scooter"),
    "adv 150": (150, "scooter"),
    "biz125": (125, "scooter"),  # Variação sem espaço
    "biz 125 es": (125, "scooter"),
    "biz125 es": (125, "scooter"),  # Variação sem espaço
    "biz 110": (110, "scooter"),
    "biz110": (110, "scooter"),  # Variação sem espaço
    "biz es": (125, "scooter"),
    "biz ex": (125, "scooter"),    
    "pop 110": (110, "scooter"),
    "pop110": (110, "scooter"),  # Variação sem espaço
    "pop 110i": (110, "scooter"),
    "pop110i": (110, "scooter"),  # Variação sem espaço
    "pcx 150": (150, "scooter"),
    "pcx150": (150, "scooter"),  # Variação sem espaço
    "pcx 160": (160, "scooter"),
    "pcx160": (160, "scooter"),  # Variação sem espaço
    "elite 125": (125, "scooter"),
    "elite125": (125, "scooter"),  # Variação sem espaço
    "nmax 160": (160, "scooter"),
    "nmax160": (160, "scooter"),  # Variação sem espaço
    "xmax 250": (250, "scooter"),
    "xmax250": (250, "scooter"),  # Variação sem espaço
    "burgman 125": (125, "scooter"),
    "burgman125": (125, "scooter"),  # Variação sem espaço
    "dafra citycom 300": (300, "scooter"),
    "citycom": (300, "scooter"),
    
    # Trail/Offroad (dual-sport, suspensão robusta)
    "nxr 150 bros": (150, "trail"),
    "shi 175": (150, "trail"),
    "nxr150 bros": (150, "trail"),  # Variação sem espaço
    "nxr 160": (160, "trail"),
    "nxr160": (160, "trail"),  # Variação sem espaço
    "bros 160": (160, "trail"),
    "bros160": (160, "trail"),  # Variação sem espaço
    "nxr 160 bros": (160, "trail"),
    "nxr160 bros": (160, "trail"),  # Variação sem espaço
    "xre 190": (190, "trail"),
    "xre190": (190, "trail"),  # Variação sem espaço
    "xre 300": (300, "trail"),
    "xre300": (300, "trail"),  # Variação sem espaço
    "xre 300 sahara": (300, "trail"),
    "xre300 sahara": (300, "trail"),  # Variação sem espaço
    "sahara 300": (300, "trail"),
    "sahara300": (300, "trail"),  # Variação sem espaço
    "sahara 300 rally": (300, "trail"),
    "sahara300 rally": (300, "trail"),  # Variação sem espaço
    "xr300l tornado": (300, "trail"),
    "xr 300l tornado": (300, "trail"),
    "crf 230f": (230, "offroad"),
    "crf230f": (230, "offroad"),  # Variação sem espaço
    "dr 160": (160, "trail"),
    "dr160": (160, "trail"),  # Variação sem espaço
    "dr 160 s": (160, "trail"),
    "dr160 s": (160, "trail"),  # Variação sem espaço
    "xtz 150": (150, "trail"),
    "xtz150": (150, "trail"),  # Variação sem espaço
    "xtz 250": (250, "trail"),
    "xtz250": (250, "trail"),  # Variação sem espaço
    "xtz 250 tenere": (250, "trail"),
    "xtz250 tenere": (250, "trail"),  # Variação sem espaço
    "tenere 250": (250, "trail"),
    "tenere250": (250, "trail"),  # Variação sem espaço
    "lander 250": (250, "trail"),
    "lander250": (250, "trail"),  # Variação sem espaço
    "falcon": (400, "trail"),
    "dl160": (160, "trail"),
    
    # BigTrail/Adventure (alta cilindrada, touring)
    "cb 500x": (500, "bigtrail"),   
    "tiger 660": (660, "trail"),
    "DL 650": (650, "bigtrail"),
    "DL 650 XT": (650, "bigtrail"),
    "R 1200 GS": (1200, "bigtrail"),
    "DL 1000": (1000, "bigtrail"),
    "PAN AMERICA 1250": (1250, "bigtrail"),
    "crf 1100l": (1100, "bigtrail"),
    "crf1100l": (1100, "bigtrail"),
    "NC 750": (750, "bigtrail"),
    "g 310": (300, "bigtrail"),
    "g310": (300, "bigtrail"),  # Variação sem espaço
    "g 310 gs": (300, "bigtrail"),
    "g310 gs": (300, "bigtrail"),  # Variação sem espaço
    "f 750 gs": (850, "bigtrail"),
    "f750 gs": (850, "bigtrail"),  # Variação sem espaço
    "f 850 gs": (850, "bigtrail"),
    "f850 gs": (850, "bigtrail"),  # Variação sem espaço
    "f 900": (900, "bigtrail"),
    "f900": (900, "bigtrail"),  # Variação sem espaço
    "f 900 gs": (900, "bigtrail"),
    "f900 gs": (900, "bigtrail"),  # Variação sem espaço
    "r 1250": (1250, "bigtrail"),
    "r1250": (1250, "bigtrail"),  # Variação sem espaço
    "r 1250 gs": (1250, "bigtrail"),
    "r1250 gs": (1250, "bigtrail"),  # Variação sem espaço
    "r 1300": (1300, "bigtrail"),
    "r1300": (1300, "bigtrail"),  # Variação sem espaço
    "r 1300 gs": (1300, "bigtrail"),
    "r1300 gs": (1300, "bigtrail"),  # Variação sem espaço
    "g 650 gs": (650, "bigtrail"),
    "g650 gs": (650, "bigtrail"),  # Variação sem espaço
    "versys 300": (300, "bigtrail"),
    "versys300": (300, "bigtrail"),  # Variação sem espaço
    "versys 650": (650, "bigtrail"),
    "versys650": (650, "bigtrail"),  # Variação sem espaço
    "versys-x 300": (300, "bigtrail"),
    "versysx 300": (300, "bigtrail"),  # Variação sem hífen
    "tiger 800": (800, "bigtrail"),
    "tiger800": (800, "bigtrail"),  # Variação sem espaço
    "tiger 900": (900, "bigtrail"),
    "tiger900": (900, "bigtrail"),  # Variação sem espaço
    "himalayan": (400, "bigtrail"),
    "700 x": (700, "bigtrail"),
    "TIGER 1200": (1200, "bigtrail"),
    
    # Esportiva Carenada (supersport, carenagem completa)
    "GSX-R 1000": (1000, "esportiva carenada"),
    "s 1000 rr": (1000, "esportiva carenada"),
    "cbr 250": (250, "esportiva carenada"),
    "cbr250": (250, "esportiva carenada"),  # Variação sem espaço
    "cbr 300": (300, "esportiva carenada"),
    "cbr300": (300, "esportiva carenada"),  # Variação sem espaço
    "cbr 500": (500, "esportiva carenada"),
    "cbr500": (500, "esportiva carenada"),  # Variação sem espaço
    "cbr 600": (600, "esportiva carenada"),
    "cbr600": (600, "esportiva carenada"),  # Variação sem espaço
    "cbr 650": (650, "esportiva carenada"),
    "cbr650": (650, "esportiva carenada"),  # Variação sem espaço
    "cbr 1000": (1000, "esportiva carenada"),
    "cbr1000": (1000, "esportiva carenada"),  # Variação sem espaço
    "cbr 1000r": (1000, "esportiva carenada"),
    "cbr1000r": (1000, "esportiva carenada"),  # Variação sem espaço
    "yzf r3": (300, "esportiva carenada"),
    "yzf r-3": (300, "esportiva carenada"),
    "yzf r-6": (600, "esportiva carenada"),
    "r15": (150, "esportiva carenada"),
    "r1": (1000, "esportiva carenada"),
    "ninja 300": (300, "esportiva carenada"),
    "ninja300": (300, "esportiva carenada"),  # Variação sem espaço
    "ninja 400": (400, "esportiva carenada"),
    "ninja400": (400, "esportiva carenada"),  # Variação sem espaço
    "ninja 650": (650, "esportiva carenada"),
    "ninja650": (650, "esportiva carenada"),  # Variação sem espaço
    "ninja 1000": (1050, "esportiva carenada"),
    "ninja1000": (1050, "esportiva carenada"),  # Variação sem espaço
    "ninja zx-10r": (1000, "esportiva carenada"),
    "ninja zx10r": (1000, "esportiva carenada"),  # Variação sem hífen
    "s 1000": (1000, "esportiva carenada"),
    "s1000": (1000, "esportiva carenada"),  # Variação sem espaço
    "panigale v2": (950, "esportiva carenada"),
    "panigale v4": (1100, "esportiva carenada"),
    "hayabusa": (1350, "esportiva carenada"),
    
    # Esportiva Naked (naked sport, sem carenagem)
    "Z 400": (400, "esportiva naked"),    
    "310 R": (310, "esportiva naked"),
    "Z 1000": (1000, "esportiva naked"),
    "mt 03": (300, "esportiva naked"),
    "mt-03": (300, "esportiva naked"),
    "mt03": (300, "esportiva naked"),
    "mt 07": (690, "esportiva naked"),
    "mt-07": (690, "esportiva naked"),
    "mt07": (690, "esportiva naked"),  # Variação sem hífen
    "mt 09": (890, "esportiva naked"),
    "mt-09": (890, "esportiva naked"),
    "mt09": (890, "esportiva naked"),  # Variação sem hífen
    "cb 500": (500, "esportiva naked"),
    "cb500": (500, "esportiva naked"),  # Variação sem espaço
    "cb 650": (650, "esportiva naked"),
    "cb650": (650, "esportiva naked"),  # Variação sem espaço
    "cb 1000r": (1000, "esportiva naked"),
    "cb1000r": (1000, "esportiva naked"),  # Variação sem espaço
    "hornet 600": (600, "esportiva naked"),
    "hornet600": (600, "esportiva naked"),  # Variação sem espaço
    "cb 600f": (600, "esportiva naked"),
    "cb600f": (600, "esportiva naked"),  # Variação sem espaço
    "xj6": (600, "esportiva naked"),
    "z300": (300, "esportiva naked"),
    "z400": (400, "esportiva naked"),
    "z650": (650, "esportiva naked"),
    "z750": (750, "esportiva naked"),
    "z800": (800, "esportiva naked"),
    "z900": (950, "esportiva naked"),
    "z1000": (1000, "esportiva naked"),
    "er6n": (650, "esportiva naked"),
    "er-6n": (650, "esportiva naked"),
    "bandit 600": (600, "esportiva naked"),
    "bandit600": (600, "esportiva naked"),  # Variação sem espaço
    "bandit 650": (650, "esportiva naked"),
    "bandit650": (650, "esportiva naked"),  # Variação sem espaço
    "bandit 1250": (1250, "esportiva naked"),
    "bandit1250": (1250, "esportiva naked"),  # Variação sem espaço
    "gsx 650f": (650, "esportiva naked"),
    "gsx650f": (650, "esportiva naked"),  # Variação sem espaço
    "gsx-s 750": (750, "esportiva naked"),
    "gsxs 750": (750, "esportiva naked"),  # Variação sem hífen
    "gsx-s 1000": (1000, "esportiva naked"),
    "gsxs 1000": (1000, "esportiva naked"),  # Variação sem hífen
    "gixxer 250": (250, "esportiva naked"),
    "gixxer250": (250, "esportiva naked"),  # Variação sem espaço
    "gs500": (500, "esportiva naked"),
    "monster 797": (800, "esportiva naked"),
    "monster797": (800, "esportiva naked"),  # Variação sem espaço
    "monster 821": (820, "esportiva naked"),
    "monster821": (820, "esportiva naked"),  # Variação sem espaço
    "monster 937": (940, "esportiva naked"),
    "monster937": (940, "esportiva naked"),  # Variação sem espaço
    "street triple": (750, "esportiva naked"),
    "speed triple": (1050, "esportiva naked"),
    "trident 660": (660, "esportiva naked"),
    "trident660": (660, "esportiva naked"),  # Variação sem espaço
    
    # Custom/Cruiser (posição relaxada, estética clássica)
    "FAT BOY": (1690, "custom"),
    "NIGHTSTER SPECIAL": (975, "custom"),
    "iron 883": (883, "custom"),
    "v-rod": (1250, "custom"),
    "iron883": (883, "custom"),  # Variação sem espaço
    "forty eight": (1200, "custom"),
    "sportster s": (1250, "custom"),
    "fat bob": (1140, "custom"),
    "meteor 350": (350, "custom"),
    "meteor350": (350, "custom"),  # Variação sem espaço
    "classic 350": (350, "custom"),
    "classic350": (350, "custom"),  # Variação sem espaço
    "hunter 350": (350, "custom"),
    "hunter350": (350, "custom"),  # Variação sem espaço
    "interceptor 650": (650, "custom"),
    "interceptor650": (650, "custom"),  # Variação sem espaço
    "continental gt 650": (650, "custom"),
    "continental gt650": (650, "custom"),  # Variação sem espaço
    "diavel 1260": (1260, "custom"),
    "diavel1260": (1260, "custom"),  # Variação sem espaço
    "r 18": (1800, "custom"),
    "r18": (1800, "custom"),  # Variação sem espaço
    "bonneville": (900, "custom"),
    "mt 01": (1700, "custom"),
    "mt01": (1700, "custom"),
    "Meteor Supernova": (350, "custom"),
    "VT 600": (600, "custom"),
    
    # Touring (longas distâncias, conforto)
    "ELECTRA GLIDE ULTRA": (1700, "touring"),
    "GOLD WING 1500": (1500, "touring"),
    "road glide": (2150, "touring"),
    "street glide": (1750, "touring"),
    "k 1300": (1300, "touring"),
    "k1300": (1300, "touring"),  # Variação sem espaço
    "k 1600": (1650, "touring"),
    "k1600": (1650, "touring"),  # Variação sem espaço
    "xt 660": (660, "touring"),
    "xt660": (660, "touring"),  # Variação sem espaço
    "xt 600": (600, "touring"),
    "xt600": (600, "touring"),  # Variação sem espaço
    "HERITAGE": (1690, "touring"),
    
    # ATV/Quadriciclo
    "cforce 1000": (1000, "custom"),
    "cforce1000": (1000, "custom"),  # Variação sem espaço
    "trx 420": (420, "custom"),
    "trx420": (420, "custom"),  # Variação sem espaço
    "t350 x": (350, "custom"),
    "t350x": (350, "custom"),  # Variação sem espaço
    
    # Modelos especiais
    "commander 250": (250, "street"),
    "commander250": (250, "street"),  # Variação sem espaço
    "gk350": (350, "street"),
}

# Mapeamento legado apenas para cilindrada (compatibilidade)
MAPEAMENTO_CILINDRADAS = {modelo: cilindrada for modelo, (cilindrada, _) in MAPEAMENTO_MOTOS.items()}
