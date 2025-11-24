from fastapi import FastAPI
from pydantic import BaseModel, Field, RootModel
from typing import Dict

# --- 1. Importação Segura da IA ---
try:
    from use_model import predict_flood_risk
except ImportError:
    print("CRÍTICO: 'use_model.py' não encontrado.")
    predict_flood_risk = None

# --- 2. DADOS: O Backend detém o conhecimento das elevações ---
# Lista oficial dos bairros continentais de Belém e suas cotas médias.
# Fonte aproximada: Topografia de Belém (Baixadas vs Espigão).

BAIRROS_BELEM = {
    # --- ZONA BAIXA (Cota 4m - 6m) -> Alto Risco de Maré ---
    "Jurunas": 4.0,
    "Condor": 4.0,
    "Guamá": 4.5,
    "Terra Firme": 4.5,
    "Cremação": 5.0,
    "Cidade Velha": 5.0,
    "Reduto": 5.0,
    "Campina": 6.0,
    "Comércio": 4.0,
    "Telégrafo": 5.0,
    "Barreiro": 5.0,
    "Sacramenta": 5.5,
    "Val-de-Cans": 4.0,
    "Pratinha": 4.0,
    "Miramar": 5.0,
    "Universitário": 5.0,
    "Maracacuera": 5.0,
    "Paracuri": 5.0,
    
    # --- ZONA MÉDIA (Cota 6m - 9m) ---
    "Umarizal": 6.0,
    "Batista Campos": 9.0,
    "Canudos": 8.0,
    "Fátima": 9.0,
    "Pedreira": 7.0,
    "Souza": 9.0,
    "Aurá": 8.0,
    "Cabanagem": 8.0,
    "Una": 7.0,
    "Tapanã": 7.0,
    "Bengui": 6.0,
    "Agulha": 7.0,
    "Águas Negras": 6.0,
    "Campina de Icoaraci": 7.0,
    "Parque Guajará": 6.0,
    "Ponta Grossa": 6.0,
    "Maracangalha": 6.0,
    
    # --- ZONA ALTA (Cota > 10m) -> Baixo Risco ---
    "Nazaré": 13.0,
    "São Brás": 12.0,
    "Marco": 13.0,
    "Curió-Utinga": 10.0,
    "Guanabara": 10.0,
    "Castanheira": 11.0,
    "Marambaia": 12.0,
    "Mangueirão": 10.0,
    "Parque Verde": 14.0,
    "Coqueiro": 10.0,
    "Águas Lindas": 15.0,
    "São Clemente": 12.0,
    "Tenoné": 11.0,
    "Cruzeiro": 10.0
}

# --- 3. Contratos de Dados (Schemas) ---

class RiscoInput(BaseModel):
    # O Frontend envia apenas o clima atual (O que muda no tempo)
    Rainfall_mm: float = Field(..., description="Chuva nas últimas 24h")
    WaterLevel_m: float = Field(..., description="Nível da maré")
    
    class Config:
        extra = "ignore"

# Modelo de DETALHE do bairro (O que o frontend vai ler)
class DetalheBairro(BaseModel):
    risco: float          # O valor predito (0 ou 1, ou decimal)
    elevacao_media: float # A elevação usada no cálculo

class RiscoOutput(RootModel):
    # O JSON final será: { "NomeBairro": { "risco": X, "elevacao_media": Y } }
    root: Dict[str, DetalheBairro]

# --- 4. Inicialização da API ---
app = FastAPI(title="Motor de Risco Belém", version="Final")

# --- 5. O Loop Simplificado ---

@app.post("/prever_risco", response_model=RiscoOutput)
async def prever_risco(dados: RiscoInput):
    
    json_final = {}

    # Segurança: Se a IA falhar, retorna vazio
    if predict_flood_risk is None:
        return {}

    # LOOP CENTRAL:
    # Percorre cada bairro, puxa a elevação fixa, calcula com a chuva atual
    # e escreve no dicionário final.
    for bairro, altitude_fixa in BAIRROS_BELEM.items():
        
        # 1. Puxa os valores e Calcula
        risco_ia = predict_flood_risk(
            rainfall=dados.Rainfall_mm,
            water_level=dados.WaterLevel_m,
            elevation=altitude_fixa
        )
        
        # 2. Escreve no JSON final
        json_final[bairro] = {
            "risco": float(risco_ia),
            "elevacao_media": altitude_fixa
        }

    return json_final