from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, RootModel
from typing import Dict

# --- 1. Importação Segura ---
try:
    from use_model import predict_flood_risk
except ImportError:
    predict_flood_risk = None

# --- 2. Lista Oficial (Bairros e Cotas) ---
BAIRROS_BELEM = {
    # ZONA BAIXA (Cota 4m - 6m) -> Sofre com Maré > 3.0m
    "Jurunas": 4.0, "Condor": 4.0, "Guamá": 4.5, "Terra Firme": 4.5,
    "Cremação": 5.0, "Cidade Velha": 5.0, "Reduto": 5.0,
    "Campina": 6.0, "Comércio": 4.0, "Telégrafo": 5.0,
    "Barreiro": 5.0, "Sacramenta": 5.5, "Val-de-Cans": 4.0,
    "Pratinha": 4.0, "Miramar": 5.0, "Universitário": 5.0,
    "Maracacuera": 5.0, "Paracuri": 5.0, "Bengui": 6.0,
    
    # ZONA MÉDIA (Cota 6m - 9m) -> Sofre com Chuva Forte + Maré
    "Umarizal": 6.0, "Batista Campos": 9.0, "Canudos": 8.0,
    "Fátima": 9.0, "Pedreira": 7.0, "Souza": 9.0,
    "Aurá": 8.0, "Cabanagem": 8.0, "Una": 7.0,
    "Tapanã": 7.0, "Agulha": 7.0, "Águas Negras": 6.0,
    "Campina de Icoaraci": 7.0, "Parque Guajará": 6.0,
    "Ponta Grossa": 6.0, "Maracangalha": 6.0,
    
    # ZONA ALTA (Cota > 10m) -> Seguro (exceto Catástrofe)
    "Nazaré": 13.0, "São Brás": 12.0, "Marco": 13.0,
    "Curió-Utinga": 10.0, "Guanabara": 10.0, "Castanheira": 11.0,
    "Marambaia": 12.0, "Mangueirão": 10.0, "Parque Verde": 14.0,
    "Coqueiro": 10.0, "Águas Lindas": 15.0, "São Clemente": 12.0,
    "Tenoné": 11.0, "Cruzeiro": 10.0
}

# --- 3. Contratos ---
class RiscoInput(BaseModel):
    Rainfall_mm: float = Field(..., description="Chuva (mm)")
    WaterLevel_m: float = Field(..., description="Nível Rio (m)")
    class Config: extra = "ignore"

class DetalheBairro(BaseModel):
    risco: float
    elevacao_media: float
    classificacao: str

class RiscoOutput(RootModel):
    root: Dict[str, DetalheBairro]

app = FastAPI(title="Motor de Risco (Marés de Belém)", version="Final-Tide")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. O Endpoint Inteligente ---
@app.post("/prever_risco", response_model=RiscoOutput)
async def prever_risco(dados: RiscoInput):
    json_final = {}
    
    if predict_flood_risk is None:
        return {}

    # 1. DETECÇÃO DE CENÁRIOS (Baseado na Hidrografia de Belém)
    
    # Nível 4: CATÁSTROFE (Recorde histórico ou Dilúvio)
    # Maré > 3.8m OU Chuva > 100mm
    is_catastrofe = dados.WaterLevel_m >= 3.8 or dados.Rainfall_mm > 100

    # Nível 3: CRÍTICO (Transbordamento)
    # Maré > 3.5m (Água invade o Ver-o-Peso e canais)
    is_critico = dados.WaterLevel_m > 3.5

    # Nível 2: ALERTA (Sizígia)
    # Maré > 3.0m (Canais cheios, qualquer chuva alaga)
    is_alerta = dados.WaterLevel_m > 3.0

    for bairro, elevacao_fixa in BAIRROS_BELEM.items():
        
        # 2. Risco Base da IA
        risco_ia = predict_flood_risk(
            rainfall=dados.Rainfall_mm,
            water_level=dados.WaterLevel_m,
            elevation=elevacao_fixa
        )
        
        risco_ajustado = float(risco_ia)

        # 3. APLICAÇÃO DE VIÉS (Regra de Negócio Topográfica)
        
        if is_catastrofe:
            # CENÁRIO 4: Apocalipse. 
            # Ignora a altura. O risco da IA (que deve ser alto) prevalece puro.
            # Em zonas baixas, forçamos para o máximo.
            if elevacao_fixa < 6.0:
                risco_ajustado = 1.0
            else:
                risco_ajustado = risco_ajustado # Zonas altas seguem a IA
            
        elif is_critico:
            # CENÁRIO 3: Maré Crítica (> 3.5m)
            # Zonas Baixas (< 6m) SÃO SACRIFICADAS com força (+30%)
            if elevacao_fixa <= 6.0:
                risco_ajustado += 0.30
            # Zonas Altas ainda tem desconto, mas menor
            elif elevacao_fixa >= 10.0:
                risco_ajustado -= (elevacao_fixa * 0.03)

        elif is_alerta:
            # CENÁRIO 2: Maré Alta (> 3.0m)
            # Zonas Baixas ganham risco leve (+15%)
            if elevacao_fixa <= 6.0:
                risco_ajustado += 0.15
            # Zonas Altas funcionam normal
            elif elevacao_fixa >= 10.0:
                risco_ajustado -= (elevacao_fixa * 0.04)
                
        else:
            # CENÁRIO 1: Maré Normal (< 3.0m)
            # A altura protege bem todo mundo
            if elevacao_fixa >= 10.0:
                risco_ajustado -= (elevacao_fixa * 0.05) # Desconto forte
            elif elevacao_fixa > 6.0:
                risco_ajustado -= (elevacao_fixa * 0.02) # Desconto leve

        # 4. Travas e Classificação
        if risco_ajustado < 0.0: risco_ajustado = 0.0
        if risco_ajustado > 1.0: risco_ajustado = 1.0
        
        # Escala de Cores
        if risco_ajustado <= 0.45:
            label = "Baixo"   # Verde
        elif risco_ajustado <= 0.75: 
            label = "Médio"   # Amarelo
        else:
            label = "Alto"    # Vermelho

        json_final[bairro] = {
            "risco": round(risco_ajustado, 2),
            "elevacao_media": elevacao_fixa,
            "classificacao": label
        }

    return json_final