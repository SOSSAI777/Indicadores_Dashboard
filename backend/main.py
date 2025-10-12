from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import redis
import json
import asyncio
from datetime import datetime
import logging

# Importações dos serviços
from data_service import DataService
from websocket_service import websocket_manager, realtime_service
from alert_service import AlertService, AlertNotifier
from backtest_engine import BacktestEngine
from annotation_service import AnnotationService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar aplicação
app = FastAPI(title="TradingView Clone API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# Inicializar serviços
data_service = DataService()
backtest_engine = BacktestEngine()
alert_service = AlertService(redis_client)
annotation_service = AnnotationService(redis_client)
alert_notifier = AlertNotifier(websocket_manager, alert_service)

# Endpoints básicos
@app.get("/")
async def root():
    return {
        "message": "TradingView Clone API - Fase 3",
        "status": "online",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/symbols")
async def get_available_symbols():
    """Retorna lista de símbolos disponíveis"""
    return {
        "symbols": data_service.get_available_symbols(),
        "count": len(data_service.get_available_symbols())
    }

@app.get("/api/chart/{symbol}")
async def get_chart_data(
    symbol: str,
    interval: str = "1d",
    period: str = "6mo"
):
    """Endpoint principal para dados do gráfico"""
    try:
        result = data_service.get_historical_data(symbol, interval, period)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/api/chart/{symbol}/with-indicators")
async def get_chart_with_indicators(
    symbol: str,
    interval: str = "1d",
    period: str = "6mo",
    indicators: str = None
):
    """Endpoint com indicadores técnicos"""
    try:
        selected_indicators = indicators.split(",") if indicators else None
        
        result = data_service.get_historical_data_with_indicators(
            symbol, interval, period, selected_indicators
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

# WebSocket endpoint
@app.websocket("/ws/realtime/{client_id}")
async def websocket_realtime(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    try:
        # Cliente envia os símbolos que quer acompanhar
        data = await websocket.receive_text()
        subscription = json.loads(data)
        symbols = subscription.get('symbols', [])
        
        await websocket_manager.connect(websocket, client_id, symbols)
        
        # Envia dados iniciais em cache
        for symbol in symbols:
            cached_data = realtime_service.get_cached_data(symbol)
            if cached_data:
                await websocket.send_json(cached_data)
        
        # Mantém conexão aberta
        while True:
            # Heartbeat para manter conexão
            await asyncio.sleep(30)
            await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, symbols)
    except Exception as e:
        logger.error(f"Erro WebSocket: {e}")
        websocket_manager.disconnect(websocket, symbols)

# Endpoints de Alertas (que você já tem)
@app.post("/api/alerts/{user_id}")
async def create_alert(user_id: str, alert_data: dict):
    """Cria um novo alerta"""
    alert = alert_service.create_alert(user_id, alert_data)
    if alert:
        return JSONResponse(content=alert)
    raise HTTPException(status_code=400, detail="Erro ao criar alerta")

@app.get("/api/alerts/{user_id}")
async def get_user_alerts(user_id: str):
    """Recupera alertas do usuário"""
    alerts = alert_service.get_user_alerts(user_id)
    return JSONResponse(content=alerts)

@app.delete("/api/alerts/{user_id}/{alert_id}")
async def delete_alert(user_id: str, alert_id: str):
    """Remove alerta"""
    if alert_service.delete_alert(user_id, alert_id):
        return {"message": "Alerta removido"}
    raise HTTPException(status_code=404, detail="Alerta não encontrado")

# Endpoints de Backtest (que você já tem)
@app.post("/api/backtest")
async def run_backtest(backtest_request: dict):
    """Executa backtest"""
    try:
        # Busca dados históricos
        symbol = backtest_request['symbol']
        data = data_service.get_historical_data(symbol, "1d", "1y")
        
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        
        # Converte para DataFrame
        df = pd.DataFrame(data['data'])
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('datetime', inplace=True)
        
        # Executa backtest
        results = backtest_engine.run_backtest(
            backtest_request['strategy_config'], 
            df
        )
        
        return JSONResponse(content=results)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoints de Anotações (que você já tem)
@app.post("/api/annotations/{user_id}")
async def create_annotation(user_id: str, annotation_data: dict):
    """Cria uma nova anotação"""
    annotation = annotation_service.create_annotation(user_id, annotation_data)
    if annotation:
        return JSONResponse(content=annotation)
    raise HTTPException(status_code=400, detail="Erro ao criar anotação")

@app.get("/api/annotations/{user_id}")
async def get_user_annotations(user_id: str, symbol: str = None):
    """Recupera anotações do usuário"""
    annotations = annotation_service.get_user_annotations(user_id, symbol)
    return JSONResponse(content=annotations)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tradingview-api"}

# Iniciar serviço de tempo real quando a aplicação iniciar
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(realtime_service.start_real_time_updates())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)