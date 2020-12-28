import json

from django.shortcuts import render
from django.http import JsonResponse

from src import generator
from src import simulator


def home(request):
    return render(request, 'home.html', {})


def results(request):
    request_data = json.loads(request.body)
    frequency = float(request_data["frequency"])
    bandwidth = float(request_data["bandwidth"])
    coordinates = request_data["coordinates"]
    radius = float(request_data["radius"])

    params = {
        "antenna_type": "macro",
        "avg_building_height": float(request_data["avg_building_height"]),
        "avg_street_width": float(request_data["avg_street_width"]),
        "tx_height": float(request_data["tx_height"]),
        "rx_height": float(request_data["rx_height"]),
        "area_type": "urban",
        "city_type": "large",
        "tx_power": float(request_data["tx_power"]),
        "tx_gain": float(request_data["tx_gain"]),
        "tx_losses": float(request_data["tx_losses"]),
        "rx_gain": float(request_data["rx_gain"]),
        "rx_losses": float(request_data["rx_losses"]),
    }

    data = generator.generate_data(coordinates, radius)
    sim = simulator.Simulator(data, params)
    results_dict = sim.run(frequency=frequency, bandwidth=bandwidth)

    complete_data = data["sites"].append(data["centroids"]).append(data["receivers"])
    complete_data.crs = "EPSG:3765"
    complete_data = complete_data.to_crs("EPSG:4326")
    complete_data = complete_data.to_json()
    results_dict["complete_data"] = complete_data

    return JsonResponse(results_dict, safe=False)
