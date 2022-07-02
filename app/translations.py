import json

translations = {}

# read translations from json file and store them in a dictionary
with open("../static/lang/en.json", mode="r", encoding="utf-8-sig") as file:
	translations['en'] = json.load(file)

with open("../static/lang/tr.json", mode="r", encoding="utf-8-sig") as file:
	translations['tr'] = json.load(file)

# read detranslations from json file and store them in a dictionary
with open("../static/lang/detranslations.json", mode="r", encoding="utf-8-sig") as file:
	detranslations = json.load(file)


def detranslate(name: str) -> str:
	try:
		return detranslations[name]
	except KeyError:
		return name


def translate(name: str, lan: str) -> str:
	try:
		return translations[lan][name]
	except KeyError:
		return name


if __name__ == '__main__':
	print(detranslate("erkek"))
	print(translate('about', 'tr'))
