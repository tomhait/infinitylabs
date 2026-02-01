import os
import pathlib
import string
from itertools import islice
import csv
import json

__all__ = ("generate_eng_letter_files","read_first_n_lines",
           "corona_stats","filter_corona_field","csv_to_json", "merge_files")

def generate_eng_letter_files(location):
    """ Creates a new folder abc within location
    and add 26 text files named byu english alphabet
    containing their names
    """
    upper_str = string.ascii_uppercase
    base_path = pathlib.Path(location)
    base_path = base_path / "abc"
    base_path.mkdir(parents=True, exist_ok=True)
    for x in upper_str:
        with open(base_path.joinpath(x + ".txt"), 'w') as f:
            f.write(x + "\n")

def read_first_n_lines(file_name, n):
    """ Reads the first n lines to a list from file_name
    if file_name not found in the file system
    returns empty list
    """
    lines = []
    for root, dirs, files in os.walk('.'):
        if file_name in files:
            base_path = pathlib.Path(root)
            base_path = base_path / file_name
            with open(base_path) as f:
                lines_iterator = islice(f, n)
                lines += [line.strip('\n') for line in lines_iterator]
    return lines

def corona_stats(file_name):
    """ Prints the min/max age of vaccinated and unvaccinated
    people, and the average length of hospitalization
    """
    age_vac = []
    age_unvac = []
    host_length = []
    with open(file_name) as f:
        line = f.readline().strip().split(',')
        age_index = line.index("Age")
        vac_index = line.index("Is_vaccinated")
        host_index = line.index("Length_of_hospitalization")
        for line in f:
            line = line.strip().split(",")
            if line[vac_index] == "Y":
                age_vac.append(int(line[age_index]))
            else:
                age_unvac.append(int(line[age_index]))
            host_length.append(int(line[host_index]))
    print(f"Min age of vaccinated people: {min(age_vac)}")
    print(f"Max age of vaccinated people: {max(age_vac)}")
    print(f"Min age of Un-vaccinated people: {min(age_unvac)}")
    print(f"Max age of Un-vaccinated people: {max(age_unvac)}")
    print(f"Average length of hospitalization: {sum(host_length) / len(host_length):.2f}")

def _age_input():
    age_range_str = input("Choose age range (\"min-max\" format): ")
    lst = age_range_str.split('-')
    return int(lst[0]), int(lst[1])

def _gender_input():
    gender = input("Choose gender (M/F/ALL): ")
    return gender

def _vaccinated_input():
    is_vac = input("Choose if vaccinated or not (Y/N/ALL): ")
    return is_vac

fields = ("gender", "Age", "Is_vaccinated")

def filter_corona_field(corona_file, output_file_name):
    """ Filter the requested field name from the corona file
    and write it to output_file_name
    """
    gender = _gender_input()
    ages = _age_input()
    is_vac = _vaccinated_input()
    data = []
    with open(corona_file) as f, open(output_file_name, 'w') as out_f:
        line = f.readline().strip().split(',')
        try:
            csv_field_index = {field_name: line.index(field_name) for field_name in fields}
        except ValueError:
            print("Field name was not found")
            return None
        csv_writer = csv.DictWriter(out_f, fieldnames=fields)
        csv_writer.writeheader()
        for line in f:
            line = line.strip().split(",")
            out_dict = {}
            sex = line[csv_field_index["gender"]]
            age = int(line[csv_field_index["Age"]])
            vac = line[csv_field_index["Is_vaccinated"]]
            if gender == "ALL" or sex == gender:
                out_dict["gender"] = line[csv_field_index["gender"]]
            else:
                continue
            if ages[0] <= age <= ages[1]:
                out_dict["Age"] = line[csv_field_index["Age"]]
            else:
                continue
            if is_vac == "ALL" or vac == is_vac:
                out_dict["Is_vaccinated"] = line[csv_field_index["Is_vaccinated"]]
            else:
                continue
            data.append(out_dict)
        csv_writer.writerows(data)


def csv_to_json(csv_name, json_name):
    """ Converts a csv file to JSON file"""
    lst = []
    with open(csv_name) as csv_f:
        reader = csv.DictReader(csv_f)
        for line in reader:
            lst.append(line)

    with open(json_name, 'w') as json_f:
        json.dump(lst, json_f, indent=4)


def merge_files(dir_name, out_file_name):
    """ Merge all text files in dir_name
    into one file
    """
    for file_path in pathlib.Path(dir_name).iterdir():
        if file_path.is_file() and file_path.suffix == ".txt":
            with open(file_path) as f, open(out_file_name,'a') as out_f:
                lines = f.readlines()
                out_f.writelines(lines)


