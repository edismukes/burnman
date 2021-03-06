# BurnMan - a lower mantle toolkit
# Copyright (C) 2012, 2013, Heister, T., Unterborn, C., Rose, I. and Cottaar, S.
# Released under GPL v2 or later.

import numpy as np
import scipy.optimize as opt
import warnings

import birch_murnaghan as bm
import burnman.debye as debye
import equation_of_state as eos

class SLBBase(eos.EquationOfState):
    """
    Base class for the finite strain-Mie-Grueneiesen-Debye equation of state detailed
    in :cite:`Stixrude2005`.  For the most part the equations are
    all third order in strain, but see further the :class:`burnman.slb.SLB2` and 
    :class:`burnman.slb.SLB3` classes.
    """

    def __debye_temperature(self,x,params):
        """
        Finite strain approximation for Debye Temperature [K]
        x = ref_vol/vol
        """
        f = 1./2. * (pow(x, 2./3.) - 1.)
        a1_ii = 6. * params['grueneisen_0'] # EQ 47
        a2_iikk = -12.*params['grueneisen_0']+36.*pow(params['grueneisen_0'],2.) - 18.*params['q_0']*params['grueneisen_0'] # EQ 47
        return params['Debye_0'] * np.sqrt(1. + a1_ii * f + 1./2. * a2_iikk*f*f)

    def volume_dependent_q(self, x, params):
        """
        Finite strain approximation for :math:`q`, the isotropic volume strain
        derivative of the grueneisen parameter.
        """
        f = 1./2. * (pow(x, 2./3.) - 1.)
        a1_ii = 6. * params['grueneisen_0'] # EQ 47
        a2_iikk = -12.*params['grueneisen_0']+36.*pow(params['grueneisen_0'],2.) - 18.*params['q_0']*params['grueneisen_0'] # EQ 47
        nu_o_nu0_sq = 1.+ a1_ii*f + (1./2.)*a2_iikk * f*f # EQ 41
        gr = 1./6./nu_o_nu0_sq * (2.*f+1.) * ( a1_ii + a2_iikk*f )
        q = 1./9.*(18.*gr - 6. - 1./2. / nu_o_nu0_sq * (2.*f+1.)*(2.*f+1.)*a2_iikk/gr)
        return q

    def __isotropic_eta_s(self, x, params):
        """
        Finite strain approximation for :math:`eta_{s0}`, the isotropic shear
        strain derivative of the grueneisen parameter.
        """
        f = 1./2. * (pow(x, 2./3.) - 1.)
        a2_s = -2.*params['grueneisen_0'] - 2.*params['eta_s_0'] # EQ 47
        a1_ii = 6. * params['grueneisen_0'] # EQ 47
        a2_iikk = -12.*params['grueneisen_0']+36.*pow(params['grueneisen_0'],2.) - 18.*params['q_0']*params['grueneisen_0'] # EQ 47
        nu_o_nu0_sq = 1.+ a1_ii*f + (1./2.)*a2_iikk * pow(f,2.) # EQ 41
        gr = 1./6./nu_o_nu0_sq * (2.*f+1.) * ( a1_ii + a2_iikk*f )
        eta_s = - gr - (1./2. * pow(nu_o_nu0_sq,-1.) * pow((2.*f)+1.,2.)*a2_s) # EQ 46 NOTE the typo from Stixrude 2005
        return eta_s

    def pressure(self, temperature, volume, params):
        return bm.birch_murnaghan(params['V_0']/volume, params) + \
                self.__thermal_pressure(temperature,volume, params) - \
                self.__thermal_pressure(300.,volume, params)

    #calculate isotropic thermal pressure, see
    # Matas et. al. (2007) eq B4
    def __thermal_pressure(self,T,V, params):
        Debye_T = self.__debye_temperature(params['V_0']/V, params)
        gr = self.grueneisen_parameter(0., T, V, params) # P not important
        P_th = gr * debye.thermal_energy(T,Debye_T, params['n'])/V
        return P_th

    def volume(self, pressure, temperature, params):
        """
        Returns molar volume. :math:`[m^3]`
        """
        T_0 = self.reference_temperature( params )
        debye_T = lambda x : self.__debye_temperature(params['V_0']/x, params)
        gr = lambda x : self.grueneisen_parameter(pressure, temperature, x, params)
        E_th =  lambda x : debye.thermal_energy(temperature, debye_T(x), params['n']) #thermal energy at temperature T
        E_th_ref = lambda x : debye.thermal_energy(T_0, debye_T(x), params['n']) #thermal energy at reference temperature

        b_iikk= 9.*params['K_0'] # EQ 28
        b_iikkmm= 27.*params['K_0']*(params['Kprime_0']-4.) # EQ 29
        f = lambda x: 0.5*(pow(params['V_0']/x,2./3.)-1.) # EQ 24
        func = lambda x: (1./3.)*(pow(1.+2.*f(x),5./2.))*((b_iikk*f(x)) \
            +(0.5*b_iikkmm*pow(f(x),2.))) + gr(x)*(E_th(x) - E_th_ref(x))/x - pressure #EQ 21

        # we need to have a sign change in [a,b] to find a zero. Let us start with a
        # conservative guess:
        a = 0.6*params['V_0']
        b = 1.2*params['V_0']

        # if we have a sign change, we are done:
        if func(a)*func(b)<0:
            return opt.brentq(func, a, b)
        else:
            tol = 0.0001
            sol = opt.fmin(lambda x : func(x)*func(x), 1.0*params['V_0'], ftol=tol, full_output=1, disp=0)
            if sol[1] > tol*2:
                raise ValueError('Cannot find volume, likely outside of the range of validity for EOS')
            else:
                warnings.warn("May be outside the range of validity for EOS")
                return sol[0]

    def pressure( self, temperature, volume, params):
        """
        Returns the pressure of the mineral at a given temperature and volume [Pa]
        """
        debye_T = self.__debye_temperature(params['V_0']/volume, params)
        gr = self.grueneisen_parameter(0.0, temperature, volume, params) #does not depend on pressure
        E_th = debye.thermal_energy(temperature, debye_T, params['n'])
        E_th_ref = debye.thermal_energy(300., debye_T, params['n']) #thermal energy at reference temperature

        b_iikk= 9.*params['K_0'] # EQ 28
        b_iikkmm= 27.*params['K_0']*(params['Kprime_0']-4.) # EQ 29
        f = 0.5*(pow(params['V_0']/volume,2./3.)-1.) # EQ 24
        P = (1./3.)*(pow(1.+2.*f,5./2.))*((b_iikk*f) \
            +(0.5*b_iikkmm*pow(f,2.))) + gr*(E_th - E_th_ref)/volume #EQ 21

        return P

    def grueneisen_parameter(self, pressure, temperature, volume, params):
        """
        Returns grueneisen parameter :math:`[unitless]` 
        """
        x = params['V_0'] / volume
        f = 1./2. * (pow(x, 2./3.) - 1.)
        gruen_0 = params['grueneisen_0']
        a1_ii = 6. * gruen_0 # EQ 47
        a2_iikk = -12.*gruen_0 + 36.*gruen_0*gruen_0 - 18.*params['q_0']*gruen_0 # EQ 47
        nu_o_nu0_sq = 1.+ a1_ii*f + (1./2.)*a2_iikk * f*f # EQ 41
        return 1./6./nu_o_nu0_sq * (2.*f+1.) * ( a1_ii + a2_iikk*f )

    def isothermal_bulk_modulus(self, pressure,temperature, volume, params):
        """
        Returns isothermal bulk modulus :math:`[Pa]` 
        """
        T_0 = self.reference_temperature( params )
        debye_T = self.__debye_temperature(params['V_0']/volume, params)
        gr = self.grueneisen_parameter(pressure, temperature, volume, params)

        E_th = debye.thermal_energy(temperature, debye_T, params['n']) #thermal energy at temperature T
        E_th_ref = debye.thermal_energy(T_0,debye_T, params['n']) #thermal energy at reference temperature

        C_v = debye.heat_capacity_v(temperature, debye_T, params['n']) #heat capacity at temperature T
        C_v_ref = debye.heat_capacity_v(T_0,debye_T, params['n']) #heat capacity at reference temperature

        q = self.volume_dependent_q(params['V_0']/volume, params)

        K = bm.bulk_modulus(volume, params) \
            + (gr + 1.-q)* ( gr / volume ) * (E_th - E_th_ref) \
            - ( pow(gr , 2.) / volume )*(C_v*temperature - C_v_ref*T_0)

        return K

    def adiabatic_bulk_modulus(self, pressure, temperature, volume, params):
        """
        Returns adiabatic bulk modulus. :math:`[Pa]` 
        """
        K_T=self.isothermal_bulk_modulus(pressure, temperature, volume, params)
        alpha = self.thermal_expansivity(pressure, temperature, volume, params)
        gr = self.grueneisen_parameter(pressure, temperature, volume, params)
        K_S = K_T*(1. + gr * alpha * temperature)
        return K_S

    def shear_modulus(self, pressure, temperature, volume, params):
        """
        Returns shear modulus. :math:`[Pa]` 
        """
        T_0 = self.reference_temperature( params )
        debye_T = self.__debye_temperature(params['V_0']/volume, params)
        eta_s = self.__isotropic_eta_s(params['V_0']/volume, params)

        E_th = debye.thermal_energy(temperature ,debye_T, params['n'])
        E_th_ref = debye.thermal_energy(T_0,debye_T, params['n'])

        if self.order==2:
            return bm.shear_modulus_second_order(volume, params) - eta_s * (E_th-E_th_ref) / volume
        elif self.order==3:
            return bm.shear_modulus_third_order(volume, params) - eta_s * (E_th-E_th_ref) / volume
        else:
            raise NotImplementedError("")

    def heat_capacity_v(self, pressure, temperature, volume, params):
        """
        Returns heat capacity at constant volume. :math:`[J/K/mol]` 
        """
        debye_T = self.__debye_temperature(params['V_0']/volume, params)
        return debye.heat_capacity_v(temperature, debye_T,params['n'])

    def heat_capacity_p(self, pressure, temperature, volume, params):
        """
        Returns heat capacity at constant pressure. :math:`[J/K/mol]` 
        """
        alpha = self.thermal_expansivity(pressure, temperature, volume, params)
        gr = self.grueneisen_parameter(pressure, temperature, volume, params)
        C_v = self.heat_capacity_v(pressure, temperature, volume, params)
        C_p = C_v*(1. + gr * alpha * temperature)
        return C_p

    def thermal_expansivity(self, pressure, temperature, volume, params):
        """
        Returns thermal expansivity. :math:`[1/K]` 
        """
        C_v = self.heat_capacity_v(pressure, temperature, volume, params)
        gr = self.grueneisen_parameter(pressure, temperature, volume, params)
        K = self.isothermal_bulk_modulus(pressure, temperature, volume, params)
        alpha = gr * C_v / K / volume
        return alpha

    def gibbs_free_energy( self, pressure, temperature, volume, params):
        """
        Returns the Gibbs free energy at the pressure and temperature of the mineral [J/mol]
        """
        G = self.helmholtz_free_energy( pressure, temperature, volume, params) + pressure * volume
        return G

    def entropy( self, pressure, temperature, volume, params):
        """
        Returns the entropy at the pressure and temperature of the mineral [J/K/mol]
        """
        x = params['V_0'] / volume
        f = 1./2. * (pow(x, 2./3.) - 1.)
        Debye_T = self.__debye_temperature(params['V_0']/volume, params)
        S = debye.entropy( temperature, Debye_T, params['n'] )
        return S 

    def enthalpy( self, pressure, temperature, volume, params):
        """
        Returns the enthalpy at the pressure and temperature of the mineral [J/mol]
        """
        
        return self.helmholtz_free_energy( pressure, temperature, volume, params) + \
               temperature * self.entropy( pressure, temperature, volume, params) + \
               pressure * self.volume( pressure, temperature, params)

    def helmholtz_free_energy( self, pressure, temperature, volume, params):
        """
        Returns the Helmholtz free energy at the pressure and temperature of the mineral [J/mol]
        """
        x = params['V_0'] / volume
        f = 1./2. * (pow(x, 2./3.) - 1.)
        Debye_T = self.__debye_temperature(params['V_0']/volume, params)

        F_quasiharmonic = debye.helmholtz_free_energy( temperature, Debye_T, params['n'] ) - \
                          debye.helmholtz_free_energy( 300., Debye_T, params['n'] )

        b_iikk= 9.*params['K_0'] # EQ 28
        b_iikkmm= 27.*params['K_0']*(params['Kprime_0']-4.) # EQ 29

        F = params['F_0'] + \
            0.5*b_iikk*f*f*params['V_0'] + (1./6.)*params['V_0']*b_iikkmm*f*f*f +\
            F_quasiharmonic

        return F

    def validate_parameters(self, params):
        """
        Check for existence and validity of the parameters
        """

        #if G and Gprime are not included this is presumably deliberate,
        #as we can model density and bulk modulus just fine without them,
        #so just add them to the dictionary as nans
        if 'G_0' not in params:
            params['G_0'] = float('nan')
        if 'Gprime_0' not in params:
            params['Gprime_0'] = float('nan')
        if 'eta_s_0' not in params:
            params['eta_s_0'] = float('nan')
        if 'F_0' not in params:
            params['F_0'] = float('nan')
  
        #check that all the required keys are in the dictionary
        expected_keys = ['V_0', 'K_0', 'Kprime_0', 'G_0', 'Gprime_0', 'molar_mass', 'n', 'Debye_0', 'grueneisen_0', 'q_0', 'eta_s_0']
        for k in expected_keys:
            if k not in params:
                raise KeyError('params object missing parameter : ' + k)
        
        #now check that the values are reasonable.  I mostly just
        #made up these values from experience, and we are only 
        #raising a warning.  Better way to do this? [IR]
        if params['V_0'] < 1.e-7 or params['V_0'] > 1.e-3:
            warnings.warn( 'Unusual value for V_0', stacklevel=2 )
        if params['K_0'] < 1.e9 or params['K_0'] > 1.e13:
            warnings.warn( 'Unusual value for K_0', stacklevel=2 )
        if params['Kprime_0'] < 0. or params['Kprime_0'] > 10.:
            warnings.warn( 'Unusual value for Kprime_0', stacklevel=2 )
        if params['G_0'] < 0. or params['G_0'] > 1.e13:
            warnings.warn( 'Unusual value for G_0', stacklevel=2 )
        if params['Gprime_0'] < -5. or params['Gprime_0'] > 10.:
            warnings.warn( 'Unusual value for Gprime_0', stacklevel=2 )
        if params['molar_mass'] < 0.001 or params['molar_mass'] > 10.:
            warnings.warn( 'Unusual value for molar_mass', stacklevel=2 )
        if params['n'] < 1. or params['n'] > 1000.:
            warnings.warn( 'Unusual value for n', stacklevel=2 )
        if params['Debye_0'] < 1. or params['Debye_0'] > 10000.:
            warnings.warn( 'Unusual value for Debye_0', stacklevel=2 )
        if params['grueneisen_0'] < 0. or params['grueneisen_0'] > 10.:
            warnings.warn( 'Unusual value for grueneisen_0' , stacklevel=2)
        if params['q_0'] < -10. or params['q_0'] > 10.:
            warnings.warn( 'Unusual value for q_0' , stacklevel=2)
        if params['eta_s_0'] < -10. or params['eta_s_0'] > 10.:
            warnings.warn( 'Unusual value for eta_s_0' , stacklevel=2)



class SLB3(SLBBase):
    """
    SLB equation of state with third order finite strain expansion for the
    shear modulus (this should be preferred, as it is more thermodynamically
    consistent.)
    """
    def __init__(self):
        self.order=3


class SLB2(SLBBase):
    """
    SLB equation of state with second order finite strain expansion for the
    shear modulus.  In general, this should not be used, but sometimes
    shear modulus data is fit to a second order equation of state.  In that
    case, you should use this.  The moral is, be careful!
    """
    def __init__(self):
        self.order=2
