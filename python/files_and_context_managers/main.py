from context_managers import *

if __name__ == "__main__":
    generate_eng_letter_files(".")
    print(read_first_n_lines("corona.csv",3))
    corona_stats("corona.csv")
    filter_corona_field("corona.csv", "filter.csv")
    csv_to_json("corona.csv", "corona.json")
    merge_files("./abc", "./abc/merged.txt")
    cipher_encode_decode("cipher_info.txt", "cipher_encoded.txt")
    cipher_encode_decode("encoded.txt", "decoded.txt", is_encode = False)
    with EncDecCipherManager("cipher_encoded.txt") as dec_f:
        for line in dec_f.content:
            print(line)

