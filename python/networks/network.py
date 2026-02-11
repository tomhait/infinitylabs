import http.client
import requests

api_key = "caf4e244e2msh52934742de09cefp1d9c11jsnb375a275f6ab"
rapidapi_host = "google-translate113.p.rapidapi.com"

url = "https://" + rapidapi_host + "/api/v1/translator/support-languages"

headers = {
	"x-rapidapi-key": "caf4e244e2msh52934742de09cefp1d9c11jsnb375a275f6ab",
	"x-rapidapi-host": "google-translate113.p.rapidapi.com"
}

response = requests.get(url, headers=headers)

data = response.json()

print("Supported languages are:")

for lang in data[1:]:
    print(lang['language'])


url = "https://" + rapidapi_host + "/api/v1/translator/text"

payload = {
	"from": "auto",
	"to": "en",
	"text": "שלום, תודה על השימוש בשירותינו"
}
headers = {
	"x-rapidapi-key": api_key,
	"x-rapidapi-host": rapidapi_host,
	"Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

data = response.json()

print(f"{data['trans']}")