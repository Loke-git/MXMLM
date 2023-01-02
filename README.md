# MunchXMLMuncher 2.0.3
Developed by research assistant Loke Sjølie for the University of Oslo
## Changelog
### Version 2 release
1. Cleaned up the script and converted it to regular .py
2. Enabled automatic installation of dependencies
3. CMIF correspAction element is now created with persName/orgName where appropriate *if* the distinction is visible in the source data.
4. Enabled ref attribute for entities that have this value. Edvard Munch has a custom ref attribute.
#### 2.0.1
1. Fixed an error that would throw an exception if script was run without correspondence.xml
#### 2.0.2
1. Updated prepackaged correspondence.xml and register_tei.xml files
2. Updated prepackaged config.ini file
3. Enabled person and institution refID linking to eMunch where applicable. Entities without an ID are left with a persName element without attributes.
#### 2.0.2a
1. Edvard Munch is now given his VIAF ID instead of his Wikidata ID.
2. Updated prepackaged output files
#### 2.0.3
1. Script now outputs to a folder called "output" with subfolders CMIF, datasets
2. Minor miscellaneous cleanup (mostly non-used code, old comments)
#### 2.0.4 (current)
1. Source attribute is now prefixed with *#*
2. Second pass to remove newlines from prettify
3. Various bugfixes for running the script without xml-filer

### Version 2 beta
1. Extreme overall performance increase
2. New and more accurate method of constructing CMIF file.
3. Fixed the dummy and empty elements bugs. Note: the "bug" present in MM_K0279's date is due to erroneous data entry.


### Version 2 alpha
1. Significant performance and completeness increase in fetching placenames
2. Significantly increased number of dates included from the chronology, **with some caveats**: the chronology file now requires mostly-correct document/object ID formatting. See optional files - chronology for details.
3. Combined Preprocessor and Core scripts for ease of use
4. Integrated place and date augmentation into JSON data creation for correspondence and register_tei

## Introduction
This script takes 1-2 files in eMunch's TEI/XML format and converts them to a complete CMIF/TEIXML file. The script is heavily customized to the project's specifications, and is incredibly unlikely to produce anything worthwhile with files that do not match their exact XML specifications.

The script targets documents that have been tagged with **"brev"** or **"letter"** (excluding, as a rule, drafts), and extracts from these:
1. Document ID, which is extrapolated to form an eMunch URL
2. Document Author(s), names and IDs
3. Document Authored Date, which is converted to YYYY-MM-DD (or YYYY-MM, or YYYY) or a range that can be from or from-to or to.
4. Document Recipient(s), names and IDs

... and then places these in a hierarchy: <CorrespDesc(DocumentID)><CorrespAction*Author*(s)><*Date*/><*/Author*><CorrespAction*Recipient*(s)/>. No date is available for the recipient at this time, though CMIF will accept it if you do locate some.

Optional files enable the script to get updated dates from a chronology file and/or placename augmentation. See section *Optional files* below for in-depth explanation.

### MXMLM2
MXMLM has three parts: the Preprocessor, Core and CMIF Production scripts. All these work together to create a tailored CMIF file. From version 2 onwards, MXMLM is once again a single, integrated script.

The Preprocessor script scrapes, cleans and transforms data from the optional files to prepare them for use in the core script. See section *Optional files* below.

The Core script scrapes data from the register_tei.xml and/or correspondence.xml files. Please note that these files MUST be named properly for the script to function. The script produces an updated JSON data file for each that is ready to be converted into CMIF. If the script finds the Preprocessor's output (in the same folder), it'll create an additional data set with any modifications from preprocessing integrated.

The Production script takes the output of Preprocessor and Core and creates a CMIF-compliant XML file.

## Required variables and metadata
There is a text file by the name config.ini alongside the script. Before running the script, you **must** open this file **in NOTEPAD** (or an appropriate IDE) and do the following:
1. Change the cmifUID to represent this run if applicable (see CMIF documentation for explanation)
2. Change the editorName and editorMail variables - this is you and your e-mail
3. Change the publicationStatementFull variable. This variable should contain a "Full bibliographical statement of the scholarly edition or repository where this file points to"
4. Change publisherURL, publisherName, cmifURL, cmifTitle, typeOfBibl as required

The script currently supports a **single** publisher and a **single** editor. Additional publishers/editors must be edited into the CMIF file afterwards, if applicable.

## Required files
To run this script, you will **require** the following in a folder:

A version of register_tei.xml and/or a version of correspondence.xml and the MXMLM2 script file.

You'll also need Python - it's been tested with a normal Anaconda install and works fine. I **recommend** using Windows. The script has been tested on Windows. I do not guarantee that it will work on any other operating system.

### Optional files
#### Chronology
MXMLM Preprocessor searches for and will use a file named Kronologi_Munchs_brev with the .xlsx filetype if it exists in the same folder as the script. As long as the file contains the exact phrase Kronologi_Munchs_brev and is .xlsx, it'll be found (example: Kronologi_Munchs_brev_20220831.xlsx and Kronologi_Munchs_brev_foo_bar_2020.xlsx WILL be found, while Kronologi_brev.xlsx will NOT be found). If there are multiple files matching the criteria, the last modified file will be used (possibly Windows-dependent).

If a chronology file is found, the script will index all letters included and replace the dates found in the register/correspondence file with the dates found in the chronology file if such a replacement is possible.

##### Info: Naming conventions
**IMPORTANT**: when using the chronology file, ensure that ALL object IDs are correct and compliant. This means that all object IDs MUST follow one of two formats. These are the 6-character PN objects (PN1234), and the 11-character No objects (No-MM_X1234). You are permitted to leave or remove leading zeroes following the full prefix (PN or No-MM_X). Regular/placement names in the ID field ("MM K 1234") will not be registered.

In cases where the object ID is too short (PN50), zeroes (0) are added immediately after the prefix until it complies (PN0050). In cases where the object ID is too long (No-MM_X012345678, kap 1-2) and there is a comma, **everything** to the right of the comma is expunged. If the string is too long *and* the string has a No-prefix, characters matching 0 are removed from immediately after the prefix until it complies (this is common). Once the prefix is not followed by 0 and the string is more than 11 characters long, characters are removed from the end of the string until it complies (resulting in No-MM_X1234). The string is then checked for compliance: it must be 6 or 11 characters long, and the last 4 characters must be numeric.

##### Info: Date conventions
The script instantly accepts datetime-formatted dates. If the script locates "uncertain" dates expressed by a ? character, the date is trimmed incrementally (D?.MM.YYYY becomes MM.YYYY, ??.YYYY becomes YYYY). If a date contains the character -, it is assigned as a range date and is split in from and to dates. The script will correct from-to dates where the to date is more specific than the from date, as in 11-12.2000 -> 11.2000-12.2000. *Note that the script will alert but **not** correct date ranges where the from date is more specific, as in 11.2000-12.* Date ranges are stored in the format FROM%TO in the datasets. If the date does not contain the character -, it is formatted as a single-instance date (YYYY.MM.DD).

All dates are fetched whole, including the day and/or the month wherever possible: the minimum requirement is a 4-digit year. If a complete 4-digit long year is not found, the entire date is expunged. Be advised that the script does **not** validate whether the date is between 1860-1950, nor if it is a valid day/month (29.02, 31.11). Additionally, the script does not check for overfeeding (placing full date in the year element, then adding month and day to the month and day elements) at this time. Thus: if the source data's year element contains a full date ("<year when="2000-10-10"/>) the script will output anomalous dates for this document.

#### Placenames
The script searches for a folder named "xml-filer" located in the same folder as itself AND a spreadsheet named "ID_sted-verdier.xlsx". You **must** provide the spreadsheet if you wish to use this functionality, as well as *n* XML files in xml-filer. If found, the script will scan every XML file in that folder (recursive; subfolders are allowed, as long as the top-level folder is named xml-filer) expecting to see a series of letter files. 

The script will search for a dateline element, which may or may not have a placename. The script only looks for a sender because the dateline element is intended to only ever represent the sender's address and date. If the dateline element has a placename element (recursively, again), the script will assume that the first @key attribute of this placename element is the address ID of the sender.

If the script is able to locate a placename in the expected format (address, dateline), the value of the @key attribute will be used to compare with ID_sted-verdier.xlsx. The address/place string associated with the @key value is harvested and used as an address element. Otherwise, no place element is appended.

## Instructions for use
1. Place the MXMLM2 script in a folder that contains **at least one** required file (see header REQUIRED FILES).
2. If desired, place optional files and/or folders beside the script (see subheader OPTIONAL FILES). Remember that some options have dependencies. Ensure that the chronology file has correctly formatted object/document IDs and that the folder structure is correct (everything in one folder except the individual letter xml files (as in "No-MM_N0002.xml") in a folder named "xml-filer").
3. Run MXMLM2 via python (cd to directory and run: python MXMLM2.py). The script SHOULD take care of installing required packages on its own.
4. The resulting CMIF files and JSON/CSV data sets are placed in the same folder as the script upon completion.

## Known bugs and issues
The script does not fetch external UIDs. This would entail using the VIAF API to get IDs on everyone - which is fine in itself. But you'd have to make sure that it's the *correct* IDs, which can pose a considerable challenge to do automatically, and time-consuming to do manually.

The script does not fetch a UID for placenames at time of writing. The CMIF documentation suggests Geonames as an acceptable source of placename UIDs.

The script does not evaluate whether a given date is "certain" or not beyond applying a date range or an "exact" date. It assumes that the dates provided are certain enough (when they form valid dates).

If you run into any other errors or issues, please let me know.
