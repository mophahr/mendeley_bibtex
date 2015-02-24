#! /usr/bin/python2
# -*- coding: utf-8 -*-
'''
   Copyright 2015 M. Schönwetter.
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
from __future__ import print_function
from __future__ import division
import pickle
from os.path import isfile
from sys import exit
import re
from pprint import PrettyPrinter
pp=PrettyPrinter()
import sys

''' This script takes a Mendeley-generated bibfile, changes the citation key and removes al unused fields from the bibtex entry.'''
if sys.argv[1:]==[]:
   verbose=False
elif sys.argv[1:]==["-v"]:
   verbose=True
else:
   print("unknown option")
   exit(1)

print("Fixing Mendeley's output...")

bibfile="./bibl_mendeley.bib"
fixed_bibfile="bibl.bib"
journals_dictionary_pickle="./journals_dictionary.pickle"

if not isfile(bibfile):
   print("The Mendeley-bibliography file "+bibfile+" doesn't exist. Provide it or change the filename in this script.")
   exit(1)
with open(bibfile) as f:
   raw_file_content=f.read()


if not isfile(journals_dictionary_pickle):
   print("No journals dictionary found at "+journals_dictionary_pickle+". Provide it or create a new one using \"$ add_to_dictionary.py\".")
   exit(1)
with open(journals_dictionary_pickle, 'r') as journals_dictionary_file:
   journals_dictionary=pickle.load(journals_dictionary_file)

fields_to_keep_dict={  "article" : frozenset(["author", "doi", "journal", "year", "volume", "number", "pages", "title"]),\
                  "book":     frozenset(["author", "title", "year", "doi", "publisher"]) }

entries=raw_file_content.split("@")[1:]

fixed_entries={}
for entry in entries:
   if verbose:
      print("\n\nMendeley entry:")
      print("@"+entry)
   fields=entry.split(",\n")
   #remove extra stuff from last line:
   fields[-1]=fields[-1].split("\n")[0]

   #the first entry noe loogs like 
   #  article{Einstein1910
   #so we can get the publication type and the Mendeley-citation-key
   entry_type,mendeley_citation_key=fields[0].split("{")[0],fields[0].split("{")[1]
   citation_key_name=re.findall(r'[a-zA-Z]+', mendeley_citation_key)[0]
   
   fields=fields[1:]
   #now we make a directory from the fields provided keeping only entries from fields_to_keep
   fields_to_keep=fields_to_keep_dict[entry_type]
   entry_props={field.split(" = ")[0]:field.split(" = ")[1] for field in fields if {field.split(" = ")[0]}<=fields_to_keep}
   entry_props.update({"type":entry_type})
   
   #check if a minimal abbreviation for the new citation key exists (only for articles):
   if entry_type=="article":
      journal_name=entry_props["journal"][1:-1]
      try:
         shortest=journals_dictionary[journal_name]["shortest"]
      except:
         print("no entry for "+journal_name+" in "+journals_dictionary_pickle+". create one using\
               \n\t$ add_to_dictionary.py \""+journal_name+"\" \"<short name>\" \"<very short name>\"")
         exit(1)
   elif entry_type=="book":
      shortest="Book"

   year=entry_props["year"][1:-1]
   
   new_citation_key=citation_key_name+":"+shortest+year

   entry_props={new_citation_key:entry_props}
   fixed_entries.update(entry_props)
   if verbose:
      print("fixed Mendeley entry:")
      pp.pprint(entry_props)

sorted_citation_keys=sorted(fixed_entries)
with open(fixed_bibfile,"w") as outfile:
   outfile.seek(0)
   outfile.truncate()
   for key in sorted_citation_keys:
      entry_type=fixed_entries[key]["type"]
      outfile.write("@"+entry_type+"{"+key)
      for field in fixed_entries[key]:
         if not field=="type":
            outfile.write(",\n"+field+" = "+fixed_entries[key][field])
      outfile.write("\n}\n")


