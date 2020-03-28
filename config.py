'''
Contains all object definitions to be used in function calculations
Code should be robust enough to handle most arbitrary changes
  Don't like siemens because they're just omh**-1? Toss em'!
  Want to add your own unit? Go for it!
'''
import numpy as np

#List of SI derived unit to be used.
#(Unit name, Unit dimesions [M,L,T,A], Unit count [0 for no bias])
derived_units = np.array([('hertz',   ( 0, 0,-1, 0) ,0),
                          ('newton',  ( 1, 1,-2, 0) ,0),
                          ('pascal',  ( 1,-1,-2, 0) ,0),
                          ('joule',   ( 1, 2,-2, 0) ,0),
                          ('watt',    ( 1, 2,-3, 0) ,0),
                          ('coulomb', ( 0, 0, 1, 1) ,0),
                          ('volt',    ( 1, 2,-3,-1) ,0),
                          ('farad',   (-1,-2, 4, 2) ,0),
                          ('ohm',     ( 1, 2,-3,-2), 0),
                          ('siemen',  (-1,-2, 3, 2), 0),
                          ('weber',   ( 1, 2,-2,-1), 0),
                          ('tesla',   ( 1, 0,-2,-1), 0),
                          ('henry',   ( 1, 2,-2,-2), 0),
                          ('sievert', ( 0, 2,-2, 0), 0)],
                          dtype=[('uname','U10'), ('dims',np.ndarray),('count',np.float32)])

#List of SI prefixes and their associated powers
#Removing prefixes in the range (-1,1) may cause basis spanning issues in calls with very tight user tolerances.
prefixes = np.array([('yotta', 24),
                     ('zetta', 21),
                     ('exa',   18),
                     ('peta',  15),
                     ('tera',  12),
                     ('giga',   9),
                     ('mega',   6),
                     ('kilo',   3),
                     ('hecto',  2),
                     ('deca',   1),
                     ('',       0),
                     ('deci',  -1),
                     ('centi', -2),
                     ('milli', -3),
                     ('micro', -6),
                     ('nano',  -9),
                     ('pico', -12),
                     ('femto',-15),
                     ('atto', -18),
                     ('zepto',-21),
                     ('yocto',-24)],
                     dtype=[('name','U10'), ('mag',np.int8)])
















#
