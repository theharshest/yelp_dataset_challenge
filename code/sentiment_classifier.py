from bs4 import BeautifulSoup
import preprocessing
import numpy as np
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.pipeline import Pipeline
from sklearn.grid_search import GridSearchCV
import pickle

def get_data(filename):
	'''
	Get data from XML file into a numpy array
	Extract and normalize the sentiment score
	'''
	soup = soup = BeautifulSoup(open(filename))

	sentences = soup.find_all('sentence')

	data = np.array([]).reshape(0,2)

	for sentence in sentences:
		positives = len(sentence.aspectcategories(polarity="positive"))
		negatives = len(sentence.aspectcategories(polarity="negative"))
		review = sentence.text.strip()

		score = positives - negatives
		if score > 2:
			score = 2
		elif score < -2:
			score = -2

		row = np.array([review, score])

		data = np.vstack((data, row))

	return data

def build_sentiment_classifier(data):
	'''
	Train and pickle the sentiment classifier
	'''
	X = data[:, 0]
	y = data[:, 1]

	tfidf = TfidfVectorizer(tokenizer=word_tokenize, stop_words='english')
	X_tfidf = 	tfidf.fit_transform(X)

	clf_SVM = Pipeline([('chi2', SelectKBest(chi2)), ('svm', LinearSVC())])

	# Uncomment the section below to enable Grid Search for optimal parameter
	# search
	'''
	params = {
          'chi2__k': [800, 1200, 1600, 2000, 'all'],
          'svm__C': [0.01, 0.5, 1, 10],
          'svm__tol': [1e-2, 1e-3, 1e-4],
          'svm__dual': [True, False]
          }

	gs = GridSearchCV(clf_SVM, params, cv=5, scoring='f1')
	
	gs.fit(X_tfidf, y)
	print gs.best_score_
	print gs.best_estimator_.get_params()
	'''

	clf_SVM = Pipeline([('chi2', SelectKBest(chi2, k='all')), ('svm',
		LinearSVC(C=0.5, tol=1e-3, dual=False))])

	clf_SVM.fit(X_tfidf, y)

	f = open('sentiment_classifier', 'wb')
	pickle.dump(clf_SVM, f)
	f.close

if __name__ == "__main__":
	data = get_data("Restaurants_Train.xml")
	build_sentiment_classifier(data)