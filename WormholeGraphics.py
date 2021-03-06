import WormholeRayTracer as w
import cv2
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import InbeddingDiagramDNeg as Dia
import os

def Make_Pict_RB(q):
    # input: q: matrix with coordinates in configuration space on first row ouput:
    # 3D matrix (2D matrix of rays each containing a coordinate in colorspace)
    # RGB based on sign(l), q = (l, phi, theta)
    pict = []
    for j in range(len(q[0])):
        row = []
        for i in range(len(q[0][0])):
            if q[0][j,i] <= 0:
                row.append([255, 0, 0])
            else:
                row.append([0, 0, 255])
        pict.append(row)
    return cv2.cvtColor(np.array(pict, np.float32), 1)


def Grid_constr_2D(q, N_a, R, w):
    # input: q: matrix with coordinates in configuration space on first row
    #        N_a: subdivision angles
    #        N_r: linspace radius to form grid
    #        w: ratio
    #output: 2D boolean array
    Nz, Ny =  q[0].shape
    r, phi, theta = q

    # subdivides theta and phi
    Par_phi = np.linspace(0, 2*np.pi, N_a-1)
    Par_th = np.linspace(0, np.pi, N_a-1)

    # Defines point on polar grid
    on_phi = np.any(
        np.abs(phi.reshape(1,Nz,Ny) -
               np.transpose(np.tile(Par_phi, (Nz, Ny,1)), (2,0,1)))
        < 2*np.pi/N_a*w, axis=0)

    on_theta = np.any(
        np.abs(theta.reshape(1,Nz,Ny) -
               np.transpose(np.tile(Par_th, (Nz, Ny,1)), (2,0,1)))
        < np.pi/N_a*w,  axis=0)

    return on_phi | on_theta


def Grid_constr_3D_Sph(q, N_a, R, w, Slice = None):
    # input: q: matrix with coordinates in configuration space on first row
    #        N_a: subdivision angles
    #        R: linspace radius to form grid
    #        w: ratio
    #output: 2D boolean array
    Nz, Ny =  q[0].shape
    if np.any(Slice == None):
        Slice = np.zeros((Nz, Ny), dtype=bool)
    Slice_inv = ~Slice
    r, phi, theta = q

    # subdivides theta and phi
    Par_phi = np.linspace(0, 2*np.pi, N_a-1)
    Par_th = np.linspace(0, np.pi, N_a-1)

    # Defines point on spherical grid
    rr = r[Slice_inv]
    M = len(rr)
    on_shell = (np.abs(R - np.mod(rr, R)) < R*w) | (np.abs(np.mod(rr, R) - R) < R*w)

    on_phi = np.any(
        np.abs(phi[Slice_inv].reshape(1,M) - np.tile(Par_phi, (M,1)).T)
        < 2*np.pi/N_a*w, axis=0)

    on_theta = np.any(
        np.abs(theta[Slice_inv].reshape(1,M) - np.tile(Par_th, (M,1)).T)
        < np.pi/N_a*w,  axis=0)

    # Boolean conditions for when rays lands on spherical grid
    Slice[Slice_inv] = (on_phi & on_theta) | (on_phi & on_shell) | (on_shell & on_theta)
    return Slice


def Sph_cart(psi):
    r, phi, theta = psi
    x = r*np.cos(phi)*np.sin(theta)
    y = r*np.sin(phi)*np.sin(theta)
    z = r*np.cos(theta)
    return np.array([x,y,z])


def Grid_constr_3D_Cart(q, N_a, R, w, Slice = None):
    # input: q: matrix with coordinates in configuration space on first row
    #        N_a: subdivision angles
    #        R: linspace radius to form grid 
    #        w: ratio
    #output: 2D boolean array
    Nz, Ny =  q[0].shape
    if np.any(Slice == None):
        Slice = np.zeros((Nz, Ny), dtype=bool)
    Slice_inv = ~Slice
    x, y, z = Sph_cart(q)
    
    # Defines point on spherical grid
    xx = x[Slice_inv]
    on_x = (np.abs(R - np.mod(xx, R)) < R*w) | (np.abs(np.mod(xx, R) - R) < R*w)
    yy = y[Slice_inv]
    on_y = (np.abs(R - np.mod(yy, R)) < R*w) | (np.abs(np.mod(yy, R) - R) < R*w)
    zz = z[Slice_inv]
    on_z = (np.abs(R - np.mod(zz, R)) < R*w) | (np.abs(np.mod(zz, R) - R) < R*w)
    # Boolean conditions for when rays lands on spherical grid
    Slice[Slice_inv] = (on_x & on_z) | (on_y & on_z) | (on_x & on_y)
    return Slice


def Make_Pict_RGBP(q, Grid):
    # input: q: matrix with coordinates in configuration space on first row
    # output: 3D matrix (2D matrix of rays each containing a coordinate in colorspace)
    Nz, Ny =  q[0].shape
    pict = np.empty((Nz, Ny, 3))
    Grid_inv = ~Grid
    r, phi, theta = q
    
    pict[Grid] = np.array([0,0,0])
    # colors based on sign azimutha angle and inclination
    pict[((phi > np.pi) & (theta > np.pi/2)) & Grid_inv] = np.array([0, 1, 0])
    pict[((phi > np.pi) & (theta < np.pi/2)) & Grid_inv] = np.array([1, 0, 0])
    pict[((phi < np.pi) & (theta > np.pi/2)) & Grid_inv] = np.array([0, 0, 1])
    pict[((phi < np.pi) & (theta < np.pi/2)) & Grid_inv] = np.array([0.5, 0.5, 0])
    # invert color for points on oposite side of wormhole
    pict[(r < 0) & Grid_inv] = 1 - pict[(r < 0) & Grid_inv]
    
    pict = cv2.cvtColor(np.array(pict, np.float32), 1)
    return pict

def plot_CM(CM, Label, name, path):
    #input: 3D array containing energy of each ray over time, advancement in time on first row
    #       Label: list of labels of constants
    #       name: picture/filename
    #       path: directory
    # plot the constants of motion over the partition of the rays
    
    x = np.arange(len(CM))
    if len(Label) > 1:
        Sh = CM[0,0].shape
    else:
        Sh = CM[0].shape 
    if len(Sh) > 1:
        Ny, Nz = Sh
        cl, ind = ray_spread(Nz, Ny)
        if len(Label) > 1:
            CM = np.transpose(CM, (1,0,2,3))
    else:
        N = Sh[0]
        cl = plt.cm.viridis(np.arange(N)/N)
        if len(Label) > 1:
            CM = np.transpose(CM, (1,0,2))
    if len(Label) > 1:
        N_C = len(CM)
        fig, ax = plt.subplots(1, N_C)
        for k in range(N_C):
            if len(Sh) > 1:
                for i in range(Nz):
                    for j in range(Ny):
                        ij = i + Nz*j
                        cl_i =cl[ind[ij]]
                        ax[k].plot(x, CM[k,:,i,j], color=cl_i)
            else:
                for i in range(N):
                        x[k].plot(x, CM[k,:,i], color=cl[i])        
            ax[k].set_yscale("symlog")
            # ax[k].set_title(Label[k] + ",  Donker pixels binnenkant scherm, lichte pixels buitenkant")
                
            ax[k].set_ylabel(Label[k])
            if k == 1:
                ax[k].set_xlabel("\npercentage of path finished [%]")
            else:
                ax[k].set_xlabel("percentage of path finished [%]")
            ax[k].set_title("sum subdivision rays")
    else:
        fig, ax = plt.subplots()
        if len(Sh) > 1:
            for i in range(Nz):
                for j in range(Ny):
                    ij = i + Nz*j
                    cl_i =cl[ind[ij]]
                    ax.plot(x, CM[:,i,j], color=cl_i)
        else:
            for i in range(N):
                ax.plot(x, CM[:,i], color=cl[i])        
        ax.set_yscale("symlog")
        # ax[k].set_title(Label[k] + ",  Donker pixels binnenkant scherm, lichte pixels buitenkant")
                
        ax.set_ylabel(Label[0])
        ax.set_xlabel("percentage of path finished [%]")
        ax.set_title("sum subdivision rays")
            
    plt.tight_layout()
    plt.savefig(os.path.join(path, name), dpi=150)
    plt.show()
    plt.savefig('Constants.png')


def ray_spread(Nz, Ny):
    # input: Ny: amount of horizontal arrays, Nz: amount of vertical arrays
    # output: cl: color based on deviation of the norm of a ray compared to direction obeserver is facing
            #ind ind of original ray mapped to colormap
    S_c = w.screen_cart(Nz, Ny, 1, 1)
    S_cT = np.transpose(S_c, (2,0,1))
    n = np.linalg.norm(S_cT, axis=0)
    n_u, ind = np. unique(n, return_inverse=True)
    N = n_u.size
    cl = plt.cm.viridis(np.arange(N)/N)

    return cl, ind


def gdsc(Motion, Par, name, path, geo_label = None, select = None, reduce = False):
    # input: Motion: 5D matrix, the elements being [p, q] with p, q as defined earlier
    #       Par: parameters wormhole
    #       Name: picture/filename
    #       Path: directory
    #       select: Give a list of 2D indices to plot only specific geodesiscs
    #       geo_label: if you're just plotting a list of geodesics (thus its elements in order time, [p,q], coordinate),
    #                   then give here a list of strings that which will be the label of your geodesics, corresponding to the order of your geodesics.
    #       reduce: if true sample geodescics uniformly
    M, rho, a = Par

    if np.any(select == None):
        if np.any(reduce == False):
            Sample = np.transpose(Motion, (1,2,3,0))
        else:
            Motion = np.transpose(Motion, (1,2,0,3,4))
            Ny, Nz =  Motion[0][0][0].shape
            Ny_s = int(np.sqrt(Nz))
            Nz_s = int(np.sqrt(Ny))

            # Samples a uniform portion of the rays for visualisation
            Sample = Motion[:, :, :, 1::Nz_s, 1::Ny_s]
            cl, ind = ray_spread(Nz_s, Ny_s)

    else:
        Motion = np.transpose(Motion, (3,4,0,1,2))
        Sample = np.transpose(
            [Motion[tuple(select[k])] for k in range(len(select))]
            , (2,3,1,0))

    p, q = Sample
    p_l, p_phi, p_th = p
    l, phi, theta = q
    # caluclates coordinates in inbedded space
    ax = plt.figure().add_subplot(projection='3d')
    r = w.dneg_r(l, M, rho, a)
    X, Y = r*np.cos(phi), r*np.sin(phi)
    
    S_l = np.linspace(np.max(l), np.min(l), len(l))
    Col_l = np.concatenate((l.T, np.expand_dims(S_l, axis=0)), axis=0).T
    Col_Z = Dia.imb_f_int(Col_l, Par)
    Z = Col_Z[:,:-1]
    S_Z0 = Col_Z[:,-1] + np.max(Z)

    if np.any(reduce == False):
        for k in range(len(Sample[0,0,0])):
            if np.any(geo_label == None):
                gl = str(select[k])
            else:
                gl = geo_label[k]
            ax.plot(X[:,k], Y[:,k], Z[:,k], label = gl )
        ax.scatter(X[0,0] , Y[0,0], Z[0,0], label='camera', c = 'r')
        #ax.set_title("Path of a geodesic that lead to noise")
        ax.legend()
    else:
        for i in range(Nz_s):
            for j in range(Ny_s):
                ij = i + Nz_s*j
                cl_i =cl[ind[ij]]
                ax.plot(X[:,i,j], Y[:,i,j], Z[:,i,j], color = cl_i, alpha=0.5)
        ax.scatter(X[0,0,0] , Y[0,0,0], Z[0,0,0], label='camera', c = 'r')
        ax.set_title("Geodesics")
        ax.legend()

    # adds surface

    #S_l = np.linspace(np.max(l), np.min(l), len(l))
    S_phi = np.linspace(0, 2*np.pi, len(l))
    S_R, S_PHI = np.meshgrid(w.dneg_r(S_l, M, rho, a), S_phi) # radius is r(l)

    # tile because symmetric for rotations, undependant on phi
    # Integral for Z direction like defined in the paper
    S_Z = np.tile(S_Z0, (len(l), 1)) #z(l)
    
    S_X, S_Y = S_R*np.cos(S_PHI), S_R*np.sin(S_PHI)
    #print(S_X.shape, S_Y.shape, S_Z.shape)
    ax.plot_surface(S_X, S_Y, S_Z, cmap=plt.cm.coolwarm, alpha=0.5)
    plt.tight_layout()
    # Hide grid lines
    ax.grid(False)

    ax.axis("off")
    # ax.set_zlim([-15,15])
    plt.savefig(os.path.join(path, name), dpi=150)
    plt.show()
    
def fullplothalf(ax, q_cart, l_cond, cl, ind, L):
    for i in range(len(q_cart[0,0])):
        for j in range(len(q_cart[0,0,0])):
            ij = j + len(q_cart[0,0])*i
            cl_i =cl[ind[ij]]
            ax.plot(q_cart[0,:,i,j][l_cond[:,i,j]],
                    q_cart[1,:,i,j][l_cond[:,i,j]],
                    q_cart[2,:,i,j][l_cond[:,i,j]],
                    color = cl_i)
    ax.set_xlim([-L,L])
    ax.set_ylim([-L,L])
    ax.set_zlim([-L,L])
    ax.axis("off")

def fullplot(q, a):
    q = np.transpose(q, (1,0,2,3))
    print(q[0][q[0] < 0].shape, q[0].shape)
    Nz, Ny =  q[0,0].shape

    # Samples a uniform portion of the rays for visualisation
    Sample = q[:, :, 1::a, 1::a]
    print(Sample[0][Sample[0] < 0].shape, Sample[0].shape)
    cl, ind = ray_spread(len(Sample[0,0]), len(Sample[0,0,0]))
    
    # boolean array to check sgn l
    l_cond = Sample[0] > 0
    print(np.any(l_cond == False))
    #print(Sample[0], Sample.shape, l_cond, l_cond.shape)
    # inverse boolean condition
    inv_l_cond = ~l_cond
    # set l postive on the other side and change to cartesian coordinates
    Sample[0][inv_l_cond] = -Sample[0][inv_l_cond]
    q_cart = w.Sph_cart(Sample)
    
    L = 20
    fig = plt.figure(figsize=plt.figaspect(0.5))
    ax = fig.add_subplot(1, 2, 1, projection='3d')
    fullplothalf(ax, q_cart, l_cond, cl, ind, L)
    ax = fig.add_subplot(1, 2, 2, projection='3d')
    fullplothalf(ax, q_cart, inv_l_cond, cl, ind, L)
            
    plt.tight_layout()
    plt.show()   
    
    
def density_states_plot(pq_final, Par, H_max, n_bins, path, name):
    # input: pq_final: final position in phase space, pixels indices on last rows
    #       Par: parameters wormhole
    #       H_max: cut_off point
    #       n_bins: amount of bins
    #       name: picture/filename
    #       path: directory
    # output: Density states plot
    
    p, q = pq_final.astype(np.float64)
    M, rho, a = Par

    p_l, p_phi, p_th = p
    l, phi, theta = q

    # defining r(l):
    r = w.dneg_r(l, M, rho, a)

    rec_r = 1/r
    rec_r_2 = rec_r**2
    sin1 = np.sin(theta)
    sin2 = sin1**2
    rec_sin2 = 1/sin2

    # defining hamiltonian
    H1 = p_l**2
    H2 = p_th**2*rec_r_2
    H3 = p_phi**2*rec_sin2*rec_r_2

    H = 0.5*(H1 + H2 + H3).flatten()
    K = len(H)
    M = K - len(H[H>H_max])
    H = H[H<H_max]

    fig, ax = plt.subplots(tight_layout=True)
    
    logbins = np.geomspace(H.min(), H.max(), n_bins)
    N, bins, patches = ax.hist(H, bins=logbins)
    
    # We'll color code by height, but you could use any scalar
    fracs = N / N.max()
    
    # we need to normalize the data to 0..1 for the full range of the colormap
    norm = mcolors.Normalize(fracs.min(), fracs.max())
    
    # Now, we'll loop through our objects and set the color of each accordingly
    for thisfrac, thispatch in zip(fracs, patches):
        color = plt.cm.viridis(norm(thisfrac))
        thispatch.set_facecolor(color)
    
    ax.set_xscale("symlog")
    y_sc = ax.get_yticks()
    ax.set_yticklabels(y_sc/K*100)
    ax.set_ylabel('occupation level [%]')
    ax.set_xlabel('$H$[$m^{2}$]')
    plt.savefig(os.path.join(path, name), dpi=150)
    print(str(M)+ " out of "+ str(K) + " values shown")
    plt.show()
        
        
        
        
        
        
        
        
        
        
        