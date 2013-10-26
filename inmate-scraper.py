"""

Given a list of names, extract prison records from the Nebraska DOC inmate search dooder-bop thingamajig skideela bi di bi di do bap do.

"""

from mechanize import Browser
from bs4 import *
from time import *
import re
import csv

# open the file to write to
f = open('timeserved.txt', 'wb')

# add headers to file
f.write("lastname|firstname|middle|crimes|gender|race|dob|startsentence|endsentence|sentencebegin|projectedrelease|goodtimedays|paroleeligibility|paroledischarge|releasedate|releasetype|mug\n")

# crank up a browser
mech = Browser()

# add a user-agent string
mech.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

# ignore robots
mech.set_handle_robots(False)

# define opening url
baseurl = "http://dcs-inmatesearch.ne.gov/Corrections/COR_input.html"

# beautifulsoup that bizzo
page = mech.open(baseurl)
html = page.read()
soup = BeautifulSoup(html)

# read in names from csv
ifile  = open('names.txt', "rb")
reader = csv.reader(ifile)

for names in reader:
	lname = names[0]
	fname = names[1]

	# select the correct form on the page
	mech.select_form(nr=0)
	
	# fill out the form
	mech.form['LastName'] = lname
	mech.form['FirstName'] = fname
	
	# submit, read in the results page
	req = mech.submit()
	resultspage = req.read()
	
	#soup the results page
	soup = BeautifulSoup(resultspage)
	
	# check to see if the search returned any records
	error = re.compile(r'The name was not found')
	if error.search(str(soup)):
		print 'Sez ' + fname + ' ' + lname + ' ain\'t err been in the joint. Trying the next one ...\n'
		sleep(3)
		mech.back()
		continue
	else:
		pass
		print 'Inmate found. Slurping data now...'
	
	# if search was successful, append links to a list
	stints = []
	for link in mech.links(url_regex='DcsId'):
		stints.append(link.url)

	# loop through links and extract that sweet, sweet data
	for url in stints:
		page = mech.open(url + '&showInmateImage=true')
		html = page.read()
		soup = BeautifulSoup(html) 
		datadata = soup.findAll('td', {'class': 'fieldData'})
		
        # get the name
		lastname = datadata[0].renderContents().strip()
		firstname = datadata[1].renderContents().strip()
		middle = datadata[2].renderContents().strip()
		print 'Pulling record for ' + firstname + " " + lastname
		
        # get the mugshot
		muglist = [x['src'] for x in soup.findAll('img', {'alt': 'Inmate Image'})]
		for pic in muglist:
			mug = 'http://dcs-inmatesearch.ne.gov/Corrections/' + pic
		
        # other personal data
		gender = datadata[8].renderContents().strip()
		race = datadata[9].renderContents().strip()
		dob = datadata[10].renderContents().strip()
		
        # some ugly regex to find sentencing info
		findstartyears = re.search('(\d)\s+Years', datadata[13].renderContents().strip())
		startyears = findstartyears.group().replace("  Years","")
		findstartmonths = re.search('(\d)\s+Months', datadata[13].renderContents().strip())
		startmonths = findstartmonths.group().replace("  Months","")
		findstartdays = re.search('(\d)\s+Days', datadata[13].renderContents().strip())
		startdays = findstartdays.group().replace(" Days","")
		findendyears = re.search('(\d)\s+Years', datadata[14].renderContents().strip())
		endyears = findendyears.group().replace("  Years","")
		findendmonths = re.search('(\d)\s+Months', datadata[14].renderContents().strip())
		endmonths = findendmonths.group().replace("  Months","")
		findenddays = re.search('(\d)\s+Days', datadata[14].renderContents().strip())
		enddays = findenddays.group().replace(" Days","")
		startsentence = startyears + " years, " + startmonths + " months, " + startdays + " days"
		endsentence = endyears + " years, " + endmonths + " months, " + enddays + " days"
		sentencebegin = datadata[15].renderContents().strip()
		goodtimedays = datadata[16].renderContents().strip()
		projectedrelease = datadata[17].renderContents().strip()
		paroleeligibility = datadata[18].renderContents().strip()
		paroledischarge = datadata[21].renderContents().strip()
		releasedate = datadata[24].renderContents().strip()    
		releasetype = datadata[25].renderContents().strip()    
		
        # the table with  information about the crimes
		offensedata = soup.findAll('td', class_='tableData')[::2]
		tablength = len(offensedata)
		g = 0
		crimelist = []
        while g < tablength:
            crimelist.append(offensedata[g].renderContents().strip())
            g += 3
        crimes = ", ".join(crimelist)
        fullrecord = (lastname, firstname, middle, crimes, gender, race, dob, startsentence, endsentence, sentencebegin, projectedrelease, goodtimedays, paroleeligibility, paroledischarge, releasedate, releasetype, mug, "\n")
        
        # write it to a file
        f.write("|".join(fullrecord))
        print "Success! Record written. Going back for more...\n"
        
        # navigate back
        mech.back()
        sleep(3)
    
	page = mech.open(baseurl)
	html = page.read()
	soup = BeautifulSoup(html)
	sleep(3)

f.close()
