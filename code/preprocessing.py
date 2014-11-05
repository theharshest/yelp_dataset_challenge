import replacers

def common_preprocessing(text):
	'''
	Includes common preprocessing tasks on text data -
	lowercasing, term expansion, spelling correction, repeated chars removal
	'''

	# Converting to lowercase
	text = text.lower()

	# Term Expansion, eg. won't -> will not, we've -> we have, etc
	term_expander = replacers.RegexpReplacer()
	text = term_expander.replace(text)

	tokens = text.split()

	# Repeated character removal, eg. loooovvveee -> love
	repeated_char_remover = replacers.RepeatReplacer()
	tokens = [repeated_char_remover.replace(token) for token in tokens]

	# Spelling correction within one edit distance of dictionary word
	spelling_corrector = replacers.SpellingReplacer()
	tokens = [spelling_corrector.replace(token) for token in tokens]

	text = ' '.join(tokens)

	return text

