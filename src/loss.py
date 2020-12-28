import numpy as np

"""
Method determines valid propagation model for given frequency
and returns path loss rounded to 2 decimal places

Parameters:
    frequency: channel frequency in GHz
    area_type: urban, suburban or rural
    city_type: small, medium or large
    antenna_type: macro or micro
    avg_building_height: average building height in meters
    avg_street_width: average street width in meters
    
Returns:
    loss: path loss in dB
"""

def get_loss_object(frequency, area_type=None, city_type=None, antenna_type=None, avg_building_height=None, avg_street_width=None):
    if 0.15 <= frequency < 2:
        return OkumuraHata(area_type, city_type)
    if 2 <= frequency <= 100:
        return Etsi(area_type, antenna_type, avg_building_height, avg_street_width)
    else:
        raise ValueError("Frequency out of range")


"""
Base class for loss models
"""

class Loss(object):

    """
    Class initializer

    Parameters:
        area_type: urban, suburban or rural
    """

    def __init__(self, area_type=None):
        self.area_type = area_type
        self.min_distance = None
        self.max_distance = None
        self.name = None

    """
    Abstract method for calculating path loss
    
    Parameters:
        frequency: channel frequency in GHz
        distance: distance between transmitter and receiver in meters
        tx_height: transmitter height
        rx_height: receiver height
    """
    def compute_loss(self, frequency, distance, tx_height, rx_height):
        pass


"""
Okumura Hata propagation model for path loss
"""

class OkumuraHata(Loss):

    def __init__(self, area_type, city_type):
        super().__init__(area_type)
        self.city_type = city_type
        self.min_distance = 1000
        self.max_distance = 10000
        self.name = "Okumura-Hata"

    def compute_loss(self, frequency, distance, tx_height, rx_height):

        frequency = frequency * 1000    # Conversion from GHz to MHz
        distance = distance / 1000      # Conversion from m to km

        if self.city_type == 'small' or self.city_type == 'medium':
            correction_factor = 0.8 + (1.1 * np.log10(frequency) - 0.7) * rx_height - 1.56 * np.log10(frequency)
        elif self.city_type == 'large':
            if 150 <= frequency <= 200:
                correction_factor = 8.29 * np.power(np.log10(1.54 * rx_height), 2) - 1.1
            elif 200 <= frequency <= 1500:
                correction_factor = 3.2 * np.power(np.log10(11.75 * rx_height), 2) - 4.97
            else:
                correction_factor = 0.0
        else:
            raise ValueError("Incorrect city type")

        loss = 69.55 + 26.16 * np.log10(frequency) - 13.82 * np.log10(tx_height) - correction_factor + (
                    44.9 - 6.55 * np.log10(tx_height)) * np.log10(distance)

        if self.area_type == 'urban':
            return round(loss, 2)
        elif self.area_type == 'suburban':
            loss += -2 * np.power(np.log10(frequency / 28), 2) - 5.4
            return round(loss, 2)
        elif self.area_type == 'rural':
            loss += -4.78 * np.power(np.log10(frequency), 2) + 18.33 * np.log10(frequency) - 40.94
            return round(loss, 2)


"""
Propagation model for path loss as defined in ETSI TR 38 901
"""

class Etsi(Loss):

    def __init__(self, area_type, antenna_type, avg_building_height=None, avg_street_width=None):

        super().__init__(area_type)
        self.antenna_type = antenna_type
        self.avg_building_height = avg_building_height
        self.avg_street_width = avg_street_width
        self.name = "ETSI-TR-38-901"

        if self.avg_building_height is None:
            self.avg_building_height = 5.0
        if self.avg_street_width is None:
            self.avg_street_width = 20.0

        if area_type == "urban" and antenna_type == "macro":
            self.min_distance = 10
            self.max_distance = 5000

        elif area_type == "urban" and antenna_type == "micro":
            self.min_distance = 10
            self.max_distance = 5000

        elif area_type == "rural" and antenna_type == "macro":
            self.min_distance = 10
            self.max_distance = 10000

    def compute_loss(self, frequency, distance, tx_height, rx_height):

        if self.area_type == "urban" and self.antenna_type == "macro":
            return etsi_urban_macro_loss(frequency, distance, tx_height, rx_height)

        elif self.area_type == "urban" and self.antenna_type == "micro":
            return etsi_urban_micro_loss(frequency, distance, tx_height, rx_height)

        elif self.area_type == "rural" and self.antenna_type == "macro":
            return etsi_rural_macro_loss(frequency, distance, tx_height, rx_height, self.avg_building_height, self.avg_street_width)


def etsi_urban_macro_loss(frequency, distance, tx_height, rx_height):

    distance2d = distance
    distance3d = np.sqrt(np.power(distance2d, 2) + np.power((tx_height - rx_height), 2))

    if distance2d <= 18:
        line_of_sight = "los"
    else:
        if rx_height <= 13:
            c = 0
        else:
            c = np.power(((rx_height-13)/10),1.5)
        if (18 / distance2d)+np.exp((-distance2d / 63) * (1 - (18 / distance2d)))*(1 + c * (5 / 4) * np.power(distance2d / 100, 3) * np.exp(-distance2d / 150)) >= 0.5:
            line_of_sight = 'los'
        else:
            line_of_sight = 'nlos'

    effective_environment_height = 1.0
    breaking_point_distance = 4 * (tx_height - effective_environment_height) * (
            rx_height - effective_environment_height) * (frequency * 10e9) / 3e8  # Frequency in Hz

    if 10 <= distance2d <= breaking_point_distance:
        loss = 28.0 + 22 * np.log10(distance3d) + 20 * np.log10(frequency)
    elif breaking_point_distance <= distance2d <= 5000:
        loss = 28.0 + 40 * np.log10(distance3d) + 20 * np.log10(frequency) - 9 * np.log10(
            np.power(breaking_point_distance, 2) + np.power(tx_height - rx_height, 2))
    else:
        # Optional loss
        loss = 32.4 + 20*np.log10(frequency) + 30*np.log10(distance3d)
        return loss

    if line_of_sight == 'los':
        return round(loss, 2)
    else:
        loss_nlos = 13.54 + 39.08 * np.log10(distance3d) + 20 * np.log10(frequency) - 0.6 * (rx_height - 1.5)
        if 10 <= distance2d <= 5000:
            loss = max(loss, loss_nlos)
            return round(loss, 2)
        else:
            loss = 32.4 + 20 * np.log10(frequency) + 30 * np.log10(distance3d)
            return round(loss, 2)


def etsi_urban_micro_loss(frequency, distance, tx_height, rx_height):

    distance2d = distance
    distance3d = np.sqrt(np.power(distance2d, 2) + np.power((tx_height - rx_height), 2))

    if distance2d <= 18:
        line_of_sight = 'los'
    else:
        if (18 / distance2d) + np.exp((-distance2d / 36) * (1 - (18 / distance2d))) >= 0.5:
            line_of_sight = 'los'
        else:
            line_of_sight = 'nlos'

    effective_environment_height = 1.0
    breaking_point_distance = 4 * (tx_height - effective_environment_height) * (rx_height - effective_environment_height) * (
                frequency * 10e9) / 3e8  # Frequency in Hz

    if 10 <= distance2d <= breaking_point_distance:
        loss = 32.4 + 21 * np.log10(distance3d) + 20 * np.log10(frequency)
    elif breaking_point_distance <= distance2d <= 5000:
        loss = 32.4 + 40 * np.log10(distance3d) + 20 * np.log10(frequency) - 9.5 * np.log10(
            np.power(breaking_point_distance, 2) + np.power(tx_height - rx_height, 2))
    else:
        # Optional loss
        loss = 32.4 + 20 * np.log10(frequency) + 31.9 * np.log10(distance3d)
        return loss

    if line_of_sight == 'los':
        return round(loss, 2)
    else:
        loss_nlos = 35.3 * np.log10(distance3d) + 22.4 + 21.3 * np.log10(frequency) - 0.3 * (rx_height - 1.5)
        if 10 <= distance2d <= 5000:
            loss = max(loss, loss_nlos)
            return round(loss, 2)
        else:
            loss = 32.4 + 20 * np.log10(frequency) + 31.9 * np.log10(distance3d)
            return round(loss, 2)


def etsi_rural_macro_loss(frequency, distance, tx_height, rx_height, avg_building_height, avg_street_width):

    distance2d = distance
    distance3d = np.sqrt(np.power(distance2d, 2) + np.power((tx_height - rx_height), 2))

    if distance2d <= 10:
        line_of_sight = 'los'
    else:
        if np.exp(-1 * (distance2d - 10) / 1000) >= 0.5:
            line_of_sight = 'los'
        else:
            line_of_sight = 'nlos'

    breaking_point_distance = 2 * np.pi * tx_height * rx_height * (frequency * 10e9) / 3e8  # Frequency in Hz
    if 10 <= distance2d <= breaking_point_distance:
        loss = 20 * np.log10(40 * np.pi * distance3d * frequency / 3) + min(0.03 * np.power(avg_building_height, 1.72),
                                                                            10) * np.log10(distance3d) - min(
            0.044 * np.power(avg_building_height, 1.72), 14.77) + 0.002 * np.log10(avg_building_height) * distance3d
    elif breaking_point_distance <= distance2d <= 10000:
        loss = 20 * np.log10(40 * np.pi * breaking_point_distance * frequency / 3) + min(
            0.03 * np.power(avg_building_height, 1.72), 10) * np.log10(breaking_point_distance) - min(
            0.044 * np.power(avg_building_height, 1.72), 14.77) + 0.002 * np.log10(
            avg_building_height) * breaking_point_distance + 40 * np.log10(distance3d / breaking_point_distance)
    else:
        loss = None

    if line_of_sight == 'los':
        return round(loss, 2)
    else:
        loss_nlos = 161.04 - 7.1 * np.log10(avg_street_width) + 7.5 * np.log10(avg_building_height) - (
                    24.37 - 3.7 * np.power(avg_building_height / tx_height, 2)) * np.log10(tx_height) + (
                    43.42 - 3.1 * np.log10(tx_height)) * (np.log10(distance3d) - 3) + 20 * np.log10(
                    frequency) - (3.2 * np.power(np.log10(11.75 * rx_height), 2) - 4.97)
        if 10 <= distance2d <= 5000:
            loss = max(loss, loss_nlos)
            return round(loss, 2)
        else:
            return None
