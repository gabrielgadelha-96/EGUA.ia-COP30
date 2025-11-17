## 📖 README do Projeto de Previsão de Enchente (Random Forest)

Este projeto demonstra como treinar um modelo de Machine Learning (**Random Forest Classifier**) usando dados climáticos e geográficos do Kaggle e, em seguida, como salvar e utilizar esse modelo para fazer previsões de risco de enchente.

-----

## 1\. ⚙️ Pré-requisitos e Instalação

Para executar este projeto, você precisará ter o **Python** instalado e as seguintes bibliotecas. É altamente recomendável usar um **ambiente virtual**.

### Instalação das Bibliotecas

Execute o comando abaixo no seu terminal para instalar todas as dependências necessárias:

```bash
pip install pandas scikit-learn joblib numpy kagglehub
```

-----

## 2\. 📂 Estrutura do Projeto

O projeto é dividido em dois arquivos principais para separar as responsabilidades de treinamento e uso do modelo.

  * **`train_model.py`**: Baixa o dataset do Kaggle, realiza o pré-processamento, treina o modelo **Random Forest Classifier** e salva o modelo treinado.
  * **`use_model.py`**: Carrega o modelo salvo e o utiliza para prever o risco de enchente com novos dados de entrada.
  * **`random_forest_flood_classifier_model.joblib`**: O arquivo binário do modelo treinado (será gerado após a execução de `train_model.py`).

-----

## 3\. Como Usar

Siga estes passos na ordem para treinar e, em seguida, usar o seu modelo.

### Passo 1: Treinar e Salvar o Modelo

O script `train_model.py` é responsável por todo o processo de Machine Learning, desde a aquisição dos dados até o salvamento do modelo.

Mas, já existe o script do modelo treinado, então você pode pular para a etapa de execução do modelo. Pode seguir do passo 2.

#### Execução:

1.  Abra o seu terminal no diretório do projeto.

2.  Execute o arquivo de treinamento:

    ```bash
    python train_model.py
    ```

#### O que Acontece:

  * O script baixa automaticamente o dataset do Kaggle (usando `kagglehub`).
  * Ele carrega o arquivo CSV, identifica as colunas de entrada e a coluna alvo (`FloodOccurrence`).
  * Treina o **Random Forest Classifier**.
  * Salva o modelo no arquivo **`random_forest_flood_classifier_model.joblib`**.

-----

### Passo 2: Usar o Modelo Salvo para Previsão

O script `use_model.py` simula o uso do modelo em um ambiente de produção, carregando-o e fazendo uma previsão com dados de entrada.

#### Execução:

1.  Certifique-se de que o `train_model.py` foi executado com sucesso e que o arquivo `.joblib` existe.

2.  Execute o arquivo de uso:

    ```bash
    python use_model.py
    ```

#### O que Acontece:

  * O script **carrega** o modelo `random_forest_flood_classifier_model.joblib`.
  * Ele define um conjunto de dados de teste (simulando uma leitura de sensores).
  * Faz uma previsão, que será **0** (Sem Enchente) ou **1** (Risco de Enchente), com base nas colunas:
      * `Rainfall_mm` (Chuva em mm)
      * `WaterLevel_m` (Nível da Água em metros)
      * `Elevation_m` (Elevação da Cidade em metros)

-----

## 4\. Personalização do `use_model.py`

Você pode facilmente testar o modelo com seus próprios dados de entrada editando a função `predict_flood_risk` no `use_model.py`.

### Exemplo de Alteração:

Para testar um cenário de baixa chuva e nível de água:

```python
if __name__ == '__main__':
    # Novos dados para previsão: Baixa chuva, nível baixo, elevação alta
    chuva_baixa = 10.5
    nivel_baixo = 0.5
    elevacao_alta = 45.0
    umidade_normal = 50.0 # Adicione a umidade do solo

    # A função agora requer 4 parâmetros
    predict_flood_risk(chuva_baixa, nivel_baixo, elevacao_alta)
```

**Lembre-se de manter a ordem dos parâmetros:** `Rainfall_mm`, `WaterLevel_m`, `Elevation_m`.