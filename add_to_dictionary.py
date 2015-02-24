#! /usr/bin/python2
from __future__ import print_function
from __future__ import division
import sys
import pickle
from pprint import PrettyPrinter
pp=PrettyPrinter()
from os.path import isfile

'''This script updates (or creates) the dictionary of journal_abbreviations. It needs 3 strings as an argument.
   Usage:   $ ./add_to_dictionary.py <full name>               <shortest form>   <readable abbreviation>
   Example: $ ./add_to_dictionary.py "Physical Review Letters" "PRL"             "Phys. Rev. Lett."

   If an etry with the same full name already exists it can be overwritten, deleted or ignored, depending on user-input.'''

journals_dictionary_file_location="./journals_dictionary.pickle"

if sys.argv[1:] == []:
   #no arguments provided; display help text and exit.
   print("\nERROR: This script needs 3 strings as an argument. \n\nUsage:\n\t$ ./add_to_dictionary.py <full name> <shortest form> <readable abbreviation>\nExample:\n\t$ ./add_to_dictionary.py \"Physical Review Letters\" \"PRL\" \"Phys. Rev. Lett.\"")
   exit(1)

#get command line argumets and make a dictionary from it.:
journal_name,short,shortest=sys.argv[1:]
new_entry={journal_name:{"short":short, "shortest":shortest}}

#try to load existing dictionary; if the file does not exist, ask if we should create it:
if not isfile(journals_dictionary_file_location):
   answered=False
   while not answered:
      print(journals_dictionary_file_location+" does not exist. create new one?\n\t(y)es (default), or\n\t(n)o?")
      answer=raw_input("([y]/n): ")
      if answer=="" or answer=="y":
         answered=True
         print("creating new dictionary...")
         print("\nupdated dictionary:")
         pp.pprint(new_entry)
         with open(journals_dictionary_file_location,"w") as journals_dictionary_file:
            pickle.dump(new_entry,journals_dictionary_file)
         exit(0)
      if answer=="n":
         answered=True
         exit(1)
else:  
   #it does exist, so we load it.
   with open(journals_dictionary_file_location,"r") as journals_dictionary_file:
      journals_dictionary=pickle.load(journals_dictionary_file)

print("\ncurrent dictionary:")
pp.pprint(journals_dictionary)
if journal_name in journals_dictionary.keys():
   #entry for that journal already exists; ask whatt to do (and repeat until answered=True)
   answered=False
   while not answered:
      print("\nnew entry:")
      pp.pprint(new_entry)
      print("\nThis entry already exists.\n\t(o)verwrite (default), \n\t(r)emove entry, or \n\t(a)bort?")
      answer=raw_input("([o]/r/a): ")
      if answer=="" or answer=="o":
         print("overwriting...")
         answered=True
         journals_dictionary.update(new_entry)
      elif answer=="r":
         print("removing...")
         answered=True
         journals_dictionary={i:journals_dictionary[i] for i in journals_dictionary if i!=journal_name}
      elif answer=="a":
         print("aborting...")
         answered=True
         exit(1)
else:
   #No conflicts with existing entries; simply add new entry
   print("adding entry...")
   journals_dictionary.update(new_entry)

print("\nupdated dictionary:")
pp.pprint(journals_dictionary)

#save updates:
with open(journals_dictionary_file_location,"w") as journals_dictionary_file:
   pickle.dump(journals_dictionary,journals_dictionary_file)


