"""
This module implements a fate17 player related to the course
    Computer Programming, S18
by J.-L. Huang
May 2018

v0  20180511
    A random player.
v1  20180522
    Still a random player. Documentation added.
v2 20180524
    Cards are graded to assist decision making.
    Also fix the bug that the host didn't give back replacement cards.
v2.1 20180527
    After showhand, receive from host the opponent's cards.
"""

import random
ANTE = 5
name = 'veryopopkai' # make decisions according to "S"core



def analyzeHand(cards):
    """
    20180524
    Grade the a fate17 game hand.
    The score can be used to decide the winning hand; its value doesn't reflect its rareness.

    cards: a list or set of five cards.
        The 17 possible cards are 'J' and {'S','H','D','C'} x {'A','K','Q','J'}.
    
    Returns:
        This function returns a tuple (score, category).
        The ranges of possible categories are as follows.
        90000: five card
        80000: royal straight flush
        >= 70000: four card
        >= 60000: full house
        >= 50000: straight
        >= 40000: three card
        >= 30000: two pair
        >= 20000: one pair
    """
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


def betting2(name,iQ,rQ,minBet,maxBet,adjustscore,target,hand):
    """
    20180524
    This function implements a random betting strategt.
    During the betting process, this player gets instructions from iQ (instruction queue)
    and, if necessary, places responses in rQ (response queue).

    name: player name, a string
    iQ: the instruction queue. Use "aString = iQ.get()" to get the instruction.
    rQ: the response queue. Use "rQ.put(aString)" to put the response.
    minBet: the initial minimum bet of this betting interval.
    maxBet: the maximum bet of this betting interval.
    target (new in v1): the target bet. If None (default), a random target is generated.

    Returns: myBet,oppBet,isSetter
        myBet/oppBet is the amount of money, excluding ante, that this player/the opponent
        has placed in the pot.
        If myBet > oppBet, the opponent has folded.
        If myBet < oppBet, this player has folded.
        If myBet == oppBet, there are two cases.
            Case I: myBet == 0
                Both players checked.
            Case II: myBet > 0
                Bet agreed. If isSetter is True, this player is the one who sets the bet, i.e.,
                the opponent "calls." Otherwise, the opponent is the one who sets the bet.
    """

    oppChecked = False # True/False if the opponent has/hasn't checked.
    checked = False # True/False if this player has/hasn't checked.
    myBet = 0 # The bet, excluding ante, that this player has placed in the pot.
    oppBet = 0 # The bet, excluding ante, that the opponent has placed in the pot.
    isSetter = None # True/False if this player/the opponent sets the agreed bet. 誰是下注下到別人需要跟注的一方

    #拿到two pairs and one pairs要下注的方法
    while adjustscore == 0:                              
        instruction = iQ.get()
        if instruction == 'action:bet,check':
            checked = True
            rQ.put('check')
            if oppChecked: # both check, end betting
                break
        elif instruction == 'action:raise,call,fold': 
            rQ.put('fold')
            break 
        elif instruction == 'action:call,fold':
            rQ.put('fold')
            break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        
    #拿到5 cards 時，第一輪要下注的方法
    while adjustscore > 0.7 and maxBet == 15: #maxBet == 15代表是第一輪下注
        instruction = iQ.get()
        if instruction == 'action:bet,check': #第一輪下注，而且是從你開始下注
            myBet = target #Target函數先計算每一種牌型要下注的金額然後匯入的target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #第一輪下注，對手先下注，而且下注的金額不到max(15元)，問你要有什麼反應
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一輪下注，對手先下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet #第一輪下注，你先check，對手下注，那會繼續進行這個while迴圈
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise #第一輪下注，你先下注一個金額，對手反raise你，那會繼續進行這個while迴圈
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check': #第一輪下注，你先check，對手也check
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold': #第一輪下注，而且是從你開始下注，對手fold掉
            break
        elif instruction == 'opponent call': #第一輪下注，而且是從你開始下注，對手call
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))
    
            
    #拿到5 cards 時，第二輪要下注的方法
    while adjustscore > 0.7 and maxBet == 30:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第二輪下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))

    #拿到flush straight 時，第一輪要下注的方法
    while(0.7>adjustscore>0.66) and maxBet==15:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))
    

    #拿到flush straight 時，第二輪要下注的方法
    while(0.7>adjustscore>0.66) and maxBet==30:        
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))

    

    #拿到4cards 時，第一輪要下注的方法
    while (0.66>adjustscore>0.56) and maxBet==15:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))
    

    #拿到4cards 時，第二輪要下注的方法
    while 0.66>adjustscore>0.56 and maxBet==30:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))
    

    #拿葫蘆時，第一輪要下注的方法
    while (0.45<=adjustscore<=0.54) and maxBet==15:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))
    

    #拿到葫蘆 時，第二輪要下注的方法
    while (0.45<=adjustscore<=0.54) and maxBet==30:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))

    

    #拿straight時，第一輪要下注的方法
    while 0.33<adjustscore<0.4 and maxBet==15:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))

    

    #拿到straight時，第二輪要下注的方法
    while 0.33<adjustscore<0.4 and maxBet==30:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))


    #拿 3cards 時，第一輪要下注的方法
    while 0<adjustscore<0.33 and maxBet==15:
        instruction = iQ.get()
        if instruction == 'action:bet,check'  : #第一次下注時而且是從你開始下注
            myBet = target
            isSetter = True
            rQ.put('bet %d' % myBet)
        elif instruction == 'action:raise,call,fold': #對方下注時，而且對方下注還沒到最大上限
            if target > oppBet: # raise
                myBet = oppBet
                myRaise = target-oppBet
                myBet += myRaise
                isSetter = True
                rQ.put('raise %d to be %d' % (myRaise,myBet))
            elif target == oppBet: # call
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
            else:
                myBet = oppBet
                rQ.put('call %d' % oppBet)
                break
        elif instruction == 'action:call,fold': # 第一次下注時，對方有下注，還下max
            if oppBet >= target: # call
                myBet = oppBet
                rQ.put('call %d' % myBet)
                break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
        else:
            print('%s > unknown instruction: %s' % (name,instruction))


    #拿到 3cards 時，第二輪要下注的方法
    while 0<adjustscore<0.33 and maxBet==30:
        instruction = iQ.get()
        if instruction == 'action:bet,check':
            checked = True
            rQ.put('check')
            if oppChecked: # both check, end betting
                break
        elif instruction == 'action:raise,call,fold': 
            rQ.put('fold')
            break 
        elif instruction == 'action:call,fold':
            rQ.put('fold')
            break
        elif instruction.startswith('opponent bet'): # the 3rd token is the amount of bet
            oppBet = int(instruction.split()[2])
            isSetter = False
        elif instruction.startswith('opponent raise'): # the 3rd token the amount of raise
            oppBet = myBet + int(instruction.split()[2])
            isSetter = False
        elif instruction == 'opponent check':
            oppChecked = True
            if checked:
                break
        elif instruction == 'opponent fold':
            break
        elif instruction == 'opponent call':
            oppBet = myBet
            break
    return myBet,oppBet,isSetter

    
            
def setTarget(cards):
    """
    20180524
    Given the five cards, set the target bet.

    cards: The five cards. See "analyzeHand" for more details.

    Returns: a score such that 0 <= score <= 1.
        Larger score implies better hands and you should bet more.
    """
    score,cat = analyzeHand(cards)
    target=0
    if score<40000:
        score=0
        target=0
    else:
        score=((score-20000)/90000)

    score = max(0,score)
    score = min(1,score)
    return score

def Target(adjustscore,maxBet):
    target=0
    #5 cards
    if adjustscore>0.7 and maxBet==15:
        target=11
        return target
    elif adjustscore>0.7 and maxBet==30:
        target=28
        return target
    #皇家同花順
    elif 0.7>adjustscore>0.66 and maxBet==15:
        target=10
        return target
    elif 0.7>adjustscore>0.66 and maxBet==30:
        target=28
        return target
    #4cards
    elif 0.66>adjustscore>0.56 and maxBet==15:
        target=10
        return target
    elif 0.66>adjustscore>0.56 and maxBet==30:
        target=28
        return target
    #葫蘆
    elif 0.45<=adjustscore<=0.54 and maxBet==15:
        target=10
        return target
    elif 0.45<=adjustscore<=0.54 and maxBet==30:
        target=18
        return target
    #straight
    elif 0.33<adjustscore<0.4 and maxBet==15:
        target=10
        return target
    elif 0.33<adjustscore<0.4 and maxBet==30:
        target=17
        return target
    #3 cards
    elif 0.33>adjustscore>0 and maxBet==15:
        target=8
        return target
    elif 0.33>adjustscore>0 and maxBet==30:
        target=0
        return target
    #two pair and one pair
    elif adjustscore == 0:
        target=0
        return target
    
def changeCards(cards,maxChange=5):
    """
    20180524
    Determine which cards to change.
    The strategy is simple -- give up the singltons except for when the hand is straight.

    cards: The five cards. See "analyzeHand" for more details.
    maxChange: The maximum number of cards that can be changed.
        If there are more cards than "maxChange" that we would like to give up,
        randomly pick "maxChange" ones to replace.

    Returns: The set of cards to give up.
    """
    hasJoker = False
    rankToCount = dict()
    suitToCount = dict() # needed to tell straight from royal straight flush
    ### pre-processing
    for card in cards:
        if len(card) == 1: # joker
            hasJoker = True
        else:
            rankToCount[card[1]] = rankToCount.get(card[1],0) + 1
            suitToCount[card[0]] = suitToCount.get(card[0],0) + 1
    countToRank = dict()
    for k in rankToCount:
        countToRank.setdefault(rankToCount[k],list()).append(k) #這個會創建一個反向的dictionary ex.{2: ['A', 'K'], 1: ['J']}
   
    score,cat = analyzeHand(cards)
    targetCards = set() # the cards to change
    if cat == 'five card' or cat == 'royal straight flush' or cat == 'full house':
        pass        #不做任何事
    elif cat == 'straight' :
        for card in cards:
            if card != 'J' and (card[1]=='J'or card[1]=='Q' or card[1]=='K'):
                targetCards.add(card)
                break
    elif cat == 'four card': # change the singleton
        for card in cards:
            if card != 'J' and card[1] in countToRank[1]:
                targetCards.add(card)
                break
    elif cat == 'three card': # give up the two singleton cards
        for card in cards:
            if card != 'J' and card[1] in countToRank[1]: # skip singltons
                targetCards.add(card)
    elif cat == 'two pair' or cat == 'one pair': # give up the singletons
        for card in cards:
            if card != 'J' and card[1] in countToRank[1]:
                targetCards.add(card)
    else:
        print('SOMETHING WRONG in "changeCards()" .........................................')
    ###
    if maxChange < len(targetCards):
        targetCards = random.sample(targetCards,maxChange)
    return targetCards

def play(gameCount,iQ,rQ):
    """
    This function implements the fate17 protocol.
    Compared to the players in v1, decisions are now somewhat determinnistic, according to
    the cards in hand.
    * Bugfix:
        In v0 and v1, there was a bug that the host took the changed cards but didn't give
        back replacement cards. This is fixed in this version.

    gameCount: the number of games to play.
    iQ: the instruction queue. (See "betting2" for more.)
    rQ: the response queue. (See "betting2" for more.)
    """
    ########## ########## ########## ########## ########## INITIALIZATION
    balance = 0
    rQ.put('%s report for %d games' % (name,gameCount)) # You can say anything here ...
    ##### start games
    for gameIndex in range(1,gameCount+1):
        ##### receive the assigned order (first or second)
        instruction = iQ.get() # first or second
        leader = True if instruction == 'first' else False
        ##### pay ante
        instruction = iQ.get()
        balance -= 5
        ##### receive cards
        instruction = iQ.get()
        hand = instruction.split(' ')[1].split(',') #輸出一個排長怎樣的list
        ########## ########## ########## ########## BETTING INTERVAL I
        minBet = 5
        maxBet = 15

        adjustscore = setTarget(hand)
        target=Target(adjustscore,maxBet)
        
        myBet1,oppBet1,isSetter1 = betting2(name,iQ,rQ,minBet,maxBet,adjustscore,target,hand)
        balance -= myBet1
        if myBet1 == 0 and oppBet1 == 0: # both check
            continue # go to next game
        elif myBet1 != oppBet1: # no agreement on bet
            if isSetter1: # get all money in the pot (ante lost to the host)
                balance += myBet1 + oppBet1
            continue # go to next game
        ########## ########## ########## ########## CHANGING CARDS
        if isSetter1: # me change first
            instruction = iQ.get() # action:change
            selected = changeCards(hand,5) # can change up to 5 cards
            rQ.put('change %s' % (','.join(selected)))
            instruction = iQ.get() # cards J,QH -- was missing in v0 and v1
            newCards = list() if len(selected) == 0 else instruction.split()[1].split(',')
            iQ.get() # opponent change X cards
        else: # the opponent changes first
            instruction = iQ.get() # opponent change X cards
            oppChangeCount = int(instruction.split()[2])
            iQ.get() # action:change
            selected = changeCards(hand,7-oppChangeCount)
            rQ.put('change %s' % (','.join(selected)))
            instruction = iQ.get() # cards J,QH -- was missing in v0
            newCards = list() if len(selected) == 0 else instruction.split()[1].split(',')
        for i in selected: # remove changed cards
            hand.remove(i)
        for i in newCards: # include new cards
            hand.append(i)
        ########## ########## ########## ########## BETTING INTERVAL II
        minBet = myBet1 + 1
        maxBet = 30

        adjustscore = setTarget(hand)
        target=Target(adjustscore,maxBet)
        
        myBet2,oppBet2,isSetter2 = betting2(name,iQ,rQ,minBet,maxBet,adjustscore,target,hand)
        balance -= myBet2
        if myBet2 == 0 and oppBet2 == 0: # both check -- split the pot (no ante)
            balance += myBet1
            continue
        elif myBet2 != oppBet2: # no agreement in betting interval 2
            if isSetter2: # get all the money in the pot (no ante)
                balance += myBet1 + myBet2 + oppBet1 + oppBet2
            continue
        ########## ########## ########## ########## SHOW HANDS
        response = iQ.get() # opponent cards J,HA,DA,CQ,CA <=== added in v2.1
        response = iQ.get() # win, lose, or tie
        if response == 'win': # win the pot and ante (myBet == oppBet)
            balance += (myBet1 + myBet2 + ANTE) * 2
        elif response == 'tie': # split the pot and get ante back
            balance += myBet1 + myBet2 + ANTE
    #print('Hi, this is %s. My final balance should be %d.' % (name,balance))
    
