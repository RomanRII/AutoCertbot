import argparse
from helper import doApi

def main():
	# Create an ArgumentParser object
	parser = argparse.ArgumentParser()
	parser.add_argument("--apikey", required=True)
	parser.add_argument("--requesteddomain", required=True)
	parser.add_argument("--rootdomain", required=True)
	parser.add_argument("--requiredemail", required=True)
	# Parse the command-line arguments
	args = parser.parse_args()
	doAPIKey = args.apikey
	requestedDomain = args.requesteddomain
	rootDomain = args.rootdomain
	requiredEmail = args.requiredemail
	doApi.entry(doApiKey=doAPIKey, requestedDomain=requestedDomain, rootDomain=rootDomain, requiredEmail=requiredEmail)

if __name__ == "__main__":
	main()
