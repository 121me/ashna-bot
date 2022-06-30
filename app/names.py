from functools import lru_cache


# read 'female_first.csv' and 'male_first.csv'
# get the first names and sort alphabetically
# write the names to 'names.txt'
def __initial_write():  # DO NOT RUN THIS FUNCTION UNLESS YOU WANT TO OVERWRITE THE FILE
	with open(file='../../static/names/female_first.csv', mode='r', encoding='utf-8') as ffnf:  # FFNF: female first names file
		first_names = [name.strip().split(',')[0] for name in ffnf.readlines()]

	with open(file='../../static/names/male_first.csv', mode='r', encoding='utf-8') as mfnf:  # MFNF: male first names file
		first_names.extend(name.strip().split(',')[0] for name in mfnf.readlines())

	first_names.sort()

	with open(file='../../static/names/names.txt', mode='w', encoding='utf-8') as nf:
		nf.write('\n'.join(first_names))

	print({name: len(name) for name in first_names if len(name) < 3})


# remove the duplicate names in 'names.txt'
# write the names to 'names.txt'
def __remove_duplicates():
	with open(file='../../static/names/names.txt', mode='r', encoding='utf-8') as nf:
		first_names = [name.strip() for name in nf.readlines()]

	first_names = list(set(first_names))
	first_names.sort()

	with open(file='../../static/names/names.txt', mode='w', encoding='utf-8') as nf:
		nf.write('\n'.join(first_names))


# read 'names.txt'
with open(file='../static/names/names.txt', mode='r', encoding='utf-8') as names_txt:
	names = [name.strip() for name in names_txt.readlines()]


# check if the name is valid
@lru_cache(maxsize=512)
def check_name(name: str):
	return name in names


def main():
	# __remove_duplicates()
	print(names)
	pass


if __name__ == '__main__':
	main()
