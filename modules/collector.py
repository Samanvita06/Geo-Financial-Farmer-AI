def collect_data(city_name: str, bounds: dict = None) -> dict:
    """
    city_name: e.g. "Bangalore"
    bounds: optional dict from the map selector, like:
      {
        "center": {"lat": 12.97, "lon": 77.59},
        "bounds": {"north": 12.99, "south": 12.95, "east": 77.62, "west": 77.56},
        "area_km2": 14.5
      }
    """
    print(f"\n Locating '{city_name}'...")
    location = get_coordinates(city_name)
    lat = location["lat"]
    lon = location["lon"]

    # If user selected a specific land region, use its center instead
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
        import json
        bounds = json.loads("\n".join(lines))

    result = collect_data(city, bounds)
    print("\n--- OUTPUT ---")
    print(json.dumps(result, indent=2))