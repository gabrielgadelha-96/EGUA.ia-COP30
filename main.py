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
    # ZONA BAIXA
    "Jurunas": 4.0, "Condor": 4.0, "Guamá": 4.5, "Terra Firme": 4.5,
    "Cremação": 5.0, "Cidade Velha": 5.0, "Reduto": 5.0,
    "Campina": 6.0, "Comércio": 4.0, "Telégrafo": 5.0,
    "Barreiro": 5.0, "Sacramenta": 5.5, "Val-de-Cans": 4.0,
    "Pratinha": 4.0, "Miramar": 5.0, "Universitário": 5.0,
    "Maracacuera": 5.0, "Paracuri": 5.0, "Bengui": 6.0,
    
    # ZONA MÉDIA
    "Umarizal": 6.0, "Batista Campos": 9.0, "Canudos": 8.0,
    "Fátima": 9.0, "Pedreira": 7.0, "Souza": 9.0,
    "Aurá": 8.0, "Cabanagem": 8.0, "Una": 7.0,
    "Tapanã": 7.0, "Agulha": 7.0, "Águas Negras": 6.0,
    "Campina de Icoaraci": 7.0, "Parque Guajará": 6.0,
    "Ponta Grossa": 6.0, "Maracangalha": 6.0,
    
    # ZONA ALTA
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

app = FastAPI(title="Motor de Risco (Final)", version="1.0.0")

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

    # DETECTOR DE CATÁSTROFE: Se a chuva for extrema, ignora a altura
    is_catastrofe = dados.Rainfall_mm > 100 or dados.WaterLevel_m > 3.8

    for bairro, elevacao_fixa in BAIRROS_BELEM.items():
        
        # 1. Risco Base da IA
        risco_ia = predict_flood_risk(
            rainfall=dados.Rainfall_mm,
            water_level=dados.WaterLevel_m,
            elevation=elevacao_fixa
        )
        
        risco_ajustado = float(risco_ia)

        # 2. APLICAÇÃO DE VIÉS
        if is_catastrofe:
            # DILÚVIO: Ninguém é salvo pela altura. O risco da IA prevalece.
            risco_ajustado = risco_ajustado 
            
        elif elevacao_fixa <= 5.5:
            # BAIXADAS (Chuva Normal): SOMA risco para garantir vermelho
            risco_ajustado += 0.15 
            
        elif elevacao_fixa >= 10.0:
            # ALTOS (Chuva Normal): SUBTRAI muito risco (0.05) para garantir verde
            risco_ajustado -= (elevacao_fixa * 0.05) 
            
        else:
            # MÉDIOS (Chuva Normal): Subtrai pouco
            risco_ajustado -= (elevacao_fixa * 0.02)

        # 3. Travas
        if risco_ajustado < 0.0: risco_ajustado = 0.0
        if risco_ajustado > 1.0: risco_ajustado = 1.0
        
        # 4. Classificação
        if risco_ajustado <= 0.45:
            label = "Baixo"
        elif risco_ajustado <= 0.75: 
            label = "Médio"
        else:
            label = "Alto"

        json_final[bairro] = {
            "risco": round(risco_ajustado, 2),
            "elevacao_media": elevacao_fixa,
            "classificacao": label
        }

    return json_final