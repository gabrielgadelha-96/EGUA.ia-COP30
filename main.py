from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, RootModel
from typing import Dict

# --- 1. Importação Segura da IA ---
try:
    from use_model import predict_flood_risk
except ImportError:
    print("CRÍTICO: 'use_model.py' não encontrado.")
    predict_flood_risk = None

# --- 2. Lista Oficial: Bairros e Elevações (Fonte: Topografia Belém) ---
BAIRROS_BELEM = {
    # --- ZONA BAIXA (Risco Alto com Maré) ---
    "Jurunas": 4.0, "Condor": 4.0, "Guamá": 4.5, "Terra Firme": 4.5,
    "Cremação": 5.0, "Cidade Velha": 5.0, "Reduto": 5.0,
    "Campina": 6.0, "Comércio": 4.0, "Telégrafo": 5.0,
    "Barreiro": 5.0, "Sacramenta": 5.5, "Val-de-Cans": 4.0,
    "Pratinha": 4.0, "Miramar": 5.0, "Universitário": 5.0,
    "Maracacuera": 5.0, "Paracuri": 5.0, "Bengui": 6.0,
    
    # --- ZONA MÉDIA (Transição) ---
    "Umarizal": 6.0, "Batista Campos": 9.0, "Canudos": 8.0,
    "Fátima": 9.0, "Pedreira": 7.0, "Souza": 9.0,
    "Aurá": 8.0, "Cabanagem": 8.0, "Una": 7.0,
    "Tapanã": 7.0, "Agulha": 7.0, "Águas Negras": 6.0,
    "Campina de Icoaraci": 7.0, "Parque Guajará": 6.0,
    "Ponta Grossa": 6.0, "Maracangalha": 6.0,
    
    # --- ZONA ALTA / ESPIGÃO (Risco Baixo) ---
    "Nazaré": 13.0, "São Brás": 12.0, "Marco": 13.0,
    "Curió-Utinga": 10.0, "Guanabara": 10.0, "Castanheira": 11.0,
    "Marambaia": 12.0, "Mangueirão": 10.0, "Parque Verde": 14.0,
    "Coqueiro": 10.0, "Águas Lindas": 15.0, "São Clemente": 12.0,
    "Tenoné": 11.0, "Cruzeiro": 10.0
}

# --- 3. Contratos de Dados (Schemas) ---

class RiscoInput(BaseModel):
    # Recebe apenas o clima atual
    Rainfall_mm: float = Field(..., description="Chuva nas últimas 24h")
    WaterLevel_m: float = Field(..., description="Nível da maré")
    
    class Config:
        extra = "ignore"

class DetalheBairro(BaseModel):
    risco: float          # Será 0.0 ou 1.0
    elevacao_media: float

class RiscoOutput(RootModel):
    root: Dict[str, DetalheBairro]

# --- 4. Inicialização da API ---
app = FastAPI(title="Motor de Risco Belém (Final)", version="1.0.0")

# --- 5. CONFIGURAÇÃO DO CORS (Obrigatório para o Frontend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Permite acesso de qualquer site (Frontend)
    allow_credentials=True,
    allow_methods=["*"],      # Permite todos os métodos (POST, GET...)
    allow_headers=["*"],      # Permite todos os cabeçalhos
)

# --- 6. Endpoint Principal ---

@app.post("/prever_risco", response_model=RiscoOutput)
async def prever_risco(dados: RiscoInput):
    
    json_final = {}

    if predict_flood_risk is None:
        return {}

    # Loop pelos 48 bairros
    for bairro, elevacao_fixa in BAIRROS_BELEM.items():
        
        # 1. IA: Calcula o risco base com os dados atuais
        risco_ia = predict_flood_risk(
            rainfall=dados.Rainfall_mm,
            water_level=dados.WaterLevel_m,
            elevation=elevacao_fixa
        )
        
        # 2. CALIBRAGEM TOPOGRÁFICA
        # Subtrai 4% de risco para cada metro de altura.
        # Isso garante que bairros altos fiquem "Verdes" em chuvas médias.
        fator_seguranca = (elevacao_fixa * 0.04) 
        risco_ajustado = float(risco_ia) - fator_seguranca
        
        # 3. BINARIZAÇÃO (0 ou 1)
        if risco_ajustado > 0.5:
            risco_final = 1.0 # ALAGA (Vermelho)
        else:
            risco_final = 0.0 # SEGURO (Verde)

        # 4. Monta o JSON
        json_final[bairro] = {
            "risco": risco_final,
            "elevacao_media": elevacao_fixa
        }

    return json_final