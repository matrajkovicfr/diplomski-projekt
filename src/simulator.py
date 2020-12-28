import numpy as np

from loss import get_loss_object


class Simulator(object):

    def __init__(self, data, params):

        self.antenna = data["antenna"]
        self.sites = data["sites"]
        self.centroids = data["centroids"]
        self.receivers = data["receivers"]

        self.params = params

    def run(self, frequency, bandwidth):

        #results = []
        results = {
            "frequency": [],
            "bandwidth": [],
            "distance": [],
            "loss": [],
            "eirp": [],
            "received_power": [],
            "noise": [],
            "snr": [],
            "capacity": [],
            "interference_power": [],
            "sinr": []
        }

        for receiver in self.receivers:

            distance = round(self.antenna.distance(receiver), 2)
            loss = self.compute_path_loss(frequency, distance)
            if loss is None: continue

            eirp, received_power = self.compute_received_power(loss)
            noise = self.compute_thermal_noise(bandwidth)
            snr = self.compute_snr(received_power, noise)
            capacity = self.compute_capacity(bandwidth, snr)
            interference_power = self.compute_interference(frequency, receiver)
            sinr = self.compute_sinr(received_power, noise, interference_power)

            results["frequency"].append(frequency)
            results["bandwidth"].append(bandwidth)
            results["distance"].append(distance)
            results["loss"].append(loss)
            results["eirp"].append(eirp)
            results["received_power"].append(received_power)
            results["noise"].append(noise)
            results["snr"].append(snr)
            results["capacity"].append(capacity)
            results["interference_power"].append(interference_power)
            results["sinr"].append(sinr)

            """
            result = {
                "frequency": frequency,
                "distance": distance,
                "loss": loss,
                "eirp": eirp,
                "received_power": received_power,
                "noise": noise,
                "snr": snr,
                "capacity": capacity,
                "interference_power": interference_power,
                "sinr": sinr
            }
            results.append(result)
            """

        return results

    """
    Returns path loss in dB
    """
    def compute_path_loss(self, frequency, distance):
        loss_object = get_loss_object(frequency, self.params["area_type"], self.params["city_type"], self.params["antenna_type"], self.params["avg_building_height"], self.params["avg_street_width"])
        if loss_object.min_distance <= distance <= loss_object.max_distance:
            loss = loss_object.compute_loss(frequency, distance, self.params["tx_height"], self.params["rx_height"])
            return loss
        return None

    """
    Optional method for path loss: respecting path loss
    accuracy for given distance and model is not guaranteed
    """
    def compute_path_loss_optional(self, frequency, distance):
        loss_object = get_loss_object(frequency, self.params["area_type"], self.params["city_type"], self.params["antenna_type"], self.params["avg_building_height"], self.params["avg_street_width"])
        loss = loss_object.compute_loss(frequency, distance, self.params["tx_height"], self.params["rx_height"])
        return loss

    """
    Method returns EIRP and received power in dBm
    
    EIRP = transmitter output power [dBm] + transmitter antenna gain [dBi] - transmitter losses [dB]
    Received power = EIRP - path loss [dB] + receiver antenna gain [dBi] - receiver losses [dB] 
    """
    def compute_received_power(self, path_loss):
        eirp = self.params["tx_power"] + self.params["tx_gain"] - self.params["tx_losses"]
        received_power = eirp - path_loss + self.params["rx_gain"] - self.params["rx_losses"]
        return round(eirp, 2), round(received_power, 2)


    """
    Method returns Johnson-Nyquist noise in dBm
    Thermal noise [dBm] = 10*log10(k * T * B)
        k = Boltzmann constant, 1.38 * 10^-23
        T = temperature in K
        B = bandwidth in Hz
    
    Parameters:
        bandwidth: bandwidth in MHz
        temperature: temperature in K
    """
    def compute_thermal_noise(self, bandwidth, temperature=300):
        noise = 10 * np.log10(1.38e-23 * temperature * bandwidth * 1e6 / 1e-3)
        return round(noise, 2)

    """
    Returns signal to noise ratio in dBm
    
    Parameters:
        signal: received power for receiver in dBm
        noise: thermal noise in dBm
    """
    def compute_snr(self, signal, noise):
        snr = signal - noise
        snr = max(snr, 0)
        return round(snr, 2)

    """
    Returns capacity in kbits/s
    
    Parameters:
        bandwidth: channel bandwidth in MHz
        snr: signal to noise ratio in dBm
    """
    def compute_capacity(self, bandwidth, snr):
        capacity = bandwidth * 1e6 * np.log2(1 + snr)
        capacity /= 1e3
        return round(capacity, 2)

    def compute_interference(self, frequency, receiver):

        interference = 0.0

        for transmitter in self.centroids[1:]:
            distance = round(receiver.distance(transmitter), 2)
            loss = self.compute_path_loss_optional(frequency, distance)
            eirp, received_power = self.compute_received_power(loss)
            interference += received_power

        return round(interference, 2)

    def compute_sinr(self, signal, noise, interference):

        # dBm to W conversion
        signal = 0.001 * np.power(10, signal / 10)
        noise = 0.001 * np.power(10, noise / 10)
        interference = 0.001 * np.power(10, interference / 10)

        sinr = 10*np.log10(signal / (noise + interference))

        return round(sinr, 2)
