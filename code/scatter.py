# -*- coding: utf-8 -*-
"""
Generate a scatter plot for the specified attributes.

Arguments:
  jsonfile  - path to the JSON file (input)
  attr1     - name of the first attribute to plot
  attr2     - (optional) name of the second attribute to plot, if omitted then
              the first attribute is plotted against random noise (just to
              provide jitter to spread the data points out)
  omit      - (optional) class label to omit

Created on Thu Dec  4 01:07:50 2014

@author: John Maloney
"""

import jsonutils as ju
import feat_info as fi
import numpy as np
import matplotlib.pyplot as plt
import argparse

def main():
    desc = 'Create a scatter plot using the specified attributes from the JSON objects'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('jsonfile', help='file that holds the data to be plotted')
    parser.add_argument('attr', nargs='+', help='list of attributes to display on scatter plot')
    parser.add_argument('-l', help='the attribute that holds the class label', default=fi.label)
    parser.add_argument('-o', nargs='+', type=int, help='list of class labels to omit from scatter plot')
    
    args = parser.parse_args()
    print args.jsonfile
    print args

    attr1 = args.attr[0]
    if (len(args.attr) > 1):
        attr2 = args.attr[1]
    else:
        attr2 = None
        
    run_script(args.jsonfile, attr1, attr2, args.o)
# end main

def run_script(jsonfile, attr1, attr2=None, omitLabels=None):
    # load json objects
    print 'Loading JSON objects from %s...' % jsonfile
    objects, columns = ju.load_objects(jsonfile)

    # convert to matrix form
    print 'Convert JSON to matrix...'
    X,columns = ju.get_matrix(objects, fi.data_feat_info)

    # get class labels
    y_idx = columns.index(fi.label)
    y = X[:,y_idx]
    if (omitLabels):
        labels = [int(x) for x in np.unique(y) if x not in omitLabels]
    else:
        labels = [int(x) for x in np.unique(y)]

    print labels

    # get the data for attribute 1
    attr1_idx = columns.index(attr1)
    x1 = X[:,attr1_idx] + np.random.uniform(0,0.25,X.shape[0])

    # get the data for attribute 2
    if (attr2 is not None):
        attr2_idx = columns.index(attr2)
        x2 = X[:,attr2_idx] + np.random.uniform(0,0.25,X.shape[0])
    else:
        attr2 = 'random'
        x2 = np.random.uniform(0,1,X.shape[0])

    print 'Plot %s vs %s...' % (attr1,attr2)
    plt.clf()

    # create data series
    series_x1 = []
    series_x2 = []
    for label in labels:
        idx = np.where(y==label)[0]
        print '  class %d: %d' % (label,len(idx))
        series_x1.append(x1[idx])
        series_x2.append(x2[idx])

    colors = ['b', 'g', 'r', 'm', 'k']

    for i in labels:
        plt.scatter(series_x1[i], series_x2[i], c=colors[i], marker='+')

    plt.show()
# end run_script

# run main method when this file is run from command line
if __name__ == "__main__":
    main()