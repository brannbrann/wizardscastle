#!/usr/bin/python
# Wizard's Castle!
'''
*****************************************************
*                                                   *
* WIZARD'S CASTLE GAME FROM JULY/AUGUST 1980        *
* ISSUE OF RECREATIONAL COMPUTING MAGAZINE          *
* WRITTEN FOR EXIDY SORCERER BY JOSEPH R. POWER     *
* MODIFIED FOR HEATH MICROSOFT BASIC BY J.F.STETSON *
* NOW RE-WRITTEN IN PYTHON BY BRANN MITCHELL        *
*                                                   *
*****************************************************
'''
import random
import sys
import functools

class WizardsCastle(object):
    def __init__(self, max_speed=False, test_mode=False):
        self.second_coefficient = 1.0
        self.test_mode = test_mode
        if max_speed:
            self.make_max_speed()

    def make_max_speed(self):
        self.second_coefficient = 0

    def test_input(self, prompt, cmds, input):
        if self.test_mode:
            return input
        else:
            command = input(prompt)
            if command not in cmds:
                raise ValueError
            return command

    class Room:
        def __init__(self):
            self.revealed = False
            self.monster = ''
            self.gold = 0
            self.stairup = []
            self.stairdown = []
            self.sinkhole = []
            self.exit = False
            self.treasure = ''
            self.OrbOfZot = False
            self.RuneStaff = False
            self.misc = ''
            self.food = ''

    def play(self, test_arg=None):
        # Set up constants
        # Because we start castlemap at 1, mapsize is 513
        # 8*8*8 = 512
        # mapsize = 513, cause we start at index 1 for easy math
        mapsize = 513
        sinkholes = 4
        races = ['ELF', 'DWARF', 'HUMAN', 'HOBBIT']
        weapons = ['DAGGER', 'MACE', 'SWORD', 'HANDS']
        armors = ['LEATHER', 'CHAINMAIL', 'PLATE', 'NO ARMOR']
        monsters = ['KOBOLD', 'ORC', 'WOLF', 'GOBLIN', 'OGRE', 'TROLL', 'BEAR', 'MINOTAUR', 'GARGOYLE', 'CHIMERA',
                    'BALROG', 'DRAGON', 'VENDOR']
        treasures = ['RUBY RED', 'NORN STONE', 'PALE PEARL', 'OPAL EYE', 'GREEN GEM', 'BLUE FLAME', 'PALANTIR',
                    'SILMARIL']
        misc = ['POOL', 'CHEST', 'FLARES', 'WARP', 'CRYSTAL ORB', 'BOOK', 'LAMP']
        food = ['SANDWICH', 'STEW', 'SOUP', 'BURGER', 'ROAST', 'FILET', 'TACO', 'PIE']

        self.playintro()
        castlemap = self.initmap(mapsize, sinkholes)
        self.populatemap(castlemap, monsters, treasures, food, misc)

        # Setup player
        player = self.makeplayer(races, weapons, armors)
        playerpos = [1,0,4]
        turn = 1
        self.displaystatus
        print(f"OK, {player['race']}, YOU ARE NOW ENTERING THE CASTLE!")
        self.displaymap(castlemap, playerpos)
        self.displayroom(castlemap, playerpos) # shows room player is in

        
        # Commands for main loop
        cmds = ['N','S','E','W','U','D','DR','M','F','L','O','G','T','Q', 'H']
        turn = 0
        # Main loop
        while not player['OrbOfZot'] and not player['RuneStaff']:
            turn += 1
            try:
                command = self.test_input('ENTER YOUR COMMAND (N/S/E/W/U/D/DR/M/F/L/O/G/T/Q)? ', cmds, test_arg)
                if command == 'H':
                    self.displayhelp
            except ValueError:
                self.displayhelp
                continue
            # Begin massive if ladder
            # I wish Python had a case keyword
            # Do Stuff
            self.atmosphere(player, monsters)

    def displayroom(self, castlemap, playerpos):
        # Displays the map
        # Hide rooms not discovered
        # Always uncover the room the player is in
        level, x, y = playerpos
        castlemap[level][x][y]['revealed'] = True
        # To make a nice printout, each room is a 8 '.' list
        # Fill out the list with room properties:
        # E is Exit, M is Monster, T is Treasure, U is stairup
        # D is stairdown, P is pool, C is chest, S is sinkhole
        # Player is '@' until I can think of something better
        # We print roomd out as a 3x3 matrix
        roomd = ["."] * 8
        board = castlemap[level]
        for row in range(0,7):
            if row % 7 == 1:
                print() # print newline after a row
            for col in range(0,7):
                if board[row][col]['revealed'] == True:
                    if self.isexit(index):
                        roomd[1] = 'E'
                    if row == x and col == y:
                        roomd[4] = '@'
                    if board[row][col]['monster'] != '':
                        if board[row][col]['monster'] == 'VENDOR':
                            roomd[0] = 'V'
                        else:
                            roomd[0] = 'M'
                    if board[row][col]['treasure'] != '':
                        roomd[5] = 'T'
                    if board[row][col]['sinkhole'] != [0,0,0]:
                        roomd[4] = 'S'
                    if board[row][col]['stairup'] != [0,0,0]:
                        roomd[2] = 'U'
                    if board[row][col]['stairdown'] != [0,0,0]:
                        roomd[6] = 'D'
                    if board[row][col]['food'] != '':
                        roomd[7] = 'F'
                    if board[row][col]['misc'] != '':
                        # Set to first letter of misc value
                        what = board[row][col]['misc']
                        if what == 'CRYSTAL ORB':
                            roomd[1] = 'O'
                        else:
                            roomd[1] = what[0]
                else:
                    roomd[4] = '?'
                for index, item in enumerate(roomd, start=1):
                    print(item, end=' ' if index % 3 else '\n')

    def displaymap(self, castlemap, playerpos):
        # Displays the map
        # Hide rooms not discovered
        # Always uncover the room the player is in
        level, x, y = playerpos
        castlemap[level][x][y]['revealed'] = True
        # To make a nice printout, each room is a 3x '.' list
        # Fill out the list with room properties:
        # E is Exit, M is Monster, T is Treasure, U is stairup
        # D is stairdown, P is pool, C is chest, S is sinkhole
        # Player is '@' until I can think of something better
        # We print roomd out as a 1x3 matrix
        roomd = ["."] * 3
        board = castlemap[level]
        for row in range(0,7):
            if row % 7 == 0:
                print() # print newline after a row
            for col in range(0,7):
                if board[row][col]['revealed'] == True:
                    if self.isexit(level, x, y):
                        roomd[1] = 'E'
                    if row == x and col == y:
                        roomd[1] = '@'
                    if board[row][col]['monster'] != '':
                        if board[row][col]['monster'] == 'VENDOR':
                            roomd[0] = 'V'
                        else:
                            roomd[0] = 'M'
                    if board[row][col]['treasure'] != '':
                        roomd[2] = 'T'
                    if board[row][col]['sinkhole'] != [0,0,0]:
                        roomd[1] = 'S'
                    if board[row][col]['stairup'] != [0,0,0]:
                        roomd[2] = 'U'
                    if board[row][col]['stairdown'] != [0,0,0]:
                        roomd[0] = 'D'
                    if board[row][col]['food'] != '':
                        roomd[2] = 'F'
                else:
                    roomd[1] = '?'
                for index, item in enumerate(roomd, start=1):
                    print(item, end=' ' if index % 3 else ' ')

    def isexit(self, index):
        if index == 4:
            return True
        else:
            return False

    def encodemap(self, lvl, x, y):
        sl = (lvl - 1) * 64
        sx = x * 8
        sy = y
        index = sl + sx + sy
        return index

    def decodemap(self, index):
        lvl = (index // 64) + 1
        x = (index % 64) // 8
        y = (index % 64) - (x * 8)
        return lvl, x, y

    def initmap(self, mapsize, sinkholes):
        # Initializes castlemap, 8x8x8
        # Set up stairs
        # Set up sinkholes
        # Return castlemap
        print("ZOT'S CREATING THE CASTLE...")
        # Make the levels
        # To make it easier, castlemap is a single dimension
        # With empty rooms
        # Tom's example to decode the list:
        # room = 237
        # level = room // 64 + 1
        # x = (room % 64) // 8
        # y = (room % 64) - (x * 8)
        # print(level, x, y)
        # >>> 3 5 5
        # And it starts with 1 :)
        # Remember levels start with 1, Brann
        castlemap = {}
        for i in range(1, mapsize):
            c = {}
            c = self.Room()
            castlemap[i] = c

        # Set the exit, level 1, row 0, col 4:
        castlemap[4].exit = True
        print(sys.getsizeof(castlemap))
        # Set stairs
        print('SETTING STAIRS...')
        # increments by 64 each iter
        base = 0
        # fix for arbitrary mapsize
        for i in range(0, 7):
            # just a counter
            level = i + 1
            # add base to randroom
            rroom = base + self.genrand(0, 63)
            # rroom + 64 = downstairs room
            downstairs = rroom + 64
            if level == 1:
                castlemap[rroom].stairdown = downstairs
                castlemap[downstairs].stairup = rroom
            if 1 < level < 8:
                castlemap[rroom].stairdown = downstairs
                castlemap[downstairs].stairup = rroom
            # No downstairs on lvl 8
            print(f"level: {level}, index: {rroom}, map: {castlemap[rroom].__dict__.items()}")
            print(f"level: {level + 1}, index: {downstairs}, map: {castlemap[downstairs].__dict__.items()}")
            base += 64

        # Set sinkholes
        print('CREATING SINKHOLES...')
        sinks = self.genrand(1, sinkholes)
        for _ in range(sinks+1):
            # No sinkholes on lvl 1 and level 8
            index = self.genrand(1, mapsize)
            # Don't put sinkholes in rooms with stairs
            while ((index // 64) + 1 == 1 or (index // 64) + 1 == 8) and self.isoccupied(castlemap, index):
                level = self.genrand(1, mapsize)
            sinkto = [index + 64]
            print(sinkto)
            print(castlemap[index])
            castlemap[index].sinkhole = sinkto
        return castlemap

    def randroom(self, castlemap, index):
        # Checks the availability of a room
        # Generate new set of x, y if room is occupied
        level = self.genrand(1,8)
        x = self.genrand(0,7)
        y = self.genrand(0,7)
        while self.isoccupied(castlemap, index):
            level = self.genrand(1,8)
            x = self.genrand(0,7)
            y = self.genrand(0,7)
        return level, x, y

    # Memoize that shit, thanks @td.knox for this!
    @functools.lru_cache(maxsize=512)
    def isoccupied(self, castlemap, index):
        # Maybe fix this to accept key-value pair
        # to make it more universal
        print(castlemap[index])
        if castlemap[4]:
            return True
        elif castlemap[index].sinkhole != [0]:
            return True
        elif castlemap[index].stairup != [0]:
            return True
        elif castlemap[index].stairdown != [0]:
            return True
        elif castlemap[index].monster != '':
            return True
        # elif castlemap[level][x][y]['treasure'] != '':
        #     return True
        elif castlemap[index].misc != '':
            return True
        elif castlemap[index].food != '':
            return True
        elif castlemap[index].OrbOfZot == True:
            return True
        elif castlemap[index].RuneStaff == True:
            return True
        else:
            return False

    def populatemap(self, castlemap, monsters, treasures, food, misc):
        # Populate the dungeon!
        # Monsters, treasures, pools, chests, etc.

        # Place RuneStaff: choose random floor, room, without a sinkhole
        # Choose random monster with runestaff
        level, x, y = self.randroom(castlemap)
        castlemap[level][x][y]['RuneStaff'] = True
        # A vendor is a type of monster, but don't put one with the runestaff
        castlemap[level][x][y]['monster'] = monsters[self.genrand(0,len(monsters) - 1)]

        # Place OrbOfZot: choose random floor, room, without a sinkhole
        level, x, y = self.randroom(castlemap)
        castlemap[level][x][y]['OrbOfZot'] = True

        # Place Vendors: One per floor
        for level in len(castlemap):
            x = self.genrand(0,7)
            y = self.genrand(0,7)
            while self.isoccupied(castlemap, level, x, y):
                x = self.genrand(0,7)
                y = self.genrand(0,7)
            castlemap[level][x][y]['monster'] = 'VENDOR'

        # Populate with monsters
        # Apparently one monster and type per floor
        # I don't remember this
        for level in len(castlemap):
            x = self.genrand(0,7)
            y = self.genrand(0,7)
            while self.isoccupied(castlemap, level, x, y):
                x = self.genrand(0,7)
                y = self.genrand(0,7)
            castlemap[level][x][y]['monster'] = monsters[level]
        # For the monsters left out,'GARGOYLE', 'CHIMERA', 'BALROG', 'DRAGON'
        # Put one of each in a random level below 4th, room, with a treasure and gold
        bigmonsters = ['GARGOYLE', 'CHIMERA', 'BALROG', 'DRAGON']
        ttemp = treasures
        for level in len(castlemap):
            if level < 4:
                continue
            x = self.genrand(0,7)
            y = self.genrand(0,7)
            while self.isoccupied(castlemap, level, x, y):
                x = self.genrand(0,7)
                y = self.genrand(0,7)
            for monster in bigmonsters:
                castlemap[level][x][y]['monster'] = monster
                castlemap[level][x][y]['gold'] = self.genrand(300,1000)
                castlemap[level][x][y]['misc'] = 'CHEST'
                castlemap[level][x][y]['treasure'] = ttemp.pop(self.genrand(0,3)) # just trying something new
        # Populate with food, misc, and treasures
        for level in len(castlemap):
            x = self.genrand(0,7)
            y = self.genrand(0,7)
            while self.isoccupied(castlemap, level, x, y):
                x = self.genrand(0,7)
                y = self.genrand(0,7)
        return castlemap

    def makeplayer(self, races, weapons, armors):
        playerone = {
            'race': 'HUMAN',
            'sex': 'MALE',
            'str': 0,
            'int': 0,
            'dex': 0,
            'armortype': ['NO ARMOR'],
            'armorhealth': 1,
            'weapon': ['HANDS'],
            'weapondamage': 1,
            'haslamp': False,
            'flares': 0,
            'gold': 60,
            'bookstuck': False,
            'blind': False,
            'OrbOfZot': False,
            'RuneStaff': False,
            'food': {'taco': 1},
            'Treasures': [],
            'potions': { 'strength': 0,
                        'intelligence': 0,
                        'dexterity': 0 }
        }
        print('\nALL RIGHT, BOLD ONE.\nYOU MAY BE AN ELF, DWARF, HUMAN, OR HOBBIT.\n')
        cmds = ['E', 'D', 'HU', 'HO']
        while True:
            try:
                command = self.test_input("ENTER E, D, HU, or HO: ", cmds, None)
                break
            except ValueError:
                print("** THAT WAS INCORRECT. PLEASE TYPE E, D, HU, OR HO.")
                continue
        # Set up player attributes. 34 is the base points, with 6 more to be allocated.
        if command == 'E':
            playerone['race'] = 'ELF'
            playerone['str'] = 8
            playerone['int'] = 13
            playerone['dex'] = 13
        elif command == 'D':
            playerone['race'] = 'DWARF'
            playerone['str'] = 14
            playerone['int'] = 13
            playerone['dex'] = 8
        elif command == 'HU':
            playerone['race'] = 'HUMAN'
            playerone['str'] = 12
            playerone['int'] = 11
            playerone['dex'] = 11
        else:
            playerone['race'] = 'HOBBIT'
            playerone['str'] = 9
            playerone['int'] = 11
            playerone['dex'] = 14

        print(f"\nOK, {playerone['race']}, WHICH SEX DO YOU PREFER (M/F): ")
        cmds = ['M', 'F']
        while True:
            try:
                command = self.test_input("\nENTER M or F: ", cmds, None)
                break
            except ValueError:
                print(f"** CUTE {playerone['race']}, REAL CUTE. TRY M OR F.")
                continue

        print(f"""OK, {playerone['race']}, YOU HAVE THE FOLLOWING ATTRIBUTES: 
                STRENGTH = {playerone['str']} INTELLIGENCE = {playerone['int']} DEXTERITY = {playerone['dex']}""")
        print('YOU HAVE 6 OTHER POINTS TO ALLOCATE AS YOU WISH.')
        # Allocate points

        # Buy gear

        return playerone

    def displaystatus(self, player):
        print(f"""STRENGTH = {player['str']} INTELLIGENCE = {player['int']} DEXTERITY = {player['dex']}
                FLARES = {player['flares']} GOLD PIECES = {player['gold']}
                WEAPON = {player['weapon']} ARMOR = {player['armor']}
                TREASURES: {player['Treasures']}
                """)
        if player['haslamp']:
            print('...AND A LAMP.')

    def genrand(self, low, high):
        # Always skip the exit!
        index = random.randint(low, high)
        while index == 4:
            index = random.randint(low, high)
        return index
    
    def atmosphere(self, player, monsters):
        effects = ['A SCREAM!',
            'FOOTSTEPS!',
            'A WUMPUS!',
            'THUNDER!',
            'FAINT RUSTLING NOISES!',
            'A BAT FLY BY!',
            'FEEL LIKE YOU\'RE BEING WATCHED!',
            'STEPPED ON A FROG!'
            'SNEEZED!'
            ]
        atmos = "YOU "
        if self.genrand(0,20) <= 10:
            what = self.genrand(0,9)
            if what == 5 and player['isblind']:
                print(atmos + 'HEAR ' + effects[what])
            else:
                print(atmos + 'SEE ' + effects[what])
            if what < 5:
                print(atmos + 'HEAR ' + effects[what])
            if what > 5 and what <= 8:
                print(atmos + effects[what])
            if what == 9:
                print(atmos + f"SMELL {monsters[self.genrand(0,11)]} FRYING!")

            

    def playintro(self):
        print(
            '''
                        * * * THE WIZARD'S CASTLE * * *
            MANY CYCLES AGO, IN THE KINGDOM OF N'DIC, THE GNOMIC
            WIZARD ZOT FORGED HIS GREAT *ORB OF POWER*. HE SOON
            VANISHED, LEAVING BEHIND HIS VAST SUBTERRANEAN CASTLE
            FILLED WITH ESURIENT MONSTERS, FABULOUS TREASURES, AND
            THE INCREDIBLE *ORB OF ZOT*. FROM THAT TIME HENCE, MANY
            A BOLD YOUTH HAS VENTURED INTO THE WIZARD'S CASTLE. AS
            OF NOW, *NONE* HAS EVER EMERGED VICTORIOUSLY! BEWARE!!
            '''
        )

    def displayhelp(self, player):
        print(
            '''
            *** WIZARD'S CASTLE COMMAND AND INFORMATION SUMMARY ***
            
            THE FOLLOWING COMMANDS ARE AVAILABLE :

            H/ELP     N/ORTH    S/OUTH    E/AST     W/EST     U/P
            D/OWN     DR/INK    M/AP      F/LARE    L/AMP     O/PEN
            G/AZE     T/ELEPORT Q/UIT"
            
            THE CONTENTS OF ROOMS ARE AS FOLLOWS :

            . = EMPTY ROOM      B = BOOK            C = CHEST
            D = STAIRS DOWN     E = ENTRANCE/EXIT   F = FLARES
            G = GOLD PIECES     M = MONSTER         O = CRYSTAL ORB
            P = MAGIC POOL      S = SINKHOLE        T = TREASURE
            U = STAIRS UP       V = VENDOR          W = WARP/ORB

            THE BENEFITS OF HAVING TREASURES ARE :

            RUBY RED - AVOID LETHARGY     PALE PEARL - AVOID LEECH
            GREEN GEM - AVOID FORGETTING  OPAL EYE - CURES BLINDNESS
            BLUE FLAME - DISSOLVES BOOKS  NORN STONE - NO BENEFIT
            PALANTIR - NO BENEFIT         SILMARIL - NO BENEFIT

            PRESS RETURN WHEN READY TO RESUME, ";R$(RC);".";

            ** SILLY ";R$(RC);", THAT WASN'T A VALID COMMAND!
            '''
        )
        try:
            input(f"PRESS ENTER WHEN READY TO RESUME, {player['race']}.")
        except ValueError:
            print(f"** SILLY {player['race']}, THAT WASN'T A VALID COMMAND!")
            pass

if __name__ == "__main__":
    game = WizardsCastle()
    game.play()
