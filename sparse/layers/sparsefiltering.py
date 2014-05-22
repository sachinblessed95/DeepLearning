"""
==================
 Sparse filtering
==================

Python port of the sparse filtering matlab code by Jiquan Ngiam.

Requires numpy and scipy installed.
"""
import numpy as np
from scipy.optimize import minimize

MAX_ITER = 500

def l2row(X):
    """
    L2 normalize X by rows. We also use this to normalize by column with l2row(X.T)
    """
    N = np.sqrt((X**2).sum(axis=1)+1e-8)
    #sum = Sum of array elements over a given axis.
    #axis = 1 means sum over rows
    #N.shape = (256,)
    Y = (X.T/N).T
    #Y is now normalized in some way...
    return Y,N


def l2rowg(X,Y,N,D):
    """
    Backpropagate through Normalization.

    Parameters
    ----------

    X = Raw (possibly centered) data.
    Y = Row normalized data.
    N = Norms of rows.
    D = Deltas of previous layer. Used to compute gradient.

    Returns
    -------

    L2 normalized gradient.
    """
    return (D.T/N - Y.T * (D*X).sum(axis=1) / N**2).T


def sparseFiltering(N,X):
    "N = # features, X = input data (examples in column)"
    #type(X) - <type 'numpy.ndarray'>
    #X.shape() = (256, 50000)
    optW = np.random.randn(N,X.shape[0]) #returns an array of random floats - the parameters are the dimensions of the returned array
    #optW = matrix[256][256]

    # Objective function!
    def objFun(W):
        #W = matrix[256][256]
        """ Feed forward """
        W = W.reshape((N,X.shape[0])) #gives a new shape to an array without changing its data - prob. from 2x3 to 3x2
        F = W.dot(X) #dot product
        #F.shape() = (256, 50000)
        
        Fs = np.sqrt(F**2 + 1e-8)
        #F**2  square of very cell of the matrix
        #root square of the square of every cell + 1*10^-8
        #Fs ~ F  -- only small differences

        """Sparse optimization <---------------------- <--------------------- <------------------------"""
        NFs, L2Fs = l2row(Fs)
        #NFs = matrix normalized by rows
        #L2Fs = squared sum over rows
        Fhat, L2Fn = l2row(NFs.T)
        #Fhat = matrix normalized by columns
        #L2Fn = squared sum over columns

        # Compute objective function
        """ Backprop through each feedforward step """
        DeltaW = l2rowg(NFs.T, Fhat, L2Fn, np.ones(Fhat.shape))
        #np.ones returns a matrix of all 1
        DeltaW = l2rowg(Fs, NFs, L2Fs, DeltaW.T)
        DeltaW = (DeltaW*(F/Fs)).dot(X.T)
        return Fhat.sum(), DeltaW.flatten()

    def call(xk):
        pass
        #print 'xk'
        #print xk

    # Actual optimization
    w,g = objFun(optW)

    res = minimize(objFun, optW, method='L-BFGS-B', jac = True, options = {'maxiter':MAX_ITER, 'disp':10}, callback=call)
    print w
    return res.x.reshape(N,X.shape[0])


def feedForwardSF(W,X):
    "Feed-forward"
    #W - output of sparseFiltering()
    #X - initial data
    F = W.dot(X)
    Fs = np.sqrt(F**2 + 1e-8)
    #Fs ~ F
    NFs = l2row(Fs)[0]
    #NFs = first row of the normalized version of Fs
    return l2row(NFs.T)[0].T
