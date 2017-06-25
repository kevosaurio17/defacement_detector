'''
spidy Web Crawler
Built by rivermont and FalconWarriorr
'''
VERSION = '1.0'


############
## IMPORT ##
############

#Time statements.
#This is done before anything else to enable timestamp logging at every step
import time as t
START_TIME = int(t.time())
def get_time():
	return t.strftime('%H:%M:%S')
def get_full_time():
	return t.strftime('%H:%M:%S, %A %b %Y')

from os import path
#Get current working directory of spidy
CRAWLER_DIR = path.dirname(path.realpath(__file__))

#Open log file for logging
LOG_FILE = open('{0}/logs/spidy_log_{1}.txt'.format(CRAWLER_DIR, START_TIME), 'w+')

print('[{0}] [spidy] [INIT]: Starting spidy Web Crawler version {1}'.format(get_time(), VERSION))
LOG_FILE.write('\n[{0}] [spidy] [INIT]: Starting spidy Web Crawler version {1}'.format(get_time(), VERSION))

print('[{0}] [spidy] [INIT]: Importing required libraries...'.format(get_time()))
LOG_FILE.write('\n[{0}] [spidy] [INIT]: Importing required libraries...'.format(get_time()))

#Import required libraries
import requests
import sys
import urllib.request
import shutil
from lxml import html, etree
from os import makedirs


###############
## FUNCTIONS ##
###############

print('[{0}] [spidy] [INIT]: Creating functions...'.format(get_time()))
LOG_FILE.write('\n[{0}] [spidy] [INIT]: Creating functions...'.format(get_time()))

def check_link(item):
	'''
	Returns True if item is not a valid url.
	Returns False if item passes all inspections (is valid url).
	'''
	#Shortest possible url being 'http://a.b'
	if len(item) < 10:
		return True
	#Links longer than 255 characters usually are useless or full of foreign characters, and will also cause problems when saving
	elif len(item) > 255:
		return True
	#Must be an http(s) link
	elif item[0:4] != 'http':
		return True
	#Can't have visited already
	elif item in DONE:
		return True
	else:
		for badLink in KILL_LIST:
			if badLink in item:
				return True
	return False

def check_word(word):
	'''
	Returns True if word is not valid.
	Returns False if word passes all inspections (is valid).
	'''
	#If word is longer than 16 characters (avg password length is ~8)
	if len(word) > 16:
		return True
	else:
		return False

def check_extension(path):
	'''
	Returns True if file should be saved as .html.
	Returns False if file extension is (probably) a valid type.
	'''
	if path in ['com', 'com/', 'org', 'org/', 'net', 'net/']:
		return True
	elif len(path) > 5:
		return True
	elif path[-1] == '/':
		return True
	else:
		return False

def check_path(filePath):
	'''
	Checks the path of a given filename to see whether it will cause errors when saving.
	Returns True if path is valid.
	Returns False if path is invalid.
	'''
	if len(filePath) > 256:
		return False
	else:
		return True

def make_words(site):
	'''
	Returns list of all valid words in page.
	'''
	page = str(site.content) #Get page content
	wordList = page.split() #Split content into lits of words, as separated by spaces
	del page
	wordList = list(set(wordList)) #Remove duplicates
	for word in wordList:
		if check_word(word): #If word is invalid
			wordList.remove(word) #Remove invalid word from list
	return wordList

def save_files(wordList):
	'''
	Saves the TODO, done, word, and bad lists into their respective files.
	Also logs the action to the console.
	'''
	with open(TODO_FILE, 'w') as todoList:
		for site in TODO:
			try:
				todoList.write(site + '\n') #Save TODO list
			except UnicodeError:
				continue
	print('[{0}] [spidy] [LOG]: Saved TODO list to {1}'.format(get_time(), TODO_FILE))
	LOG_FILE.write('[{0}] [spidy] [LOG]: Saved TODO list to {1}'.format(get_time(), TODO_FILE))
	
	with open(DONE_FILE, 'w') as doneList:
		for site in DONE:
			try:
				doneList.write(site + '\n') #Save done list
			except UnicodeError:
				continue
	print('[{0}] [spidy] [LOG]: Saved done list to {1}'.format(get_time(), DONE_FILE))
	LOG_FILE.write('\n[{0}] [spidy] [LOG]: Saved done list to {1}'.format(get_time(), DONE_FILE))
	
	if SAVE_WORDS:
		update_file(WORD_FILE, wordList, 'words')
	update_file(BAD_FILE, BAD_LINKS, 'bad links')

def save_page(url):
	'''
	Download content of url and save to the save folder.
	'''
	url = str(url) #Sanitize input
	newUrl = url
	if newUrl[-1] == '.':
		ext = 'html'
	else:
		ext = newUrl.split('.')[-1] #Get all characters from the end of the url to the last period - the file extension.
	for char in '''"/\ ''': #Replace folders with -
		newUrl = newUrl.replace(char, '-')
	for char in '''|:?<>*''': #Remove illegal filename characters
		newUrl = newUrl.replace(char, '')
	if check_extension(ext): #If the extension is invalid, default to .html
		ext = 'html'
	newUrl = newUrl.replace(ext, '') #Remove extension from file name
	fileName = newUrl + '.' + ext #Create full file name
	path = '{0}/saved/{1}'.format(CRAWLER_DIR, fileName)
	del newUrl, fileName, ext
	if check_path(path):
		with urllib.request.urlopen(url) as response, open(path, 'wb+') as saveFile:
			shutil.copyfileobj(response, saveFile)
	else:
		log('\nLINK: {0}\nLOG: Filename too long.'.format(url))
		print('[{0}] [spidy] [ERR]: Filename too long, page will not be saved.'.format(get_time()))
		LOG_FILE.write('\n[{0}] [spidy] [ERR]: Filename too long, page will not be saved.'.format(get_time()))
		err_saved_message()

def update_file(file, content, type):
	with open(file, 'r+') as f: #Open save file for reading and writing
		fileContent = f.readlines() #Make list of all lines in file
		fileContent = [x.strip() for x in fileContent]
		for item in fileContent:
			content.update(item) #Otherwise add item to content (set)
		del fileContent
		for item in content:
			f.write('\n' + str(item)) #Write all words to file
		f.truncate() #Delete everything in file beyond what has been written (old stuff)
	print('[{0}] [spidy] [LOG]: Saved {1} {2} to {3}'.format(get_time(), len(content), type, file))
	LOG_FILE.write('\n[{0}] [spidy] [LOG]: Saved {1} {2} to {3}'.format(get_time(), len(content), type, file))

def info_log():
	'''
	Logs important information to the console and log file.
	'''
	sinceStart = int(t.time() - START_TIME)
	
	#Print to console
	time = get_time()
	print('[{0}] [spidy] [INFO]: {1} seconds elapsed since start.'.format(time, sinceStart))
	print('[{0}] [spidy] [INFO]: {1} links in TODO.'.format(time, len(TODO)))
	print('[{0}] [spidy] [INFO]: {1} links in done.'.format(time, len(DONE)))
	print('[{0}] [spidy] [INFO]: {1} bad links removed.'.format(time, REMOVED_COUNT))
	print('[{0}] [spidy] [INFO]: {1}/{2} new errors caught.'.format(time, NEW_ERROR_COUNT, MAX_NEW_ERRORS))
	print('[{0}] [spidy] [INFO]: {1}/{2} HTTP errors encountered.'.format(time, HTTP_ERROR_COUNT, MAX_HTTP_ERRORS))
	print('[{0}] [spidy] [INFO]: {1}/{2} known errors caught.'.format(time, KNOWN_ERROR_COUNT, MAX_KNOWN_ERRORS))
	
	LOG_FILE.write('\n[{0}] [spidy] [INFO]: {1} seconds elapsed since start.'.format(time, sinceStart))
	LOG_FILE.write('\n[{0}] [spidy] [INFO]: {1} links in TODO.'.format(time, len(TODO)))
	LOG_FILE.write('\n[{0}] [spidy] [INFO]: {1} links in done.'.format(time, len(DONE)))
	LOG_FILE.write('\n[{0}] [spidy] [INFO]: {1} bad links removed.'.format(time, REMOVED_COUNT))
	LOG_FILE.write('\n[{0}] [spidy] [INFO]: {1}/{2} new errors caught.'.format(time, NEW_ERROR_COUNT, MAX_NEW_ERRORS))
	LOG_FILE.write('\n[{0}] [spidy] [INFO]: {1}/{2} HTTP errors encountered.'.format(time, HTTP_ERROR_COUNT, MAX_HTTP_ERRORS))
	LOG_FILE.write('\n[{0}] [spidy] [INFO]: {1}/{2} known errors caught.'.format(time, KNOWN_ERROR_COUNT, MAX_KNOWN_ERRORS))
	
def log(message):
	'''
	Logs a single message to the logFile.
	Prints message verbatim, so message must be formatted correctly outside of the function call.
	'''
	with open(ERR_LOG_FILE, 'a') as log:
		log.write('\n\n======LOG======') #Write opening line
		log.write('\nTIME: {0}'.format(get_full_time())) #Write current time
		log.write(message) #Write message
		log.write(LOG_END) #Write closing line

def err_print(item):
	'''
	Announce that an error occurred.
	'''
	print('[{0}] [spidy] [ERR]: An error was raised trying to process {1}'.format(get_time(), item))
	LOG_FILE.write('\n[{0}] [spidy] [ERR]: An error was raised trying to process {1}'.format(get_time(), item))

def err_saved_message():
	'''
	Announce that error was successfully saved to log.
	'''
	print('[{0}] [spidy] [LOG]: Saved error message and timestamp to {1}'.format(get_time(), ERR_LOG_FILE_NAME))
	LOG_FILE.write('\n[{0}] [spidy] [LOG]: Saved error message and timestamp to {1}'.format(get_time(), ERR_LOG_FILE_NAME))

def err_log(url, error1, error2):
	'''
	Saves the triggering error to the log file.
	error1 is the trimmed error source.
	error2 is the extended text of the error.
	'''
	time = t.strftime('%H:%M:%S, %A %b %Y') #Get the current time
	with open(ERR_LOG_FILE, 'a') as log:
		log.write('\n\n=====ERROR=====') #Write opening line
		log.write('\nTIME: {0}\nURL: {1}\nERROR: {2}\nEXT: {3}'.format(time, url, error1, str(error2)))
		log.write(LOG_END) #Write closing line

def get_avg(state1, state2):
	'''
	Takes two values and returns the percentage of state1 that is state2.
	'''
	if state1 == 0:
		return 0
	else:
		return (state2 / state1) * 100

def zip(out_fileName, dir):
	'''
	Creates a .zip file in the current directory containing all contents of dir, then deletes dir.
	'''
	shutil.make_archive(str(out_fileName), 'zip', dir) #Zips files
	shutil.rmtree(dir) #Deletes folder
	makedirs(dir[:-1]) #Creates empty folder of same name (minus the '/')
	print('[{0}] [spidy] [LOG]: Zipped documents to {1}.zip'.format(get_time(), out_fileName))
	LOG_FILE.write('\n[{0}] [spidy] [LOG]: Zipped documents to {1}.zip'.format(get_time(), out_fileName))

##########
## INIT ##
##########

print('[{0}] [spidy] [INIT]: Creating variables...'.format(get_time()))
LOG_FILE.write('\n[{0}] [spidy] [INIT]: Creating variables...'.format(get_time()))

#Initialize required variables

#Error log location
ERR_LOG_FILE = '{0}/logs/spidy_error_log_{1}.txt'.format(CRAWLER_DIR, START_TIME)
ERR_LOG_FILE_NAME = 'spidy_error_log_{0}.txt'.format(START_TIME)

#User-Agent Header String
HEADERS = {
'User-Agent': 'Mozilla/5.0 (compatible; spidy Web Crawler  (bot, +https://github.com/rivermont/spidy))',
'Accept-Encoding': 'gzip'
}

KILL_LIST = [
#Pages that cause problems with the crawler in some way
'http://scores.usaultimate.org/',
'https://web.archive.org/web/',
'psychologytoday.com/rms',
'www.newsyarena.com'
#Sites that we have been asked not to crawl:
#None! Yay
]

#Empty set for error-causing links
BAD_LINKS = set([])

#Line to print at the end of each logFile log
LOG_END = '\n======END======'

#Counter variables
COUNTER = 0
REMOVED_COUNT = 0
NEW_ERROR_COUNT = 0
KNOWN_ERROR_COUNT = 0
HTTP_ERROR_COUNT = 0

#Amount of errors allowed to happen before automatic shutdown
MAX_NEW_ERRORS = 10
MAX_KNOWN_ERRORS = 25
MAX_HTTP_ERRORS = 100

#Empty set for word scraping
WORDS = set([])

#Getting arguments

#Web directories to use in case TODO file is empty
START = [
'https://en.wikipedia.org/wiki/List_of_most_popular_websites',
'http://www.clambr.com/49-free-web-directories-for-building-backlinks/'
]

yes = ['y', 'yes', 'Y', 'Yes', 'True', 'true']
no = ['n', 'no', 'N', 'No', 'False', 'false']

try:
	if sys.argv[1] == 'Default':
		print('[{0}] [spidy] [INFO]: Using default configuration.'.format(get_time()))
		LOG_FILE.write('\n[{0}] [spidy] [INFO]: Using default configuration.'.format(get_time()))
		OVERWRITE = False
		RAISE_ERRORS = False
		ZIP_FILES = False
		SAVE_PAGES = True
		SAVE_WORDS = True
		TODO_FILE = 'crawler_todo.txt'
		DONE_FILE = 'crawler_done.txt'
		WORD_FILE = 'crawler_words.txt'
		BAD_FILE = 'crawler_bad.txt'
		SAVE_COUNT = 100
		
		GET_ARGS = False
	else:
		print('[{0}] [spidy] [ERR]: Invalid argument(s).'.format(get_time()))
		LOG_FILE.write('\n[{0}] [spidy] [ERR]: Invalid argument(s).'.format(get_time()))
		GET_ARGS = True
except IndexError:
	GET_ARGS = True
	
if GET_ARGS:
	print('[{0}] [spidy] [INIT]: Please enter the following arguments. Leave blank to use the default values.'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INIT]: Please enter the following arguments. Leave blank to use the default values.'.format(get_time()))
	
	INPUT = input('[{0}] [spidy] [INPUT]: Should spidy load from existing save files? (y/n) (Default: Yes)'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INPUT]: Should spidy load from existing save files? (y/n) (Default: Yes)'.format(get_time()))
	if not bool(INPUT): #Use default value
		OVERWRITE = False
	elif INPUT in yes: #Yes
		OVERWRITE = False
	elif INPUT in no: #No
		OVERWRITE = True
	else: #Invalid input
		LOG_FILE.write('\n[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
		raise SyntaxError('[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
	
	INPUT = input('[{0}] [spidy] [INPUT]: Should spidy raise NEW errors and stop crawling? (y/n) (Default: No)'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INPUT]: Should spidy raise NEW errors and stop crawling? (y/n) (Default: No)'.format(get_time()))
	if not bool(INPUT):
		RAISE_ERRORS = False
	elif INPUT in yes:
		RAISE_ERRORS = True
	elif INPUT in no:
		RAISE_ERRORS = False
	else:
		LOG_FILE.write('\n[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
		raise SyntaxError('[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
	
	INPUT = input('[{0}] [spidy] [INPUT]: Should spidy zip saved documents when autosaving? (y/n) (Default: No)'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INPUT]: Should spidy zip saved documents when autosaving? (y/n) (Default: No)'.format(get_time()))
	if not bool(INPUT):
		ZIP_FILES = False
	elif INPUT in yes:
		ZIP_FILES = True
	elif INPUT in no:
		ZIP_FILES = False
	else:
		LOG_FILE.write('\n[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
		raise SyntaxError('[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
	
	INPUT = input('[{0}] [spidy] [INPUT]: Should spidy save the pages it scrapes to the saved folder?'.format(get_time()))
	LOG_FILE.write('[{0}] [spidy] [INPUT]: Should spidy save the pages it scrapes to the saved folder?'.format(get_time()))
	if not bool(INPUT):
		SAVE_PAGES = True
	elif INPUT in yes:
		SAVE_PAGES = True
	elif INPUT in no:
		SAVE_PAGES = False
	else:
		LOG_FILE.write('\n[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
		raise SyntaxError('[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
	
	INPUT = input('[{0}] [spidy] [INPUT]: Should spidy scrape words and save them? (y/n) (Default: Yes)'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INPUT]: Should spidy scrape words and save them? (y/n) (Default: Yes)'.format(get_time()))
	if not bool(INPUT):
		SAVE_WORDS = True
	elif INPUT in yes:
		SAVE_WORDS = True
	elif INPUT in no:
		SAVE_WORDS = False
	else:
		LOG_FILE.write('\n[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
		raise SyntaxError('[{0}] [spidy] [ERR]: Please enter a valid input. (yes/no)'.format(get_time()))
	
	INPUT = input('[{0}] [spidy] [INPUT]: Location of the TODO save file (Default: crawler_todo.txt):'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INPUT]: Location of the TODO save file (Default: crawler_todo.txt):'.format(get_time()))
	if not bool(INPUT):
		TODO_FILE = 'crawler_todo.txt'
	else:
		TODO_FILE = INPUT
	
	INPUT = input('[{0}] [spidy] [INPUT]: Location of the done save file (Default: crawler_done.txt):'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INPUT]: Location of the done save file (Default: crawler_done.txt):'.format(get_time()))
	if not bool(INPUT):
		DONE_FILE = 'crawler_done.txt'
	else:
		DONE_FILE = INPUT
	
	if SAVE_WORDS:
		INPUT = input('[{0}] [spidy] [INPUT]: Location of the word save file: (Default: crawler_words.txt)'.format(get_time()))
		LOG_FILE.write('\n[{0}] [spidy] [INPUT]: Location of the word save file: (Default: crawler_words.txt)'.format(get_time()))
		if not bool(INPUT):
			WORD_FILE = 'crawler_words.txt'
		else:
			WORD_FILE = INPUT
	else:
		WORD_FILE = ''
	
	INPUT = input('[{0}] [spidy] [INPUT]: Location of the bad link save file (Default: crawler_bad.txt):'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INPUT]: Location of the bad link save file (Default: crawler_bad.txt):'.format(get_time()))
	if not bool(INPUT):
		BAD_FILE = 'crawler_bad.txt'
	else:
		BAD_FILE = INPUT
	
	INPUT = input('[{0}] [spidy] [INPUT]: After how many queried links should spidy autosave? (default 100)'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INPUT]: After how many queried links should spidy autosave? (default 100)'.format(get_time()))
	if not bool(INPUT):
		SAVE_COUNT = 100
	elif not INPUT.isdigit():
		LOG_FILE.write('\n[{0}] [spidy] [ERR]: Please enter a valid integer.'.format(get_time()))
		raise SyntaxError('[{0}] [spidy] [ERR]: Please enter a valid integer.'.format(get_time()))
	else:
		SAVE_COUNT = INPUT
	
	#Remove INPUT variable from memory
	del INPUT

#Import saved TODO file data
if OVERWRITE:
	print('[{0}] [spidy] [INIT]: Creating save files...'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INIT]: Creating save files...'.format(get_time()))
	TODO = START
	DONE = []
else:
	print('[{0}] [spidy] [INIT]: Loading save files...'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INIT]: Loading save files...'.format(get_time()))
	with open(TODO_FILE, 'r') as f:
		contents = f.readlines()
	TODO = [x.strip() for x in contents]
	#Import saved done file data
	with open(DONE_FILE, 'r') as f:
		contents = f.readlines()
	DONE = [x.strip() for x in contents]
	del contents

	print('[{0}] [spidy] [INIT]: Pruning invalid links from TODO...'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INIT]: Pruning invalid links from TODO...'.format(get_time()))

	before = len(TODO)

	#Remove invalid links from TODO list
	for link in TODO:
		if check_link(link):
			TODO.remove(link)

	#If TODO list is empty, add default starting pages
	if len(TODO) == 0:
		TODO += START

	after = abs(before - len(TODO))
	REMOVED_COUNT += after
	print('[{0}] [spidy] [INIT]: {1} invalid links removed from TODO.'.format(get_time(), after))
	LOG_FILE.write('\n[{0}] [spidy] [INIT]: {1} invalid links removed from TODO.'.format(get_time(), after))
	
	del before
	del after

print('[{0}] [spidy] [INIT]: TODO first value: {1}'.format(get_time(), TODO[0]))
LOG_FILE.write('\n[{0}] [spidy] [INIT]: TODO first value: {1}'.format(get_time(), TODO[0]))

def main():
	#Declare global variables
	global VERSION, START_TIME, LOG_FILE, ERR_LOG_FILE_NAME
	global HEADERS, CRAWLER_DIR, KILL_LIST, BAD_LINKS, LOG_END
	global COUNTER, REMOVED_COUNT, NEW_ERROR_COUNT, KNOWN_ERROR_COUNT, HTTP_ERROR_COUNT
	global MAX_NEW_ERRORS, MAX_KNOWN_ERRORS, MAX_HTTP_ERRORS
	global OVERWRITE, RAISE_ERRORS, ZIP_FILES, SAVE_WORDS, SAVE_PAGES, SAVE_COUNT
	global TODO_FILE, DONE_FILE, ERR_LOG_FILE, WORD_FILE, BAD_FILE
	global WORDS, TODO, DONE
	
	print('[{0}] [spidy] [INIT]: Successfully started spidy Web Crawler version {1}...'.format(get_time(), VERSION))
	log('LOG: Successfully started crawler.')
	LOG_FILE.write('\n[{0}] [spidy] [INIT]: Successfully started spidy Web Crawler version {1}...'.format(get_time(), VERSION))
	
	print('[{0}] [spidy] [INFO]: Using headers: {1}'.format(get_time(), HEADERS))
	LOG_FILE.write('\n[{0}] [spidy] [INFO]: Using headers: {1}'.format(get_time(), HEADERS))
	
	while len(TODO) != 0: #While there are links to check
		try:
			if NEW_ERROR_COUNT >= MAX_NEW_ERRORS or KNOWN_ERROR_COUNT >= MAX_KNOWN_ERRORS or HTTP_ERROR_COUNT >= MAX_HTTP_ERRORS: #If too many errors have occurred
				print('[{0}] [spidy] [ERR]: Too many errors have accumulated, stopping crawler.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: Too many errors have accumulated, stopping crawler.'.format(get_time()))
				save_files(WORDS)
				sys.exit()
			elif COUNTER >= SAVE_COUNT: #If it's time for an autosave
				try:
					print('[{0}] [spidy] [LOG]: Queried {1} links. Saving files...'.format(get_time(), str(COUNTER)))
					LOG_FILE.write('\n[{0}] [spidy] [LOG]: Queried {1} links. Saving files...'.format(get_time(), str(COUNTER)))
					save_files(WORDS)
					info_log()
					if ZIP_FILES:
						zip(t.time(), 'saved/')
				finally:
					#Reset variables
					COUNTER = 0
					WORDS.clear()
					BAD_LINKS.clear()
			elif check_link(TODO[0]): #If the link is invalid
				del TODO[0]
				continue
			#Run
			else:
				page = requests.get(TODO[0], headers=HEADERS) #Get page
				if SAVE_WORDS:
					wordList = make_words(page) #Get all words from page
					WORDS.update(wordList) #Add words to word list
				links = []
				for element, attribute, link, pos in html.iterlinks(page.content): #Get all links on the page
					links.append(link)
				links = (list(set(links))) #Remove duplicates and shuffle links
				for link in links: #Check for invalid links
					if check_link(link):
						links.remove(link)
						REMOVED_COUNT += 1
					link = link.encode('utf-8', 'ignore') #Encode each link to UTF-8 to minimize errors
				TODO += links #Add scraped links to the TODO list
				DONE.append(TODO[0]) #Add crawled link to done list
				if SAVE_PAGES:
					save_page(TODO[0])
				if SAVE_WORDS:
					print('[{0}] [spidy] [CRAWL]: Found {1} links and {2} words on {3}'.format(get_time(), len(wordList), len(links), TODO[0])) #Announce which link was crawled
					LOG_FILE.write('\n[{0}] [spidy] [CRAWL]: Found {1} links and {2} words on {3}'.format(get_time(), len(wordList), len(links), TODO[0]))
				else:
					print('[{0}] [spidy] [CRAWL]: Found {1} links on {2}'.format(get_time(), len(links), TODO[0])) #Announce which link was crawled
					LOG_FILE.write('\n[{0}] [spidy] [CRAWL]: Found {1} links on {2}'.format(get_time(), len(links), TODO[0]))
				del TODO[0]#Remove crawled link from TODO list
				COUNTER += 1
		
		#ERROR HANDLING
		except KeyboardInterrupt: #If the user does ^C
			print('[{0}] [spidy] [ERR]: User performed a KeyboardInterrupt, stopping crawler...'.format(get_time()))
			log('\nLOG: User performed a KeyboardInterrupt, stopping crawler.')
			LOG_FILE.write('\n[{0}] [spidy] [ERR]: User performed a KeyboardInterrupt, stopping crawler...'.format(get_time()))
			save_files(WORDS)
			LOG_FILE.close()
			sys.exit()
		except Exception as e:
			link = TODO[0].encode('utf-8', 'ignore')
			err_print(link)
			errMRO = type(e).mro()
			
			#HTTP Errors
			if str(e) == 'HTTP Error 403: Forbidden':
				print('[{0}]] [spiy] [ERR]: HTTP 403: Access Forbidden'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: HTTP 403: Access Forbidden'.format(get_time()))
				BAD_LINKS.add(link)
			
			elif str(e) == 'HTTP Error 429: Too Many Requests':
				print('[{0}] [spidy] [ERR]: HTTP 429: Too Many Requests'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: HTTP 429: Too Many Requests.'.format(get_time()))
				TODO += TODO[0] #Move link to end of TODO list
			
			elif urllib.error.HTTPError in errMRO: #Bad HTTP Response
				HTTP_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: Bad HTTP response.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: Bad HTTP response.'.format(get_time()))
				err_log(link, 'Bad Response', e)
				BAD_LINKS.add(link)
			
			#Other errors
			elif etree.XMLSyntaxError in errMRO or etree.ParserError in errMRO: #Error processing html/xml
				KNOWN_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: An XMLSyntaxError occured. A web dev screwed up somewhere.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: An XMLSyntaxError occured. A web dev screwed up somewhere.'.format(get_time()))
				err_log(link, 'XMLSyntaxError', e)
			
			elif UnicodeError in errMRO: #Error trying to convert foreign characters to Unicode
				KNOWN_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: A UnicodeError occurred. URL had a foreign character or something.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: A UnicodeError occurred. URL had a foreign character or something.'.format(get_time()))
				err_log(link, 'UnicodeError', e)
			
			elif requests.exceptions.SSLError in errMRO: #Invalid SSL certificate
				KNOWN_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: An SSLError occured. Site is using an invalid certificate.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: An SSLError occured. Site is using an invalid certificate.'.format(get_time()))
				err_log(link, 'SSLError', e)
				BAD_LINKS.add(link)
			
			elif requests.exceptions.ConnectionError in errMRO: #Error connecting to page
				KNOWN_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: A ConnectionError occurred. There is something wrong with somebody\'s network.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: A ConnectionError occurred. There is something wrong with somebody\'s network.'.format(get_time()))
				err_log(link, 'ConnectionError', e)
			
			elif requests.exceptions.TooManyRedirects in errMRO: #Exceeded 30 redirects.
				KNOWN_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: A TooManyRedirects error occurred. Page is probably part of a redirect loop.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: A TooManyRedirects error occurred. Page is probably part of a redirect loop.'.format(get_time()))
				err_log(link, 'TooManyRedirects', e)
				BAD_LINKS.add(link)
			
			elif requests.exceptions.ContentDecodingError in errMRO: #Received response with content-encoding: gzip, but failed to decode it.
				KNOWN_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: A ContentDecodingError occurred. Probably just a zip bomb, nothing to worry about.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: A ContentDecodingError occurred. Probably just a zip bomb, nothing to worry about.'.format(get_time()))
				err_log(link, 'ContentDecodingError', e)
			
			elif OSError in errMRO:
				KNOWN_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: An OSError occurred.'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: An OSError occurred.'.format(get_time()))
				err_log(link, 'OSError', e)
				BAD_LINKS.add(link)
			
			else: #Any other error
				NEW_ERROR_COUNT += 1
				print('[{0}] [spidy] [ERR]: An unknown error happened. New debugging material!'.format(get_time()))
				LOG_FILE.write('\n[{0}] [spidy] [ERR]: An unknown error happened. New debugging material!'.format(get_time()))
				err_log(link, 'Unknown', e)
				if RAISE_ERRORS:
					LOG_FILE.close()
					save_files(WORDS)
					raise e
				else:
					continue
			
			err_saved_message()
			del TODO[0]
			COUNTER += 1
		finally:
			TODO = list(set(TODO)) #Removes duplicates and shuffles links so trees don't form.
			#For debugging purposes; to check one link and then stop
			# save_files(WORDS)
			# sys.exit()
	
	print('[{0}] [spidy] [GOD]: How the hell did this happen? I think you\'ve managed to download the internet. I guess you\'ll want to save your files...'.format(get_time()))
	LOG_FILE.write('[{0}] [spidy] [GOD]: How the hell did this happen? I think you\'ve managed to download the internet. I guess you\'ll want to save your files...'.format(get_time()))
	save_files(WORDS)

if __name__ == '__main__':
	main()
else:
	print('[{0}] [spidy] [INIT]: Successfully imported spidy Web Crawler.'.format(get_time()))
	LOG_FILE.write('\n[{0}] [spidy] [INIT]: Successfully imported spidy Web Crawler.'.format(get_time()))
