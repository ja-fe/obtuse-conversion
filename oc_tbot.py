#Built ins
import logging
import re
import time
#Extenals
import tweepy
from quantulum3 import parser
from pint import UnitRegistry
#Customs
from auth import authenticateAPI
import botfunc as bf
import config  as cf


#Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

ureg = UnitRegistry()

def respond_to_mentions(api, since_id):
    '''
    Replies to twitter mentions of the bot
    Considers any tweet after since_id to be fresh and in need of reply

    Args
        api       --  tweepy api object with initialized authentication
        since_id  --  tweepy tweet ID object associated with the last successfully replied to tweet

    Returns
        updated_since_id -- tweepy tweet ID object associated with the (new) last successfully replied to tweet
    '''
    updated_since_id = since_id
    #Extended mode is neccessary now that twitter bumped certain (now all?) languages to allow 280 characters
    #Legacy version may be safer in other languages
    for tweet in tweepy.Cursor(api.mentions_timeline, since_id = since_id, tweet_mode = "extended").items(): #Use cursor to ignore pagination
        updated_since_id = max(tweet.id, updated_since_id)

        #Don't respond to replies, only fresh tweets
        if tweet.in_reply_to_status_id is not None:
            return

        #Parse units
        quantunit = parser.parse(tweet.full_text)[0]
        #print(dir(parser))
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

        ureg.define('base_unit = ' + baseunit[:-1] + '= bu')
        pintunit.ito('bu')

        #Obtusify the unit
        obtuse_quant = bf.obtusify(pintunit.magnitude, dims, cf.derived_units, cf.prefixes, minvalord=-8, maxvalord=8)

        #Reply with the original tweet quoted, replacing the units
        handle = " @%s"%tweet.user.screen_name
        if len(tweet.full_text) + len(obtuse_quant) + len(handle) > 280:
            #Can't fit quotation in reply, just reply with quantity
            if len(obtuse_quant) + len(handle) > 280:
                #This will never trigger under the base parameters, but catch anyway
                log.info("Obtuse quantitiy too long to tweet, aborting reply")
                log.info("Quantity: ", obtuse_quant)
                continue
            log.info("Tweet too long to quote with obtuse unit, replying with just unit")
            log.info("Tweet ID: ", tweet.ID)
            reply = obtuse_quant + handle
        else:
            scrubbed_tweet = re.sub("@obtuse_units", "", tweet.full_text)
            reply = re.sub(quantunit.surface, obtuse_quant, scrubbed_tweet) + handle

        #Reply
        api.update_status(status = reply, in_reply_to_status_id = tweet.id)

        return updated_since_id

def main():
    '''
    Have the bot routinely check for and reply to mentions
    '''
    api = authenticateAPI()
    since_id = 1
    while True:
        since_id = respond_to_mentions(api, since_id)
        logger.info("Waiting...")
        exit() #Don't actually keep this thing running
        time.sleep(60)

if __name__ == "__main__":
    main()
