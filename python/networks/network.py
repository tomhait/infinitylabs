import requests

class MyTranslator:
	api_key = "caf4e244e2msh52934742de09cefp1d9c11jsnb375a275f6ab"
	rapidapi_host = "google-translate113.p.rapidapi.com"
	url_lang = "https://" + rapidapi_host + "/api/v1/translator/support-languages"
	url_trans = "https://" + rapidapi_host + "/api/v1/translator/text"


	def get_supported_lang(self):
		headers = {
			"x-rapidapi-key": self.api_key,
			"x-rapidapi-host": self.rapidapi_host
		}
		response = requests.get(self.url_lang, headers=headers)
		data = response.json()
		print("Supported languages are:")
		for lang in data[1:]:
			print(f"{lang['code']} {lang['language']}")

	def get_translate(self, phrase, to = "en"):
		payload = {
			"from": "auto",
			"to": to,
			"text": phrase
		}
		headers = {
			"x-rapidapi-key": self.api_key,
			"x-rapidapi-host": self.rapidapi_host,
			"Content-Type": "application/json"
		}

		response = requests.post(self.url_trans, json=payload, headers=headers)

		data = response.json()
		return data['trans']

if __name__ == "__main__":
	print("Welcome to my translator")
	trans = MyTranslator()
	while True:
		print('Options:')
		print('0 - exit')
		print("1 - show supported languages")
		print("2 - translate")
		opt = input("> ").strip()
		if opt == "0":
			break
		if opt == "1":
			trans.get_supported_lang()
			print("\n\n\n")
			continue
		if opt == "2":
			print("Default target language is: English")
			lang_change = input("Type 3 if you want a different language: ").strip()
			to = "en"
			if lang_change == "3":
				to = input("Select target language code: ").strip()
			print("Type your phrase:")
			phrase = input("> ").strip()
			print(trans.get_translate(phrase, to))
		else:
			print("Wrong option")
