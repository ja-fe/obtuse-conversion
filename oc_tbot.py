import tweepy
import logging
from auth import authenticateAPI
import botfunc as bf
import config  as cf
from quantulum3 import parser
from pint import UnitRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

ureg = UnitRegistry()

def respond_to_mentions(api, since_id):
    updated_since_id = since_id
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id = since_id).items(): #Use cursor to ignore pagination
        updated_since_id = max(tweet.id, updated_since_id)

        #Don't respond to replies, only fresh tweets
        if tweet.in_reply_to_status_id is not None:
            return

        #Parse units
        quantunit = parser.parse(tweet.text)[0]
        value = quantunit.value
        unit  = quantunit.unit.name

        #Convert to base SI units
        pintunit = value * ureg.parse_expression(unit)
        dims = [pintunit.dimensionality.get(name) for name in ['[mass]','[length]','[time]','[current]']]
        #Define and convert to a unit in terms of base SI units
        bu = ['kilogram','meter','second','ampere']
        baseunit = ''
        for i,u in zip(dims,bu):
            if i !=0:
                baseunit = baseunit + u + '**' + str(i) + '*'
        print('base_unit = ' + baseunit[:-1] + '= bu')
        ureg.define('base_unit = ' + baseunit[:-1] + '= bu')
        pintunit.ito('bu')

        #Obtusify the unit
        obtuse_quant = bf.obtusify(pintunit.magnitude, dims, cf.derived_units, cf.prefixes)

        reply = obtuse_quant + " @%s"%tweet.user.screen_name

        #Reply
        api.update_status(status = reply, in_reply_to_status_id = tweet.id)

        return updated_since_id

def main():
    #Authenticate and fetch API
    api = authenticateAPI()
    since_id = 1
    while True:
        since_id = respond_to_mentions(api, since_id)
        logger.info("Waiting...")
        time.sleep(60)

if __name__ == "__main__":
    main()
