from fastapi import Request
from datetime import datetime, timedelta
from model.network_input import NetworkInput
from services.verify_geoip import get_real_ip
from agents.synthetic_network_agent import run_network_agent

def get_network_signals(client_ip: str, device_id: str, login_history: list) -> NetworkInput:
    """Fungsi pembantu (Private) untuk menghitung IP dan Device"""
    WINDOW_MIN = 30
    time_limit = datetime.now() - timedelta(minutes=WINDOW_MIN)
    
    recent_ip_logs = [log for log in login_history if log["ip"] == client_ip and log["timestamp"] > time_limit]
    shared_ip_count = len({log["user_id"] for log in recent_ip_logs})
    
    recent_dev_logs = [log for log in login_history if log["device_id"] == device_id and log["timestamp"] > time_limit]
    shared_device_count = len({log["user_id"] for log in recent_dev_logs})
    
    return NetworkInput(
        shared_device_count=shared_device_count,
        shared_ip_count=shared_ip_count,
        cross_merchant_reuse=False 
    )

async def evaluate_network_fraud_service(
    request: Request, 
    user_id: str, 
    device_id: str, 
    login_history: list
) -> dict:
    
    ip = get_real_ip(request)

    signals = get_network_signals(ip, device_id, login_history)

    agent_result = run_network_agent(signals)

    login_history.append({
        "user_id": user_id,
        "ip": ip,
        "device_id": device_id,
        "timestamp": datetime.now()
    })

    return {
        "status": 200,
        "ip_address": ip,
        "device_id": device_id,
        "signals_detected": {
            "shared_ip_count": signals.shared_ip_count,
            "shared_device_count": signals.shared_device_count
        },
        "ai_analysis": agent_result.model_dump() if hasattr(agent_result, 'model_dump') else agent_result.dict()
    }