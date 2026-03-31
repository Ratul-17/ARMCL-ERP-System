"""
vehicle_routing.py
VRP/TSP optimizer for ARMCL-01 delivery routes.
Uses nearest-neighbor heuristic + Haversine distances.
OSRM public API used for real road polylines.
"""
import math
import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

# ── Depot ─────────────────────────────────────────────────────────────────────
DEPOT_LAT = 23.8490
DEPOT_LNG = 90.3580
DEPOT_NAME = "ARMCL-01 Depot (Dhour, Turag)"

# ── Cost Parameters (BDT) ──────────────────────────────────────────────────────
DRIVER_COST_PER_HOUR    = 180.0   # BDT/hour
FUEL_COST_PER_HOUR      = 250.0   # BDT/hour at avg speed
AVG_SPEED_KMPH          = 28.0    # Dhaka urban average
TRUCK_CAPACITY_M3       = 8.0     # m³ per truck load

# Traffic multipliers (increases time, hence cost)
TRAFFIC_FACTORS = {
    "Early Morning (6–8 AM)":  1.0,
    "Morning Peak (8–10 AM)":  1.6,
    "Mid Morning (10–12 PM)":  1.3,
    "Afternoon (12–3 PM)":     1.2,
    "Evening Peak (3–7 PM)":   1.8,
    "Night (7 PM+)":           1.1,
}

# ── Haversine distance (km) ────────────────────────────────────────────────────
def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ── Road distance factor (Dhaka roads ≈ 1.4× straight-line) ──────────────────
ROAD_FACTOR = 1.42

def road_distance(lat1, lng1, lat2, lng2) -> float:
    return haversine(lat1, lng1, lat2, lng2) * ROAD_FACTOR

# ── Nearest-neighbor TSP from depot ───────────────────────────────────────────
def nearest_neighbor_route(stops: List[Dict]) -> List[Dict]:
    """
    Given a list of stops [{client_name, lat, lng, ...}],
    returns them in nearest-neighbor order starting from depot.
    """
    if not stops:
        return []
    unvisited = stops.copy()
    route = []
    cur_lat, cur_lng = DEPOT_LAT, DEPOT_LNG

    while unvisited:
        nearest = min(unvisited, key=lambda s: road_distance(cur_lat, cur_lng, s["lat"], s["lng"]))
        route.append(nearest)
        cur_lat, cur_lng = nearest["lat"], nearest["lng"]
        unvisited.remove(nearest)

    return route

# ── Cost calculation ───────────────────────────────────────────────────────────
def calculate_route_cost(route: List[Dict], traffic_label: str) -> Dict:
    if not route:
        return {}

    traffic_factor = TRAFFIC_FACTORS.get(traffic_label, 1.0)
    total_cost_per_hour = DRIVER_COST_PER_HOUR + FUEL_COST_PER_HOUR

    # Build full path: depot → stop1 → ... → stopN → depot
    path = [(DEPOT_LAT, DEPOT_LNG)] + [(s["lat"], s["lng"]) for s in route] + [(DEPOT_LAT, DEPOT_LNG)]

    segments = []
    total_dist = 0.0
    for i in range(len(path) - 1):
        d = road_distance(path[i][0], path[i][1], path[i+1][0], path[i+1][1])
        total_dist += d
        travel_min = (d / AVG_SPEED_KMPH) * 60 * traffic_factor
        seg_cost   = (travel_min / 60) * total_cost_per_hour * traffic_factor

        from_name = DEPOT_NAME if i == 0 else route[i-1]["client_name"]
        to_name   = DEPOT_NAME if i == len(path)-2 else route[i]["client_name"]

        segments.append({
            "from":       from_name,
            "to":         to_name,
            "dist_km":    round(d, 2),
            "travel_min": round(travel_min, 1),
            "cost_bdt":   round(seg_cost, 0),
        })

    total_time_min  = sum(s["travel_min"] for s in segments)
    total_cost_bdt  = sum(s["cost_bdt"]  for s in segments)
    driver_cost     = round((total_time_min/60) * DRIVER_COST_PER_HOUR * traffic_factor, 0)
    fuel_cost       = round((total_time_min/60) * FUEL_COST_PER_HOUR   * traffic_factor, 0)

    return {
        "segments":        segments,
        "total_dist_km":   round(total_dist, 2),
        "total_time_min":  round(total_time_min, 1),
        "total_cost_bdt":  round(total_cost_bdt, 0),
        "driver_cost_bdt": driver_cost,
        "fuel_cost_bdt":   fuel_cost,
        "traffic_factor":  traffic_factor,
        "traffic_label":   traffic_label,
        "n_stops":         len(route),
    }

# ── OSRM route polyline ────────────────────────────────────────────────────────
def get_osrm_route(coords: List[Tuple[float,float]], timeout=8) -> List[List[float]]:
    """
    Fetch actual road route geometry from OSRM public API.
    coords: list of (lat, lng)
    Returns list of [lat, lng] waypoints for the polyline.
    Falls back to straight lines if OSRM is unavailable.
    """
    if len(coords) < 2:
        return []
    # OSRM expects lng,lat
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in coords)
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson"
    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            geo = resp.json()["routes"][0]["geometry"]["coordinates"]
            return [[pt[1], pt[0]] for pt in geo]  # convert to [lat,lng]
    except Exception:
        pass
    # Fallback: straight lines
    return [[lat, lng] for lat, lng in coords]

# ── Cluster stops into truck loads ────────────────────────────────────────────
def cluster_into_trucks(stops: List[Dict]) -> List[List[Dict]]:
    """Split stops into truck loads by capacity."""
    trucks, current, current_load = [], [], 0.0
    for stop in stops:
        qty = float(stop.get("qty_m3", 0))
        if current_load + qty > TRUCK_CAPACITY_M3 and current:
            trucks.append(current)
            current, current_load = [], 0.0
        current.append(stop)
        current_load += qty
    if current:
        trucks.append(current)
    return trucks

# ── Main optimization entry point ─────────────────────────────────────────────
def optimize_day(df_day: pd.DataFrame, traffic_label: str) -> Dict:
    """
    Full optimization for a single day's deliveries.
    Returns dict with route, cost breakdown, and map data.
    """
    stops = df_day[["client_name","project_address","lat","lng","qty_m3","psi","pump_status"]].to_dict("records")
    route = nearest_neighbor_route(stops)
    cost  = calculate_route_cost(route, traffic_label)

    # Coords for OSRM (depot + route + depot)
    all_coords = (
        [(DEPOT_LAT, DEPOT_LNG)] +
        [(s["lat"], s["lng"]) for s in route] +
        [(DEPOT_LAT, DEPOT_LNG)]
    )
    # Limit to 25 waypoints for OSRM free tier
    if len(all_coords) > 25:
        sampled = [all_coords[0]] + all_coords[1:-1:max(1,(len(all_coords)-2)//23)] + [all_coords[-1]]
        polyline = get_osrm_route(sampled)
    else:
        polyline = get_osrm_route(all_coords)

    trucks = cluster_into_trucks(route)

    return {
        "route":      route,
        "cost":       cost,
        "polyline":   polyline,
        "trucks":     trucks,
        "n_trucks":   len(trucks),
        "all_coords": all_coords,
    }
