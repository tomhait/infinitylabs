def list_to_dict(car_makes: list):
    return {(car, color): price for car, color, price in car_makes}

def get_unique_car_makes(car_makes: list):
    return {(car, color, price): (car, color, price) for car, color, price in car_makes}

car_makes = [["Toyota", "white", 350.1], ["Toyota", "black", 299.2],
             ["Chevy", "white", 521.0], ["Chevy", "black", 431.5],
             ["Chevy", "white", 521.0]]

print(list_to_dict(car_makes))
print(get_unique_car_makes(car_makes))