'''
Contains the functions used by the bot
'''

import numpy as np
import random

def obtusify(val, idims, SI, pref, loops = 2, maxvalord = None, minvalord = None, maxprefs = None, spread = None):
    '''
    Yes, obfuscate is a word but it's not as fun now is it? And this is as close as I'll ever get to casting a Harry Potter spell.
    Given a quantity in SI base units, returns an equivalent value in an obtuse combination of
      derived SI units and prefixes

    Args:
      val   -- float : numerical value of quantity in base units
      idims -- (4,) : tuple corresponding to dimensionality of input quantity (M,L,T,I)
      SI    -- (n,5) struct ndarray : information on SI derived units, see config
      pref  -- (n,2) struct ndarray : indicating a set of SI prefixes to superfluously add

    Kwargs:
      loops       -- int : Number of derived units to be present in the obfuscation. Set it irresponsibly high!
      maxvalord   -- int : If not None, maximum order of output numeric value
      minvalord   -- int : If not None, minimum order of output numeric value
      maxprefs    -- int : If not None, maximum number of SI prefixes to include in output
      spread      -- float [0,1) : If not None, creates a bias towards including more individual unit names
                       in the output (vs. less unique names with higher powers). Strong interaction with loops.

    Returns:
      ostring -- string : quantity equal to input, expressed obtusely

    Sample Usage:
        # Obtusification of 8024 metres
        obtusify(8024, (0,1,0,0), config.SI, config.pref) --> "8.024 microsievert-kilograms per nanonewton"
    '''

    #Basic input checks
    if maxvalord == None: maxvalord =  np.inf
    if minvalord == None: minvalord = -np.inf
    if maxvalord - minvalord < 0:
        print("You set the output value order minimum higher than the maximum. Don't think I don't see you trying to crash the prefix algorithm.")
        raise Exception


    #Pick a random non-zero positive dimension
    nzi = [i for i,x in enumerate(idims) if x > 0]
    ind = random.choice(nzi)

    #Pick a random SI derived unit which is nonzero positive in this dimension (ensures at least one unit on numerator)
    SIinds = [i for i,x in enumerate(SI['dims']) if x[ind] > 0]
    SIind = random.choice(SIinds)
    SI['count'][SIind] += 1

    #Check which dimensions remain to be filled
    wSI = [np.array(x)*y for x,y in zip(SI['dims'], SI['count'])]
    remainder = idims - np.sum(wSI, axis=0)


    #Loop while dimensions are not matched
    i = 0
    while i < loops:
        i += 1

        #Find the derived unit which would most decrease the remainder if added to the numerator
        diffs = np.sum(np.abs([list(x) - remainder for x in SI['dims']]), axis=1).astype(np.float32)
        diffs[SI['count'] < 0] = np.nan #Ignore options which would simply cancel out existing units
        n,ndiff = np.where(diffs == np.nanmin(diffs))[0][0], np.nanmin(diffs)
        #Find the derived unit which would most decrease the remainder if added to the denominator
        diffs = np.sum(np.abs([list(x) + remainder for x in SI['dims']]), axis=1).astype(np.float32)
        diffs[SI['count'] > 0] = np.nan
        d,ddiff = np.where(diffs == np.nanmin(diffs))[0][0], np.nanmin(diffs) #when added to the denominator

        #Sometimes selecting the unit which best moves the dimensionality towards the target actually produces
        #  lackluster results, e.g. feedback loops of two units undoing eachother around the target.
        #These options are ways to introduce bias for more interesting results
        if spread is not None and loops - i > 3:
            #Adds a chance to instead select a random unused unit if possible
            if np.random.rand() > spread and 0 in SI['count']:
                unused_units = [i for i,x in enumerate(SI['count']) if x == 0]
                uu = random.choice(unused_units)
                if np.random.rand() > .5:
                    SI['count'][uu] += 1 #Slap it on the numerator
                else:
                    SI['count'][uu] -= 1 #Slap it on the denominator
        else:
            if ndiff <= ddiff:
                SI['count'][n] += 1
            else:
                SI['count'][d] -= 1

        #Check which dimensions remain to be filled
        wSI = [np.array(x)*y for x,y in zip(SI['dims'], SI['count'])]
        remainder = idims - np.sum(wSI, axis=0)

    #Assign SI prefixes
    nslots = np.sum(SI['count'] > 0) + np.sum(remainder > 0) #Number of slots available on numerator
    dslots = np.sum(SI['count'] < 0) + np.sum(remainder < 0) #Number of slots available on denominator
    pn = np.full(nslots, None)
    pd = np.full(dslots, None)

    #Bound the number of prefixes to be added
    if maxprefs is not None:
        nempty, dempty = np.sum(pn == None), np.sum(pd == None)
        while nempty + dempty > maxprefs:
            #Fill a random slot with an empty prefix (uniform selection across all slots)
            ratio = nempty/(nempty + dempty)
            if np.random.rand() < ratio:
                i = [i for i,x in enumerate(pn) if x == None]
                pn[random.choice(i)] = 0
            else:
                i = [i for i,x in enumerate(pd) if x == None]
                pd[random.choice(i)] = 0
            nempty, dempty = np.sum(pn == None), np.sum(pd == None)

    #Assign arbitrary prefixes to open slots slots, avoiding dupes
    for i in [i for i,x in enumerate(pn) if x == None]:
        pn[i] = random.choice(pref['mag'])
    for i in [i for i,x in enumerate(pd) if x == None]:
        pd[i] = random.choice(pref['mag'])

    #Unit exponents (and thus prefix powers)
    en =  [ i for i in SI['count'][SI['count'] > 0]] #Derived units
    en += [ i for i in remainder if i > 0]           #Base units
    ed =  [-i for i in SI['count'][SI['count'] < 0]] #Derived units
    ed += [-i for i in remainder if i < 0]           #Base units

    #Lower/raise prefixes until within user tolerance
    current_ord = sum([p*e for p,e in zip(pn,en)]) - sum([p*e for p,e in zip(pd,ed)]) - np.floor(np.log10(val))
    ratio = len(pn)/ (len(pn) + len(pd))
    numprobs = [e if p!=0 else 0 for e,p in zip(en,pn)] #Favour modifying high power values (no one wnats to see "yoctometres octed" (I kinda do though))
    numprobs = np.array(numprobs)/np.sum(numprobs) #  Additionally, don't select empty prefixes for change to prevent conflict with maxprefs
    denprobs = [e if p!=0 else 0 for e,p in zip(ed,pd)] #Favour modifying high power values (no one wnats to see "yoctometres octed" (I kinda do though))
    denprobs = np.array(denprobs)/np.sum(denprobs) #  Additionally, don't select empty prefixes for change to prevent conflict with maxprefs
    t = 0
    while current_ord > maxvalord or current_ord < minvalord:
        t+=1
        if t>100:
            print("Error, unable to meet user tolerance for output value magnitude within %i iteration attempts"%t)
            print("Keywords minvalord/maxvalord most likely define an extremely narrow range")
            raise Exception()
        if current_ord > maxvalord:
            if np.random.rand() < ratio:
                #Go down one prefix in a numerator slot
                i = np.random.choice(range(len(pn)), p=numprobs)
                newprefs = pref['mag'][pref['mag'] < pn[i]]
                if len(newprefs) == 0: continue #If there is no such prefix, reiterate
                pn[i] = min(newprefs, key=lambda x:abs(x-pn[i]))
            else:
                #Go up on prefix in a denominator slot
                i = np.random.choice(range(len(pd)), p=denprobs)
                newprefs = pref['mag'][pref['mag'] > pd[i]]
                if len(newprefs) == 0: continue
                pd[i] = min(newprefs, key=lambda x:abs(x-pd[i]))
        else:
            if np.random.rand() < ratio:
                #Go up one prefix in a numerator slot
                i = np.random.choice(range(len(pn)), p=numprobs)
                newprefs = pref['mag'][pref['mag'] > pn[i]]
                if len(newprefs) == 0: continue
                pn[i] = min(newprefs, key=lambda x:abs(x-pn[i]))
            else:
                #Go down on prefix in a denominator slot
                i = np.random.choice(range(len(pd)), p=denprobs)
                newprefs = pref['mag'][pref['mag'] < pd[i]]
                if len(newprefs) == 0: continue
                pd[i] = min(newprefs, key=lambda x:abs(x-pd[i]))
        current_ord = sum([p*e for p,e in zip(pn,en)]) - sum([p*e for p,e in zip(pd,ed)]) - np.floor(np.log10(val))

    #Calculate new numerical value of quantity
    oval = val / (10**np.floor(np.log10(val))) * 10**-current_ord

    #Convert numerical prefix orders to their corresponding strings
    pn = [pref['name'][pref['mag'] == i][0] for i in pn]
    pd = [pref['name'][pref['mag'] == i][0] for i in pd]
    if len(pd) > 0: pd[0] = ' per ' + pd[0]


    #Convert exponent values to their corresponding strings
    enames = {1:'', 2:'s-squared', 3:'s-cubed', 4:'s-quarted', 5: 's-quinted', 6: 's-sexted', 7: 's-hepted', 8: 's-octed',
              9: 'nonned????', 10: 'dude', 11: 'stop', 12: 'the', 13 : 'words', 14: ' don\'t', 15: 'even', 16: 'go', 17: 'this', 18:'high'} #If you get a key error on this you requested a BEEG obfuscation
    en = [enames[i] for i in en]
    ed = [enames[i] for i in ed]

    #Unit strings
    bnames = {0:'kilogram', 1: 'metre', 2: 'second', 3: 'ampere'}
    un =  list(SI['uname'][SI['count'] > 0])                     #Derived units
    un += [bnames[i] for i,x in enumerate(remainder) if x > 0]   #Base units
    ud =  list(SI['uname'][SI['count'] < 0])
    ud += [bnames[i] for i,x in enumerate(remainder) if x < 0]

    #Construct final value string
    ustring = ''
    for p,u,e in zip(pn, un, en):
        ustring += '-%s%s%s'%(p,u,e)
    ustring += 's' #Pluralize
    for p,u,e in zip(pd, ud, ed):
        ustring += '%s%s%s-'%(p,u,e)
    ustring = ustring[1:] #Chop off superfluous hyphens
    if len(pd) != 0:
        ustring = ustring[:-1]

    #Round oval for readability
    oval  = np.format_float_positional(oval, precision=4, unique=False, fractional=False, trim='k')
    ostring = str(oval) + ' ' + ustring

    #Cleanup plurals
    ostring = ostring.replace('hertzs', 'hertz')
    ostring = ostring.replace('henrys', 'henries')

    return ostring
