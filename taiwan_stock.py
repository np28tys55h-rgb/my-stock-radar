import os
import sys
import time

# ==========================================
# 🌟 iPhone 免黑視窗專用：自動下載環境套件
# ==========================================
try:
    import yfinance as yf
    import lxml
except ImportError:
    print("📡 偵測到雲端主機尚未安裝套件，正在自動幫您裝載環境...")
    os.system(f"{sys.executable} -m pip install --user yfinance pandas lxml")
    print("✅ 環境裝載成功！重啟程式中...")
    # 讓程式自動重新讀取新安裝的套件
    os.execv(sys.executable, ['python3'] + sys.argv)

import requests
import pandas as pd
from datetime import datetime

# ==========================================
# ⚙️ 核心設定區：您的 Discord Webhook 網址
# ==========================================
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1509236757277708391/q01BcfdfN7Ya80lyOrM5v1m0JZQI7oT9xZHIo8eSx0SHPArpncB_NihO5MAfPVeepbXZ'

def send_discord(message):
    """發送 Discord 通知"""
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        return response.status_code in [200, 204]
    except:
        return False

def get_all_tw_tickers():
    """自動從證交所抓取所有最新的上市股票代號，並過濾掉權證與ETF"""
    print("📡 正在向台灣證券交易所獲取最新股票清單...")
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    
    try:
        tables = pd.read_html(url)
        df = tables[0]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        
        df = df[df['CFICode'] == 'ESVTFR']
        
        ticker_dict = {}
        for item in df['有價證券代號及名稱']:
            try:
                code, name = item.split('\u3000')
                if len(code) == 4 and code.isdigit():
                    ticker_dict[f"{code}.TW"] = name
            except:
                continue
                
        print(f"✅ 成功獲取上市股票共 {len(ticker_dict)} 檔！")
        return ticker_dict
    except Exception as e:
        print(f"❌ 擷取證交所清單失敗: {e}")
        return {"2330.TW": "台積電", "2317.TW": "鴻海"}

def scan_engine(stock_code, name):
    """核心濾網邏輯：均線糾結 + 爆量突破"""
    try:
        stock = yf.Ticker(stock_code)
        df = stock.history(period="35d", progress=False)
        
        if len(df) < 20:
            return False
            
        df = df.reset_index()
        df.columns = df.columns.str.lower()
        
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['vol_ma20'] = df['volume'].rolling(20).mean()
        
        today = df.iloc[-1]
        today_vol_sheets = today['volume'] / 1000
        avg_vol_20d_sheets = today['vol_ma20'] / 1000
        
        ma_list = [today['ma5'], today['ma10'], today['ma20']]
        dispersion = (max(ma_list) - min(ma_list)) / today['close'] * 100
        
        is_糾結 = dispersion <= 2.5
        is_站上均線 = today['close'] > max(ma_list)
        is_爆量 = today['volume'] > (today['vol_ma20'] * 1.8) and today_vol_sheets > 1000
        is_紅K = today['close'] > today['open'] * 1.025
        
        if is_糾結 and is_站上均線 and is_爆量 and is_紅K:
            msg = (
                f"```ini\n"
                f"🌟【全台股掃描：黑馬突破股現形】🌟\n"
                f"📌 股票：{stock_code.split('.')[0]} {name}\n"
                f"📈 收盤價：{today['close']:.2f} 元\n"
                f"📐 均線密集度：{dispersion:.2f}% (籌碼高度集中)\n"
                f"📊 今日成交量：{today_vol_sheets:.0f} 張 (達20日均量 {today_vol_sheets/max(1, avg_vol_20d_sheets):.1f} 倍)\n"
                f"📋 實戰備忘：此檔橫盤整理平台遭帶量長紅突破，請列入明日自選焦點！\n"
                f"```"
            )
            send_discord(msg)
            print(f"🎯 發現標的：{stock_code} {name}")
            return True
    except:
        pass
    return False

if __name__ == "__main__":
    start_time = datetime.now()
    send_discord(f"🚀 全台股雷達開工！開始全面清洗 1000 多檔標的...")
    
    watch_list = get_all_tw_tickers()
    match_count = 0
    
    for i, (code, name) in enumerate(watch_list.items()):
        if i % 50 == 0 and i > 0:
            time.sleep(0.5)
            print(f"已掃描 {i} 檔股票...")
            
        if scan_engine(code, name):
            match_count += 1
            
    end_time = datetime.now()
    duration = (end_time - start_time).seconds
    
    report = f"🏁 全台股地毯式掃描完畢！\n⏱️ 總耗時：{duration // 60} 分 {duration % 60} 秒\n🎯 今日符合【糾結爆量突破】共：{match_count} 檔。"
    print(report)
    send_discord(f"```\n{report}\n```")
