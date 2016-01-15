#! /usr/bin/python2
# -*- coding: utf-8 -*-
'''
   Copyright 2015,2016 M. Schönwetter & J. M. Moitto.
   
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
import pickle
from os.path import isfile
import unicodedata
import re
from pprint import PrettyPrinter
pp=PrettyPrinter()
import sys
import argparse
''' 
This script takes a Mendeley-generated bibfile, changes the citation key and removes al unused fields from the bibtex entry.
Use like:
   $ ./fix_bibfile.py file.bib
'''

parser = argparse.ArgumentParser(prog="fix_bibfile.py", description='Takes a bibfile created by Mendeley and cleans it up.')

parser.add_argument('bibfile',
		metavar='dirty_file', type=str,
		help='dirty bibfile')
parser.add_argument('-v',
		dest='verbose', action='store_const',
		const=True, default=False,
		help='talk more')
parser.add_argument('--inplace',
		dest='in_place', action='store_const',
		const=True, default=False,
		help='overwrite input file (default: False) !!not yet implemented!!')
parser.add_argument('-o',
		help='clean bibfile (default: <dirty_file>_clean.bib)')
parser.add_argument('-j',
		help='journals pickle (default: ./journals_dictionary.pickle)')

args = parser.parse_args()

bibfile = args.bibfile
in_place = args.in_place
verbose = args.verbose

if verbose:
	print "argumets:", args

fixed_bibfile = args.o
if in_place:
	fixed_bibfile=bibfile
	print "--inplace not implemented."
	sys.exit()
if fixed_bibfile == None:
	fixed_bibfile = bibfile[:-4]+"_clean.bib"

journals_dictionary_pickle = args.j
if journals_dictionary_pickle == None:
	journals_dictionary_pickle = "./journals_dictionary.pickle"

print "dirty bibfile: ", bibfile
print "clean bibfile: ", fixed_bibfile
print "journals dictionary: ", journals_dictionary_pickle

print("Fixing Mendeley's output...")

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

#hack to convert unicode accents to LaTeX \' format
#http://tex.stackexchange.com/questions/23410/how-to-convert-characters-to-latex-code
accents = {
   0x0300: '`', 0x0301: "'", 0x0302: '^', 0x0308: '"',
   0x030B: 'H', 0x0303: '~', 0x0327: 'c', 0x0328: 'k',
   0x0304: '=', 0x0331: 'b', 0x0307: '.', 0x0323: 'd',
   0x030A: 'r', 0x0306: 'u', 0x030C: 'v',
}

#other_replacements = { str("ł") : r"{\L}", str("ł") : r"{\l}" }
other_replacements = { u"\u0141" : "{\L}", u"\u0142" : "{\l}" }
#print other_replacements
def uni2tex(text):
   out = ""
   txt = tuple(text)
   i = 0
   while i < len(txt):
      char = text[i]
      code = ord(char)
      if char in other_replacements.keys():
          out += other_replacements[char]  
      elif unicodedata.category(char) in ("Mn", "Mc") and code in accents:
      # combining marks
         out += "\\%s{%s}" %(accents[code], txt[i+1])
         i += 1
      elif unicodedata.decomposition(char):
      # precomposed characters
         base, acc = unicodedata.decomposition(char).split()
         acc = int(acc, 16)
         base = int(base, 16)
         if acc in accents:
            out += "\\%s{%s}" %(accents[acc], unichr(base))
         else:
            out += char
      else:
         out += char
   
      i += 1
   
   return out

class Entry:
   '''
      class to handle the entries.
      it keeps a dictionary of entries and provides a __repr__ for printing
   '''
   list = {}
   
   def __init__(self,entry_type,fields,key=None):
      self.entry_type = entry_type
      self.fields = fields
      if key is None:
         if self.entry_type=='book':
            shortest = 'book'
         elif self.entry_type=='article':
            journal_name = self.fields['journal']
            try:
               shortest = journals_dictionary[journal_name]["shortest"]
            except:
               print("no entry for "+journal_name+" in "+journals_dictionary_pickle+". create one using\
               \n\t$ add_to_dictionary.py \""+journal_name+"\" \"<short name>\" \"<very short name>\"")
               exit(1)
         self.key = '{0[citation_key_name]}:{1}{0[year]}'.format(self.fields,shortest)
      del self.fields['citation_key_name']
      Entry.list[self.key] = self
      if self.fields['author']:
         self.fields['author'] = uni2tex(self.fields['author'].decode('utf8'))
      if self.fields['title']:
         self.fields['title'] = uni2tex(self.fields['title'].decode('utf8'))
   
   def __repr__(self):
     fields = ',\n'.join(['{}={{{}}}'.format(k,v) for k,v in self.fields.items()])
     text = '@{}{{{},\n{}\n}}'.format(self.entry_type,self.key,fields)
     return text



fields_to_keep_dict={
   "article" : frozenset([
      "author", "doi", "journal", "year", "volume", "number", "pages", "title"
      ]),
   "book" : frozenset([
      "author", "title", "year", "doi", "publisher"
      ])
   }

def read_entry(entry):
   fields=entry.split(",\n")
   #remove extra stuff from last line:
   fields[-1]=fields[-1].split("\n")[0]
   #the first entry now looks like 
   #  article{Einstein1910
   # so we can get the publication type and the Mendeley-citation-key
   entry_type, mendeley_citation_key = fields[0].split("{")
   #now we make a dictionary from the fields provided keeping only entries from fields_to_keep
   fields_to_keep = fields_to_keep_dict[entry_type]
   #the old code in the next line
   #fails for author = {{last name}, first}:
   #entry_props = {field.split(" = ")[0]:field.split(" = ")[1].rstrip('}').lstrip('{') for field in fields[1:] if {field.split(" = ")[0]}<=fields_to_keep}
   #longer version:
   entry_props = {}
   for field in fields[1:]:
      if {field.split(" = ")[0]}<=fields_to_keep:
         key = field.split(" = ")[0]
         val = field.split(" = ")[1]
         while val[0]=="{" and val[-1]=="}":
             val = val[1:-1]
         entry_props.update({key : val})
   entry_props['citation_key_name'] = re.findall(r'[a-zA-Z]+', mendeley_citation_key)[0]
   
   # create Entry with the read fields
   entry = Entry(entry_type, entry_props, key=None) 
   if verbose:
      print("fixed entry:")
      print(str(entry))

def parse(content):
   entries = content.split("@")[1:]
   fixed_entries={}
   for entry in entries:
      if verbose:
         print("\n\nMendeley entry:")
         print("@"+entry)
      read_entry(entry)

parse(raw_file_content)

sorted_citation_keys = sorted(Entry.list.keys())
with open(fixed_bibfile,"w") as outfile:
   for key in sorted(Entry.list.keys()):
      entry = Entry.list[key]
      outfile.write(entry.__repr__()+'\n')
