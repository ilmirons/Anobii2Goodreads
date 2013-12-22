#!/usr/bin/env python

# Customise these variables to define input and output
anobii_file = "anobii.csv"
goodreads_file = "import_to_goodreads.csv" 
goodreads_date_fmt = "%Y/%m/%d"

from datetime import date, datetime
import csv, codecs, cStringIO, re

class UTF8Recoder:
	"""
	Iterator that reads an encoded stream and reencodes the input to UTF-8
	"""
	def __init__(self, f, encoding):
		self.reader = codecs.getreader(encoding)(f)
	
	def __iter__(self):
		return self
	
	def next(self):
		return self.reader.next().encode("utf-8")

class UnicodeReader:
	"""
	A CSV reader which will iterate over lines in the CSV file "f",
	which is encoded in the given encoding.
	"""
	
	def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
		f = UTF8Recoder(f, encoding)
		self.reader = csv.reader(f, dialect=dialect, **kwds)
	
	def next(self):
		row = self.reader.next()
		return [unicode(s, "utf-8") for s in row]
	
	def __iter__(self):
		return self

class UnicodeWriter:
	"""
	A CSV writer which will write rows to CSV file "f",
	which is encoded in the given encoding.
	"""
	
	def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
		# Redirect output to a queue
		self.queue = cStringIO.StringIO()
		self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
		self.stream = f
		self.encoder = codecs.getincrementalencoder(encoding)()

	def writerow(self, row):
		items = []
		for s in row:
			if type(s) == type(u"s"):
				items.append(s.encode("utf8"))
			else:
				items.append(s)

		self.writer.writerow(items)
		# Fetch UTF-8 output from the queue ...
		data = self.queue.getvalue()
		data = data.decode("utf-8")
		# ... and reencode it into the target encoding
		data = self.encoder.encode(data)
		# write to the target stream
		self.stream.write(data)
		# empty queue
		self.queue.truncate(0)

	def writerows(self, rows):
		for row in rows:
			self.writerow(row)


reader = UnicodeReader(open(anobii_file, "rb"))
reader.next() # first line is column titles
target = []

target.append(["Title", "Author", "Additional Authors", "ISBN", "ISBN13", "My Rating", "Average Rating", "Publisher", "Binding", "Number of Pages", "Year Published", "Original Publication Year", "Date Read", "Date Added", "Bookshelves", "My Review", "Spoiler", "Private Notes", "Recommended For", "Recommended By"])

for l in reader:
        
        bookshelves = []
        
	isbn = l[0].replace('[', '').replace(']', '')
	title = l[1]
	subtitle = l[2] # Unused
	author = l[3]
	format = l[4]
	pages = l[5]
	publisher = l[6]
	
	pubdate = l[7]
	pubyear = ""
	if pubdate:
	    pubyear = pubdate[1:-1].split('-')[0]
	
	privnote = l[8] # Unused
	commentTitle = l[9] # Unused
	comment = l[10]
	
	def convertdate(dateString):
            """
            Dispatch date string to correct parsing function. Useful to handle dates which do not include date or month (partial dates)
            """
            if "," in dateString:
                return fullDate(dateString)
            else:
                return partialDate(dateString)
            
	
	def fullDate(d):
	    dt = datetime.strptime(d, "%b %d, %Y")
	    # Goodreads takes US formatted dates without century (just as stupid as Anobii really)
	    return dt.strftime(goodreads_date_fmt)

	def partialDate(txt):
		# thanks to the wonderful http://txt2re.com/index-python.php3?s=Aug%202004&3&7&2
		re1='((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?))'	# Month 1
		re2='(\\s+)'	# White Space 1
		re3='((?:(?:[1]{1}\\d{1}\\d{1}\\d{1})|(?:[2]{1}\\d{3})))(?![\\d])'	# Year 1

		rg = re.compile(re1 + re2 + re3,re.IGNORECASE|re.DOTALL)
		m = rg.search(txt)
		if m:
		    month1 = m.group(1)
		    ws1 = m.group(2)
		    year1 = m.group(3)
		    return convertdate(month1 + " 1, " + year1)
		else:
			if len(txt)>=4:
				return convertdate("Jan 1, " + txt)

	
	# Fragile but it works
	status = l[11]
	readdate = ""
	if "Finito" in status:
            bookshelves.append("read")
	    if "il" in status:
	        readdate = convertdate(status[10:])
	elif "Non Iniziato" in status:
	    bookshelves.append("not-started")
	elif "In lettura" in status:
	    bookshelves.append("currently-reading")
	elif "Abbandonato" in status:
            bookshelves.append("abandoned")
        elif "Non finito" in status:
            bookshelves.append("unfinished")
        elif "Da consultazione" in status or "Nota di riferimento" in status:
            bookshelves.append("reference")
	
	stars = l[12]
	tags = l[13].replace(" ","-").replace("-/-"," ") # unused
	
	tline = [title, author, "", "", isbn, stars, "", publisher, format, pages, pubyear, "", readdate, "", ",".join(bookshelves), comment, "", privnote, "", ""]
	target.append(tline)

writer = UnicodeWriter(open(goodreads_file, "wb"), dialect='excel', quoting = csv.QUOTE_NONNUMERIC)
writer.writerows(target)

print "Done! saved output to " + goodreads_file
