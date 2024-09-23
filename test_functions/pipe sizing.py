import numpy as np
import math
from scipy.optimize import fsolve,leastsq

Qmax=500000
T=50
dT=60
dp=400
epsilon=0.000045
rho=988
cp=4180

kin_viscosity = 1/((0.1*(273.15+T)**2-34.335*(273.15+T)+2472)*rho)
print(kin_viscosity)

Re=100000



def myFunction(z,rho,Re):
    f = z[0]
    di= z[1]
    vel= z[2]

    F = np.empty((3))
    F[0] = 1.14+2*math.log(di/epsilon,10)-2*math.log(1+9.3/((Re) * epsilon/di*f**0.5),10) - 1/f**0.5
    F[1] = (16*f/(math.pi**2*rho*cp**2*dp))**0.2*(Qmax/dT)**0.4 - di
    F[2] = 4* Qmax / (math.pi*di**2*rho*cp*dT) - vel  

    return F

zGuess = np.array([0.02,0.075,2])
#zGuess = np.array([0.0016,0.075,2.5])
#z = fsolve(lambda zGuess: myFunction(zGuess,rho),zGuess)
Re_old=0
while abs(Re-Re_old)>100:
    z = fsolve(lambda zGuess: myFunction(zGuess,rho,Re),zGuess)
    Re_old=Re
    Re=z[2]*z[1]/kin_viscosity
    
print(abs(Re-Re_old))
print(z)













