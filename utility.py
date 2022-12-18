import queue
import threading
import random
import importlib

ANTE = 5

def log(src,message):
    print('### %s log > %s' % (src,message))
class Player:
    def __init__(self,source,gameCount):
        playerModule = importlib.import_module(source)
        print(playerModule)
        self.name = playerModule.name
        self.balance = 0
        self.iQ = queue.Queue()
        self.rQ = queue.Queue()
        self.cards = None
        self.gameCount = gameCount
        self.misbehave = False
        self.thread = threading.Thread(target=playerModule.play,args=(self.gameCount,self.iQ,self.rQ),daemon=True)
    def start(self):
        self.thread.start()
    def join(self):
        self.thread.join()

class Deck:
    def __init__(self):
        self.cards = set(('%s%s' % (suit,rank)) for suit in ['S','H','D','C'] for rank in ['A','K','Q','J'])
        self.cards.add('J')
    def size(self):
        return len(self.cards)
    def deal(self,count=1):
        if len(self.cards) < count:
            return None
        selected = set(random.sample(self.cards,count))
        self.cards -= selected
        return selected
    def toString(self):
        return ','.join(self.cards)

class Bet:
    def __init__(self):
        self.pot = 0 # money in the pot (excluding ante)
        self.pending = 0 # the amount to pay to participate (call or raise)
        self.setter = None
        self.follower = None # settled if this is set
    def toString(self):
        msg = ('pot: %d' % self.pot)
        if self.setter:
            msg += (', setter: %s' % (self.setter.name))
            if self.follower:
                msg += (', follower: %s' % (self.follower.name))
        return msg
    def bet(self,p,amount):
        self.follower = None # unsettled
        self.setter = p
        self.pot = amount
        self.pending = amount
    def call(self,p):
        self.follower = p
        self.pot += self.pending
        self.pending = 0
    def raiseBet(self,p,r):
        self.follower = None
        self.setter = p
        self.pot += self.pending + r
        self.pending = r
    def isFolded(self): # somebody fold
        return self.setter and not self.follower
    def bothCheck(self): # nothing happens
        return not self.setter
    def getBet(self):
        return (self.pot-self.pending)/2 + self.pending

class Fate17Hand:
    def __init__(self,cards):
        self.cards = cards
        self.score = 0
        self.type = None
        # 90000: five card
        # 80000: royal straight flush
        # >= 70000: four card
        # >= 60000: full house
        # >= 50000: straight
        # >= 40000: three card
        # >= 30000: two pair
        # >= 20000: one pair
    def analyze(self):
        rankWeight = {'A': 8, 'K': 6, 'Q': 4, 'J': 2}
        hasJoker = False
        rankToCount = dict()
        suitToCount = dict() # needed to tell straight from royal straight flush
        for card in self.cards:
            if len(card) == 1: # joker
                hasJoker = True
            else:
                rankToCount[card[1]] = rankToCount.get(card[1],0) + 1
                suitToCount[card[0]] = suitToCount.get(card[0],0) + 1
        countToRank = dict()
        for k in rankToCount:
            countToRank.setdefault(rankToCount[k],list()).append(k)
        if hasJoker and 4 in countToRank: # five card
            self.type = 'five card'
            self.score = 90000
        elif hasJoker and len(rankToCount) == 4: # straight
            if len(suitToCount) == 1: # same suit: royal straight flush
                self.type = 'royal straight flush'
                self.score = 80000
            else: # straight
                self.type = 'straight'
                self.score = 50000
        elif not hasJoker and 4 in countToRank: # four card w/o joker
            self.type = 'four card'
            self.score = 70000
            self.score += rankWeight[countToRank[4][0]] * 1000
            self.score += rankWeight[countToRank[1][0]] * 100
        elif hasJoker and 3 in countToRank: # four card w/ joker
            self.type = 'four card'
            self.score = 70000 + rankWeight[countToRank[3][0]] * 1000 + rankWeight[countToRank[1][0]] * 100
        elif 3 in countToRank and 2 in countToRank: # full house w/o joker
            self.type = 'full house'
            self.score = 60000 + rankWeight[countToRank[3][0]] * 1000 + rankWeight[countToRank[2][0]] * 100
        elif hasJoker and 2 in countToRank and len(countToRank[2]) == 2: # full house w/ joker
            self.type = 'full house'
            r1 = countToRank[2][0]
            r2 = countToRank[2][1]
            self.score = 60000 + max(rankWeight[r1] * 1000 + rankWeight[r2] * 100,
                                        rankWeight[r2] * 1000 + rankWeight[r1] * 100)
        elif not hasJoker and 3 in countToRank and 2 not in countToRank: # 3 card w/o joker
            self.type = 'three card'
            r1 = countToRank[1][0]
            r2 = countToRank[1][1]
            self.score = 40000 + rankWeight[countToRank[3][0]] * 1000 + \
                        max(rankWeight[r1] * 100 + rankWeight[r2] * 10, rankWeight[r2] * 100 + rankWeight[r1] * 10)
        elif hasJoker and 2 in countToRank and 1 in countToRank: # 3 card w/ joker
            self.type = 'three card'
            r1 = countToRank[1][0]
            r2 = countToRank[1][1]
            self.score = 40000 + rankWeight[countToRank[2][0]] * 1000 + \
                        max(rankWeight[r1] * 100 + rankWeight[r2] * 10, rankWeight[r2] * 100 + rankWeight[r1] * 10)
        elif not hasJoker and 2 in countToRank and len(countToRank[2]) == 2: # 2 pair (must be w/o joker)
            self.type = 'two pair'
            p1 = countToRank[2][0]
            p2 = countToRank[2][1]
            self.score = 30000 +  \
                        max(rankWeight[p1] * 1000 + rankWeight[p2] * 100,
                            rankWeight[p2] * 1000 + rankWeight[p1] * 100) + \
                        rankWeight[countToRank[1][0]] * 10
        elif not hasJoker and len(rankToCount) == 4: # 1 pair (must be w/o joker)
            self.type = 'one pair'
            p = countToRank[2][0]
            self.score = 20000 + rankWeight[p] * 1000
            if p == 'A':
                self.score += rankWeight['K'] * 100 + rankWeight['Q'] * 10 + rankWeight['J']
            elif p == 'K':
                self.score += rankWeight['A'] * 100 + rankWeight['Q'] * 10 + rankWeight['J']
            elif p == 'Q':
                self.score += rankWeight['A'] * 100 + rankWeight['K'] * 10 + rankWeight['J']
            else: # p = 'J'
                self.score += rankWeight['A'] * 100 + rankWeight['K'] * 10 + rankWeight['Q']
        else:
            print('ops, this one is out of my analysis... %s' % (','.join(self.cards)))
    def getScore(self):
        return self.score
    def toString(self):
        return ','.join(self.cards) + ': ' + str(self.score) + ' ('+ self.type + ')'




# 90000: five card
# 80000: royal straight flush
# >= 70000: four card
# >= 60000: full house
# >= 50000: straight
# >= 40000: three card
# >= 30000: two pair
# >= 20000: one pair
def analyzeHand(cards): # a list or set of 5 cards
    rankWeight = {'A': 8, 'K': 6, 'Q': 4, 'J': 2}
    hasJoker = False
    rankToCount = dict()
    suitToCount = dict() # needed to tell straight from royal straight flush
    score = 0
    category = None
    ### pre-processing
    for card in cards:
        if len(card) == 1: # joker
            hasJoker = True
        else:
            rankToCount[card[1]] = rankToCount.get(card[1],0) + 1
            suitToCount[card[0]] = suitToCount.get(card[0],0) + 1
    countToRank = dict()
    for k in rankToCount:
        countToRank.setdefault(rankToCount[k],list()).append(k)
    ### 
    if hasJoker and 4 in countToRank: # five card
        category = 'five card'
        score = 90000
    elif hasJoker and len(rankToCount) == 4: # straight
        if len(suitToCount) == 1: # same suit: royal straight flush
            category = 'royal straight flush'
            score = 80000
        else: # straight
            category = 'straight'
            score = 50000
    elif not hasJoker and 4 in countToRank: # four card w/o joker
        category = 'four card'
        score = 70000
        score += rankWeight[countToRank[4][0]] * 1000
        score += rankWeight[countToRank[1][0]] * 100
    elif hasJoker and 3 in countToRank: # four card w/ joker
        category = 'four card'
        score = 70000 + rankWeight[countToRank[3][0]] * 1000 + rankWeight[countToRank[1][0]] * 100
    elif 3 in countToRank and 2 in countToRank: # full house w/o joker
        category = 'full house'
        score = 60000 + rankWeight[countToRank[3][0]] * 1000 + rankWeight[countToRank[2][0]] * 100
    elif hasJoker and 2 in countToRank and len(countToRank[2]) == 2: # full house w/ joker
        category = 'full house'
        r1 = countToRank[2][0]
        r2 = countToRank[2][1]
        score = 60000 + max(rankWeight[r1] * 1000 + rankWeight[r2] * 100,
                                rankWeight[r2] * 1000 + rankWeight[r1] * 100)
    elif not hasJoker and 3 in countToRank and 2 not in countToRank: # 3 card w/o joker
        category = 'three card'
        r1 = countToRank[1][0]
        r2 = countToRank[1][1]
        score = 40000 + rankWeight[countToRank[3][0]] * 1000 + \
                    max(rankWeight[r1] * 100 + rankWeight[r2] * 10, rankWeight[r2] * 100 + rankWeight[r1] * 10)
    elif hasJoker and 2 in countToRank and 1 in countToRank: # 3 card w/ joker
        category = 'three card'
        r1 = countToRank[1][0]
        r2 = countToRank[1][1]
        score = 40000 + rankWeight[countToRank[2][0]] * 1000 + \
                    max(rankWeight[r1] * 100 + rankWeight[r2] * 10, rankWeight[r2] * 100 + rankWeight[r1] * 10)
    elif not hasJoker and 2 in countToRank and len(countToRank[2]) == 2: # 2 pair (must be w/o joker)
        category = 'two pair'
        p1 = countToRank[2][0]
        p2 = countToRank[2][1]
        score = 30000 +  \
                    max(rankWeight[p1] * 1000 + rankWeight[p2] * 100,
                        rankWeight[p2] * 1000 + rankWeight[p1] * 100) + \
                    rankWeight[countToRank[1][0]] * 10
    elif not hasJoker and len(rankToCount) == 4: # 1 pair (must be w/o joker)
        category = 'one pair'
        p = countToRank[2][0]
        score = 20000 + rankWeight[p] * 1000
        if p == 'A':
            score += rankWeight['K'] * 100 + rankWeight['Q'] * 10 + rankWeight['J']
        elif p == 'K':
            score += rankWeight['A'] * 100 + rankWeight['Q'] * 10 + rankWeight['J']
        elif p == 'Q':
            score += rankWeight['A'] * 100 + rankWeight['K'] * 10 + rankWeight['J']
        else: # p = 'J'
            score += rankWeight['A'] * 100 + rankWeight['K'] * 10 + rankWeight['Q']
    else:
        print('ops, this one is out of my analysis... %s' % (','.join(cards)))
    ###
    return score,category
