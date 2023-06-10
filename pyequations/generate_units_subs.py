from pyequations import RAND_RANGE, EPSILON
from random import uniform
import sympy.physics.units as u
from sympy.physics.units import *
import time


class UnitSub:
    """
    Singleton class that generates a mapping of units to numbers
    """
    __instance = None

    @staticmethod
    def get_instance():
        if UnitSub.__instance is None:
            UnitSub()
        return UnitSub.__instance

    def __init__(self):
        if UnitSub.__instance is None:
            UnitSub.__instance = self
            UnitSub.mapping_a = generate()
            UnitSub.mapping_b = generate()

    @staticmethod
    def get_mappings() -> tuple[dict, dict]:
        """
        Returns the mapping of units to numbers
        Returns two mappings, two ensure that the mappings do not present any false positives
        :return: the mappings
        """

        return UnitSub.get_instance().mapping_a, UnitSub.get_instance().mapping_b


def generate_rand_unit(already_generated: set) -> float:
    """
    Generates a random number between 1 - RAND_RANGE and 1 + RAND_RANGE
    :return: the random number
    """
    ret = uniform(1 - RAND_RANGE, 1 + RAND_RANGE)

    while True:
        # Check if the number is within EPSILON of any number that has already been generated
        # If it is, generate a new number
        if any(abs(ret - num) < EPSILON for num in already_generated):
            ret = uniform(1 - RAND_RANGE, 1 + RAND_RANGE)
        else:
            break

    # Add the number to the set of generated numbers
    already_generated.add(ret)

    return ret


def generate():
    # Use this to find all units
    # all_units = [getattr(u, a) for a in dir(u) if isinstance(getattr(u, a), Unit)]

    # Fundamental units are length, mass, time, electric current, temperature, amount of substance,
    # and luminous intensity
    # everything else is derived from these

    # For convenience, will also add bit and radian

    # Keep track of all the numbers that have been generated to ensure that no two numbers are within
    # EPSILON of each other
    # Could stall with a large enough EPSILON or a small enough RAND_RANGE
    generated = set()

    mapping = {
        # Length
        meter: generate_rand_unit(generated),

        # Mass
        kilogram: generate_rand_unit(generated),

        # Time
        second: generate_rand_unit(generated),

        # Electric current
        ampere: generate_rand_unit(generated),

        # Temperature
        kelvin: generate_rand_unit(generated),

        # Amount of substance
        mole: generate_rand_unit(generated),

        # Luminous intensity
        candela: generate_rand_unit(generated),

        # Extra units

        # Bit
        bit: generate_rand_unit(generated),

        # Radian
        radian: generate_rand_unit(generated)
    }

    _meter = mapping[meter]
    _kilogram = mapping[kilogram]
    _second = mapping[second]
    _ampere = mapping[ampere]
    _kelvin = mapping[kelvin]
    _mole = mapping[mole]
    _candela = mapping[candela]
    _bit = mapping[bit]
    _radian = mapping[radian]

    # Add the rest of the units
    # Done separately, so we can reference the fundamental units

    # This is maybe a bit more hardcoded than I would like, but it is much more efficient that trying to figure out
    # how to do it programmatically
    mapping.update({
        acceleration_due_to_gravity: 9.80665 * _meter / _second ** 2,
        angular_mil: 0.001 * _radian,
        anomalistic_year: 365.259636 * 24 * 60 * 60 * _second,
        atmosphere: 101325 * _kilogram / (_meter * _second ** 2),
        atomic_mass_constant: 1.66053906660e-27 * _kilogram,
        astronomical_unit: 149597870700 * _meter,
        avogadro_constant: 6.02214076e23 * _mole ** -1,
        avogadro_number: 6.02214076e23,
        bar: 1e5 * _kilogram / (_meter * _second ** 2),
        becquerel: _second ** -1,
        boltzmann_constant: 1.380649e-23 * _meter ** 2 * _kilogram * _second ** -2 * _kelvin ** -1,
        byte: 8 * _bit,
        centiliter: 1e-5 * _meter ** 3,
        centimeter: 0.01 * _meter,
        common_year: 365 * 24 * 60 * 60 * _second,
        coulomb: _second * _ampere,
        coulomb_constant: 8.9875517923e9 * _meter ** 3 * _kilogram ** -1 * _second ** -2 * _ampere ** -2,
        day: 86400 * _second,
        deciliter: 1e-4 * _meter ** 3,
        decimeter: 0.1 * _meter,
        degree: 0.0174532925199433 * _radian,
        dioptre: _meter ** -1,
        draconic_year: 346.620075883 * 24 * 60 * 60 * _second,
        vacuum_permittivity: 8.8541878128e-12 * _meter ** -3 * _kilogram ** -1 * _second ** 4 * _ampere ** 2,
        electronvolt: 1.602176634e-19 * _meter ** 2 * _kilogram * _second ** -2,
        elementary_charge: 1.602176634e-19 * _ampere * _second,
        exbibyte: 2 ** 63 * _bit,
        farad: _meter ** -2 * _kilogram ** -1 * _second ** 4 * _ampere ** 2,
        faraday_constant: 96485.33212 * _ampere * _second * _mole ** -1,
        foot: 0.3048 * _meter,
        full_moon_cycle: 29.530588853 * 24 * 60 * 60 * _second,
        gibibyte: 2 ** 33 * _bit,
        gram: 1e-3 * _kilogram,
        gaussian_year: 365.256898326 * 24 * 60 * 60 * _second,
        gravitational_constant: 6.67430e-11 * _meter ** 3 * _kilogram ** -1 * _second ** -2,
        gray: _meter ** 2 * _second ** -2,
        hbar: 1.054571817e-34 * _meter ** 2 * _kilogram * _second ** -1,
        hectare: 1e4 * _meter ** 2,
        henry: _meter ** 2 * _kilogram * _second ** -2 * _ampere ** -2,
        hertz: 1 / _second,
        hour: 3600 * _second,
        inch: 0.0254 * _meter,
        josephson_constant: 483597.8484e9 * _second ** -1 * _meter ** 2 * _kilogram * _ampere ** -2,
        joule: _meter ** 2 * _kilogram * _second ** -2,
        julian_year: 365.25 * 24 * 60 * 60 * _second,
        katal: _mole * _second ** -1,
        kibibyte: 2 ** 13 * _bit,
        kilometer: 1000 * _meter,
        liter: 0.001 * _meter ** 3,
        lightyear: 9460730472580800 * _meter,
        lux: _candela * _meter ** -2,
        magnetic_constant: 1.25663706212e-6 * _meter * _kilogram * _second ** -2 * _ampere ** -2,
        mebibyte: 2 ** 23 * _bit,
        milliliter: 1e-6 * _meter ** 3,
        tonne: 1000 * _kilogram,
        milligram: 1e-3 * _kilogram,
        mile: 1609.344 * _meter,
        microgram: 1e-6 * _kilogram,
        micrometer: 1e-6 * _meter,
        microsecond: 1e-6 * _second,
        millimeter: 0.001 * _meter,
        minute: 60 * _second,
        mmHg: 133.322 * _kilogram / (_meter * _second ** 2),
        milli_mass_unit: 1.66053906660e-30 * _kilogram,
        molar_gas_constant: 8.31446261815324 * _meter ** 2 * _kilogram * _second ** -2 * _kelvin ** -1 * _mole ** -1,
        millisecond: 1e-3 * _second,
        nanometer: 1e-9 * _meter,
        nanosecond: 1e-9 * _second,
        nautical_mile: 1852 * _meter,
        newton: _kilogram * _meter / _second ** 2,
        ohm: _meter ** 2 * _kilogram * _second ** -3 * _ampere ** -2,
        pascal: _kilogram / (_meter * _second ** 2),
        pebibyte: 2 ** 53 * _bit,
        percent: 0.01,
        permille: 0.001,
        picometer: 1e-12 * _meter,
        picosecond: 1e-12 * _second,
        planck: 5.39116e-44 * _second,
        planck_acceleration: 5.560e51 * _meter / _second ** 2,
        planck_angular_frequency: 1.854e43 / _second,
        planck_area: 2.612e-70 * _meter ** 2,
        planck_charge: 1.875e-18 * _ampere * _second,
        planck_current: 3.478e25 * _ampere,
        planck_density: 5.155e96 * _kilogram / _meter ** 3,
        planck_energy: 1.956e9 * _kilogram * _meter ** 2 / _second ** 2,
        planck_energy_density: 1.354e112 * _kilogram / _meter,
        planck_force: 1.210e44 * _kilogram * _meter / _second ** 2,
        planck_impedance: 29.979 * _kilogram * _second / _ampere ** 2,
        planck_intensity: 1.358e121 * _kilogram / _meter ** 2 / _second ** 3,
        planck_length: 1.616e-35 * _meter,
        planck_mass: 2.176e-8 * _kilogram,
        planck_momentum: 6.524e-24 * _kilogram * _meter / _second,
        planck_power: 3.628e52 * _kilogram * _meter ** 2 / _second ** 3,
        planck_pressure: 4.633e113 * _kilogram / _meter / _second ** 2,
        planck_temperature: 1.416e32 * _kelvin,
        planck_time: 5.391e-44 * _second,
        planck_voltage: 1.221e27 * _kilogram * _meter ** 2 / _ampere / _second ** 3,
        planck_volume: 4.222e-105 * _meter ** 3,
        pound: 0.45359237 * _kilogram,
        psi: 6894.757293168361 * _kilogram / (_meter * _second ** 2),
        quart: 0.946352946 * _meter ** 3,
        sidereal_year: 365.256363004 * 24 * 60 * 60 * _second,
        siemens: _second ** 3 * _ampere ** 2 * _kilogram ** -1 * _meter ** -2,
        speed_of_light: 299792458 * _meter / _second,
        steradian: _radian ** 2,
        stefan_boltzmann_constant: 5.670374419e-8 * _kilogram * _second ** -3 * _kelvin ** -4,
        tebibyte: 2 ** 43 * _bit,
        tesla: _kilogram * _second ** -2 * _ampere ** -1,
        tropical_year: 365.24219 * 24 * 60 * 60 * _second,
        von_klitzing_constant: 25812.8074555 * _meter ** 2 * _kilogram * _second ** -3 * _ampere ** -2,
        volt: _meter ** 2 * _kilogram * _second ** -3 * _ampere ** -1,
        watt: _meter ** 2 * _kilogram * _second ** -3,
        yard: 0.9144 * _meter,
    })

    return mapping
