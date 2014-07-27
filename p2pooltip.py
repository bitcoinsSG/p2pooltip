	

    import time
    import praw
    import urllib.request
    import json
    import pymysql
     
    # ---------------------------------------- CONFIGURATIONS ----------------------------------------
    ownerusername 'aaaaaaaaaaa' # Reddit username of bot owner
    walletIdentifier = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'       # blockchain.info wallet identifer
    walletPassword = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'         # blockchain.info wallet password
    dbuser = 'root'                         # database username
    dbpass = 'aaaaaaaaaaaaaaaa'     # database password
    dbdb = 'p2pooltip'                      # database name
    # ------------------------------------------------------------------------------------------------
     
    r = praw.Reddit(user_agent="bot by /u/{0}".format(ownerusername))
    r.login()
    already_done = []       # array containing messages already processed
     
    # Return the first substring in a string between two search strings
    def find_between(s, first, last):
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""
     
    # Return the last substring in a string between two search strings
    def rfind_between(s, first, last):
        try:
            start = s.rindex(first) + len(first)
            end = s.rindex(last, start)
            return s[start:end]
        except ValueError:
            return ""
     
    # Return a p2pool sendmany for a given tip amount
    def getTipSendMany(amount):
            response = urllib.request.urlopen('http://p2pool.org:9332/patron_sendmany/'+str(float(amount)/100000000))
            sendmanybtc = json.loads(response.read().decode('ascii', 'ignore'))
            sendmany = '%7B'
            for key, value in sendmanybtc.items():
                    sendmany += '%22'+key+'%22%3A%20'+str(round(value*100000000))+'%2C%20'
            sendmany = sendmany[:-6]+'%7D'
            return sendmany
     
    # Return a child comment from a post, containing the tip
    def getChildTipCommentFromPost(parent, tipper):
            submission = r.get_info(thing_id=parent.parent_id)
            for reply in submission.comments:
                    if reply.author.name == tipper:
                            return reply
            return 0
     
    # Return a child comment containing the tip
    def getChildTipComment(parent, tipper):
            for reply in parent.replies:
                    if reply.author.name == tipper:
                            return reply
            return 0
     
    # Return previously processed commentid's from the database
    def loadFromDatabase():
            conn = pymysql.connect(host='127.0.0.1', port=3306, user=dbuser, passwd=dbpass, db=dbdb)
            cur = conn.cursor()
            cur.execute('SELECT messageid FROM tips')
            commentids = []
            for r in cur.fetchall():
                    commentids.append(r[0])
            cur.close()
            conn.close()
            return commentids
     
    # Store information for a tip in the database
    def storeInDatabase(commentid, messageid, amount, sendamount, username, txid):
            conn = pymysql.connect(host='127.0.0.1', port=3306, user=dbuser, passwd=dbpass, db=dbdb)
            cur = conn.cursor()
            cur.execute('INSERT INTO tips (commentid, messageid, amount, sent, username, txid) VALUES ("'+commentid+'", "'+messageid+'", '+str(amount)+', '+str(sendamount)+', "'+username+'", "'+txid+'")')
            cur.close()
            conn.commit()
            conn.close()
            return True
     
    already_done.extend(loadFromDatabase()) # append previously processed commentid's to avoid processing them again
     
    while True:
            inbox = r.get_inbox()
            for message in inbox:
                    if message.author.name == 'changetip':
                            if message.subject == 'You\'ve received a tip via ChangeTip':
                                    if message.id not in already_done:
                                            already_done.append(message.id)
                                            start = "The tip has been delivered, and "
                                            end = " is available in your"
                                            tip = rfind_between(message.body.encode('utf-8'), start.encode('utf-8'), end.encode('utf-8'))
                                            number = float(tip.split(' '.encode('utf-8'))[0].decode('ascii', 'ignore'))
                                            denomination = tip.split(' '.encode('utf-8'))[1]
                                            amount = 0
                                            if denomination == 'BTC'.encode('utf-8'):
                                                    amount = round(number * 100000000)
                                            elif denomination == 'mBTC'.encode('utf-8'):
                                                    amount = round(number * 100000)
                                            else: # denomination == microBTC
                                                    amount = round(number * 100)
                                            parentIsPost = find_between(message.body.encode('utf-8').decode('ascii', 'ignore'), '[your post]', ')')[-1:] == '/'
                                            parentID = find_between(message.body.encode('utf-8').decode('ascii', 'ignore'), '/comments/', '/') if parentIsPost else rfind_between(find_between(message.body.encode('utf-8').decode('ascii', 'ignore'), '[your post]', ')')+').', '/', ')')
                                            thethingid = 't'+('3' if parentIsPost else '1')+'_'+parentID
                                            parent = r.get_submission(r.get_info(thing_id=thethingid).permalink).comments[0]
                                            username = find_between(message.body, 'Fellow Redditor /u/', ' sent you')
                                            tipComment = getChildTipCommentFromPost(parent, username) if parentIsPost else getChildTipComment(parent, username)
                                            if tipComment != 0:
                                                    if amount < 100000:
                                                            tipComment.reply('I\'m sorry, but the minimum P2Pool tip is currently 1 mBTC because of transaction fees.\n\n/u/changetip '+str(amount)+' satoshis')
                                                            commentid = tipComment.id
                                                            amount = 0
                                                            sendamount = 0
                                                            txid = 'none'
                                                            storeInDatabase(commentid, message.id, amount, sendamount, username, txid)
                                                    else:
                                                            sendamount = amount - 10000
                                                            sendamount *= 1.00 #0.99 for 1% fee
                                                            sendamount = round(sendamount)
                                                            sendMany = getTipSendMany(sendamount)
                                                            sendManyUrl = 'https://blockchain.info/merchant/'+walletIdentifier+'/sendmany?password='+walletPassword+'&recipients='+sendMany
                                                            response = urllib.request.urlopen(sendManyUrl).read().decode('ascii', 'ignore')
                                                            sendmanyresponse = json.loads(response)
                                                            txid = sendmanyresponse["tx_hash"]
                                                            commentid = tipComment.id
                                                            print('\n'+username+' tipped '+str(round(float(amount)/100000, 2))+' mBTC.')
                                                            storeInDatabase(commentid, message.id, amount, sendamount, username, txid)
                                                            tipComment.reply('The Bitcoin tip for '+str(round(float(amount)/100000, 2))+' mBTC (minus fees) [has been forwarded](https://blockchain.info/tx/'+txid+') to P2Pool miners.\n\n^(Brought to you by /u/'+ownerusername+'.)')
            time.sleep(5)

