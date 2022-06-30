with open(file='../static/domains/domains.txt', mode='r', encoding='utf-8') as domains_txt:
	# Reads the file and splits it into a list of domains, stores it in dictionary
	# university:domain
	domains = {university: domain for university, domain in (line.strip().split(':') for line in domains_txt)}


def main():
	print(domains)


if __name__ == '__main__':
	main()
