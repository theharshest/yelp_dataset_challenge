from bs4 import BeautifulSoup
import preprocessing
import numpy as np
import json
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer, HashingVectorizer
from sklearn.svm import LinearSVC
from sklearn.feature_selection import SelectKBest, chi2, f_classif
from sklearn.pipeline import Pipeline
from sklearn.grid_search import GridSearchCV
import pickle

def get_data(filename1, filename2):
	'''
	Get data from XML file into a numpy array
	Extract and normalize the sentiment score
	'''
	soup = soup = BeautifulSoup(open(filename1))

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

	X1 = data[:, 0]
	y = np.array(data[:, 1], dtype=np.int32)

	X2 = np.array([])
	business_ids = np.array([])

	test_data = open(filename2)
	for line in test_data:
		line = json.loads(line)
		X2 = np.hstack((X2, np.array(line['text'])))
		business_ids = np.hstack((business_ids, np.array(line['business_id'])))
	test_data.close()	

	X1 = np.hstack((X1, X2))

	return X1, y, business_ids

def build_sentiment_classifier(X, y, bids):
	'''
	Train and pickle the sentiment classifier
	'''
	n_train_samples = y.shape[0]

	tfidf = HashingVectorizer(tokenizer=word_tokenize, stop_words='english', \
		ngram_range=(1, 3), n_features=10000)
	X_tfidf = tfidf.fit_transform(X)#.todense()
	'''
	X1 = X[:n_train_samples]
	X2 = X[n_train_samples:]
	'''
	X1_tfidf = X_tfidf[:n_train_samples, :]
	X2_tfidf = X_tfidf[n_train_samples:, :]

	# Uncomment the section below to enable Grid Search for optimal parameter
	# search

	'''
	clf_SVM = Pipeline([('clf_SVM',	LinearSVC())])

	params = {
          'clf_SVM__C': [0.01, 0.5, 1, 10],
          'clf_SVM__tol': [1e-2, 1e-3, 1e-4],
          'clf_SVM__dual': [True, False]
          }

	gs = GridSearchCV(clf_SVM, params, cv=5, scoring='f1')
	
	gs.fit(X1_tfidf, y)
	print gs.best_score_
	print gs.best_estimator_.get_params()
	'''

	clf_SVM = LinearSVC(C=0.5, tol=1e-2, dual=False)

	clf_SVM.fit(X1_tfidf, y)

	y2 = clf_SVM.predict(X2_tfidf)
	y2 = np.vstack((bids, y2))

	return y2

if __name__ == "__main__":
	filename = sys.argv[1]
	
	X, y, bids = get_data("Restaurants_Train.xml", filename)
	score = build_sentiment_classifier(X, y, bids)

	picklefile = open('score_pickle', 'wb')
	pickle.dump(score, picklefile)
	picklefile.close()
