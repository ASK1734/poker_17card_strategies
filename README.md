# Seventeen Cards

## Overview
This release is intended to  
1. get you familiar with the communication between the host and the player, and    
2. provide player templates based on which you can develop your own player.

---

## Contents
This release includes four Python source files, a README file, the game flow, and the game instruction file.

### PK.py
This is the management program. It coordinates the game play.  


### <span style="color:orange">Ref01.py</span>
This player set the betting target according to the cards in hand.  
The card changing strategy is straightforward -- give up the singletonn cards except for straight.  
The player's name is ***sandy***.

### <span style="color:orange">team18.py</span>
The player that I develop.

### utility.py
Tools and classes defined to facilitate the game play.  

### README.pdf
This file.

### fate17_gameFlow
The game flow.  

### fate17_instructions
List all instructions and show where they appear in the game flow.  
<span style="color:orange">Updated to include the missing instruction that gives back the replacement cards.</span>

---

## Host Instructions & Player Responses
To try the release, run the "PK.py" file.  
You will see the instructions the host send to the players and the player responses.  
The following is an example.

	<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Game 981 of 1000
	> rambo: first
	> sandy: second
	> rambo: ante
	> sandy: ante
	> rambo: cards J,CQ,CK,HQ,SJ
	> sandy: cards HA,DA,DK,SQ,CA
	
This is the initialization stage.  
The format of instructions sent to players is  
	> *name*: *instruction*  
where *name* is the player name that you define in your player source program, e.g., `name = 'sandy'` in "Ref01.py", and *instruction* is the message that the player, sandy or rambo here, receives.

Thus, `> rambo: first` informs rambo that he is the first player of this game, `> sandy: ante` informs sandy that she has to deduct 5 coins from her balance, and `> rambo: cards J,CQ,CK,HQ,SJ` indicates the five cards dealt to rambo.


	<<<<<<<<<<<<<<<<<<<<< BETTING INTERVAL I
	> rambo: action:bet,check
	rambo > bet 15
	> sandy: opponent bet 15
	> sandy: action:call,fold
	sandy > call 15
	> rambo: opponent call
	> rambo's balance: -3417
	> sandy's balance: -4623

	
This is the first betting interval.  
An instruction starting with `action:` means that a response is expected.  
For instance, after rambo receives `action:bet,check`, he has to decide and tell the host whether to `bet` or `check`.  
To bet, send to the host the message `bet n` where *n* is the amount of bet.
To check, simply send the `check` message to the host.  
Note that the host will forward rarmbo's response to sandny.  
Here, rambo decides to bet 15; so, sandy receives the instruction `opponent bet 15`.

	<<<<<<<<<<<<<<<<<<<<<<<<< CHANGING CARDS
	> rambo: action:change
	rambo > change CQ,J,CK
	> rambo: cards SK,DJ,HK                 # added in v2.
	> sandy: opponent change 3 cards
	> sandy: action:change
	sandy > change SQ,DK
	> sandy: cards SA,HJ                    # added i v2.
	> rambo: opponent change 2 cards
	
This is the card changing stage.  
The bet setter gets to change cards first.
Here rambo decides to change three cards; therefore, he replies with `change` followed by the cards separated by ','.  
Host will send rambo three replacement cards.
On the other hand, sandy changes two cards.  
Note that the other player will be informed of the number of changed cards, not the cards.


	<<<<<<<<<<<<<<<<<<<< BETTING INTERVAL II
	> rambo: action:bet,check
	rambo > bet 30
	> sandy: opponent bet 30
	> sandy: action:call,fold
	sandy > call 30
	> rambo: opponent call
	> sandy's balance: -4653
	> rambo's balance: -3447
	
This is the second betting interval; it is the same as interval 1 except for the lower and upper bounds of bet.


	<<<<<<<<<<<<<<<<<<<<<<<<<<<<< SHOW HANDS
	> rambo: opponent cards HA,DA,CA,SA,HJ    # added in v2.1
	> sandy: opponent cards HQ,SJ,SK,DJ,HK    # added in v2.1
	> sandy: win
	> rambo: lose
	> rambo's balance: -3447
	> sandy's balance: -4553



If the game stands, the winner will be determined and the balance shown.

### Adjustment

Currently, the number of games is 1000 (`gameCount = 1000` at line 302 of PK.py).  
Feel free to adjust the game count.

## <span style="color:orange">Designing Your Own Player</span>
There are now two players, i.e., Ref01 and Ref02, that you can reference.  
**Ref01** is a somewhat deterministic player; **Ref02**, on the other hand, is a random player.

A player file must define the following.  
1. The global variable `name` which is the player name.  
2. The function `play(gameCount,iQ,rQ)` where *gameCount* is the number of games to play, *iQ* the instruction queue, and *rQ* the response queue.

A player communicates with the host via the instruction queue *iQ* and the response queue *rQ*.  
The `iQ.get()` expression gets one host instruction which is a string.  
On the other hand, `rQ.put()` with the response as the argument passes your decision to the host.

If you receive an instruction that starts with "action", you must respond within 10 seconds; otherwise, you will be timeout-ed.

It is very important that you **strictly** follow the communication protocol. Otherwise, your program will hang and nothing happens.

### <span style="color:orange">Note</span>
1. If you want to used codes in *utility.py*, copy and paste them to your own program.
2. PK.py and utility.py may be changed or renamed without notice.
3. To specify the players in the PK game, just modify P1 and/or P2 near the end of PK.py.  
For example, if you want your player (in file: T03\_XYZ.py) to PK against sandy, P1 and P2 should be set as follows.  
	```P1 = 'Ref01'```  
	```P2 = 'T03_XYZ'```  
To avoid file/player name conflict in the future, you should start your file and player names with **T_XX** where **XX** is your two-digit team number, e.g., 03 for team 3 and 12 for team 12.
