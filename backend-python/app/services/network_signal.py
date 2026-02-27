from datetime import datetime, timedelta
from dtos.network_input import NetworkInput

def get_network_signals(client_ip: str, device_id: str, login_history: list) -> NetworkInput:
    WINDOW_MIN = 30
    time_limit = datetime.now() - timedelta(minutes=WINDOW_MIN)
    
    recent_ip_logs = [
        log for log in login_history 
        if log["ip"] == client_ip and log["timestamp"] > time_limit
    ]
    shared_ip_count = len({log["user_id"] for log in recent_ip_logs})
    
    recent_dev_logs = [
        log for log in login_history 
        if log["device_id"] == device_id and log["timestamp"] > time_limit
    ]
    shared_device_count = len({log["user_id"] for log in recent_dev_logs})
    
    return NetworkInput(
        shared_device_count=shared_device_count,
        shared_ip_count=shared_ip_count,
        cross_merchant_reuse=False
    )