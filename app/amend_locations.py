import csv
import time

from geopy.geocoders import Nominatim
from loguru import logger

from data.onchain_data import get_location_id
from util.csv import load_csv

LOCATIONS_CSV_FILE='./locations.csv'
LOCATIONS_CSV_FILE_OUT='./locations_amended.csv'
DELIMITER = ';'

OPENSTREETMAP="https://www.openstreetmap.org/#map=14"

def geocode(geolocator, info):
    location = geolocator.geocode(info)
    if not location:
        return None
    
    lat=location.latitude
    long=location.longitude
    coordinates = f"{lat};{long};{OPENSTREETMAP}/{lat}/{long}"
    print(f"info '{info}' coordinates {coordinates}")
    return coordinates


def get_coordinates(province, department, village):
    geolocator = Nominatim(user_agent="my_geocoder")

    try:
        location_village = geocode(geolocator, f"Burkina Faso, {village}")
        if location_village:
            return f"{location_village};VILLAGE"

        location_department = geocode(geolocator, f"Burkina Faso, {department}")
        if location_department:
            return f"{location_department};DEPARTMENT"

        location_province = geocode(geolocator, f"Burkina Faso, {province}")
        if location_province:
            return f"{location_province};PROVINCE"

        return None

    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
    locs_in = load_csv(LOCATIONS_CSV_FILE)
    locs_out = []

    for key, location in locs_in.items():
        print(f"key {key} location {location}")

        region = location['region']
        province = location['province']
        department = location['department']
        village = location['village']

        location['onchainId'] = get_location_id(region, province, department, village)
        location['openstreetmap'] = None
        location['latitude'] = None
        location['longitude'] = None
        location['locationLevel'] = None
    
        loc = get_coordinates(province, department, village)
        if loc:
            (latitude, longitude, openstreetmap, level) = loc.split(';')
            location['latitude'] = latitude
            location['longitude'] = longitude
            location['openstreetmap'] = openstreetmap
            location['coordinatesLevel'] = level

        nano_id = location['nanoId']
        locs_out.append(location)

    write_csv(locs_out)


def write_csv(data):
    with open(LOCATIONS_CSV_FILE_OUT, 'w', newline='', encoding='utf-8') as f:
        csv_writer = csv.DictWriter(
            f, 
            fieldnames=['nanoId','country','region','province','department','village','onchainId','latitude','longitude','openstreetmap','coordinatesLevel'], 
            extrasaction='ignore', 
            delimiter=DELIMITER)

        csv_writer.writeheader()

        for row in data:
            print(f"row {row}")
            csv_writer.writerow(row)


if __name__ == "__main__":
    main()
