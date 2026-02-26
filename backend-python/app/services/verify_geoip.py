from fastapi import HTTPException, Request
import requests

def is_private_ip(ip: str) -> bool:
    return ip.startswith((
        "127.", "10.", "192.168", "172.16", "::1"
    ))

def get_real_ip(request: Request) -> str:
    headers = request.headers

    if "x-forwarded-for" in headers:
        return headers["x-forwarded-for"].split(",")[0].strip()

    if "x-real-ip" in headers:
        return headers["x-real-ip"]

    return request.client.host

def get_ip_geo_ipinfo(ip: str):
    try:
        res = requests.get(
            f"https://ipinfo.io/{ip}/json",
            timeout=5
        )

        if res.status_code != 200:
            return None

        data = res.json()

        if "error" in data:
            return None

        return {
            "country": data.get("country"),
            "city": data.get("city")
        }

    except requests.exceptions.RequestException:
        return None

def get_ip_geo_ipapi(ip: str):
    try:
        res = requests.get(
            f"http://ip-api.com/json/{ip}",
            timeout=5
        )

        if res.status_code != 200:
            return None

        data = res.json()

        if data.get("status") != "success":
            return None

        return {
            "country": data.get("countryCode"),
            "city": data.get("city")
        }

    except requests.exceptions.RequestException:
        return None

def get_ip_geo(ip: str):
    if is_private_ip(ip):
        raise HTTPException(
            status_code=400,
            detail="INVALID_TEST_IP"
        )

    geo = get_ip_geo_ipinfo(ip)

    if not geo or not geo.get("country"):
        geo = get_ip_geo_ipapi(ip)

    if not geo or not geo.get("country"):
        raise HTTPException(
            status_code=400,
            detail="IP_LOCATION_NOT_FOUND"
        )

    return geo

async def check_geo_ip(
    ip: str,
    declared_country: str,
    declared_city: str = None
):
    input_country = declared_country.strip().upper()
    input_city = declared_city.strip().upper() if declared_city else None

    ip_geo = get_ip_geo(ip)

    ip_country = ip_geo["country"].strip().upper()
    ip_city = ip_geo["city"].strip().upper() if ip_geo.get("city") else None

    geo_ip_mismatch = False

    if ip_country != input_country:
        geo_ip_mismatch = True

    elif input_city and ip_city and ip_city != input_city:
        geo_ip_mismatch = True

    return {
        "success": True,
        "ip": ip,
        "declared_country": declared_country,
        "declared_city": declared_city,
        "ip_country": ip_country,
        "ip_city": ip_city,
        "geo_ip_mismatch": geo_ip_mismatch 
    }