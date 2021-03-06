import numpy as np
import time
import WormholeGraphics as wg
import Symplectic_DNeg as Smpl
import scipy.integrate as integr
from math import floor
from tqdm.auto import tqdm
#import scipy as sc



#Dit is op de master branch:
def dneg_r(l, M , rho, a):
    # input: scalars
    # output: scalar
    # define r(l) for a DNeg wormhole without gravity

    r = np.empty(l.shape)
    l_abs = np.abs(l)
    l_con = l_abs >= a
    inv_l_con = ~l_con

    x = 2*(l_abs[l_con] - a)/(np.pi*M)
    r[l_con] = rho + M*(x*np.arctan2(2*(l_abs[l_con] - a), np.pi*M) - 0.5*np.log(1 + x**2))
    r[inv_l_con] = rho
    return r

def dneg_dr_dl(l, M, a):
    # input:scalars
    # output: scalar
    # define derivative of r to l

    dr_dl = np.empty(l.shape)
    l_abs = np.abs(l)
    l_con = l_abs >= a
    inv_l_con = ~l_con

    x = 2*(l_abs[l_con] - a)/(np.pi*M)
    dr_dl[l_con] = (2/np.pi)*np.arctan(x)*np.sign(l[l_con])
    dr_dl[inv_l_con] = 0

    return dr_dl


def dneg_d2r_dl2(l, M, a):
    # input: scalars
    # output: scalars
    # define second derivative of r to l

    d2r_dl2 = np.empty(l.shape)
    l_abs = np.abs(l)
    l_con = l_abs >= a
    inv_l_con = ~l_con

    d2r_dl2[l_con] = (4*M)/(4*a**2 + M**2*np.pi**2 + 4*l[l_con]**2 - 8*a*l_abs[l_con])
    d2r_dl2[inv_l_con] = 0

    return d2r_dl2


def screen_cart(Nz, Ny, L1 = 1, L2=2):
     # input: Nz amount of pixels on vertical side screen
     #        Ny amount pixels horizontal side screen ,
     #        L = physical width and lenght of the screen.
     # output: 3D matrix (2d matrix of each ray/pixel, containing its location in 3D space)

    My = np.linspace(-L2/2, L2/2, Ny)
    Mz = np.linspace(-L1/2, L1/2, Nz)
     #cartesian product My X Mz
    arr = []
    for j in range(Nz):
        for i in range(Ny):
            # Placed at x = 1, (y,z) in My X Mz
            arr.append([3.3, My[i],Mz[j]]) #(x, y, z)

    return np.array(arr).reshape(Nz, Ny, 3) #Flat array into matrix



def cart_Sph(v):
    # input: matrix with cart. coord on first row,
    # output: matrix with Sph. coord on first row

    x,y,z = v

    # from carthesian to spherical coordinates
    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    phi = np.arctan2(y, x)
    theta = np.arccos(z / r)
    v_sph = np.array([r, phi, theta])

    return v_sph

def Sph_cart(psi):
    r, phi, theta = psi
    x = r*np.cos(phi)*np.sin(theta)
    y = r*np.sin(phi)*np.sin(theta)
    z = r*np.cos(theta)
    return np.array([x,y,z])


def inn_momenta(S_c, S_sph, Cst_f, inn_p_f, Par):
    # input: S_c: 3D matrix as an output of "screen_cart",
    #        S_sph: 3D matrix with Sph. coord. on first row and then a 2D matrix
    #               within that containing value for that coordinate
    #        Cst_f: function that calculates constant of motion
    #        inn_p_f: function that calculates inn. momenta
    # output: p: 3D matrix with coordinates in impulse space on first row and
    #         then a 2D matrix within that with the value for each ray,
    #         Cst: list of cst of motion containing the value for each ray in 2D matrix

    r, phi, theta = S_sph
    M, rho, a = Par
    Sh = S_sph[0].shape
    S_n = S_c/r.reshape(tuple(list(Sh) + [1])) # normalize direction light rays
    S_n = np.transpose(S_n, tuple(np.roll(np.arange(len(Sh)+1), 1))) # start array in terms of coordinates
    p = inn_p_f(S_n, S_sph, Par) # calculate initial momenta, coords still on first row matrix
    Cst = Cst_f(p, S_sph) # calculate constant of motions

    return [p, Cst]


def Cst_DNeg(p, q):
    # input: p: matrix with coordinates in momentum space on first row,
    #        q: matrix with coordinates in configuration space on first row ,
    # output: list of cst of motion containing the value for each ray in 2D matrix

    p_l, p_phi, p_th = p
    l, phi, theta = q

    # defining the constants of motion
    b = p_phi
    B_2 = p_th**2 + p_phi**2/np.sin(theta)**2
    Cst = np.array([b, B_2])

    return Cst


def inn_mom_DNeg(S_n, q, Par):
    # input: S_c: 3D matrix as earlier defined the in output of "screen_cart", from which
    #             we can calculate S_n
    #        S_sph: 3D matrix with Sph. coord. on first row and then a 2D matrix
    #               within that containing value for that coordinate,
    # output: 3D matrix with coordinates in impulse space on first row and then
    #         a 2D matrix within that with the value for each ray

    l, phi, theta = q
    M, rho, a = Par

    # defining r(l)
    r = dneg_r(l, M, rho, a)

    # defining the momenta
    p_l = -S_n[0]
    p_phi = -r*np.sin(theta)*S_n[1]
    p_th = r*S_n[2]
    p = np.array([p_l, p_phi, p_th])

    return p


def Simulate_DNeg(integrator, Par, h, N, q0, Nz = 14**2, Ny = 14**2, Gr_D = '2D', mode = False, Grid_constr_3D = None, Rad = False):
    #input: function that integrates(p(t), q(t)) to (p(t + h), q(t + h))
    #       h: stepsize
    #       N amount of steps
    #       Ni pixels
    #       q0: initial position
    #       mode: enables data collection
    #output: motion: 5D matrix the elements being [p, q] p, q being 3D matrices
    #        output: 2D boolean array

    if Rad == False:
        S_c = screen_cart(Nz, Ny, 1, 1)
        S_cT = np.transpose(S_c, (2,0,1))
    else:
        end = int(np.ceil(np.sqrt(Ny**2+Nz**2)))
        S_c = screen_cart(end, end)
        S_c = S_c[ int(end/2) - 1, int(end/2 - 1):end, :]
        S_cT = S_c.T
        
    Sh = S_cT[0].shape 
    q = np.transpose(np.tile(q0, tuple(list(Sh) + [1])), tuple(np.roll(np.arange(len(Sh)+1), 1))) + h*0.001
    p, Cst = inn_momenta(S_c, q, Cst_DNeg, inn_mom_DNeg, Par)
    if N <= 1000:
        M = N
    else:
        M = 1000
        
    Motion = np.empty(tuple([M,2,3] + list(Sh)), dtype=np.float32)
    Motion[0] = [p, q]
    CM_0 = np.array(DNeg_CM(p, q , Par))
    CM = np.empty(tuple([M]+list(CM_0.shape)), dtype=np.float32)
    CM[0] = CM_0
    Grid = np.zeros((Nz, Ny), dtype=bool)
    
    Sh = tuple([3,6]+list(p[0].shape))
    n = len(Sh)
    P = np.zeros(Sh)
    Q = np.zeros(Sh)
    P[:,0] = p
    Q[:,0] = q
    r = np.empty(q[0].shape)
    dr = np.empty(q[0].shape)
    d2r = np.empty(q[0].shape)
    S = np.arange(n)
    S[0:2] = [1,0]
    S = tuple(S)
    h_vect = h**np.arange(6).reshape(tuple([6] + [1]*(n-1)))

    start = time.time()
    Time = np.empty(N-1)
    # Integration
    m = 0
    for i in tqdm(range(N-1)):
        p, q , CM_i, Time[i] = integrator(p, q, Cst, h_vect, Par, P, Q, r, dr, d2r, S)
        if mode == True:
            if N<= 1000:
                Motion[i+1] = [p, q]
                CM[i+1] =  CM_i
            else:
                if np.mod(i+1, N/1000) == 0:
                    m += 1
                    Motion[m] = [p, q]
                    CM[m] =  CM_i
        if Gr_D == '3D':
            # change parameters grid here
            Grid = Grid_constr_3D(q, 9, 12, 0.012, Grid)

    if mode == True:
        CM[-1] = DNeg_CM(p, q, Par)
    Motion[-1] = [p, q]
    end = time.time()
    print(end - start)
    print("Time spent:" + str(np.sum(Time)))
    return Motion, Grid, CM




def diff_equations(t, variables):
    """
    Defines the differential equations of the wormhole metric
    """
    l, phi, theta, p_l, p_phi, p_th, M, rho, a, b, B = variables
    r = dneg_r(l, M, rho, a)
    rec_r = 1/r
    rec_r_2 = rec_r**2
    rec_r_3 = rec_r_2*rec_r
    rec_sin1 = 1/np.sin(theta)
    cos1 = np.cos(theta)
    rec_sin2 = rec_sin1**2
    rec_sin3 = rec_sin1*rec_sin2
    B = p_th**2 + p_phi**2 * rec_sin2
    b = p_phi

    # Using the hamiltonian equations of motion
    dl_dt       = p_l
    dtheta_dt   = p_th * rec_r_2

    dphi_dt     = b * rec_sin2 * rec_r_2
    dpl_dt      = B * (dneg_dr_dl(l, M, a)) * rec_r_3
    dpth_dt     = b ** 2 * cos1 * rec_sin3 * rec_r_2

    diffeq = [-dl_dt, -dphi_dt, -dtheta_dt, -dpl_dt, np.zeros(dl_dt.shape), -dpth_dt, 0, 0, 0, 0, 0]
    return diffeq



def simulate_radius(t_end, Par, q0, h, Nz = 14**2, Ny = 14**2, methode = 'BDF', mode = False):
    """
    Solves the differential equations using a build in solver (solve_ivp) with
    specified method.
    Input:  - t_end: endtime of the Integration
            - Par: wormhole parameters
            - q0: position of the camera
            - Nz: number of vertical pixels
            - Ny: number of horizontal pixels
            - methode: method used for solving the ivp (standerd runge-kutta of fourth order)
            - h: absolute tolerance / min stepsize

    Output: - endmom: matrix with the momenta of the solution
            - endpos: matrix with the positions of the solution
    """
    print('Initializing screen and calculating initial condition...')
    # Reads out data and calculates parameters
    M, rho, a = Par
    q1, q2, q3 = q0
    end = int(np.ceil(np.sqrt(Ny**2+Nz**2)))
    S_c = screen_cart(end, end) 
    S_cT = S_c.T
    Sh = S_cT[0].shape 
    q_v = np.transpose(np.tile(q0, tuple(list(Sh) + [1])), tuple(np.roll(np.arange(len(Sh)+1), 1))) + h*0.001
    p, Cst = inn_momenta(S_c, q_v, Cst_DNeg, inn_mom_DNeg, Par)
    p1, p2, p3 = p
    if mode == True:
        T = 1000
        data = np.linspace(0, -t_end, T)
    else:
        T = 1
        data = [-t_end]
    Motion = np.empty((len(p1[0]) - int(len(p1[0])/2 - 1), 6, T))
    #Define height of the ray
    teller1 = int(len(p1)/2) - 1
    #Loop over half of the screen
    print('Integrating ray...')
    nstep = []
    for teller2 in tqdm(range(int(len(p1[0])/2 - 1), len(p1[0]))):
        initial_values = np.array([q1, q2, q3, p1[teller1][teller2], p2[teller1][teller2], p3[teller1][teller2], M, rho, a, Cst[0,teller1,teller2], Cst[1,teller1,teller2]])
        # Integrate to the solution
        i = teller2 - int(len(p1[0])/2 - 1)
        sol = integr.solve_ivp(diff_equations, [0, -t_end], initial_values, method = methode, t_eval=data, rtol=h**(1/2), atol=h)
        Motion[i] = sol.y[:6]
        nstep.append(sol.nfev)
    print(np.amax(Motion[:,1]))
    Motion[:,1] = np.mod(Motion[:,1], 2*np.pi)
    Motion[:,2] = np.mod(Motion[:,2], np.pi)
    avstep = sum(nstep)/len(nstep)
    print('radius saved!')
    print(f'Average number of steps is: {avstep}.')
    return Motion[:, 3:], Motion[:, :3]


def simulate_raytracer(tijd = 100, Par = [0.43/1.42953, 1, 0.48], q0 = [6.68, np.pi, np.pi/2], Nz = 14**2, Ny = 14**2, methode = 'RK45'):
    """
    Solves the differential equations using a build in solver (solve_ivp) with
    specified method.
    Input:  - t_end: endtime of the Integration
            - Par: wormhole parameters
            - q0: position of the camera
            - Nz: number of vertical pixels
            - Ny: number of horizontal pixels
            - methode: method used for solving the ivp (standerd runge-kutta of fourth order)

    Output: - endmom: matrix with the momenta of the solution
            - endpos: matrix with the positions of the solution
    """
    print('Initializing screen and calculating initial condition...')

    # end = int(np.ceil(np.sqrt(Ny**2+Nz**2)))
    M, rho, a = Par

    # Reading out values and determining parameters
    S_c = screen_cart(Nz, Ny)
    S_cT = np.transpose(S_c, (2,0,1))
    Sh = S_cT[0].shape 
    q_v = np.transpose(np.tile(q0, tuple(list(Sh) + [1])), tuple(np.roll(np.arange(len(Sh)+1), 1))) + 0.00001
    p, Cst = inn_momenta(S_c, q_v, Cst_DNeg, inn_mom_DNeg, Par)
    p1, p2, p3 = p
    q1, q2, q3 = q0
    endpos = []
    endmom = []

    # Looping over all momenta
    for teller1 in tqdm(range(0, len(p1))):
        row_pos = []
        row_mom = []
        start_it = time.time()
        for teller2 in range(0, len(p1[0])):

            start_it = time.time()
            initial_values = np.array([q1, q2, q3, p1[teller1][teller2], p2[teller1][teller2], p3[teller1][teller2], M, rho, a, Cst[0,teller1,teller2], Cst[1,teller1,teller2]])
            # Integrates to the solution
            sol = integr.solve_ivp(diff_equations, [tijd, 0], initial_values, method = methode, t_eval=[0])
            #Reads out the data from the solution
            l_end       = sol.y[0][-1]
            phi_end     = sol.y[1][-1]

            # Correcting for phi and theta values out of bounds
            while phi_end>2*np.pi:
                phi_end = phi_end - 2*np.pi
            while phi_end<0:
                phi_end = phi_end + 2*np.pi

            theta_end   = sol.y[2][-1]
            while theta_end > np.pi:
                theta_end = theta_end - np.pi
            while theta_end < 0:
                theta_end = theta_end + np.pi

            pl_end      = sol.y[3][-1]
            pphi_end    = sol.y[4][-1]
            ptheta_end  = sol.y[5][-1]
            # adds local solution to row
            row_pos.append(np.array([l_end, phi_end, theta_end]))
            row_mom.append(np.array([pl_end, pphi_end, ptheta_end]))

        # adds row to matrix
        endpos.append(np.array(row_pos))
        endmom.append(np.array(row_mom))
        end_it = time.time()
        duration = end_it - start_it
        # print('Iteration ' + str((teller1, teller2)) + ' completed in ' + str(duration) + 's.')
    return np.array(endmom), np.array(endpos)


def simulate_raytracer_fullpath(t_end, Par, q0, N, Nz = 14**2, Ny = 14**2, methode = 'RK45', mode = False):
    """
    Solves the differential equations using a build in solver (solve_ivp) with
    specified method.
    Input:  - t_end: endtime of the Integration
            - Par: wormhole parameters
            - q0: position of the camera
            - Nz: number of vertical pixels
            - Ny: number of horizontal pixels
            - methode: method used for solving the ivp (standerd runge-kutta of fourth order)
            - mode enables data collection (Energy)

    Output: - Motion: Usual 5D matrix
    """
    print('Initializing screen and calculating initial condition...')

    # end = int(np.ceil(np.sqrt(Ny**2+Nz**2)))
    M, rho, a = Par

    # Reading out values and determining parameters
    S_c = screen_cart(Nz, Ny, 1, 1)
    S_cT = np.transpose(S_c, (2,0,1))
    Sh = S_cT[0].shape 
    q_v = np.transpose(np.tile(q0, tuple(list(Sh) + [1])), tuple(np.roll(np.arange(len(Sh)+1), 1))) + 0.00001
    p, Cst = inn_momenta(S_c, q_v, Cst_DNeg, inn_mom_DNeg, Par)
    p1, p2, p3 = p
    q1, q2, q3 = q0
    endpos = []
    endmom = []

    Time = np.empty(p1.shape)
    # Looping over all momenta
    for teller1 in tqdm(range(0, len(p1))):
        row_pos = []
        row_mom = []
        start_it = time.time()
        for teller2 in range(0, len(p1[0])):
  
            initial_values = np.array([q1, q2, q3, p1[teller1][teller2], p2[teller1][teller2], p3[teller1][teller2], M, rho, a, Cst[0,teller1,teller2], Cst[1,teller1,teller2]])
            # Integrates to the solution
            start_it = time.time()
            sol = integr.solve_ivp(diff_equations, [t_end, 0], initial_values, method = methode, t_eval=np.flip(np.arange(0, t_end, t_end/N)))
            end_it = time.time()
            Time[teller1,teller2] = end_it - start_it
            #Reads out the data from the solution
            l_end       = sol.y[0]
            phi_end     = sol.y[1]
            # Correcting for phi and theta values out of bounds
            phi_end = np.mod(phi_end, 2*np.pi)
            theta_end   = sol.y[2]
            theta_end = np.mod(theta_end, np.pi)
            pl_end      = sol.y[3]
            pphi_end    = sol.y[4]
            ptheta_end  = sol.y[5]
            # adds local solution to row
            row_pos.append(np.array([l_end, phi_end, theta_end]))
            row_mom.append(np.array([pl_end, pphi_end, ptheta_end]))

        # adds row to matrix
        endpos.append(np.array(row_pos))
        endmom.append(np.array(row_mom))
        
        # print('Iteration ' + str((teller1, teller2)) + ' completed in ' + str(duration) + 's.')
    print("Time spent:" + str(np.sum(Time)))
    Motion = np.transpose(np.array([endmom, endpos]), (4,0,3,1,2)) #output same shape as sympl. intgr.
    if mode == False:
        return Motion
    else:
        print("calculating constants of motion")
        CM = np.array([DNeg_CM(Motion[k,0], Motion[k,1], Par) for k in range(len(Motion))])
        return Motion , CM


def rotate_ray(ray, Nz, Ny):
    """
    The function assumes a 'horizontal' ray for theta = pi/2 and phi: pi to 2pi
    with position values and returns a full 2D picture of the wormhole.
    Inputs: - ray: the calculated 1D line
            - Nz: vertical number of pixels
            - Ny: horizontal number of pixels
    Output: - pic: a 5D array with the pixels and their l, phi, theta
    """
    # Make list of point with position relative to center of the matrix
    Mz = np.arange(-Nz/2, Nz/2, 1)
    My = np.arange(-Ny/2, Ny/2, 1)
    # Make the matrix to fill with the parameter values
    pic = np.zeros((Nz, Ny, 3))
    # print(pic.shape)

    # Loop over every element (pixel) of the matrix (picture)
    for i in tqdm(range(0, len(Mz))):
        height = Mz[i]
        for width in My:
            # Determine distance from the center
            r = int(round(np.sqrt(width**2 + height**2)))
            # Correcting for endvalue
            if r == len(ray):
                r = r-1

            # Carthesian coordinates of the gridpoint relative to upper left corner
            z = int(-height + Nz/2) - 1
            y = int(width + Ny/2) - 1
            # Get the corresponding values from the calculated ray
            l, phi, theta = ray[r]

            #Flip screen when left side
            if width < 0:
                phi = 2*np.pi - phi
            #Adjust theta relative to the upper side of the screen
            theta = z*(np.pi/Nz)

            # Correct when theta of phi value gets out of bound
            while phi>2*np.pi:
                phi = phi - 2*np.pi
            while phi<0:
                phi = phi + 2*np.pi
            while theta > np.pi:
                theta = theta - np.pi
            while theta < 0:
                theta = theta + np.pi
            loc = np.array([l, phi, theta])
            pic[z][y] = loc

    return pic


def carth_polar(y, z):
    """
    Turns Carthesian coordinates to polar coordinates
    """

    return np.sqrt(y*y + z*z), np.arctan2(z,y)


def rotation_qubits(ray, Nz, Ny):
    """
    The function assumes a 'horizontal' ray for theta = pi/2 and phi: pi to 2pi.
    Rotation is of the 'horizontal' ray is done with qubit method.
    Inputs: - ray: the calculated 1D line
            - Nz: vertical number of pixels
            - Ny: horizontal number of pixels
    Output: - pic: a 3D array with the pixels and their l, phi, theta
    """

    # Make list of point with position relative to center of the matrix
    Mz = np.arange(-Nz/2, Nz/2, 1, dtype=int)
    My = np.arange(-Ny/2, Ny/2, 1, dtype=int)

    # Make the matrix to fill with the parameter values
    pic = np.zeros((Nz, Ny, 3))

    # Loop over every element (pixel) of the matrix (picture)
    for i in tqdm(range(0, len(Mz))):
        height = Mz[i]
        for width in My:

            # Find the coordinates in polar coordinates
            radius, alpha = carth_polar(width, height)

            r = int(floor(radius))

            # Carthesian coordinates of the gridpoint relative to upper left corner
            z = int(-height + Nz/2) - 1
            y = int(width + Ny/2) - 1

            # Get the corresponding values from the calculated ray
            l, phi, theta = ray[r]

            # Initializing qubit for rotation
            psi = np.array([np.cos(theta/2), np.exp(phi*1j)*np.sin(theta/2)])

            # Rotationmatrix (rotation axis is x-axis)
            R_x = np.array([np.array([np.cos(alpha/2), -1j*np.sin(alpha/2)]), np.array([-1j*np.sin(alpha/2), np.cos(alpha/2)])])
            rot_psi = np.matmul(psi, R_x) # Matrix multiplication

            # Find rotated phi and theta
            z_0, z_1 = rot_psi

            rot_theta = 2*np.arctan2(np.absolute(z_1),np.absolute(z_0))
            rot_phi   = np.angle(z_1) - np.angle(z_0)

            loc = np.array([l, rot_phi, rot_theta])

            pic[z][y] = loc

    return pic


def sum_subd(A):
    # A 2D/1D matrix such that the lengt of sides have int squares
    Sh = A.shape
    if len(Sh) > 1:
        Ny, Nz =  Sh
        Ny_s = int(np.sqrt(Ny))
        Nz_s = int(np.sqrt(Nz))
        B = np.zeros((Ny_s, Nz_s))
        for i in range(Ny_s):
            for j in range(Nz_s):
                B[i,j] = np.sum(A[Ny_s*i:Ny_s*(i+1), Nz_s*j:Nz_s*(j+1)])
    else:
        N = Sh
        N_s = int(np.sqrt(N))
        B = np.zeros(N_s)
        for i in range(N_s):
            B[i] = np.sum(A[N_s*i:N_s*(i+1)])
    return B



def DNeg_CM(p, q , Par):
    #input: p, q  3D matrices as defined earlier
    #output: 1D matrix, constants of Motion defined in each timestep
    M, rho, a = Par

    p_l, p_phi, p_th = p
    l, phi, theta = q

    # defining r(l):
    r = dneg_r(l, M, rho, a)

    rec_r = 1/r
    rec_r_2 = rec_r**2
    sin1 = np.sin(theta)
    sin2 = sin1**2
    rec_sin2 = 1/sin2

    # defining hamiltonian
    H1 = p_l**2
    H2 = p_th**2*rec_r_2
    H3 = p_phi**2*rec_sin2*rec_r_2

    H = 0.5*sum_subd(H1 + H2 + H3)
    B2_C = sum_subd(p_th**2 + p_phi**2*rec_sin2)
    b_C = sum_subd(p_phi)

    return [H, b_C, B2_C]



def wormhole_with_symmetry(t_end=200, q0 = [7.25, np.pi, np.pi/2], Nz=1024, Ny=2048, Par=[0.05/1.42953, 1, 1], h = 10**-10, choice=True, mode=False):

    """
    One function to calculate the ray and rotate it to a full picture with the
    given parameters (used to easily run the symmetry code in other files)
    Input:  - time: initial time (backwards integration thus end time)
            - initialcond: initial conditions which take the form [l, phi, theta]
            - Nz: vertical number of pixels
            - Ny: horizontal number of pixels
            - Par: wormhole parameters [M, rho, a]
            - h: stepsize (for selfmade)
            - choice: switch build in / selfmade
            - mode enables data collection (Energy)
    Output: - picture: a 2D matrix containing the [l, phi, theta] value of the endpoint of each pixel
    """

    start = time.time()
    if choice == True:
        sol = simulate_radius(t_end, Par, q0, h, Nz, Ny, methode = 'RK45', mode = mode)
        momenta, position = sol
        if mode == True:
            print("calculating constants of motion")
            CM = np.array([DNeg_CM(momenta[:,:,i].T, position[:,:,i].T , Par) for i in range(len(momenta[0,0]))])
        position = position[:,:,-1]
    else:
        sol = Simulate_DNeg(Smpl.Sympl_DNeg, Par, h, int(t_end/h), q0, Nz, Ny, '2D', mode, wg.Grid_constr_3D_Sph, True)
        momenta, position = sol[0][-1]
        if mode == True:
            CM = sol[2]
        position = position.T
    end = time.time()
    print('Tijdsduur = ' + str(end-start))

    print('Rotating ray...')
    picture = rotation_qubits(position, Nz, Ny)
    print('Ray rotated!')
    if mode == True:
        return picture, CM
    else:
        return picture
