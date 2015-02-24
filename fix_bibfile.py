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
import pickle
from os.path import isfile
import unicodedata
import re
#from pprint import PrettyPrinter
#pp=PrettyPrinter()
import sys
''' 
This script takes a Mendeley-generated bibfile, changes the citation key and removes al unused fields from the bibtex entry.
Use like:
   $ ./fix_bibfile.py file.bib
'''

if len(sys.argv) < 2:
   sys.exit("No input file defined.\nUsage:\t$ %s file.bib" % sys.argv[0])
arguments = sys.argv[1:]
print(arguments)
verbose = False
for argument in arguments:
   if '.bib' in argument:
      bibfile = argument
   else:
      sys.exit("Sorry, but bibfiles must end with \"bib\".")
       

print("Fixing Mendeley's output...")

fixed_bibfile = bibfile[:-4]+"_fix.bib"
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

#hack to convert unicode accents to LaTeX \' format
#http://tex.stackexchange.com/questions/23410/how-to-convert-characters-to-latex-code
accents = {
   0x0300: '`', 0x0301: "'", 0x0302: '^', 0x0308: '"',
   0x030B: 'H', 0x0303: '~', 0x0327: 'c', 0x0328: 'k',
   0x0304: '=', 0x0331: 'b', 0x0307: '.', 0x0323: 'd',
   0x030A: 'r', 0x0306: 'u', 0x030C: 'v',
}
def uni2tex(text):
   out = ""
   txt = tuple(text)
   i = 0
   while i < len(txt):
      char = text[i]
      code = ord(char)

      # combining marks
      if unicodedata.category(char) in ("Mn", "Mc") and code in accents:
         out += "\\%s{%s}" %(accents[code], txt[i+1])
         i += 1
      # precomposed characters
      elif unicodedata.decomposition(char):
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

class Author:
   list = {}
   
   def __init__(self,key,meta):
      Author.list[key] = self
      self.key = key
      for key, value in meta.iteritems():
         setattr(self, key, value)
      self.abb_name = ' '.join(map(lambda x:x[0]+'.', self.name.split(' ')))
   
   def __repr__(self):
      text = '{[0].surname}, {[0].abb_name}'.format(self)
      print text
      return text

def clean_authors(author_field):
   author_list = author_field.split(' and ')
   authors = []
   for author in authors:
      x,y = author.split(',')
      meta = {'name':x, 'surname':y}
      a = Author(author,meta)
      authors.append(a)
   authors_repr = [author.__repr__() for author in authors]
   text = ' and '.join(authors_repr)
   return text


# class to handle the entries
class Entry:
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
   entry_props = {field.split(" = ")[0]:field.split(" = ")[1].rstrip('}').lstrip('{') for field in fields[1:] if {field.split(" = ")[0]}<=fields_to_keep}
   entry_props['citation_key_name'] = re.findall(r'[a-zA-Z]+', mendeley_citation_key)[0]
   
   # create Entry with the read fields
   e = Entry(entry_type, entry_props, key=None) 

def parse(content):
   entries = content.split("@")[1:]
   fixed_entries={}
   print len(entries)
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
