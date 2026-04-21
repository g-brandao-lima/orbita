"""Mapeamento IATA -> nome de cidade para titulos SEO.

Fallback: se IATA nao estiver no dict, retorna o proprio codigo em maiusculas.
"""
IATA_CITIES: dict[str, str] = {
    # BR domesticas
    "GRU": "São Paulo", "CGH": "São Paulo", "VCP": "Campinas",
    "GIG": "Rio de Janeiro", "SDU": "Rio de Janeiro",
    "BSB": "Brasília", "CNF": "Belo Horizonte", "SSA": "Salvador",
    "REC": "Recife", "FOR": "Fortaleza", "POA": "Porto Alegre",
    "CWB": "Curitiba", "MAO": "Manaus", "NAT": "Natal", "BEL": "Belém",
    "MCZ": "Maceió", "FLN": "Florianópolis", "VIX": "Vitória",
    "AJU": "Aracaju", "THE": "Teresina", "SLZ": "São Luís",
    "CGB": "Cuiabá", "CGR": "Campo Grande", "GYN": "Goiânia",
    "IGU": "Foz do Iguaçu", "JPA": "João Pessoa", "PMW": "Palmas",
    "PVH": "Porto Velho", "BVB": "Boa Vista", "MCP": "Macapá",
    "RBR": "Rio Branco", "CPV": "Campina Grande", "RAO": "Ribeirão Preto",
    # Internacionais principais
    "LIS": "Lisboa", "MAD": "Madri", "BCN": "Barcelona",
    "CDG": "Paris", "ORY": "Paris", "LHR": "Londres", "LGW": "Londres",
    "FCO": "Roma", "MXP": "Milão", "FRA": "Frankfurt", "MUC": "Munique",
    "AMS": "Amsterdã", "ZRH": "Zurique", "VIE": "Viena", "BRU": "Bruxelas",
    "DUB": "Dublin", "OPO": "Porto",
    "MIA": "Miami", "JFK": "Nova York", "EWR": "Nova York", "LGA": "Nova York",
    "LAX": "Los Angeles", "MCO": "Orlando", "IAH": "Houston",
    "ORD": "Chicago", "DFW": "Dallas", "ATL": "Atlanta", "BOS": "Boston",
    "SFO": "São Francisco", "LAS": "Las Vegas", "SEA": "Seattle",
    "YYZ": "Toronto", "YUL": "Montreal", "YVR": "Vancouver",
    "MEX": "Cidade do México", "CUN": "Cancún",
    "EZE": "Buenos Aires", "AEP": "Buenos Aires",
    "SCL": "Santiago", "LIM": "Lima", "BOG": "Bogotá",
    "UIO": "Quito", "MVD": "Montevidéu", "ASU": "Assunção",
    "PTY": "Cidade do Panamá", "SJO": "San José",
    "DXB": "Dubai", "DOH": "Doha", "IST": "Istambul",
    "NRT": "Tóquio", "HND": "Tóquio", "ICN": "Seul",
    "HKG": "Hong Kong", "SIN": "Singapura", "BKK": "Bangkok",
    "SYD": "Sydney", "MEL": "Melbourne", "JNB": "Joanesburgo",
    "CPT": "Cidade do Cabo",
}


def iata_to_city(code: str) -> str:
    return IATA_CITIES.get(code.upper(), code.upper())
