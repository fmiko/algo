##############################################################
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# psoRun.py, runs and performs analysis on the Partical Swarm Optimization algorithm
#
# Written by Jared Smith and David Cunningham for COSC 427/527
# at the University of Tennessee, Knoxville
#
###############################################################

import sys
import os
import argparse
import logging
import contextlib
from argparse import RawTextHelpFormatter

import numpy as np
import matplotlib.pyplot as plt

from psoAlgorithm import PSO
from Problems import *

# Function for changing directories safely
@contextlib.contextmanager
def cd(newPath):
    savedPath = os.getcwd()
    os.chdir(newPath)
    yield
    os.chdir(savedPath)


#distance with wrapping
def Distance(s1, s2):
   x = s2.pos - s1
   x = np.minimum(x, (s2.maxPos) - x)
   return sum((x)**2)**.5


# Setup the command line parser
def setup_argparser():

    parser = argparse.ArgumentParser(description='' +
                                     ' BioPy: Particle Swarm Optimization' +
                                     ' Algorithm in Python.\n'
                                     version='1.0.0',
                                     formatter_class=RawTextHelpFormatter)

    requiredArguments = parser.add_argument_group('required Arguments')
    requiredArguments.add_argument('-exp', dest='experiment_number', required=True, type=str, help="Number of this experiment.")
    optionalArguments = parser.add_argument_group('optional Arguments')
    optionalArguments.add_argument('--num_part', dest='npart', required=False, type=int, default=40, help="Number of particles in the world. Default is 40.")
    optionalArguments.add_argument('--phi', dest='phi', required=False, type=tuple, default=(2, 2, 2), help="The conscious, social and potential neighboorhood parameters. Defaults are 2, 2, 2.")
    optionalArguments.add_argument('--maxVel', dest='maxVel', required=False, type=int, default=20, help="Maximum Velocity of the PSO. Default is 20.")
    optionalArguments.add_argument('--dim', dest='dim', required=False, type=tuple, default=(100, 100), help="Ranges of the dimensions of the world. Default is 100x100.")
    optionalArguments.add_argument('--inertia', dest='inertia', required=False, type=float, default=1.0, help="Starting inertia of the particles. Default is 1.")
    optionalArguments.add_argument('--inerPrime', dest='inerPrime', required=False, type=float, default=0.99, help="Percentage rate of change of inertia each iteration. Default is 0.99.")
    optionalArguments.add_argument('--minError', dest='minError', required=False, type=float, default=.01, help="The minimum error the system must reach before it ceases updating. Default is 0.01.")
    optionalArguments.add_argument('--maxIter', dest='maxIter', required=False, type=int, default=1000, help="Maximum number of iterations before the system ceases updating. Default is 1000.")
    optionalArguments.add_argument('--Q', dest='Q', required=False, type=str, default='Problem1', help="Fitness function to use. Default is Problem1 specified in Problems.py.")
    optionalArguments.add_argument('--num_neighbors', dest='k', required=False, type=int, default=0, help="Number of neighbors a particle has, or neighborhood range if Euclid parameter\n" +
                                   "for Euclidean Topology is True. Default is 0.")
    optionalArguments.add_argument('--Euclid', dest='Euclid', required=False, type=bool, default=False, help="Whether or not to use the Euclidian Topology. Default is False.")
    return parser


def setup_logger(log_path, logger_name, logfile_name):

    logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    rootLogger = logging.getLogger(logger_name)
    rootLogger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler("{0}/{1}.log".format(log_path, logfile_name), mode='w')
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    return rootLogger


def PlotScatter(swarm, maxes, best, iteration):
    #if swarm is 2D plot
    #create x and y arrays
    x = []
    y = []
    for i in swarm:
        x.append(i.pos[0])
        y.append(i.pos[1])
    #Plot figure
    fig = plt.figure()
    subplt = plt.subplot(111)
    subplt.scatter(x, y, marker = "o", c = 'b', alpha=0.5, label = "Particle")
    subplt.scatter(np.array([best[0]]), np.array([best[1]]), s=100,marker = 'x', c = "r", label = "Global Best")
    plt.xlim([-1*maxes[0]/2, maxes[0]/2])
    plt.ylim([-1*maxes[1]/2, maxes[1]/2])
    plt.title("Locations of Particles after Iteration %d" % iteration)
    plt.xlabel("X")
    plt.ylabel('Y')
    plt.legend(loc="upper left", bbox_to_anchor=[0, 1], ncol=2, shadow=True, title="Legend", fancybox=True)
    filename = "Scatter Plots/Scatter-%d.png" % iteration
    fig.savefig(filename)
    plt.close(fig)


def PlotError(dim_error):
    fig = plt.figure()
    subplt = plt.subplot(111)
    for n, val in enumerate(dim_error):
        x = np.arange(0,len(val))
        subplt.plot(x, np.array(val), label ="n={}".format(n))
    plt.xlabel('Iteration')
    plt.ylabel('Error')
    plt.title('Error for %d Epochs for %d Dimensions' % (len(dim_error[0])-1, len(dim_error)))
    plt.grid()
    plt.legend(loc="upper left", bbox_to_anchor=[0, 1], ncol=2, shadow=True, title="Dimension", fancybox=True)
    fig.savefig('Error.png', bbox_inches='tight')
    plt.close(fig)


def PlotConvergence(vals):
    fig = plt.figure()
    subplt = plt.subplot(111)
    x = np.arange(0,len(vals))
    subplt.plot(x, np.array(vals))
    plt.xlabel('Iteration')
    plt.ylabel('Convergencing Particles')
    i = len(vals) - 1
    plt.title('Pecentange of Converging Particles over %d Epochs' % i)
    plt.grid()
    fig.savefig('PercentConvergence.png', bbox_inches='tight')
    plt.close(fig)


def FindPercentConverge(swarm, best):
    filtered = filter(lambda x: Distance(best, x)<.5, swarm)
    return 100*((1.0*len(filtered)/len(swarm)))


def main():
    parser = setup_argparser()
    args = parser.parse_args()
    experiment_number = args.experiment_number

    print args.Q
    if str(args.Q) == 'Problem1':
        args.Q = Problem1
    elif str(args.Q) == 'Problem2':
        args.Q = Problem2
    else:
        print 'Incorrectly specified argument to Q (fitness function). Must be Problem1 or Problem2.'
        sys.exit(1)

    print args.Q

    # Setup directories for storing results
    if not os.path.exists('results'):
        os.makedirs('results')
    os.chdir('results')
    if not os.path.exists('data'):
        os.makedirs('data')
    os.chdir('data')
    if not os.path.exists('Experiment-' + str(experiment_number)):
        os.makedirs('Experiment-' + str(experiment_number))
    os.chdir('Experiment-' + str(experiment_number))
    if (len(args.dim)) == 2:
        if not os.path.exists('Scatter Plots'):
            os.makedirs('Scatter Plots')
    args_dict = vars(args)
    print args.dim
    args.dim=tuple(map(lambda x: x+x%2, args.dim)) #adjust dimensions so that they are even.
    logger = setup_logger(os.getcwd(), "__main__", "main")
    logger.info("Program Arguments:")
    for key, value in args_dict.iteritems():
        logger.info("%s=%s" % (str(key), str(value)))

    #####RUN PSO##########
    logger.info("\n\n###################################RUNNING EXPERIMENT NUM " +
                "%s#########################", str(experiment_number))
    pso = PSO(npart = args.npart, inertia=args.inertia, phi = args.phi, dimensions = args.dim , maxvelocity=args.maxVel, Q = args.Q, inertiaPrime = args.inerPrime)
    if args.Euclid is True:
        pso.setEuclidianNeigbors(args.k)
    else:
        pso.setClosestNeighbors(args.k)

    error_plot = [[] for i in range(len(args.dim))]
    convergence_plot =[]
    ###Run iieratons###
    for i in range(args.maxIter+1):
        cont = False
        logger.info("EPOCH %d:" % i)
        logger.info("Error:")
        error = pso.getError()
        logger.info(error)
        #add error dimensions error to the plot
        for n, plot in zip(error, error_plot):
            plot.append(n)
            if n>args.minError: #if all values for every dimension is below min error, we can break
                cont = True
        #add percent convergence to plot list:
        convergence_plot.append(FindPercentConverge(pso.swarm, pso.globalBest))
        #if swarm is 2D make a Scatter Plot
        if len(args.dim) == 2:
            logger.info("Creating scatter plot for iteration")
            PlotScatter(pso.swarm, args.dim, pso.globalBest, i)
            logger.info("Finished created scatter plot")
        #if we've converged to within a minimum error, break
        if cont is False:
            logger.info("Errors are below the threshold. Exiting now...")
            break
        #otherwise update and begin next iteration:
        logger.info("Updating PSO:")
        pso.Update()
    logger.info("\n\n######################ANALYZING DATA######################:")

    logger.info("Plotting error")
    PlotError(error_plot)
    logger.info("Finished plotting error")
    logger.info("Plotting percentage convergence")
    PlotConvergence(convergence_plot)
    logger.info("Finished plotting percentage convergence")

    logger.info("Experiment complete")
if __name__ == "__main__":
    main()
