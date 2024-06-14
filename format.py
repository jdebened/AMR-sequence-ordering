import sys

if len(sys.argv) < 4:
	print("Usage is: python script.py wordsfile amrfile outputfile")
	exit(1)

with open(sys.argv[1]) as f:
	sentences = f.readlines()

print("Read in ",len(sentences), " sentences")

with open(sys.argv[2]) as f:
	amrs = f.readlines()

print("Read in ", len(amrs), " AMRs")

if len(sentences) != len(amrs):
	print("mismatched numbers")
	exit(1)


with open(sys.argv[3],'w') as g:
	for i in range(len(amrs)):
		out = "# ::snt " + sentences[i] + amrs[i] + "\n"
		g.write(out)

