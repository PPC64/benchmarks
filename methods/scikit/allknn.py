'''
  @file allknn.py
  @author Marcus Edel

  All K-Nearest-Neighbors with scikit.
'''

import os
import sys
import inspect

# Import the util path, this method even works if the path contains symlinks to
# modules.
cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(
  os.path.split(inspect.getfile(inspect.currentframe()))[0], "../../util")))
if cmd_subfolder not in sys.path:
  sys.path.insert(0, cmd_subfolder)

from log import *
from timer import *

import numpy as np
from sklearn.neighbors import NearestNeighbors

'''
This class implements the All K-Nearest-Neighbors benchmark.
'''
class ALLKNN(object):

  '''
  Create the All K-Nearest-Neighbors benchmark instance.

  @param dataset - Input dataset to perform All K-Nearest-Neighbors on.
  @param timeout - The time until the timeout. Default no timeout.
  @param verbose - Display informational messages.
  '''
  def __init__(self, dataset, timeout=0, verbose=True):
    self.verbose = verbose
    self.dataset = dataset
    self.timeout = timeout

  '''
  Use the scikit libary to implement All K-Nearest-Neighbors.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def AllKnnScikit(self, options):
    def RunAllKnnScikit(q):
      totalTimer = Timer()

      # Load input dataset.
      # If the dataset contains two files then the second file is the query file
      # In this case we add this to the command line.
      Log.Info("Loading dataset", self.verbose)
      if len(self.dataset) == 2:
        referenceData = np.genfromtxt(self.dataset[0], delimiter=',')
        queryData = np.genfromtxt(self.dataset[1], delimiter=',')
      else:
        referenceData = np.genfromtxt(self.dataset, delimiter=',')

      with totalTimer:
        # Get all the parameters.
        k = re.search("-k (\d+)", options)
        leafSize = re.search("-l (\d+)", options)
        radius = re.search("--radius (\d+)", options)
        tree_type = re.search("-t (\s+)", options)
        metric = re.search("--metric (\s+)", options)
        # Parameter for the Minkowski metric. 
        # When p=1 it is equivalent to using manhattan_distance and euclidean for p=2. 
        # For arbitrary p, minkowski_distance is used.
        p = re.search("-p (\d+)", options)
        n_jobs = re.search("--n_jobs (\d+)", options)
        if not k:
          Log.Fatal("Required option: Number of furthest neighbors to find.")
          q.put(-1)
          return -1
        else:
          k = int(k.group(1))
          if (k < 1 or k > referenceData.shape[0]):
            Log.Fatal("Invalid k: " + k.group(1) + "; must be greater than 0"
              + " and less or equal than " + str(referenceData.shape[0]))
            q.put(-1)
            return -1

        if not leafSize:
          leafSize = 20
        elif int(leafSize.group(1)) < 0:
          Log.Fatal("Invalid leaf size: " + str(leafSize.group(1)) + ". Must" +
              " be greater than or equal to 0.")
          q.put(-1)
          return -1
        else:
          leafSize = int(leafSize.group(1))
        if not tree_type:
            tree_type = 'kd_tree'
        elif str(tree_type.group(1)):
            tree_type = str(tree_type.group(1))
            if tree_type !='auto' or tree_type !='ball_tree' or tree_type != 'kd_tree' or tree_type != 'brute':
                Log.Fatal("Invalid tree type: "+ str(tree_type.group(1)) 
                          + ". Must be either auto, ball_tree, kd_tree or brute.")
                q.put(-1)
                return -1
        radius = 1.0 if not radius else float(radius.group(1))
        p = 2 if not p else int(p.group(1))
        if not metric:
            metric = 'minkowski'
        elif metric.group(1):
            metric = str(metric.group(1))
            if metric not in ['cityblock', 'cosine', 'euclidean', 'l1', 'l2', 'manhattan']:
                Log.Fatal("Invalid metric type: "+ str(metric.group(1))
                          + ". Must be either cityblock, cosine, euclidean, l1, l2 or manhattan")
                q.put(-1)
                return -1
        n_jobs = 1 if not n_jobs else int(n_jobs.group(1))

        try:
          # Perform All K-Nearest-Neighbors.
          model = NearestNeighbors(n_neighbors=k, 
                                   algorithm=tree_type, 
                                   leaf_size=leafSize, 
                                   radius=radius, 
                                   metric=metric, 
                                   p=p, 
                                   n_jobs=n_jobs)
          model.fit(referenceData)

          if len(self.dataset) == 2:
            out = model.kneighbors(queryData, k, return_distance=True)
          else:
            # We have to increment k by one because mlpack ignores the
            # self-neighbor, whereas scikit-learn will happily return the
            # nearest neighbor of point 0 as point 0.
            out = model.kneighbors(referenceData, k + 1, return_distance=True)
        except Exception as e:
          q.put(-1)
          return -1

      time = totalTimer.ElapsedTime()
      q.put(time)
      return time

    return timeout(RunAllKnnScikit, self.timeout)

  '''
  Perform All K-Nearest-Neighbors. If the method has been successfully completed
  return the elapsed time in seconds.

  @param options - Extra options for the method.
  @return - Elapsed time in seconds or a negative value if the method was not
  successful.
  '''
  def RunMetrics(self, options):
    Log.Info("Perform ALLKNN.", self.verbose)

    results = self.AllKnnScikit(options)
    if results < 0:
      return results

    return {'Runtime' : results}
