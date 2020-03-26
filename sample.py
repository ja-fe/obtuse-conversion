import botfunc as bf
import config as cf

#Obtusify 5 kilometres
os = bf.obtusify(5000, (0,1,0,0), cf.derived_units, cf.prefixes, loops=10, minvalord = -5, maxvalord = 5, spread=.5)
print(os)