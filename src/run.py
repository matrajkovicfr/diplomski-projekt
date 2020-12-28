import matplotlib.pyplot as plt

from generator import *
from simulator import Simulator

COORDINATES = (45.801509, 15.971139)
RADIUS = 4000


data = generate_data(COORDINATES, RADIUS)

params = {
    "antenna_type": "macro",
    "avg_building_height": 5.0,
    "avg_street_width": 20.0,
    "tx_height": 40.0,
    "rx_height": 1.5,
    "area_type": "urban",
    "city_type": "large",

    "tx_power": 46.0,
    "tx_gain": 18.0,
    "tx_losses": 2.0,

    "rx_gain": 4.0,
    "rx_losses": 1.0,

}

simulator = Simulator(data, params)
results = simulator.run(frequency=2, bandwidth=20.0)

plt.plot(results["distance"], results["sinr"])
plt.show()