
import requests
from fastapi import (
    FastAPI,
    Form,
    Depends,
    BackgroundTasks,
    Request,
    status,
    HTTPException,
)
def get_public_ip():
    """Fetch the public IP address using an external service."""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()  # Raise an error for bad status codes
        ip = response.json()["ip"]
        return ip
    except requests.RequestException as e:
        print(f"Error fetching public IP: {e}")
        return None
    

# List to store IP addresses
ip_log = []


def get_geo_location(ip):
    """Get the latitude and longitude for an IP address using a third-party API."""
    try:
        # getting public ip, can be commented out when hosted on server
        ip = get_public_ip()
        response = requests.get(f"http://ip-api.com/json/{ip}")
        geo_data = response.json()
        print(geo_data)
        return geo_data['lat'], geo_data['lon']
    except:
        return None, None


@app.get("/log_ip")
async def log_ip(request: Request):
    """Log the user's IP address and return a confirmation."""
    # client_ip = request.client.host
    client_ip = get_public_ip()
    print(client_ip)
    ip_log.append(client_ip)
   
    for ip in ip_log:
        lat, lon = get_geo_location(ip)
        print(lat,lon)
        if lat and lon:
            geo_data.append({"ip": ip, "latitude": lat, "longitude": lon})
    return {"logged_ips": geo_data}

@app.get("/get_ips")
async def get_ips():
    """Return the list of logged IP addresses with geolocation data."""
    return {"logged_ips": geo_data}

@app.get("/map", response_class=HTMLResponse)
async def display_map():
    """Display a map with all logged IP addresses."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IP Address Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    </head>
    <body>
        <div id="map" style="width: 100%; height: 500px;"></div>
        <script>
            var map = L.map('map').setView([0, 0], 2);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            // Fetch IP data
            fetch('/get_ips')
                .then(response => response.json())
                .then(data => {
                    const ips = data.logged_ips;
                    ips.forEach(ipData => {
                        L.marker([ipData.latitude, ipData.longitude]).addTo(map)
                            .bindPopup('IP: ' + ipData.ip)
                            .openPopup();
                    });
                });
        </script>
    </body>
    </html>
    """



    log_ip(request)