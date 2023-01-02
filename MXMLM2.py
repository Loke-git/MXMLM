#!/usr/bin/env python
# coding: utf-8
import sys
import subprocess
import pkg_resources

# Package installation borrowed from:
# https://stackoverflow.com/questions/12332975/installing-python-module-within-code/58040520#58040520
required  = {'bs4', 'pandas'} 
installed = {pkg.key for pkg in pkg_resources.working_set}
missing   = required - installed
if missing:
    # implement pip as a subprocess:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])


# MXMLM2 All-in-one
# XML, TEI, CMI/F and data handling
from bs4 import BeautifulSoup
from bs4.formatter import HTMLFormatter
from bs4 import Comment # BS4-addon for å håndtere kommentarer <!-- X -->
import re # Regex
import numpy as np
import pandas as pd
import collections # Facilitate dynamic dict
from string import punctuation
import json # JSON!

# Time and date
from datetime import date
import datetime # Dates
#import time # Time
dt = date.today().strftime('%A')
today = date.today()
today = today.strftime("%Y-%m-%d") # Formater dato

# File and folder handling
import glob # The yeast of thought and mind
import os # File system


# Metadata and configuration
import configparser # Used to easily get statements from the config file

# https://stackoverflow.com/questions/62971773/python-beautifulsoup-changes-attribute-positioning
# Borrowed to stop the attributes from sorting off from before, after to after, before.
class UnsortedAttributes(HTMLFormatter):
    def attributes(self, tag):
        for k, v in tag.attrs.items():
            yield k, v
            
#Check if *keys (nested) exists in dict
def keys_exists(element, *keys):
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True

# Chronology - IMPORTANT. v2 **requires** modifications to the chronology file. All MM N/K/T objects must be replaced by No-MM_N/K/T. 
# All objects must have excess spaces removed. PN objects are permitted to be formatted without leading zeroes 
# following the prefix (PN99 will be read as PN0099).

hasXMLs = False
listofbaddies = []
lookupChrono = sorted(glob.glob("*Kronologi_Munchs_brev*.xlsx"), key=os.path.getmtime)
x = len(lookupChrono)-1
if x > -1:
    print("Newest chronology file:",lookupChrono[x])
    chronologyFile = lookupChrono[x]
    #shutil.copy2(chronologyFile, inputfolder+"/kronologi.xlsx")
    #chronologyFile = inputfolder+"/kronologi.xlsx"
    
    chronology = pd.read_excel(chronologyFile).dropna(axis=1, how='all').dropna(axis=0, how='all').reset_index(drop=True)
    chronology = chronology.fillna("N/A")
    
    try:
        if CHRONODICT:
            print("CHRONODICT found with content")
        else:
            print("CHRONODICT found without content")
    except:
        CHRONODICT = collections.defaultdict(dict)
        print("CHRONODICT created")
    for idx,row in chronology.iterrows():
        mismatch = False
        formattingError = False
        document = chronology.iloc[idx]['Objektnr.']
        rawdate = chronology.iloc[idx]['Dato']
        #print("Document:",document)
        if rawdate != "N/A" and document != "N/A": # If date and documents are not N/A
            #print("\thas date and ID")
            document = document.replace(" ","")
            # This section checks PN objects for compliance. Compliant PN objects have the PN prefix followed by 4 digits, total 6 chars.
            # In cases where the object ID is too short, zeroes (0) are added immediately after the PN prefix until it complies.
            # In cases where the object ID is too long, characters are removed from the end of the ID until it complies.
            # This script will function until PN object IDs exceed 9999, meaning that there are 7 characters in the PN series instead of 6.
            chkStr = document[0:2]
            if chkStr == "PN":
                # If the characters after the prefix are not ALL numeric, the object is skipped entirely.
                if len(document) < 6:
                    while len(document) < 6:
                        document = document[0:2]+'0'+document[2:len(document)]
                    #print("Extended",document)
                elif len(document) > 6:
                    document = document[0:6]
                    #print("Reduced",document)
            # This section checks No-MM_N/K objects for compliance. Compliant objects have the No prefix and a total of 11 characters.
            # Procedure is identical to PN objects.
            elif chkStr == "No":
                if len(document) < 11:
                    # Results in "extending" the document ID by appending 0 to the prefix
                    while len(document) < 11:
                        document = document[0:7]+"0"+document[7:len(document)]
                elif len(document) > 11:
                    if "," in document: # If comma in the documentID, just remove EVERYTHING to the right of it.
                        splitD = document.split(",")
                        document = splitD[0]
                    # Required to fix No-MM_N03101 and similar.
                    if document[7] == "0":
                        while len(document) > 11 and document[7] == "0":
                            document = document[0:7]+document[8:len(document)] # Discards characters after prefix
                    document = document[0:11] # Discards last n characters until 11 remain
        # If the last 4 characters are NOT ALL numeric, the object is skipped entirely. 
            if document[len(document)-4:].isnumeric() == False:
                formattingError = True # Formatting error due to invalid filename.
                listofbaddies.append(document)
                print(document,"is not a valid document ID and was excluded.")
        # If the document ID somehow is not 11 or 6 characters long, it is skipped entirely.
            elif len(document) != 11 and len(document) != 6: # If string doesn't match with No-MM_N0000 or PN0000
                #filenamePlain = "Formatting error"+filenamePlain # it is invalid.
                formattingError = True # Formatting error due to invalid filename.
                listofbaddies.append(document)
                print(document,"is not a valid document ID and was excluded.")
        # If the document ID is 11 or 6 characters long and the last 4 characters are numeric:
            else:
                if isinstance(rawdate,datetime.date): # If it's just a datetime object
                    newdate = rawdate.strftime("%Y-%m-%d")
                else:
                    dateobject = str(rawdate) # Make sure it's string
                    string4print = document+" "+dateobject
                    if ".-" in dateobject: # Like: 04.-05.1922.
                        dateobject = dateobject.replace(".-","-")
                    if "?" in dateobject:
                        dateobject = dateobject.replace("?","").strip(punctuation) # Remove n ?s and then also remove excess .
                        dateobject = dateobject.replace("..",".")
                    if "-" in dateobject:
                        splitToFrom = dateobject.split("-")
                        fromDate = splitToFrom[0]
                        toDate = splitToFrom[1]
                        
                        newFromDate = fromDate.split(".")
                        newToDate = toDate.split(".")
                        while ("" in newFromDate):
                            newFromDate.remove("")
                        while ("" in newToDate):
                            newToDate.remove("")
                        #Debug
                        
                        if len(newToDate) != len(newFromDate):
                            if len(newToDate) > len(newFromDate):
                                itemsToGet = len(newToDate)-len(newFromDate)-1
                                if itemsToGet == 1: # Get items 2 and 3
                                    while itemsToGet < len(newToDate):
                                        newFromDate.append(newToDate[itemsToGet])
                                        itemsToGet+=1
                                elif itemsToGet == 0: # Get last item
                                    newFromDate.append(newToDate[len(newToDate)-1])
                            else:
                                print("WARNING: Unable to resolve instances where From date is more specific than To date!")
                        if isinstance(newFromDate,list):
                            if len(newFromDate) > 1:
                                newdateF = newFromDate[len(newFromDate)-1]
                                for x in reversed(newFromDate):
                                    if len(x) == 4:
                                        pass
                                    else:
                                        if len(x) == 2:
                                            newdateF+="."+x
                                        else:
                                            pass 
                            else:
                                newdateF = newFromDate[0]
                        else:
                            newdateF = fromDate
                        
                        if isinstance(newToDate,list):
                            if len(newToDate) > 1:
                                newdateT = newToDate[len(newToDate)-1]
                                for x in reversed(newToDate):
                                    if len(x) == 4:
                                        pass
                                    else:
                                        if len(x) == 2:
                                            newdateT+="."+x
                                        else:
                                            pass 
                            else:
                                newdateT = newFromDate[0]
                        else:
                            newdateT = toDate
                    
                        newdate=newdateF+"%"+newdateT
                        datetype = "fromTo"

                    else:
                        datelements = dateobject.split(".")
                        newdate = datelements[len(datelements)-1]
                        datetype = "instance"
                        for x in reversed(datelements):
                            if len(x) == 4:
                                pass
                            else:
                                if len(x) == 2:
                                    newdate+="-"+x
                                else:
                                    break      

                    CHRONODICT[document]["date"] = newdate # Set the dict item's date to newdate
                    CHRONODICT[document]["datetype"] = datetype
print(f"Dates retrieved and corrected. Skipped {listofbaddies}")

## Places
if os.path.isfile("ID_sted-verdier.xlsx"):
    print("Detected ID_sted-verdier.xlsx")
    if os.path.exists("xml-filer"):
        print("XML>CMIF placename augmentation enabled")
        listXMLfiles = glob.glob("xml-filer/**/*.xml",recursive=True)
        hasXMLs = True
        # Check to see if CHRONODICT is alive or not. If it is, use it as destination. If it isn't, create it.
        try:
            if CHRONODICT:
                print("CHRONODICT found with content")
            else:
                print("CHRONODICT found without content")
        except:
            CHRONODICT = collections.defaultdict(dict)
            print("CHRONODICT created")
        print("Populating CHRONODICT with place IDs from letter XMLs")
        addrsFoundInXMLs = [] # Make a simple list to hold the short names of every file we've found addresses for
        xmlswithnoaddress = [] # Simple list for XMLs that have no address that can be printed later.
        plainnames = [] # Simple list for plain names of XMLs that have been checked.
        i=0
        for item in listXMLfiles:
            addrKey = "NONE" # Just in case
            find_address = [] # Ensure that this list clears on start of each item
            findFileName = item.split("\\") # Make filepath a list
            findFileName = findFileName[len(findFileName)-1] # Get the path destination file

            chkStr = findFileName[0:2] # Check the incoming ID - it's either PN+4 positions, or No+9 positions long.
            if chkStr == "PN": # 6 positions
                filenamePlain = findFileName[0:6] # Must be bounded to remove .xml as well as pagination from filename
                #print(findFileName,filenamePlain)
            elif chkStr == "No": # 11 positions
                filenamePlain = findFileName[0:11] # Must be bounded to remove .xml as well as pagination from filename
                #print(findFileName,filenamePlain)
            else: # This doesn't occur unless you've got files that don't belong here
                print("CRITICAL ERROR: PROBLEM IN NAME PROCESSING",findFileName,chkStr) 
            if filenamePlain not in plainnames: # For every unique name, add to plainnames
                plainnames.append(str(filenamePlain)) # Just in case we need them later
            mmmm = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90]
            
            if round(i/len(listXMLfiles)*100) in mmmm or round(i/len(listXMLfiles)*100) > 90:
                print ("\r","Progress:",round(i/len(listXMLfiles)*100),"/ 100", end='\t')
            if filenamePlain in addrsFoundInXMLs: # if we found the address for this xml
                pass # Skip if we've already found an address for this XML filename
            else:
                with open(item, "r", encoding="utf-8") as file: # Open a file
                    letterfile = file.read()
                    #letterfile = file.readlines() # Les innholdet som linjer
                    #letterfile = "".join(letterfile) # Linjene blir kombinert i en variabel

                # Faster if we search for the word "dateline", THEN soup it if it has an occurrence...
                if re.search(r'dateline', str(letterfile), flags=re.DOTALL):
                    #print("Identified dateline in",findFileName)
                    ## Code below enables retrieval of an address enclosed in a dateline element.
                    ## This is understood to be the sender's address.

                    soup = BeautifulSoup(letterfile, features="xml") # It is now soup


                    find_address = soup.find("dateline") # Look for a dateline element
                    if find_address: # If there is a dateline element:
                        #print("Dateline in",findFileName)
                        find_address = find_address.findChild("placeName", recursive=True) # Get the placename
                        #print("DATELINE",find_address)
                        try: # There are documents with datelines but no locations in them confirmed.
                            addrKey = find_address.get('key') # Get the internal ID of the placename
                            #print(addrKey)
                            try:
                                addrKey = addrKey.replace("pl","") # Remove "pl" prefix
                                addrsFoundInXMLs.append(filenamePlain) # Add the filename to the list of XMLs already found

                                CHRONODICT[filenamePlain]["location"] = addrKey

                                #print(f"\t{filenamePlain}: {addrKey}, #{len(addrsFoundInXMLs)} (out of {i})")
                            except: # Uncommon error - should be investigated. Means that there is a dateline, there is a location,
                                # but something else is going on.
                                print("\tCritical error: location found, but we encountered a problem when appending!\n")

                        except: # Harmless: means dateline does not have address
                            if filenamePlain not in xmlswithnoaddress:
                                xmlswithnoaddress.append(filenamePlain)
                            #print("Dateline without address in",findFileName)
                    else: # The dateline simultaneously exists and does not exist. This is rather suboptimal.
                        # You should not be getting this error.
                        print("\tCritical error: Schrödinger's dateline\n")
                        if filenamePlain not in xmlswithnoaddress:
                            xmlswithnoaddress.append(filenamePlain)
                else:
                    pass # No dateline found, move on to the next.

            i+=1
        print(f"\nComplete! {i} files checked, {len(addrsFoundInXMLs)} good dates acquired from {len(addrsFoundInXMLs)+len(xmlswithnoaddress)} datelines.\n({len(xmlswithnoaddress)} datelines had no location/address information)")
        howMany = 0
        placenamedf = pd.read_excel("ID_sted-verdier.xlsx").dropna(axis=1, how='all').dropna(axis=0, how='all').reset_index(drop=True)
        placenamedf = placenamedf.fillna("N/A")
        for item in CHRONODICT:
            if keys_exists(CHRONODICT,item,'location'):
                try:
                    placenameSearch = placenamedf[placenamedf['ID'].astype(str) == str(CHRONODICT[item]['location'])]
                    stedsnavn = placenameSearch["sted"].values[0]
                    regionnavn = placenameSearch["region, nasjonal"].values[0]
                    landnavn = placenameSearch["land"].values[0]
                    kontinent = placenameSearch["region, internasjonal"].values[0]
                    try:
                        if stedsnavn != "N/A":
                            #print("\tSted:",stedsnavn)
                            CHRONODICT[item]['location'] = stedsnavn
                            howMany+=1
                        else:
                            if regionnavn != "N/A":
                                #print("\tRegion:",regionnavn)
                                CHRONODICT[item]['location'] = regionnavn
                                howMany+=1
                            else:
                                if landnavn != "N/A":
                                    #print("\tLand:",landnavn)
                                    CHRONODICT[item]['location'] = landnavn
                                    howMany+=1
                                else:
                                    if kontinent != "N/A":
                                        #print("\tKontinent:",kontinent)
                                        CHRONODICT[item]['location'] = kontinent
                                        howMany+=1
                                    else:
                                        print("\tFant ikke stedsnavn.")
                    except:
                        print("\t\tCouldn't match, I guess?")
                except:
                    print("\t\tNo match for",str(CHRONODICT[item]['location']))
            #print("\n")
        print("Got",howMany,"placeNames.")
            
    else:
        print("No XML files provided. XML>CMIF placename augmentation disabled")
else:
    print("No ID_sted-verdier file provided. Skipping placename augmentation.")

pathToOutput = "output/"
pathToOutputData = pathToOutput+"datasets/"
pathToOutputCMIF = pathToOutput+"CMIF/"

# Create output folders
if os.path.exists(pathToOutput):
    pass
else:
    os.mkdir(pathToOutput)



if os.path.exists(pathToOutputData):
    pass
else:
    os.mkdir(pathToOutputData)

if os.path.exists(pathToOutputCMIF):
    pass
else:
    os.mkdir(pathToOutputCMIF)



df = pd.DataFrame.from_dict(CHRONODICT)
chronoDF = df.T.fillna("N/A").reset_index(drop=False)
# Check for presence of date column (otherwise, would crash if no chronology used)
if 'date' not in chronoDF.columns:
    chronoDF['date'] = np.nan
    print("Filled date column with NaN")
# Check for presence of location column (otherwise, would crash if no letter XMLs used)
if 'location' not in chronoDF.columns:
    chronoDF['location'] = np.nan
    print("Filled location column with NaN")
chronoDF = chronoDF.rename(columns={"index": "document"}).sort_values(by=['document']).reset_index(drop=True).fillna("N/A")
places = 0
dates = 0
items = 0
for idx,row in chronoDF.iterrows():
    if row['date'] == "N/A" and row['location'] == "N/A":
        print(f"Warning - {idx} has neither date nor location")
    else:
        items += 1
        if row['date'] != "N/A":
            dates += 1
        if row['location'] != "N/A":
            places += 1
print(places,"places and",dates,"dates added over a total of",items,"items.")
chronoDF.to_csv(pathToOutputData+"preprocessed.csv", sep=',', encoding='utf-8',index=False)
print("Preprocessing complete. Saved to preprocessed.csv. Printing report as Preprocessor Report.txt.")

goodstring = "MXMLM Preprocessor"
try:
    if plainnames:
        goodstring += "\nChecked "+str(i)+" files, of which "+str(len(plainnames))+" were identified as letters, of which "+str(len(addrsFoundInXMLs))+" had addresses."
    else:
        goodstring += "\nCAUTION Checked "+str(i)+" (zero?) files, of which "+str(len(plainnames))+" were identified as letters, of which "+str(len(addrsFoundInXMLs))+" had addresses."
except:
    goodstring+= "\nDidn't use placename augmentation?"
goodstring+="\n"+str(places)+" places and "+str(dates)+" dates added over a total of "+str(items)+" items."
if len(listofbaddies) > 0:
    errorstring = "Bad document IDs from the Chronology that could not be resolved:\n"
    for x in listofbaddies:
        errorstring+="\""+x+"\" "
    errorstring = errorstring.rstrip()
else:
    errorstring = "Didn't identify any bad document IDs that couldn't be resolved."
outputstring = goodstring+"\n"+errorstring

with open(pathToOutputData+"Preprocessor Report.txt", "w", encoding="utf-8") as output_file:
    output_file.write(outputstring)

## Main file: Correspondence
mmmm = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90]
if os.path.isfile("correspondence.xml"):
    CorrespDict = collections.defaultdict(dict)
    print("CorrespDict initiated")
    print("Melting correspondence.xml")
    with open("correspondence.xml", "r", encoding="utf-8") as file: # Open a file
        tei = file.readlines() # Les innholdet som linjer
        tei = "".join(tei) # Linjene blir kombinert i en variabel
    soup = BeautifulSoup(tei, features="xml") # It is now soup
    comments = 0
    commentDocs = 0
    # Checking for comments
    for comment in soup.findAll(string=lambda text: isinstance(text, Comment)):
        if "xml:id=\"" in comment:
            commentDocs+=1
        comment.extract()
        comments+=1
    if comments > 0:
        print("Destroyed",comments,"<!--comments-->, of which",commentDocs,"contained an @XML:ID.")
    # ... and checking it twice.
    comments = soup.findAll(string=lambda text: isinstance(text, Comment))
    if comments:
        print("INFO There are still",len(comments),"comments present.")
    else:
        pass
    print("\nInitializing documentID scan")
    documentIDs,destroyeds = [],0
    for document in soup.findAll("div", {"xml:id":True}):

        # Look for the document type assignment.
        documentType = document.find("list", {"type" : "objectType"}).findChild(True, recursive=True)#.attrs['n']
        # Checks if the words "letter" or "brev" appear in the type
        if "brev" in documentType or "letter" in documentType: 
            # Get the document ID from the <div> element.
            documentID = list(document.attrs.values())[0]
            documentIDs.append(documentID)
        else:
            document.decompose() # Destroy non-letters.
            destroyeds+=1
    print(f"Acquired {len(documentIDs)} documents classed as letters. Dropped {destroyeds} others.\n")
        
    i=1
    for eachID in documentIDs:
        if round(i/len(documentIDs)*100) in mmmm or round(i/len(documentIDs)*100) > 90:
            print ("\r","Progress:",round(i/len(documentIDs)*100),"/ 100", end='\t')
        i+=1
        docAuthors = [] # List of authors to be included in the dict.
        docAuthorRefs = [] # List of authors' reference URLs.
        docAuthorTypes = [] # The types of the above.
        # Munch is the recipient of everything in correspondence.xml.
        recipient = ["Edvard Munch"]

        # Target the document as var "document"
        document = soup.find("div", {"xml:id":eachID})

        # Target the author(s) as authorNameList
        authorNameList = document.find("item", {"n":"sender"}).findChildren(True, recursive=True)
        X=0
        for name in authorNameList:
            try:
                authorName = authorNameList[X].contents[0]
                try:
                    targetRef = authorNameList[X]['target']
                except:
                    targetRef = "N/A"
            except:
                authorName = "N/A"
                targetRef = "N/A"
            if match := re.search("[^=]*$",targetRef):
                matchRef = match.group(0)
            else:
                matchRef = "N/A"

            if targetRef != "N/A":
                if "pers" in targetRef: # Persons are persons
                    docAuthorTypes.append("persName")
                    if matchRef != "N/A":
                        matchRef = "https://emunch.no/person.xhtml?id="+str(matchRef)
                    #print("PERS")
                elif "instit" in targetRef: # Institutions are organizations
                    docAuthorTypes.append("orgName")
                    if matchRef != "N/A":
                        matchRef = "https://emunch.no/institution.xhtml?id="+str(matchRef)
                    #print("ORG")
                else: # Default to persName
                    docAuthorTypes.append("persName")
                    if matchRef != "N/A":
                        matchRef = "https://emunch.no/person.xhtml?id="+str(matchRef)
                    #print(f"??? {targetRef}") 
            else: # Default to persName if we can't tell which it is
                docAuthorTypes.append("persName")
                if matchRef != "N/A":
                    matchRef = "https://emunch.no/person.xhtml?id="+str(matchRef)
            
            
            # Data cleaning
            authorName = authorName.replace(","," ")
            authorName = re.sub(' +', ' ',authorName)
            authorName = authorName.strip()       
            
            X+=1
            docAuthors.append(authorName)
            docAuthorRefs.append(matchRef)

        isDocumentUndated = document.find("item", {"n":"undated"})
        if eachID in CHRONODICT:
            try:
                newdate = CHRONODICT[eachID]['date']
                gotDate = True
            except:
                newdate = "N/A"
                gotDate = False
            try:
                place = CHRONODICT[eachID]['location']
                gotPlace = True
            except:
                place = "N/A"
                gotPlace = False
        else:
            gotDate = False
            gotPlace = False

        if isDocumentUndated:
            # Document is straight up undated.
            date = "s.d."
            datetype = "N/A"

        else:
            isDocumentFromTo = document.find("date", {"from":True}) # Does the date element have a from assignment? 
            # ! Using "from" because PN1350 does not have a fromTo attr despite using fromTo. Uses "from", though. Works fine.
            if isDocumentFromTo: # If it does, and thus has a range
                doesDocumentHaveToDate = document.find("date", {"to":True})
                if doesDocumentHaveToDate:
                    # Both from and to attributes are present.
                    fromDate = isDocumentFromTo['from'] # Extract 'from' date. 
                    toDate = isDocumentFromTo['to'] # Extract 'to' date.
                    datetype = "fromTo"
                    date = str(fromDate)+"%"+str(toDate)
                else:
                    # If the 'from' attribute is present without the 'to', it's interpreted as "not before this date".
                    date = isDocumentFromTo['from']
                    fromDate = isDocumentFromTo['from']
                    datetype = "notBefore"

            else: # If it doesn't:
                yearSent = document.find("date", {"type":"year","when":True}) # Check for year element
                monthSent = document.find("date", {"type":"month","when":True}) # Check for month element
                daySent = document.find("date", {"type":"day","when":True}) # Check for day element
                if yearSent:
                    datetype = "instance"
                    date = yearSent.attrs["when"]
                    if monthSent: # Only look for a month if there's a year. That 1 letter with just month/day, tho...
                        M = re.sub('[-]', '', monthSent.attrs["when"]) # Strip the random '-' characters in here.
                        date+="-"+str(M) # Join month to year by YYYY-MM.
                        if daySent: # Only applies if there is a month AND a day. No point having a day if you don't have a month.
                            M = re.sub('[-]', '', daySent.attrs["when"]) # Strip the random '-' characters in here, too.
                            date+="-"+str(M) # Join day to year-month by YYYY-MM-DD.
                else: 
                # If it doesn't have a year, make one last check
                    doesDocumentHaveToDate = document.find("date", {"to":True}) # if the date just has a to date...
                    if doesDocumentHaveToDate:
                    # If the 'to' attribute is present without the 'from', it's interpreted as "not after this date".
                        datetype = "notAfter"
                        date = doesDocumentHaveToDate['to']
                    else:
                    # All else has failed. This data is expunged.
                        datetype = "N/A"
                        date = "s.d."
        # Destroy the document we were looking at.
        document.decompose()
        # By doing this, we feed the script the top entry every single time.
        
        CorrespDict[eachID]['authors'] = docAuthors
        CorrespDict[eachID]['authorsType'] = docAuthorTypes
        CorrespDict[eachID]['authorsRef'] = docAuthorRefs
        CorrespDict[eachID]['date'] = date
        CorrespDict[eachID]['datetype'] = datetype
        CorrespDict[eachID]['recipients'] = recipient
        CorrespDict[eachID]['recipientsType'] = ["persName"]
        CorrespDict[eachID]['recipientsRef'] = ["https://viaf.org/viaf/61624802/"]
        
        if gotPlace == True:
            CorrespDict[eachID]['place'] = place
        else:
            CorrespDict[eachID]['place'] = "N/A"
        if gotDate == True:
            CorrespDict[eachID]['newdate'] = newdate
            CorrespDict[eachID]['newdatetype'] = CHRONODICT[eachID]["datetype"]
        else:
            CorrespDict[eachID]['newdate'] = "s.d."
            CorrespDict[eachID]['newdatetype'] = "N/A"
    json_object = json.dumps(CorrespDict, indent=4)
    with open(pathToOutputData+"correspondence.json", "w") as outfile:
        outfile.write(json_object)
    print(f"Complete - wrote to {pathToOutputData}correspondence.json")
else:
    print("No correspondence.xml file provided. MXML will not munch letters to Munch.")

# Main Registry

if os.path.isfile("register_tei.xml"):
    RegDict = collections.defaultdict(dict)
    print("RegDict initiated")
    print("Melting register_tei.xml")
    with open("register_tei.xml", "r", encoding="utf-8") as file: # Open a file
        tei = file.readlines() # Les innholdet som linjer
        tei = "".join(tei) # Linjene blir kombinert i en variabel
    soup = BeautifulSoup(tei, features="xml") # It is now soup
    print("Registry is now soup.")
    comments = 0
    commentDocs = 0
    for comment in soup.findAll(string=lambda text: isinstance(text, Comment)):
        if "xml:id=\"" in comment:
            commentDocs+=1
        comment.extract()
        comments+=1
    if comments > 0:
        print("Destroyed",comments,"<!--comments-->, of which",commentDocs,"contained an @XML:ID.")
    # ... and checking it twice.
    comments = soup.findAll(string=lambda text: isinstance(text, Comment))
    if comments:
        print("There are still",len(comments),"comments present.")
    else:
        print("All comments destroyed.")
        
    print("\nInitializing documentID scan.")
    documentIDs = []
    for document in soup.findAll("div", {"xml:id":True}):

        # Look for the document type assignment.
        documentType = document.find("list", {"type" : "objectType"}).findChild(True, recursive=True)#.attrs['n']
        # Checks if the words "letter" or "brev" appear in the type
        if "brev" in documentType or "letter" in documentType: 
            # Get the document ID from the <div> element.
            documentID = list(document.attrs.values())[0]
            documentIDs.append(documentID)
        else:
            document.decompose() # Destroy non-letters.
            destroyeds+=1
    print(f"Acquired {len(documentIDs)} documents classed as letters. Destroyed {destroyeds} others.\n")
        
    # Slight repetition - breaking DRY, I know - but by referencing documentIDs we're 100% only treating letters,
    # not wasting time on irrelevant documents
    i=1
    for eachID in documentIDs:
        if round(i/len(documentIDs)*100) in mmmm or round(i/len(documentIDs)*100) > 90:
            print ("\r","Progress:",round(i/len(documentIDs)*100),"/ 100", end='\t')
        i+=1
        docRecipRefs = [] # List of authors' reference URLs.
        docRecipients = [] # List of recipients to be included in the dict. 
        docRecipsType = []
        # Munch is the author of everything in the registry.
        author = ["Edvard Munch"]

        # Target the document as var "document"
        document = soup.find("div", {"xml:id":eachID})

        # Target the recipients(s) as recipNameList
        recipNameList = document.find("item", {"n":"recipient"}).findChildren(True, recursive=True)
        X=0
        for name in recipNameList:
            try:
                recipName = recipNameList[X].contents[0]
                try:
                    targetRef = recipNameList[X]['target']
                except:
                    targetRef = "N/A"
            except:
                recipName = "N/A"
                targetRef = "N/A"
            
            if match := re.search("[^=]*$",targetRef):
                matchRef = match.group(0)
            else:
                matchRef = "N/A"

            if targetRef != "N/A":
                if "pers" in targetRef: # Persons are persons
                    docRecipsType.append("persName")
                    if matchRef != "N/A":
                        matchRef = "https://emunch.no/person.xhtml?id="+str(matchRef)
                elif "instit" in targetRef: # Institutions are organizations
                    docRecipsType.append("orgName")
                    if matchRef != "N/A":
                        matchRef = "https://emunch.no/institution.xhtml?id="+str(matchRef)
                else: # Default to persName
                    docRecipsType.append("persName")
                    if matchRef != "N/A":
                        matchRef = "https://emunch.no/person.xhtml?id="+str(matchRef)
            else: # Default to persName if we can't tell which it is
                docRecipsType.append("persName")
                if matchRef != "N/A":
                    matchRef = "https://emunch.no/person.xhtml?id="+str(matchRef)
                
            # Data cleaning
            recipName = recipName.replace(",","&#44;")
            recipName = recipName.strip()
            recipName = re.sub(' +', ' ',recipName)
            X+=1
            docRecipients.append(recipName)
            docRecipRefs.append(matchRef)
        isDocumentUndated = document.find("item", {"n":"undated"})
        if eachID in CHRONODICT:
            try:
                newdate = CHRONODICT[eachID]['date']
                gotDate = True
            except:
                newdate = "N/A"
                gotDate = False
            try:
                place = CHRONODICT[eachID]['location']
                gotPlace = True
            except:
                place = "N/A"
                gotPlace = False
        else:
            gotDate = False
            gotPlace = False
        if isDocumentUndated:
            # Document is straight up undated.
            date = "s.d."
            datetype = "N/A"
        else:
            isDocumentFromTo = document.find("date", {"from":True}) # Does the date element have a from assignment? 
            # ! Using "from" because PN1350 does not have a fromTo attr despite using fromTo. Uses "from", though. Works fine.
            if isDocumentFromTo: # If it does, and thus has a range
                doesDocumentHaveToDate = document.find("date", {"to":True})
                if doesDocumentHaveToDate:
                    # Both from and to attributes are present.
                    fromDate = isDocumentFromTo['from'] # Extract 'from' date. 
                    toDate = isDocumentFromTo['to'] # Extract 'to' date.
                    datetype = "fromTo"
                    date = str(fromDate)+"%"+str(toDate)
                else:
                    # If the 'from' attribute is present without the 'to', it's interpreted as "not before this date".
                    date = isDocumentFromTo['from']
                    fromDate = isDocumentFromTo['from']
                    datetype = "notBefore"
            else: # If it doesn't:
                yearSent = document.find("date", {"type":"year","when":True}) # Check for year element
                monthSent = document.find("date", {"type":"month","when":True}) # Check for month element
                daySent = document.find("date", {"type":"day","when":True}) # Check for day element
                if yearSent:
                    datetype = "instance"
                    date = yearSent.attrs["when"]
                    if monthSent: # Only look for a month if there's a year. That 1 letter with just month/day, tho...
                        M = re.sub('[-]', '', monthSent.attrs["when"]) # Strip the random '-' characters in here.
                        date+="-"+str(M) # Join month to year by YYYY-MM.
                        if daySent: # Only applies if there is a month AND a day. No point having a day if you don't have a month.
                            M = re.sub('[-]', '', daySent.attrs["when"]) # Strip the random '-' characters in here, too.
                            date+="-"+str(M) # Join day to year-month by YYYY-MM-DD.
                else: 
                # If it doesn't have a year, make one last check
                    doesDocumentHaveToDate = document.find("date", {"to":True}) # if the date just has a to date...

                    if doesDocumentHaveToDate:
                    # If the 'to' attribute is present without the 'from', it's interpreted as "not after this date".
                        datetype = "notAfter"
                        date = doesDocumentHaveToDate['to']
                    else:
                    # All else has failed. This data is expunged.
                        datetype = "N/A"
                        date = "s.d."
        RegDict[eachID]['authors'] = author
        RegDict[eachID]['authorsRef'] = ["https://viaf.org/viaf/61624802/"]
        RegDict[eachID]['authorsType'] = ["persName"]
        RegDict[eachID]['date'] = date
        RegDict[eachID]['datetype'] = datetype
        RegDict[eachID]['recipients'] = docRecipients
        RegDict[eachID]['recipientsType'] = docRecipsType
        RegDict[eachID]['recipientsRef'] = docRecipRefs
        if gotPlace == True:
            RegDict[eachID]['place'] = place
        else:
            RegDict[eachID]['place'] = "N/A"
        if gotDate == True:
            RegDict[eachID]['newdate'] = newdate
            RegDict[eachID]['newdatetype'] = CHRONODICT[eachID]["datetype"]
        else:
            RegDict[eachID]['newdate'] = "s.d."
            RegDict[eachID]['newdatetype'] = "N/A"
        # Destroy the document we were looking at.
        document.decompose()
    json_object = json.dumps(RegDict, indent=4)
    with open(pathToOutputData+"registry.json", "w") as outfile:
        outfile.write(json_object)
    print(f"Complete - wrote to {pathToOutputData}registry.json")
else:
    print("No correspondence.xml file provided. MXML will not munch letters to Munch.")

df1 = pd.DataFrame.from_dict(RegDict).T#.reset_index(drop=False)
df2 = pd.DataFrame.from_dict(CorrespDict).T#.reset_index(drop=False)
dfCombo = df1.append(df2).reset_index(drop=False).rename(columns={'index':'document'}).fillna("N/A")

result = dfCombo.to_json(orient="index")
parsed = json.loads(result)
dumped = json.dumps(parsed, indent=4)
with open(pathToOutputData+"MXMLM_Output_Combined.json", "w") as outfile:
    outfile.write(dumped)
print(f"Wrote {pathToOutputData}MXMLM_Output_Combined.json (unified dataset including optional files)")

# CMIF Production Core

print("Getting metadata from config.ini...")
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")
cmifTitle = config.get("statements", "cmifTitle")
editorName = config.get("statements", "editorName")
editorMail = config.get("statements", "editorMail")
cmifUid = config.get("statements", "cmifUid")
publisherURL = config.get("statements", "publisherURL")
publisherName = config.get("statements", "publisherName")
cmifURL = config.get("statements", "cmifURL")
typeOfBibl = config.get("statements", "typeOfBibl")
publicationStatementFull = config.get("statements", "publicationStatementFull")

print("Creating CMIF...")
# Create CMIF boilerplate object
CMIFstring = '<?xml-model href="https://raw.githubusercontent.com/TEI-Correspondence-SIG/CMIF/master/schema/cmi-customization.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?><TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><titleStmt><title>'+str(cmifTitle)+'</title><editor>'+str(editorName)+'<email>'+str(editorMail)+'</email></editor></titleStmt><publicationStmt><publisher><ref target="'+str(publisherURL)+'">'+str(publisherName)+'</ref></publisher><idno type="url">'+str(cmifURL)+'</idno><date when="'+str(today)+'"/><availability><licence target="https://creativecommons.org/licenses/by/4.0/">This file is licensed under the terms of the Creative-Commons-License CC-BY 4.0</licence></availability></publicationStmt><sourceDesc><bibl type="'+str(typeOfBibl)+'" xml:id="'+str(cmifUid)+'">'+str(publicationStatementFull)+'</bibl></sourceDesc></fileDesc><profileDesc><dummy/></profileDesc></teiheader><text><body><p/></body></text></tei>'
CMIF = BeautifulSoup(CMIFstring,"xml") # Read as XML, not HTML
profileDescElement = CMIF.find('profileDesc') # Target correspondence wrapper
for idx,row in dfCombo.iterrows():
    document,date,datetype,authors,recipients,place = row['document'],row['date'],row['datetype'],row['authors'],row['recipients'],row['place']

    # Construct CMIF correspDesc element
    correspDescElement = CMIF.new_tag("correspDesc", attrs={"key":str(document), "ref":"https://www.emunch.no/HYBRID"+str(document)+".xhtml", "source":"#"+cmifUid})
    profileDescElement.append(correspDescElement)
    i=0
    ## Author (sender) encoding
    
    for each in authors:
        # For each author, add a correspAction element...
        correspActionElement = CMIF.new_tag("correspAction", attrs={'type':'sent'})
        correspDescElement.append(correspActionElement)
        category = dfCombo.iloc[idx]["authorsType"][i]
        ref = dfCombo.iloc[idx]["authorsRef"][i]
        if category == "orgName":
            if ref != "N/A":
                persNameElement = CMIF.new_tag("orgName", attrs={"ref":ref})
            else:
                persNameElement = CMIF.new_tag("orgName")
        else:
            if ref != "N/A":
                persNameElement = CMIF.new_tag("persName", attrs={"ref":ref})
            else:
                persNameElement = CMIF.new_tag("persName")
        persNameElement.string = str(each)
        correspActionElement.append(persNameElement)
        i+=1
    # Place encoding
    if place != "N/A":
        locationElement = CMIF.new_tag("placeName")#, attrs={"ref":"#idref"+str(re.sub(' +', '',place))}) # Create place element
        locationElement.string = str(place) # Give it a string value (placename)
        correspActionElement.append(locationElement) # Append the new element to the correspAction element
    # End place encoding
    # Date encoding
    if date != "s.d.":
        if "%" in date:
            daterange = date.split("%")
            date = f"Between {daterange[0]} and {daterange[1]}"
            dateSentElement = CMIF.new_tag("date", attrs={"notBefore":daterange[0]})
            dateSentElement['notAfter'] = daterange[1]
        else:
            dateSentElement = CMIF.new_tag("date", attrs={"when":date})
        correspActionElement.append(dateSentElement)
    # End date encoding
    # End author (sender) encoding
    
    i=0
    # Recipient encoding
    for each in recipients:
        correspActionElement = CMIF.new_tag("correspAction", attrs={'type':'received'})
        correspDescElement.append(correspActionElement)
        category = dfCombo.iloc[idx]["recipientsType"][i]
        ref = dfCombo.iloc[idx]["recipientsRef"][i]
        if category == "orgName":
            if ref != "N/A":
                persNameElement = CMIF.new_tag("orgName", attrs={"ref":ref})
            else:
                persNameElement = CMIF.new_tag("orgName")
        else:
            if ref != "N/A":
                persNameElement = CMIF.new_tag("persName", attrs={"ref":ref})
            else:
                persNameElement = CMIF.new_tag("persName")
        i+=1
        persNameElement.string = str(each)
        correspActionElement.append(persNameElement)
        
        # Recipient does not have placeName augmentation as this data does not exist at the moment.
        # Same goes for date.
    # End recipient encoding
dummyElement = CMIF.find("dummy").decompose() # This will destroy the <dummy/> element.

print("Saving output...")
CMIFstr = str(CMIF)
CMIF = BeautifulSoup(CMIFstr, "xml", preserve_whitespace_tags=["orgName","placeName","bibl","corresp","title","persName","editor","email","publisher","ref","idno","licence"])
with open(pathToOutputCMIF+"CMIF_Output_Default.xml", "w", encoding="utf-8") as outfile:
    outfile.write(CMIF.prettify())
#with open(pathToOutputCMIF+"CMIF_Output_NoSortAttrs.xml", "w", encoding="utf-8") as outfile:
#    outfile.write(CMIF.prettify(formatter=UnsortedAttributes()))
with open(pathToOutputCMIF+"CMIF_Output_Default_X.xml", "w", encoding="utf-8") as outfile:
    outfile.write(str(CMIF))
print(f"OK\nSaved {pathToOutputCMIF}CMIF_Output_Default.xml (attributes in alphabetical order)")#\nSaved {pathToOutputCMIF}CMIF_Output_NoSortAttrs.xml (attributes in logical order)")

print("Checking if there are any empty tags. There should be 1 (one) empty <p/> tag showing up, nothing else.")
i=0
dates = 0
for x in CMIF.findAll(True): # For every tag
    i+=1
    if len(x.contents) == 0: # If there's no content in the tag
        if "date" not in str(x): # Dates are not intended to have any content so skip these
            print(x) # Print any tag that is empty and is not a date
        else:
            dates +=1
iX = 0
for x in CMIF.findAll("correspDesc"):
    iX+=1
    if len(x.contents) == 0: # If there's no content in the tag
        print(x)
places = 0
for x in CMIF.findAll("placeName"):
    places+=1
print(f"Check complete.\n{i} total elements across {iX} documents, of which {dates-1} are dated and {places} have places.")
print(f"Process complete. You may close the script now. Have a nice {dt}.")