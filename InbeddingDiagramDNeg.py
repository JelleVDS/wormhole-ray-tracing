

import numpy as np
import matplotlib.pyplot as plt


def dneg_r(y, M=0.43/1.42953 , p=1, a=0): #input: scalar, output: scalar
    x = 2*(np.abs(y) - a)/(np.pi*M)
    return p + M*(x*np.arctan(x) - 0.5*np.log(1 + x**2))

def dneg_dr_dl(y, M=0.43/1.42953): #input: scalar, output: scalar
    x = 2*np.abs(y)/(np.pi*M)
    return 2/np.pi*np.arctan(x)

def imb_f(l): #input: 1D array , output: 1D array
    #hoogte formule inbedding diagram
    return np.sqrt(1 - dneg_dr_dl(l)**2)

def imb_f_int(l): #input: 1D array , output: 1D array
    Z = []
    # integratie voor stijgende l
    for i in range(1,len(l)):
         Z.append(np.trapz(imb_f(l[:i]), l[:i]))
    return np.array(Z)

def inb_diagr(I, N): #input: I: interval, N: #points, output: plot
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    l = np.linspace(I[0], I[1], N+1) # N+1, want dan N intervallen
    phi = np.linspace(0, 2*np.pi, N)
    L, PHI = np.meshgrid(dneg_r(l[1:]), phi) # radius is r(l)

    #tile want symmetrisch voor rotaties, onafhankelijk van phi
    Z = np.tile(imb_f_int(l), (N, 1)) #z(l)

    X, Y = L*np.cos(PHI), L*np.sin(PHI)
    ax.plot_surface(X, Y, Z, cmap=plt.cm.YlGnBu_r)
    plt.show()


inb_diagr([-10, 10], 1000)