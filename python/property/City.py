from dataclasses import dataclass

@dataclass
class City:
    """ City class containing only data"""
    city_name: str
    country: str
    coordinates: tuple

if __name__ == "__main__":
    c1 = City("Tel-Aviv", "Israel", (25, 45))
    c2 = City("Tel-Aviv", "Israel", (25, 45))
    print(c1 == c2)
    c3 = City("Haifa", "Israel", (25, 65))
    print(c1 == c3)

