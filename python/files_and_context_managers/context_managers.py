import os
import pathlib
import string
from itertools import islice

__all__ = ("generate_eng_letter_files","read_first_n_lines","corona_stats")

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

def filter_corona_field(corona_file, field_name, output_file_name):
    """ Filter the requested field name from the corona file
    and write it to output_file_name
    """
    lst = [field_name + '\n']
    with open(corona_file) as f:
        line = f.readline().strip().split(',')
        try:
            field_index = line.index(field_name)
        except ValueError:
            print("Field name was not found")
            return None
        for line in f:
            line = line.strip().split(",")
            lst.append(line[field_index + '\n'])
