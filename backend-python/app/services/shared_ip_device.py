from datetime import datetime, timedelta

def analyze_fraud(user_id: str, device_id: str, client_ip: str, login_history: list):
    IP_THRESHOLD = 10
    DEVICE_THRESHOLD = 3
    WINDOW_MIN = 10

    time_limit = datetime.now() - timedelta(minutes=WINDOW_MIN)
    
    recent_ip_logs = [log for log in login_history if log["ip"] == client_ip and log["timestamp"] > time_limit]
    unique_users_ip = {log["user_id"] for log in recent_ip_logs}
    ip_count = len(unique_users_ip)
    
    recent_dev_logs = [log for log in login_history if log["device_id"] == device_id and log["timestamp"] > time_limit]
    unique_users_dev = {log["user_id"] for log in recent_dev_logs}
    dev_count = len(unique_users_dev)

    verdict = "CLEAN"
    score = 0
    reasons = []

    if ip_count >= IP_THRESHOLD:
        verdict = "BANNED"
        score = 100
        reasons.append(f"Detected Bot Farm: {ip_count} users on same IP")
    elif dev_count >= DEVICE_THRESHOLD:
        verdict = "FLAGGED"
        score = 75
        reasons.append(f"High Device Sharing: {dev_count} users on same device")

    return {
        "verdict": verdict,
        "fraud_score": score,
        "reasons": reasons,
        "detail": {
            "ip_users_count": ip_count,
            "device_users_count": dev_count
        }
    }