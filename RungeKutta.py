
import numpy as np

def dneg_r(y, M=0.43/1.42953 , p=1, a=0):
    # input: scalar, output: scalar
    # define r(l) for a DNeg wormhole without gravity
    x = 2*(np.abs(y) - a)/(np.pi*M)
    r = p + M*(x*np.arctan(x) - 0.5*np.log(1 + x**2))
    return r

def dneg_dr_dl(y, M=0.43/1.42953):
    # input:scalar , output: scalar
    # define derivative of r to l
    x = 2*np.abs(y)/(np.pi*M)
    dr_dl = 2/np.pi*np.arctan(x)
    return dr_dl

def runge_kutta(p, q, Cst, h):
    """
    Input:  takes the momentum matrix p, the position matrix q, the constants of motion Cst
            and the step length h.
    Output: [p, q] list of the updated momenta and position matrices after one step length h.
    """
    p_l, p_phi, p_th = p
    l, phi, theta = q
    b, B = Cst

    r = dneg_r(l)
    #Using the hamiltonian equations of motion
    dl_dt       = p_l
    dtheta_dt   = p_th / r**2
    dphi_dt     = b / (r**2 * np.sin(theta)**2)
    dpl_dt      = B**2 * (dneg_dr_dl(l)) / r**3
    dpth_dt     = b ** 2 * np.cos(theta) / (r ** 2 * np.sin(theta)**2)
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
    r = dneg_r(l)
    dl_dt       = p_l
    dtheta_dt   = p_th / r**2
    dphi_dt     = b / (r**2 * np.sin(theta)**2)
    dpl_dt      = B**2 * (dneg_dr_dl(l)) / r**3
    dpth_dt     = b ** 2 * np.cos(theta) / (r ** 2 * np.sin(theta)**2)

    k2 = [dl_dt, dphi_dt, dtheta_dt, dpl_dt, np.zeros(dl_dt.shape), dpth_dt]
    # Updating values
    l   = l + h * k2[0] / 2
    theta = theta + h * k2[1] / 2
    phi = phi + h * k2[2] / 2
    p_l = p_l + h * k2[3] / 2
    p_th = p_th + h * k2[4] / 2

    # Defining k3
    r = dneg_r(l)
    dl_dt       = p_l
    dtheta_dt   = p_th / r**2
    dphi_dt     = b / (r**2 * np.sin(theta)**2)
    dpl_dt      = B**2 * (dneg_dr_dl(l)) / r**3
    dpth_dt     = b ** 2 * np.cos(theta) / (r ** 2 * np.sin(theta)**2)

    k3 = [dl_dt, dphi_dt,dtheta_dt, dpl_dt, np.zeros(dl_dt.shape),  dpth_dt]
    # Updating values
    l   = l + h * k3[0]
    theta = theta + h * k3[1]
    phi = phi + h * k3[2]
    p_l = p_l + h * k3[3]
    p_th = p_th + h * k3[4]
    #Defining k4
    dl_dt       = p_l
    dtheta_dt   = p_th / r**2
    dphi_dt     = b / (r**2 * np.sin(theta)**2)
    dpl_dt      = B**2 * (dneg_dr_dl(l)) / r**3
    dpth_dt     = b ** 2 * np.cos(theta) / (r ** 2 * np.sin(theta)**2)

    k4 = [dl_dt, dphi_dt, dtheta_dt, dpl_dt, np.zeros(dl_dt.shape), dpth_dt]
    # Updating matrices of position and momenta
    p = p + np.multiply(k1[3:],(h/6)) + np.multiply(k2[3:],(h/3)) + np.multiply(k3[3:],(h/3)) + np.multiply(k4[3:],(h/6))
    q = q + np.multiply(k1[:3],(h/6)) + np.multiply(k2[:3],(h/3)) + np.multiply(k3[:3],(h/3)) + np.multiply(k4[:3],(h/6))

    return [p, q]
