import requests
import json

def get_coordinates(city_name: str) -> dict:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "AgriMineralPipeline/1.0"}
    res = requests.get(url, params=params, headers=headers)
    results = res.json()
    if not results:
        raise ValueError(f"Location '{city_name}' not found.")
    result = results[0]
    return {
        "name": result.get("display_name"),
        "lat": float(result["lat"]),
        "lon": float(result["lon"])
    }

def get_weather(lat: float, lon: float) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "windspeed_10m",
            "weathercode"
        ],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum"
        ],
        "timezone": "auto",
        "forecast_days": 7
    }
    res = requests.get(url, params=params)
    data = res.json()
    return {
        "current": data.get("current", {}),
        "weekly_forecast": data.get("daily", {}),
        "timezone": data.get("timezone", "unknown")
    }

def get_elevation(lat: float, lon: float) -> dict:
    url = f"https://api.opentopodata.org/v1/srtm90m?locations={lat},{lon}"
    res = requests.get(url)
    results = res.json().get("results", [])
    elevation = results[0].get("elevation") if results else None
    return {
        "elevation_m": elevation,
        "terrain_note": classify_terrain(elevation)
    }

def classify_terrain(elevation_m) -> str:
    if elevation_m is None:
        return "unknown"
    elif elevation_m < 200:
        return "lowland / plains"
    elif elevation_m < 600:
        return "hilly"
    elif elevation_m < 1500:
        return "upland / plateau"
    else:
        return "mountainous"

def get_map_link(lat: float, lon: float, city_name: str) -> dict:
    return {
        "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=12",
        "google_maps": f"https://www.google.com/maps/@{lat},{lon},12z",
        "satellite_view": f"https://www.google.com/maps/@{lat},{lon},12z/data=!3m1!1e3"
    }

def collect_data(city_name: str, bounds: dict = None) -> dict:
    print(f"\n Locating '{city_name}'...")
    location = get_coordinates(city_name)
    lat = location["lat"]
    lon = location["lon"]

    if bounds:
        lat = bounds["center"]["lat"]
        lon = bounds["center"]["lon"]
        print(f" Using selected land region center: {lat}, {lon}")
    else:
        print(f" Using city center: {lat}, {lon}")

    print(" Fetching weather data...")
    weather = get_weather(lat, lon)

    print(" Fetching elevation/terrain data...")
    terrain = get_elevation(lat, lon)

    print(" Generating map links...")
    maps = get_map_link(lat, lon, city_name)

    output = {
        "input_city": city_name,
        "location": location,
        "selected_region": bounds if bounds else None,
        "weather": weather,
        "terrain": terrain,
        "maps": maps
    }

    print("\n Data collection complete!")
    return output


if __name__ == "__main__":
    city = input("Enter city name: ").strip()
    use_map = input("Did you select a land region from the map? (y/n): ").strip().lower()
    bounds = None

    if use_map == 'y':
        print("Paste the Python dict from the map tool, then press Enter twice:")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        bounds = json.loads("\n".join(lines))

    result = collect_data(city, bounds)
    print("\n--- OUTPUT ---")
    print(json.dumps(result, indent=2))