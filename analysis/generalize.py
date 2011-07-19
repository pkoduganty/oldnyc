#!/usr/bin/python
#
# The goal here is to check whether any single-record geocodes can be extended
# to full categories.
#
# Specifically excluded are:
# o SF Residences
# o SF Streets (and variants)
# o anything in cat-codes

import sys
sys.path += (sys.path[0] + '/..')

import record
import re
from collections import defaultdict

# read in previous generalization responses
# folder -> 'y' or 'n'
responses = {}
for line in file('generalizations.txt').read().split('\n'):
  if not line: continue
  m = re.match(r'(.*):(.*)', line)
  assert m, line
  assert m.group(1) not in responses, line
  responses[m.group(1)] = m.group(2)


rs = record.AllRecords()
id_to_record = {}
for r in rs:
  id_to_record[r.photo_id()] = r

# blacklist existing catcodes
catcodes = [line.split(" : ")[1] for line in file("cat-codes.txt").read().split("\n") if line]
def IsCatCode(r):
  global catcodes
  cat = record.CleanFolder(r.location())
  if not cat: return False
  for geocat in catcodes:
    if cat.startswith(geocat):
      return True
  return False

# load geocodes: (photo_id)<tab>(lat,lon)<tab>loc_type<tab>locatable_str
# photo_id -> [("lat,lon",locatable_str), ...]
id_to_code = {}
lines = file('/tmp/geocodes.txt').read().split('\n')
for line in lines:
  if not line: continue
  parts = line.split("\t")
  photo_id = parts[0]
  latlon = parts[1]
  loc_type = parts[2]
  if loc_type != 'free-streets': continue

  if len(parts) > 3:
    locatable_str = '\t'.join(parts[2:])
  else:
    locatable_str = ''

  if photo_id in id_to_code: continue
  id_to_code[photo_id] = (latlon, locatable_str)

# category -> list of records in category
coded_cats = defaultdict(list)
folder_to_record = defaultdict(list)

for r in rs:
  if not r.location(): continue
  folder = record.CleanFolder(r.location())
  folder_to_record[folder].append(r)

  if r.photo_id() not in id_to_code: continue
  if r.location().startswith("Folder: S.F. Streets-"): continue
  if r.location().startswith('Folder: S.F. Earthquakes-1906-Streets'): continue
  if r.location().startswith('Sheet: S.F. Streets'): continue
  if r.location().startswith('Folder: S.F. Residences'): continue
  if IsCatCode(r): continue

  # now this is a record which has the potential to be generalized.
  latlon, locatable_str = id_to_code[r.photo_id()]
  coded_cats[folder].append((r.photo_id(), latlon, locatable_str))


saved = 0
for folder in coded_cats.keys():
  if len(folder_to_record[folder]) == len(coded_cats[folder]):
    continue

  if folder in responses:
    saved += len(folder_to_record[folder]) - len(coded_cats[folder])
    print '%s (%s)' % (folder, responses[folder])
    continue

  print folder
  print '  Located:'
  located = set()
  for id, latlon, locatable_str in coded_cats[folder]:
    print '    %s (%s)' % (locatable_str, latlon)
    located.add(id)
  print '  Others: %d' % (len(folder_to_record[folder]) - len(coded_cats[folder]))
  dated_rs = [(r.date(), r) for r in folder_to_record[folder]]
  for date, r in sorted(dated_rs):
    c = ' '
    if r.photo_id() in located: c = '*'
    print '   %s%s %15s %s %s' % (c, r.photo_id(),
                                  record.CleanDate(r.date()),
                                  record.CleanTitle(r.title()),
                                  r.preferred_url)
  print ''

  response = raw_input('generalize? (y or n or photo_id): ')
  if response in ['y', 'n', 'yes', 'no'] or '-' in response:
    file('generalizations.txt', 'a').write('%s:%s\n' % (folder, response))
  else:
    print '(Skipping)'

  print ''
  print ''
  print ''

print 'Saved records: %d' % saved
