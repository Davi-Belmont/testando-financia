import yfinance as yf
import pandas as pd
import time
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
ARQUIVO_ENTRADA = os.path.join(DATA_DIR, 'minha_carteira.xlsx')
ARQUIVO_SAIDA = os.path.join(DATA_DIR, 'dashboard_investimentos.xlsx')

def inicializar_arquivos():
    #Garante que a pasta e o arquivo de entrada existam antes de processar
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Pasta {DATA_DIR} criada.")

    if not os.path.exists(ARQUIVO_ENTRADA):
        print(f"Planilha de entrada não encontrada. Criando modelo em: {ARQUIVO_ENTRADA}")
        
        # Modelo padrão com colunas que o código espera
        df_modelo = pd.DataFrame({
            'Ticker': ['TASA4', 'PETR4', 'VALE3'],
            'Preco Pago': [15.50, 32.10, 70.00],
            'Qtd': [100, 50, 20],
            'Corretora': ['Nubank', 'Inter', 'BTG']
        })
        

        df_modelo.to_excel(ARQUIVO_ENTRADA, index=False)
        return False # Indica que o arquivo acabou de ser criado e está vazio/com exemplo
    
    return True

def processar_investimentos():
    
    # 1. Tenta inicializar/verificar arquivos
    if not inicializar_arquivos():
        print("⚠️ Modelo criado. Por favor, edite a planilha 'minha_carteira.xlsx' com seus dados reais.")
        return

    # 2. LEITURA
    try:
        df = pd.read_excel(ARQUIVO_ENTRADA)
    except Exception as e:
        print(f"Erro ao ler a planilha: {e}")
        return

    # 3. PREPARAÇÃO DE TICKERS
    # Adiciona .SA se o usuário esqueceu (padrão B3 no Yahoo Finance)
    tickers_original = df['Ticker'].unique().tolist()
    tickers_yf = [t + ".SA" if not t.endswith(".SA") else t for t in tickers_original]

    # 4. BUSCA DE PREÇOS (INTRADAY)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Consultando Yahoo Finance...")
    dados_mercado = yf.download(tickers_yf, period="1d", interval="1m", progress=False)

    if dados_mercado.empty:
        print("Aviso: Não foi possível obter dados do mercado agora. O mercado pode estar fechado.")
        return

    # Mapeamento de preços
    precos_atuais = {}
    for t_yf in tickers_yf:
        ticker_limpo = t_yf.replace(".SA", "")
        try:
            # Lógica para lidar com DataFrame simples ou MultiIndex (quando há múltiplos tickers)
            if len(tickers_yf) > 1:
                coluna_close = dados_mercado['Close'][t_yf]
            else:
                coluna_close = dados_mercado['Close']
            
            ultimo_preco = coluna_close.dropna().iloc[-1]
            precos_atuais[ticker_limpo] = round(float(ultimo_preco), 2)
        except Exception:
            print(f"Não foi possível obter o preço de {t_yf}")
            precos_atuais[ticker_limpo] = 0

    # 5. CÁLCULOS NO DATAFRAME
    df['Preço Atual'] = df['Ticker'].map(precos_atuais)
    df['Total Pago'] = df['Preco Pago'] * df['Qtd']
    df['Valor Atualizado'] = df['Preço Atual'] * df['Qtd']
    df['Lucro/Prejuízo R$'] = df['Valor Atualizado'] - df['Total Pago']
    
    # Previne erro de divisão por zero na rentabilidade
    df['Rentabilidade %'] = (df['Lucro/Prejuízo R$'] / df['Total Pago'].replace(0, 1)) * 100
    df['Data Ultima Atualizacao'] = datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    # 6. EXPORTAÇÃO
    df.to_excel(ARQUIVO_SAIDA, index=False)
    print(f"Dashboard atualizado com sucesso! (Salvo em: {ARQUIVO_SAIDA})")

# LOOP DE EXECUÇÃO (15 EM 15 MINUTOS)
if __name__ == "__main__":
    print("Iniciando Motor de Monitoramento de Investimentos...")
    while True:
        try:
            processar_investimentos()
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
        
        print("Próxima atualização em 1 minutos. Aguardando...")
        time.sleep(60)