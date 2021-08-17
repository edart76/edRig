

params = {
	# "index" : 5,
	# "ADS" : 8,#If the star is in Aitken's Double Star Catalog (ADS), this parameter is the designation in that catalog.""",
	# "ADS_Comp" : 8,#	The letter identification in the ADS.
	# "Alt_Name": 15, #The alternative name for stars in the Bright Star Catalog. For those stars which have this information, this is usually the Flamsteed and/or Bayer constellation-based name for the star, e.g., 54Alp Peg, where 54 is the Flamsteed number and Alp (for Alpha) is the Bayer Greek letter.""",
	# "BII": 20,#The galactic longitude of the object.
	# "BV_Color":25,#	The B-V magnitude and colors on the UBV system.
	# "BV_Uncert":26,#	If the magnitude or colors are uncertain, this is set to ':'; if the value is questionable, the uncertainty flag is set to '?'.
	# "CDec":32,#	The Declination of the object, in sexagesimal format.
	# "CDec_1950":42,#Declination, Sexagesimal in 1950 coordinates
	"Class",#Browse classification type. The classification is based on the 'Spect_Type' parameter, if one is available.
	"CRA",#The Right Ascension of the object, in sexagesimal format.
	"CRA_1950",#The Right Ascension of the object, in sexagesimal format and B1950 coordinates.
	"Dec",#The Declination of the object.
	"Dec_1900", #The Declination of the object, in B1900 coordinates.
	"Dec_1950", #The Declination of the object, in B1950 coordinates
	"DM_Cat",#The Durchmeusterung catalog ID.
	"DM_Num",#The Durchmeusterung number.
	"FK5", #This is the number of the object in the Fifth Fundamental Catalogue, if the star is included there.
	"GLat",#The original galactic latitude coordinates from the original catalog.
	"GLon",#The original galactic longitude coordinates from the original catalog.
	"HD",#This is the Henry Draper Catalogue number.
	"HR",#This is the Harvard Revised BS Catalogue number.
	"IR_Flag",#This is the infrared source flag. This parameter will have a value of 'I' if the star is a known infrared source.
	"LII",#The galactic latitude of the object.
	"M_Cnt",#The total number of components assigned to a multiple system.
	"M_ID",#The identification of the components.
	"M_Mdiff",#The magnitude difference between two components of a double, or between the two brightest components of a multiple system.
	"M_Sep",#The separation of two components of a double, or between the two brightest components of a multiple system.
	"Multiple",#'Multiple' is coded as follows when the star is a known double or multiple: 'W' = Worley (1978) update of the IDS, 'D' = Duplicity discovered by occultation, or 'S' = Duplicity discovered by speckle interferometry.
	"Name",#The standard name for the star, using the HR prefix. Note that stars in this catalog are also sometimes referred to using the prefix 'BS'.
	"Note",##An asterisk '*' indicates a note about the star can be found in the remarks.
	"Par_Code",#This flag determines the type of parallax; a 'D' indicates that the parallax is dynamical. Otherwise, the parallax is trigonometric.
	"Parallax",#This is the parallax, in seconds of arc. See the 'Par_Code' field to determine whether the parallax is dynamical or trigonometric.
	"PMDec",#The annual Declination proper motion in seconds of arc for the equinox J2000.0 in the FK5 system.
	"PMRA",#The annual Right Ascension proper motion in seconds of arc for the equinox J2000.0 in the FK5 system.
	"RA",#The Right Ascension of the object.
	"RA_1900",#The Right Ascension of the object, in B1900 coordinates.
	"RA_1950",#The Right Ascension of the object, in B1950 coordinates
	"RadVel",#The heliocentric radial velocity in km/s.
	"RadVel_Comm",#Comments on the radial velocity as follows: 'V' or 'V?' = variable or suspected variable radial velocity; 'SB', 'SB1', or 'SB2' = spectroscopic binaries, single or double lined spectra; 'O' = orbital data available.
	"RI_Code",#A star on the RI system.
	"RI_Color",#This is the R-I color of the star on the RI system. These codes are as follows: blank for the Johnson system, 'E' for Kron system colors measured mainly by Eggen, and 'C' for Cape (Cousins) system colors. Code 'D' has not been documented. Uncertainty ':' or questionable '?' are also indicated in this field.
	"RotVel",#Limiting character: '<' for "less than", '=<' for "less than or equal to", and '>' for "greater than."
	"RotVel_Comm",#The projected rotational velocity (v sin i).
	"RotVel_Uncert",#A colon ':' in indicates an uncertain rotational velocity.
	"SAO",#This is the Smithsonian Astrophysical Observatory Star Catalog number, if the object is listed in that catalog.
	"Spect_Code",#Spectral type code. The codes 'e', 'v', and 't' are not documented.
	"Spect_Type",#Spectral type on the standard Morgan-Keenan system and code.
	"UB_Color",#The U-B magnitude and colors on the UBV system.
	"UB_Uncert",#If the U-B color is uncertain, this is set to ':'; if the value is questionable, the uncertainty flag is set to '?'.
	"Var_ID",#This is the variable star designation from the General Catalogue of Variable Stars or one of its Supplements, or from the Catalogue of Suspected Variable Stars, or simply the designation 'var'.
	"Vmag",#Photographic magnitude.
	"Vmag_Code",#The photographic magnitude may also be reduced to the UBV system from the Harvard Revised Photometry of 1908 (Vmag code = 'R'), or it may also be the original HR magnitude (Vmag code = 'H').
	"Vmag_Uncert",#If the magnitude is uncertain, this is set to ':'; if the values is questionable, the uncertainty flag is set to '?'.
}

import pprint
from pathlib import PurePath
from edRig.tool.atmosphere import constant

"""data is provided in raw string, with entries justified to the same character
this is a bloody advent of code problem
and like advent of code, brute forcing is usually not a bad idea
"""
import re, json


def fetch_bright_star_list(lines):
	"""
	Read the Yale Bright Star Catalogue from disk, and return it as a list of stars.
	:return:
		Dictionary
	"""
	# Astronomical unit, in metres
	AU = 1.49598e11

	# Light year, in metres
	LYR = 9.4605284e15

	# Build a dictionary of stars, indexed by HD number
	stars = {}

	# Convert three-letter abbreviations of Greek letters into UTF-8
	greek_alphabet = {'Alp': '\u03b1', 'Bet': '\u03b2', 'Gam': '\u03b3', 'Del': '\u03b4', 'Eps': '\u03b5',
					  'Zet': '\u03b6', 'Eta': '\u03b7', 'The': '\u03b8', 'Iot': '\u03b9', 'Kap': '\u03ba',
					  'Lam': '\u03bb', 'Mu': '\u03bc', 'Nu': '\u03bd', 'Xi': '\u03be', 'Omi': '\u03bf',
					  'Pi': '\u03c0', 'Rho': '\u03c1', 'Sig': '\u03c3', 'Tau': '\u03c4', 'Ups': '\u03c5',
					  'Phi': '\u03c6', 'Chi': '\u03c7', 'Psi': '\u03c8', 'Ome': '\u03c9'}

	# Superscript numbers which we may place after Greek letters to form the Flamsteed designations of stars
	star_suffices = {'1': '\u00B9', '2': '\u00B2', '3': '\u00B3'}

	# Look up the common names of bright stars
	star_names = {}
	# for line in open("raw_data/bright_star_names.dat", "rt"):
	#     # Ignore blank lines and comment lines
	#     if (len(line) < 5) or (line[0] == '#'):
	#         continue
	#     # Catalog is indexed by the HR number of each star in the first column
	#     bs_num = int(line[0:4])
	#
	#     # The second column is the name of the star, with underscores in the place of spaces
	#     name = line[5:]
	#     star_names[bs_num] = re.sub(' ', '_', name.strip())

	# Loop through the Yale Bright Star Catalog, line by line
	bs_num = 0
	# for line in open("raw_data/bright_star_catalog.dat", "rt"):
	for line in lines:
		# Ignore blank lines and comment lines
		if (len(line) < 100) or (line[0] == '#'):
			continue

		starData = {}

		# Counter used to calculate the bright star number -- i.e. the HR number -- of each star
		bs_num += 1
		try:
			# Read the Henry Draper (i.e. HD) number for this star
			hd = int(line[25:31])

			# Read the right ascension of this star (J2000)
			ra_hrs = float(line[75:77])
			ra_min = float(line[77:79])
			ra_sec = float(line[79:82])

			# Read the declination of this star (J2000)
			dec_neg = (line[83] == '-')
			dec_deg = float(line[84:86])
			dec_min = float(line[86:88])
			dec_sec = float(line[88:90])

			# Read the V magnitude of this star
			mag = float(line[102:107])
		except ValueError:
			continue

		# Look up the Bayer number of this star, if one exists
		star_num = -1
		try:
			star_num = int(line[4:7])
		except ValueError:
			pass

		# Render a unicode string containing the name, Flamsteed designation, and Bayer designation for this star
		name_bayer = name_bayer_full = name_english = name_flamsteed_full = "-"

		# Look up the Greek letter (Flamsteed designation) of this star
		greek = line[7:10].strip()

		# Look up the abbreviation of the constellation this star is in
		const = line[11:14].strip()

		# Some stars have a suffix after the Flamsteed designation, e.g. alpha-1, alpha-2, etc.
		greek_letter_suffix = line[10]
		if greek in greek_alphabet:
			name_bayer = greek_alphabet[greek]
			if greek_letter_suffix in star_suffices:
				name_bayer += star_suffices[greek_letter_suffix]
			name_bayer_full = '{}-{}'.format(name_bayer, const)
		if star_num > 0:
			name_flamsteed_full = '{}-{}'.format(star_num, const)

		# See if this is a star with a name
		if bs_num in star_names:
			name_english = star_names[bs_num]

		# Turn RA and Dec from sexagesimal units into decimal
		ra = (ra_hrs + ra_min / 60 + ra_sec / 3600) / 24 * 360
		dec = (dec_deg + dec_min / 60 + dec_sec / 3600)
		if dec_neg:
			dec = -dec

		# Build a dictionary is stars, indexed by HD number
		# stars[hd] = [ra, dec, mag, name_bayer, name_bayer_full, name_english, name_flamsteed_full]
		stars[hd] = {
			"rightAscension" : ra,
			"declination" : dec,
			"magnitude" : mag,
			#"nameBayer" : name_bayer,
			# "nameBayerFull" : name_bayer_full,
			# "nameEnglish" : name_english,
			# "nameFlamsteed" : name_flamsteed_full
		}

	hd_numbers = list(stars.keys())
	hd_numbers.sort()

	return {
		'stars': stars,
		'hd_numbers': hd_numbers
	}

print(len(params))
def getSpaceBreaks(lines):
	"""looking for 53 individual fields
	find the end index of each field"""

	breaks = set()
	leadIndices = set()
	maxIndex = max(len(i) for i in lines)
	allSpaceIndices = {i for i in range(maxIndex)}
	allCharIndices = set(allSpaceIndices)
	for line in lines:

		# fill line to max index
		line = line + " " * (maxIndex - len(line))

		# find all break indices of lines
		# first indices of all space blocks
		spaceLeadIndices = []
		prevSpace = False # was previous char space
		spaceIndices = []
		charIndices = set()
		for i in range(len(line)):
			if line[i] == " ": # is space
				spaceIndices.append(i)
				if prevSpace:
					continue
				else:
					spaceLeadIndices.append(i)
					prevSpace = True
			else:
				prevSpace = False
				charIndices.add(i)

		spaceLeadIndices = set(spaceLeadIndices)
		leadIndices.update(spaceLeadIndices)

		spaceIndices = set(spaceIndices)
		allSpaceIndices.intersection_update(spaceIndices)

		allCharIndices.intersection_update(charIndices)
		#allCharIndices.difference_update(spaceIndices)


	print("breakIndices", allSpaceIndices)
	print("charIndices", allCharIndices)

	pass

def main():
	"""format raw catalog to useful data entries"""
	rawPath = PurePath(constant.rootDir, constant.raw)
	outPath = PurePath(constant.rootDir, constant.formatTarget)

	lines = open(rawPath).readlines()
	print(len(lines))

	# block = open(rawPath).read()
	# lines = block.split("\n")

	#lines = lines[:10]

	results = fetch_bright_star_list(lines)["stars"]
	#pprint.pprint(results["stars"])

	"""tuple raw buffer has entries
	[(rightAscension, declination, magnitude)]
	"""
	flat = [None] * len(results) * 3
	for i, result in enumerate(results.values()):
		flat[3*i] = result["rightAscension"]
		flat[3*i + 1] = result["declination"]
		flat[3*i + 2] = result["magnitude"]

	json.dump(flat, open(outPath, "w"))
	#
	# final = str(flat)
	#
	# open(outPath, "w").write(final)



if __name__ == '__main__':
	main()