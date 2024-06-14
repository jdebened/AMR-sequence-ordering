import os

trainfnames = ['../training/'+fname for fname in os.listdir('../training/')]
devfnames = ['../dev/'+fname for fname in os.listdir('../dev/')]
testfnames = ['../test/' +fname for fname in os.listdir('../test/')]

def read_from_file(fname):
	amr = ''
	amrs = []
	sents = []
	with open(fname) as f:
		lines = f.readlines()
	for line in lines:
		if line[0] == '#':
			if line.startswith("# ::snt"):
				# These are the words, keep them
				sents.append(line[8:])
			# Otherwise, not of interest to us
		elif len(line) < 2:
			# Newline on its own means move to next AMR
			if len(amr) > 0:
				amrs.append(amr)
				amr = ''
		else:
			# Not done yet, strip leading and trailing whitespace
			if len(amr) > 0:
				amr = amr + ' '
			amr = amr + line.strip()
	# Not all of the files end with a newline
	if len(amr) > 0:
		amrs.append(amr)
	return amrs, sents

def read_from_files(fnames):
	all_amrs = []
	all_sents = []
	for f in fnames:
		amrs, sents = read_from_file(f)
		all_amrs = all_amrs + amrs
		all_sents = all_sents + sents
	return all_amrs, all_sents

train_amrs, train_sents = read_from_files(trainfnames)
dev_amrs, dev_sents = read_from_files(devfnames)
test_amrs, test_sents = read_from_files(testfnames)

def write_to_files(amrs, sents, ofname):
	with open(ofname+'.words', 'w') as g:
		for sent in sents:
			g.write(sent)

	with open(ofname+'.amr','w') as h:
		for amr in amrs:
			h.write(amr+'\n')

write_to_files(train_amrs, train_sents, 'train')
write_to_files(dev_amrs, dev_sents, 'dev')
write_to_files(test_amrs, test_sents, 'test')

