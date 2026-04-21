"""Mapeamento IATA -> nome de cidade para titulos SEO.

Fallback: se IATA nao estiver no dict, retorna o proprio codigo em maiusculas.
"""
IATA_CITIES: dict[str, str] = {
    # BR domesticas
    "GRU": "Sao Paulo", "CGH": "Sao Paulo", "VCP": "Campinas",
    "GIG": "Rio de Janeiro", "SDU": "Rio de Janeiro",
    "BSB": "Brasilia", "CNF": "Belo Horizonte", "SSA": "Salvador",
    "REC": "Recife", "FOR": "Fortaleza", "POA": "Porto Alegre",
    "CWB": "Curitiba", "MAO": "Manaus", "NAT": "Natal", "BEL": "Belem",
    "MCZ": "Maceio", "FLN": "Florianopolis", "VIX": "Vitoria",
    "AJU": "Aracaju", "THE": "Teresina", "SLZ": "Sao Luis",
    "CGB": "Cuiaba", "CGR": "Campo Grande", "GYN": "Goiania",
    "IGU": "Foz do Iguacu", "JPA": "Joao Pessoa", "PMW": "Palmas",
    "PVH": "Porto Velho", "BVB": "Boa Vista", "MCP": "Macapa",
    "RBR": "Rio Branco",
    # Internacionais principais
    "LIS": "Lisboa", "MAD": "Madri", "BCN": "Barcelona",
    "CDG": "Paris", "ORY": "Paris", "LHR": "Londres", "LGW": "Londres",
    "FCO": "Roma", "MXP": "Milao", "FRA": "Frankfurt", "MUC": "Munique",
    "AMS": "Amsterda", "ZRH": "Zurique", "VIE": "Viena", "BRU": "Bruxelas",
    "DUB": "Dublin", "OPO": "Porto",
    "MIA": "Miami", "JFK": "Nova York", "EWR": "Nova York", "LGA": "Nova York",
    "LAX": "Los Angeles", "MCO": "Orlando", "IAH": "Houston",
    "ORD": "Chicago", "DFW": "Dallas", "ATL": "Atlanta", "BOS": "Boston",
    "SFO": "Sao Francisco", "LAS": "Las Vegas", "SEA": "Seattle",
    "YYZ": "Toronto", "YUL": "Montreal", "YVR": "Vancouver",
    "MEX": "Cidade do Mexico", "CUN": "Cancun",
    "EZE": "Buenos Aires", "AEP": "Buenos Aires",
    "SCL": "Santiago", "LIM": "Lima", "BOG": "Bogota",
    "UIO": "Quito", "MVD": "Montevideu", "ASU": "Assuncao",
    "PTY": "Cidade do Panama", "SJO": "San Jose",
    "DXB": "Dubai", "DOH": "Doha", "IST": "Istambul",
    "NRT": "Toquio", "HND": "Toquio", "ICN": "Seul",
    "HKG": "Hong Kong", "SIN": "Singapura", "BKK": "Bangkok",
    "SYD": "Sydney", "MEL": "Melbourne", "JNB": "Joanesburgo",
    "CPT": "Cidade do Cabo", "GRU": "Sao Paulo",
}


def iata_to_city(code: str) -> str:
    return IATA_CITIES.get(code.upper(), code.upper())
