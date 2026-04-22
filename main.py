import yfinance as yf
import pandas as pd
import datetime
import json
import os

pasta_data = 'data/historico'
if not os.path.exists(pasta_data):
    os.makedirs(pasta_data)

lista_acoes = ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "TASA4.SA", "ABEV3.SA"]

try:
    print("Consultando Yahoo Finance (Histórico)...")
    
    # Baixamos o período de 1 ano (dados consolidados)
    dados_hist = yf.download(lista_acoes, period="1y", interval="1d")

    for ticker in lista_acoes:
        print(f"Processando: {ticker}")
        
        # 2. Extraímos o histórico do ticker
        historico_acao = dados_hist.xs(ticker, axis=1, level=1).dropna()

        # 3. Criamos a lista de registros
        lista_registros = []
        for data_pregao, linha in historico_acao.iterrows():
            lista_registros.append({
                "data": data_pregao.strftime('%Y-%m-%d'),
                "preco": round(float(linha['Close']), 2),
                "atualizado_em": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "volume": int(linha['Volume'])
            })

        # 4. BUSCA O VALOR DE AGORA (Caso o dia de hoje não esteja no histórico ainda)
        print(f"Verificando cotação de hoje para {ticker}...")
        hoje = yf.download(ticker, period="1d", interval="1m").dropna()
        
        if not hoje.empty:
            ultima_data_hoje = hoje.index[-1].strftime('%Y-%m-%d')
            # Se a última data do histórico for diferente de hoje, nós adicionamos
            if lista_registros[-1]["data"] != ultima_data_hoje:
                ultima_linha_hoje = hoje.iloc[-1]
                lista_registros.append({
                    "data": ultima_data_hoje,
                    "preco": round(float(ultima_linha_hoje['Close']), 2),
                    "atualizado_em": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "volume": int(ultima_linha_hoje['Volume']),
                    "status": "intraday" # Marcador opcional para saber que é o preço de agora
                })

        # 5. Salvamos o arquivo individual
        nome_limpo = ticker.replace(".SA", "")
        caminho_arquivo = os.path.join(pasta_data, f'{nome_limpo}.json')
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(lista_registros, f, indent=4, ensure_ascii=False)

    print(f"\nSucesso! Arquivos gerados com histórico e valor atual em: {pasta_data}")

except Exception as e:
    print(f"Erro ao processar dados: {e}")