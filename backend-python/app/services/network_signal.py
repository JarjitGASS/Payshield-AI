from datetime import datetime, timedelta
from dtos.network_input import NetworkInput

def get_network_signals(client_ip: str, device_id: str, login_history: list) -> NetworkInput:
    WINDOW_MIN = 30
    time_limit = datetime.now() - timedelta(minutes=WINDOW_MIN)
    
    recent_ip_logs = []
    recent_dev_logs = []
    
    for log in login_history:
        log_time = log.get("timestamp")
        if not log_time:
            continue
            
        if isinstance(log_time, str):
            try:
                log_time = datetime.fromisoformat(log_time.replace("Z", "+00:00"))
            except ValueError:
                continue
                
        if getattr(log_time, "tzinfo", None) is not None:
            log_time = log_time.replace(tzinfo=None)
            
        if log_time > time_limit:
            if log.get("ip") == client_ip:
                recent_ip_logs.append(log)
            if log.get("device_id") == device_id:
                recent_dev_logs.append(log)
                
    shared_ip_count = len({log["user_id"] for log in recent_ip_logs})
    shared_device_count = len({log["user_id"] for log in recent_dev_logs})
    
    return NetworkInput(
        shared_device_count=shared_device_count,
        shared_ip_count=shared_ip_count,
        cross_merchant_reuse=False 
    )