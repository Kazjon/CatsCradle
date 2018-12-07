from mpl_toolkits.mplot3d import Axes3D
import math
import matplotlib
matplotlib.use("QT5Agg")

import matplotlib.pyplot as plt
import numpy as np

simplex_points = np.asarray([[1,0,0],
                  [-1./3.,math.sqrt(8)/3.,0],
                  [-1./3.,-math.sqrt(2)/3.,math.sqrt(2./3.)],
                  [-1./3.,-math.sqrt(2)/3.,-math.sqrt(2./3.)]
                  ])

def softmax(x):
    '''Compute softmax values for each sets of scores in x.'''
    return np.exp(x) / np.sum(np.exp(x), axis=0)

def randrange(n, vmin, vmax):
    '''
    Helper function to make an array of random numbers having shape (n, )
    with each number distributed Uniform(vmin, vmax).
    '''
    return (vmax - vmin)*np.random.rand(n) + vmin

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')


n = 10000
maxval = 10

weighted_points = np.asarray([softmax(randrange(4, 0, maxval)) for i in range(n)])

xs,ys,zs = np.asarray([np.sum([simplex_points[i]*p[i] for i in range(4)],axis=0) for p in weighted_points]).T

ax.scatter(xs,ys,zs,c='g',marker="o",s=30)


'''


# For each set of style and range settings, plot n random points in the box
# defined by x in [23, 32], y in [0, 100], z in [zlow, zhigh].
for c, m, zlow, zhigh in [('r', 'o', -50, -25), ('b', '^', -30, -5)]:
    xs = randrange(n, 23, 32)
    ys = randrange(n, 0, 100)
    zs = randrange(n, zlow, zhigh)
    ax.scatter(xs, ys, zs, c=c, marker=m)
'''

xs,ys,zs = simplex_points.T
ax.scatter(xs,ys,zs,c='r',marker="o",s=30)

weights = np.asarray([0.25,0.25,0.25,0.25])
x,y,z = np.sum([simplex_points[i]*weights[i] for i in range(4)],axis=0)

ax.scatter(x,y,z,c='b',marker="o",s=100)

ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_zlabel('Z Label')

plt.show()