import os
import sys
import numpy as np
from scipy.optimize import fmin_slsqp

# calculate discrete gradient  for a graph with m nodes and edges E
# NOTE: should use sparse matrices
def dg(m,E):
    ne,_ = np.shape(E)
    D = np.zeros((ne,m))
    for e in range(0,ne):
        D[e,E[e,:]] = [1,-1]
    return D

# creates a block diagonal matrix from the matrices specified
# in the Nx x Nx x Nz array T
#
# D =  [ T(:,:,1)
#                 T(:,:,2)
#      	                ...
#      		            T(:,:,Nz) ]
# NOTE: should use sparse matrices
def diagt(T):
    Nz,Ny,Nx = np.shape(T)
    assert Nx==Ny
    D = np.zeros((Nz*Nx,Nz*Nx))
    for i in range(0,Nz):
        D[(i*Nx):((i+1)*Nx),(i*Nx):((i+1)*Nx)] = T[i,:,:]
    return D


class truss:
    """Compute the position of all the nodes in the truss
        n = number of nodes
        E = connecting edges (pair of node indexes in x)
        A = indexes of the anchor nodes in x (fixed in space)
    """
    def __init__(self, n, E, A):
        self.k = 1 # stiffness of all the bars
        self.g = np.array([0,0,-250000]) # gravity (mm/s^2)
        self.E = E
        self.A = A
        self.m = n  # number of nodes
        self.nE,_ = np.shape(E) # number of edges
        self.nA = np.size(A)    # number of anchors
        # discrete gradient
        self.D = np.kron(dg(self.m, self.E), np.eye(3))
        # dofs
        self.dofs = np.setdiff1d(np.array(range(0, self.m)), self.A)


    # dofs to displacements
    def dof_to_displ(self, udof):
        u = np.zeros((3 * self.m))
        for idof in range(0, np.size(self.dofs)):
            dof = self.dofs[idof]
            u[(dof * 3):((dof + 1) * 3)] = udof[3 * idof:3 * (idof + 1)]
        return u


    def link_lengths(self, u):
        n = np.size(u)
        Du = np.matmul(self.D, u)
        L = np.zeros(n / 3)
        for i in range(0, n / 3):
            L[i] = np.dot(Du[(3 * i):(3 * (i + 1))], Du[(3 * i):(3 * (i + 1))])
        return L


    def computeNodesPositions(self, x):
        m,_ = np.shape(x)
        if m != self.m:
            raise NotImplementedError

        # vectors corresponding to all rods in equilibrium
        Dx = (self.D.dot(x.flatten())).reshape(self.nE, 3)

        # indices of edges that have at least 1 dof
        iEdof = np.argwhere([ self.E[e,0] in self.dofs or self.E[e,1] in self.dofs for e in range(0, self.nE) ]).flatten()

        # matrix conductivities (all stiffnesses are equal to k)
        s = np.zeros((self.nE, 3, 3))
        for e in range(0, self.nE):
            s[e, :, :] = self.k * np.outer(Dx[e, :], Dx[e, :]) / np.dot(Dx[e, :], Dx[e, :])

        # graph Laplacian
        L = np.matmul(self.D.transpose(), np.matmul(diagt(s), self.D))

        # anchors are fixed
        for i in range(0, self.nA):
            ia = self.A[i]
            L[(ia * 3):((ia + 1) * 3), :] = 0
            L[(ia * 3):((ia + 1) * 3),(ia * 3):((ia + 1) * 3)] = np.eye(3)

        # same force (gravity) on all dofs
        f = np.zeros((3 * m))
        for dof in self.dofs:
            f[(dof * 3):((dof + 1) * 3)] = self.g

        # objective function
        obj = lambda u: np.dot(u, np.matmul(L, u) - f)

        # constraints
        eqcons = lambda u: self.link_lengths(x.flatten() + u) - self.link_lengths(x.flatten())


        # using only dof
        obj_dof = lambda udof: obj(self.dof_to_displ(udof))
        eqcons_dof = lambda udof: eqcons(self.dof_to_displ(udof))[iEdof]


        # solve for displacements with SQP (all vars)
        #fmin_slsqp(obj,np.zeros(3*m),f_eqcons=eqcons)

        # solve for displacements with SQP (only dofs)
        ndof = np.size(self.dofs)

        # Temporarily redefine the standard output to avoid extra print done by fmin_slsqp
        null = open(os.devnull,'wb')
        sys.stdout = null
        udof, _, _, imode, smode = fmin_slsqp(obj_dof, np.zeros(3 * ndof), f_eqcons=eqcons_dof, full_output=True)
        # Restore standard output
        sys.stdout = sys.__stdout__
        
        if imode != 0:
            print "Optimisation failed: ", smode
            raise OptimisationFailedError

        u = self.dof_to_displ(udof)
        newx = x.flatten() + u

        return newx

if __name__ == '__main__':
    # Tests

    # example 1: 2 anchor points and 1 free node

    # node coordinates as x1 y1 z1
    #                     x2 y2 z2
    #                     ....
    #                     xn yn zn
    x0 = np.array([[0, 0, 0],
                  [0, 0, 0],
                  [0, 0, 0],
                  [0, 0, 0]
                  ])


    # edge connectivity as i1 j1
    #                      i2 j2
    #                      ...
    #                      iNE jNE
    E = np.array([[0, 1],
                  [0, 2],
                  [2, 3],
                  [1, 3]])

    # anchors
    A = np.array([0,1])


    t = truss(4, E, A)

    # node coordinates (in mm)
    a = 500
    pi = np.pi
    cos = np.cos
    sin = np.sin
    x = np.array([[0, 0, 0],
                  [a, 0, 0],
                  [-cos(pi/6) * a, 0, -sin(pi/6) * a],
                  [a+-cos(pi/6) * a, 0, -sin(pi/6) * a]
                  ])

    newx = t.computeNodesPositions(x)
    print newx

    x = np.array([[0, 0, 0],
                  [a, 0, 0],
                  [-cos(pi/8)*a, 0, -sin(pi/8)*a]
                  ])

    newx = t.computeNodesPositions(x)
    print newx
