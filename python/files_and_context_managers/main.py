from context_managers import *

if __name__ == "__main__":
    #generate_eng_letter_files(".")
    #print(read_first_n_lines("corona.csv",3))
    #corona_stats("corona.csv")
    filter_corona_field("corona.csv", "filter.csv", ["gender","Age", "Is_vaccinated"])
    #csv_to_json("corona.csv", "corona.json")


