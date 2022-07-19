from functools import lru_cache

# read 'names.txt'
with open(file='../static/names/names.txt', mode='r', encoding='utf-8') as names_txt:
	names = list(map(lambda name: name.strip(), names_txt.readlines()))

"""
names = list(map(lambda name: name.lower(), names))

with open(file='../static/names/names.txt', mode='w', encoding='utf-8') as names_txt:
	names_txt.writelines(map(lambda name: name + "\n", names))
"""


# check the name if it is valid
@lru_cache(maxsize=256)
def check_name(name: str):
	return name in names


if __name__ == '__main__':
	print(len(max(names, key=len)))
