
import numpy as np

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

def sum_subd(A):
    # A 2D matrix such that the lengt of sides have int squares
    Ny, Nz =  A.shape
    Ny_s = int(np.sqrt(Ny))
    Nz_s = int(np.sqrt(Nz))
    B = np.zeros((Ny_s, Nz_s))
    for i in range(Ny_s):
        for j in range(Nz_s):
            B[i,j] = np.sum(A[Ny_s*i:Ny_s*(i+1), Nz_s*j:Nz_s*(j+1)])
    return B

def runge_kutta(p, q, Cst, h, Par):
    """
    Input:  takes the momentum matrix p, the position matrix q, the constants of motion Cst
            and the step length h.
    Output: [p, q] list of the updated momenta and position matrices after one step length h.
    """
    M, rho, a = Par
    p_l, p_phi, p_th = p
    l, phi, theta = q
    b, B = Cst

    r = dneg_r(l, M, rho, a)
    rec_r = 1/r
    rec_r_2 = rec_r**2
    rec_r_3 = rec_r_2*rec_r
    sin1 = np.sin(theta)
    cos1 = np.cos(theta)
    sin2 = sin1**2
    sin3 = sin1*sin2
    H1 = p_l**2
    H2 = p_th**2*rec_r_2
    H3 = p_phi**2/sin2*rec_r_2
    H = 0.5*sum_subd((H1 + H2 + H3))
    B2_C = sum_subd(p_th**2 + p_phi**2/sin2)
    b_C = sum_subd(p_phi)

    #Using the hamiltonian equations of motion
    dl_dt       = p_l
    dtheta_dt   = p_th * rec_r_2
    dphi_dt     = b / sin2 * rec_r_2
    dpl_dt      = B**2 * (dneg_dr_dl(l, M, a)) * rec_r_3
    dpth_dt     = b ** 2 * cos1 / sin3 * rec_r_2

    #defines k1
    k1 = [dl_dt, dphi_dt, dtheta_dt, dpl_dt, np.zeros(dl_dt.shape), dpth_dt]

    # Updating values
    l   = l + h * k1[0] / 2
    theta = theta + h * k1[1] / 2
    phi = phi + h * k1[2] / 2
    p_l = p_l + h * k1[3] / 2
    p_th = p_th + h * k1[4] / 2
    # print(l)

    #Defining k2
    r = dneg_r(l, M, rho, a)
    dl_dt       = p_l
    dtheta_dt   = p_th / r**2
    dphi_dt     = b / (r**2 * np.sin(theta)**2)
    dpl_dt      = B**2 * (dneg_dr_dl(l, M, a)) / r**3
    dpth_dt     = b ** 2 * np.cos(theta) / (r ** 2 * np.sin(theta)**3)

    k2 = [dl_dt, dphi_dt, dtheta_dt, dpl_dt, np.zeros(dl_dt.shape), dpth_dt]
    # Updating values
    l   = l + h * k2[0] / 2
    theta = theta + h * k2[1] / 2
    phi = phi + h * k2[2] / 2
    p_l = p_l + h * k2[3] / 2
    p_th = p_th + h * k2[4] / 2

    # Defining k3
    r = dneg_r(l, M, rho, a)
    dl_dt       = p_l
    dtheta_dt   = p_th / r**2
    dphi_dt     = b / (r**2 * np.sin(theta)**2)
    dpl_dt      = B**2 * (dneg_dr_dl(l, M, a)) / r**3
    dpth_dt     = b ** 2 * np.cos(theta) / (r ** 2 * np.sin(theta)**3)

    k3 = [dl_dt, dphi_dt,dtheta_dt, dpl_dt, np.zeros(dl_dt.shape),  dpth_dt]

    # Updating values
    l   = l + h * k3[0]
    theta = theta + h * k3[1]
    phi = phi + h * k3[2]
    p_l = p_l + h * k3[3]
    p_th = p_th + h * k3[4]

    #Defining k4
    r = dneg_r(l, M, rho, a)
    dl_dt       = p_l
    dtheta_dt   = p_th / r**2
    dphi_dt     = b / (r**2 * np.sin(theta)**2)
    dpl_dt      = B**2 * (dneg_dr_dl(l, M, a)) / r**3
    dpth_dt     = b ** 2 * np.cos(theta) / (r ** 2 * np.sin(theta)**3)

    k4 = [dl_dt, dphi_dt, dtheta_dt, dpl_dt, np.zeros(dl_dt.shape), dpth_dt]

    # Updating matrices of position and momenta
    p = p + np.multiply(k1[3:],(h/6)) + np.multiply(k2[3:],(h/3)) + np.multiply(k3[3:],(h/3)) + np.multiply(k4[3:],(h/6))
    q = q + np.multiply(k1[:3],(h/6)) + np.multiply(k2[:3],(h/3)) + np.multiply(k3[:3],(h/3)) + np.multiply(k4[:3],(h/6))

    return [p, q, [H, b_C, B2_C]]