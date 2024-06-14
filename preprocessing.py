import re
import sys, getopt
from sacremoses import MosesTokenizer


opts, args = getopt.getopt(sys.argv[1:],'wcashtq')
if len(args) < 1:
	print("Usage is: python script.py -[options] baseFileName")
	exit(0)



sent_fname = args[0]+'.words'
amr_fname = args[0]+'.amr'
sent_ofname = 'pre_'+sent_fname
amr_ofname = 'pre_'+amr_fname


wiki = False
concepts = False
anonymize = False
tokenize = False
quotes = False
senses = False
for opt, val in opts:
	if 'w' in opt: 
		wiki=True
		sent_ofname = 'nowiki_'+sent_ofname
		amr_ofname = 'nowiki_'+amr_ofname
	elif 'c' in opt: 
		concepts=True
		sent_ofname = 'concepts_'+sent_ofname
		amr_ofname = 'concepts_'+amr_ofname
	elif 'a' in opt: 
		anonymize=True
		sent_ofname = 'anon_'+sent_ofname
		amr_ofname = 'anon_'+amr_ofname
	elif 't' in opt: 
		tokenize=True
		mt = MosesTokenizer(lang='en')
		sent_ofname = 'tokenized_'+sent_ofname
		amr_ofname = 'tokenized_'+amr_ofname
	elif 'q' in opt:
		quotes=True
		sent_ofname = 'quotes_'+sent_ofname
		amr_ofname = 'quotes_'+amr_ofname
	elif 's' in opt:
		senses=True
		sent_ofname = 'nosenses_'+sent_ofname
		amr_ofname = 'nosenses_'+amr_ofname
	elif 'h' in opt:
		print("Valid options are:")
		print("\t-w\tremove wiki edges")
		print("\t-c\textract concepts")
		print("\t-s\tremove sense information")
		print("\t-a\tanonymize names")
		print("\t-q\tremove quotation marks from AMR")
		print("\t-t\ttokenize (Moses)")
		exit(0)



def remove_wiki(amr):
	return re.sub(' :wiki \S*','', amr)


def anonymize_names(sent, amr):
	# check for name edges and anonymize
	if ':name' in amr:
		varnames = [re.sub('^\(*', '', x) for x in amr.split() if x.startswith('(')]
		anon_vars = {}
		used_vars = []
		# anonymize
		split_amr = amr.split(' :name ')
		pos = 1
		not_processed = []
		while pos < len(split_amr):
			start = split_amr[pos-1]
			end = split_amr[pos]
			labelpos = start.rfind(' ')+1
			if end[0] != '(':
				# Check for variable
				varspot = end.find(')')
				varspot2 = end.find(' ')
				if varspot < 0 or (varspot2 > -1 and varspot2 < varspot):
					varspot = varspot2
				amrvar = end[:varspot]
				if amrvar in varnames:
					if amrvar not in anon_vars:
						# Do not know what to do yet, maybe variable comes later
						not_processed.append(pos)
						pos += 1
						continue
					split_amr[pos-1] = start[:labelpos] + anon_vars[amrvar][0]
					split_amr[pos] = end[varspot:] # remove variable
					pos += 1
					continue
			# Not a variable, process as usual
			amrvar = end[1:end.find(' ')]
			label = start[labelpos:]
			i = 0
			while label+str(i) in used_vars: i+=1
			label = label + str(i)
			used_vars.append(label)
			split_amr[pos-1] = start[:labelpos] + label
			# Now find what the name is
			if end[0] != '(':
				print("Issue with line: ", sent, '\n', amr)
				exit(0)
			name = ''
			spot = 1
			endsplit = end.split()
			part = endsplit[spot]
			while(part[-1] != ')'):
				if (part[0] == '/') or (part == 'name'):
					spot += 1
					part = endsplit[spot]
				elif part[0] == ':':
					# edge
					if part.startswith(':op'):
						# next is part of the name
						namepart = endsplit[spot+1]
						if namepart[0] == '"':
							namepart = namepart[1:]
							namepart = namepart[:namepart.find('"')]
							if len(name) > 0: 
								name = name + ' ' + namepart
							else:
								name = namepart
							if endsplit[spot+1][-1] == ')':
								spot += 1
								endsplit[spot] = endsplit[spot][len(namepart)+3:]
								break
							spot += 2
							part = endsplit[spot]
						else:
							# things like numbers do not have ""
							if namepart[-1] == ')':
								namepart = namepart[:namepart.find(')')]
								if len(name) > 0: 
									name = name + ' ' + namepart
								else:
									name = namepart
								spot += 1
								endsplit[spot] = endsplit[spot][len(namepart)+1:]
								break
							if len(name) > 0: 
								name = name + ' ' + namepart
							else:
								name = namepart
							spot += 2
							part = endsplit[spot]
					else:
						exit(1)
				else:
					exit(1)
			anon_vars[amrvar] = (label, name)
			split_amr[pos] = ' '.join(endsplit[spot:])
			pos += 1
		# Now handle any with variables that had not been seen yet
		for pos in not_processed:
			start = split_amr[pos-1]
			end = split_amr[pos]
			labelpos = start.rfind(' ')+1
			if end[0] != '(':
				# Check for variable
				varspot = end.find(')')
				varspot2 = end.find(' ')
				if varspot < 0 or (varspot2 > -1 and varspot2 < varspot):
					varspot = varspot2
				amrvar = end[:varspot]
				if amrvar in varnames:
					if amrvar not in anon_vars:
						# Do not know what to do yet, maybe variable comes later
						print("still not known")
						exit(1)
					split_amr[pos-1] = start[:labelpos] + anon_vars[amrvar][0]
					split_amr[pos] = end[varspot+1:] # remove variable and )
					pos += 1
					continue
				else:
					print("not in varnames??")
					exit(1)
			else:
				print("how did we get here?")
				exit(1)
		amr = ''.join(split_amr)
		# Now handle making same change(s) in sentence
		# We need to be careful with the replacement order
		# "Basic Laws of Macao" should replace before "Macao" for example
		ordered = []
		pairs = list(anon_vars.values())
		for pair in pairs:
			for spot, entry in enumerate(ordered):
				if entry[1] in pair[1]:
					ordered.insert(spot,pair)
					break
			if pair not in ordered:
				ordered.append(pair)
		for label, name in ordered:
			# I add space to the start to capture sentences that begin with it
			orig_sent = sent
			sent = re.sub(' '+name+' ', ' '+label+' ',' '+sent+' ')[1:-1]
			sent = re.sub(' '+name+"'", ' '+label+"'",' '+sent+' ')[1:-1]
			sent = re.sub(' '+name+'\.', ' '+label+'.',' '+sent+' ')[1:-1]
			sent = re.sub(' '+name+'\?', ' '+label+'?',' '+sent+' ')[1:-1]
			sent = re.sub(' '+name+';', ' '+label+';',' '+sent+' ')[1:-1]
			sent = re.sub(' '+name+'!', ' '+label+'!',' '+sent+' ')[1:-1]
			sent = re.sub(' '+name+',', ' '+label+',',' '+sent+' ')[1:-1]
			if sent==orig_sent:
				print("no replacement made for "+name+' in:\n'+sent)
	return sent, amr


def remove_senses(amr):
	'''Given an input AMR, remove the sense tags.
	For example, begin-01 becomes begin'''
	amr = re.sub('-\d\d ',' ',amr)
	return re.sub('-\d\d\)',')',amr)


def extract_concepts(line):
	splitline = line.split()
	concepts = []
	concept = False
	varnames = [re.sub('^\(*', '', x) for x in splitline if x.startswith('(')]
	for part in splitline:
		if part=='/': 
			concept = True
		elif concept:
			concepts.append(re.sub('\)*$','',part))
			concept = False
		elif part[0] not in ':(':
			cur = re.sub('\)*$','',part)
			if cur not in varnames:
				concepts.append(cur)
	return ' '.join(concepts)
	# Previous method, did not capture (i / i) properly
	varnames = [re.sub('^\(*', '', x) for x in splitline if x.startswith('(')]
	concepts = [re.sub('\)*$', '', x) for x in splitline if not x.startswith(('(',':','/'))]
	no_vars = [x for x in concepts if x not in varnames]
	outline = ' '.join(no_vars)
	return outline


def remove_quotes(amr):
	return re.sub('"','',amr)

def tokenize(line):
	return mt.tokenize(line,return_str=True)


errs = []
with open(sent_fname) as sentin:
	with open(amr_fname) as amrin:
		with open(sent_ofname,'w') as sentout:
			with open(amr_ofname,'w') as amrout:
				for sent, amr in zip(sentin,amrin):
					if wiki: # check command line option
						amr = remove_wiki(amr)
					# Remove newline character
					sent = sent[:-1]
					if anonymize: # check command line option
						sent, amr = anonymize_names(sent, amr)
					if senses: # check command line option
						amr = remove_senses(amr)
					if concepts: # check command line option
						amr = extract_concepts(amr)
					if quotes: # check command line option
						amr = remove_quotes(amr)
					if tokenize: # check command line option
						sent = tokenize(sent)
						amr = tokenize(amr)
					sentout.write(sent+'\n')
					amrout.write(amr) 
					if amr[-1] != '\n':
						amrout.write('\n')
