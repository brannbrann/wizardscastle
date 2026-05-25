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
from __future__ import annotations
import random
import sys
import functools
from dataclasses import dataclass, field

# Optional color support for nicer map display. If colorama isn't installed
# we fall back to no-op color codes so the script still runs.
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
    C_RED = Fore.RED
    C_GREEN = Fore.GREEN
    C_BLUE = Fore.BLUE
    C_YELLOW = Fore.YELLOW
    C_CYAN = Fore.CYAN
    C_MAGENTA = Fore.MAGENTA
    C_WHITE = Fore.WHITE
    C_RESET = Style.RESET_ALL
except Exception:
    C_RED = C_GREEN = C_BLUE = C_YELLOW = C_CYAN = C_MAGENTA = C_WHITE = C_RESET = ''


# Game tuning constants
# Armor mitigation values used both in combat and for explosion traps.
ARMOR_REDUCTION = {
    'PLATE': 3,
    'CHAINMAIL': 2,
    'LEATHER': 1,
    'NO ARMOR': 0,
}

@dataclass
class Room:
    """Represents a single room in the castle."""
    revealed: bool = False
    monster: str = ''
    gold: int = 0
    potions: dict = field(default_factory=dict)
    locked: bool = False
    lock_level: int = 0
    stairup: tuple | None = None  # (level, x, y) or None
    stairdown: tuple | None = None  # (level, x, y) or None
    sinkhole: tuple | None = None  # (level, x, y) or None
    exit: bool = False
    treasure: str = ''
    OrbOfZot: bool = False
    RuneStaff: bool = False
    misc: str = ''
    food: str = ''


class WizardsCastle(object):
    def isoccupied(self, castlemap, level, x, y):
        room = castlemap[level][x][y]
        return any([
            room.stairup,
            room.stairdown,
            room.sinkhole,
            room.exit,
            room.monster != '',
            room.treasure != '',
            room.misc != '',
            room.food != '',
            room.OrbOfZot,
            room.RuneStaff
        ])

    def get_random_empty_room(self, castlemap, llevel=0):
        while True:
            # levels are 0..7, unless overridden
            level = random.randint(llevel, 7)
            x = random.randint(0, 7)
            y = random.randint(0, 7)
            if not self.isoccupied(castlemap, level, x, y):
                return level, x, y
            
    def __init__(self, max_speed=False, test_mode=False, debug=False):
        self.second_coefficient = 1.0
        self.test_mode = test_mode
        self.debug = debug
        if max_speed:
            self.make_max_speed()

    def make_max_speed(self):
        self.second_coefficient = 0

    def test_input(self, prompt, cmds, preset=None):
        # `input` is a builtin; avoid shadowing it and allow an optional
        # preset value for test mode.
        if self.test_mode:
            return preset
        else:
            command = input(prompt)
            if cmds is not None and command not in cmds:
                raise ValueError
            return command

    def play(self, test_arg=None):
        # Set up constants
        # 8*8*8 = 512 (levels 0..7, each 8x8)
        mapsize = 512
        sinkholes = 4
        races = ['ELF', 'DWARF', 'HUMAN', 'HOBBIT']
        weapons = ['DAGGER', 'MACE', 'SWORD', 'HANDS']
        armors = ['LEATHER', 'CHAINMAIL', 'PLATE', 'NO ARMOR']
        monsters = ['KOBOLD', 'ORC', 'WOLF', 'GOBLIN', 'OGRE', 'TROLL', 'BEAR', 'MINOTAUR', 'GARGOYLE', 'CHIMERA',
                    'BALROG', 'DRAGON', 'VENDOR']
        treasures = ['RUBY RED', 'NORN STONE', 'PALE PEARL', 'OPAL EYE', 'GREEN GEM', 'BLUE FLAME', 'PALANTIR',
                    'SILMARIL']
        misc = ['POOL', 'CHEST', 'FLARES', 'WARP', 'CRYSTAL ORB', 'BOOK', 'LAMP', 'SOAP']
        food = ['SANDWICH', 'STEW', 'SOUP', 'BURGER', 'ROAST', 'FILET', 'TACO', 'PIE']

        self.playintro()
        castlemap = self.initmap(mapsize, sinkholes)
        self.populatemap(castlemap, monsters, treasures, food, misc)

        # Setup player
        player = self.makeplayer(races, weapons, armors, test_arg=test_arg)
        # Entrance is at level 0, row 0, col 4 in 0-based indexing
        playerpos = [0,0,4]
        turn = 0
        self.displaystatus(player)
        print(f"OK, {player['race']}, YOU ARE NOW ENTERING THE CASTLE!")
        self.displaymap(castlemap, playerpos, player=player)
        self.displayroom(castlemap, playerpos, player=player) # shows room player is in

        
        # Commands for main loop
        cmds = ['N','S','E','W','U','D','DR','I','M','F','L','O','G','T','Q', 'H', 'RV', 'RH']
        # Main loop
        while not player['OrbOfZot'] and not player['RuneStaff']:
            turn += 1
            try:
                command = self.test_input('ENTER YOUR COMMAND (N/S/E/W/U/D/DR/I/M/F/L/O/G/T/Q)? ', cmds, test_arg)
                if command == 'H':
                    self.displayhelp(player, test_arg=test_arg)
                # Inventory
                if command == 'I':
                    self.displaystatus(player)
                    continue
                # Drink/use outside combat: prefer pool if present
                if command == 'DR':
                    try:
                        lvl, rx, ry = playerpos
                    except Exception:
                        lvl, rx, ry = playerpos[0], playerpos[1], playerpos[2]
                    try:
                        room = self.get_room(castlemap, lvl, rx, ry)
                    except Exception:
                        room = None
                    if room and getattr(room, 'misc', '') == 'POOL':
                        self.drink_from_pool(player, room, test_arg=test_arg)
                    else:
                        self.use_consumable(player, in_combat=False, test_arg=test_arg)
                    continue
                if command == 'F':
                    self.use_light_source(castlemap, playerpos, player, test_arg=test_arg, consume_flare=True)
                    continue
                if command == 'L':
                    self.use_light_source(castlemap, playerpos, player, test_arg=test_arg, consume_flare=False)
                    continue
                if command == 'G':
                    # Gaze into a Crystal Orb if present in the room
                    if not room or getattr(room, 'misc', '') != 'CRYSTAL ORB':
                        print("** IT'S HARD TO GAZE WITHOUT AN ORB!")
                        continue
                    # Possible gaze outcomes
                    outcomes = ['ITEM','BLOODY','POOL','MONSTER','ORB','SOAP']
                    choice = random.choice(outcomes)
                    # Helper to reveal a found room and describe it
                    def reveal_and_show(coords, note=None):
                        if not coords:
                            print('The orb shows nothing of interest.')
                            return
                        l,x,y = coords
                        try:
                            targ = self.get_room(castlemap, l, x, y)
                            targ.revealed = True
                        except Exception:
                            print('The orb shows a vague location.')
                            return
                        if note:
                            print(note)
                        print(f'It reveals level {l} room ({x},{y}):')
                        self.describe_room(targ)

                    # Teleport the orb to a new empty room after a gaze
                    def teleport_orb():
                        # Use the shared teleport helper to move the orb
                        try:
                            self.teleport(castlemap, is_orb=True)
                            print('The crystal orb winks and vanishes to another room.')
                        except Exception:
                            pass

                    if choice == 'SOAP':
                        print('YOU SEE A SOAP OPERA RERUN!')
                        # no map coordinate for this silly vision
                        teleport_orb()
                        continue

                    if choice == 'BLOODY':
                        print('YOURSELF IN A BLOODY HEAP!')
                        # reveal current room
                        try:
                            reveal_and_show(tuple(playerpos))
                        except Exception:
                            pass
                        teleport_orb()
                        continue

                    if choice == 'ORB':
                        print('***THE ORB OF ZOT***')
                        # find the OrbOfZot location
                        found = None
                        for L in range(len(castlemap)):
                            for X in range(8):
                                for Y in range(8):
                                    r = castlemap[L][X][Y]
                                    if getattr(r, 'OrbOfZot', False):
                                        found = (L,X,Y)
                                        break
                                if found: break
                            if found: break
                        reveal_and_show(found)
                        teleport_orb()
                        continue

                    if choice == 'MONSTER':
                        # pick a random monster type and find one in the map
                        mons = []
                        for L in range(len(castlemap)):
                            for X in range(8):
                                for Y in range(8):
                                    r = castlemap[L][X][Y]
                                    if getattr(r,'monster',''):
                                        mons.append((L,X,Y,r.monster))
                        if not mons:
                            print('The orb shows only emptiness.')
                            teleport_orb()
                            continue
                        L,X,Y,mon = random.choice(mons)
                        print(f'{mon} GAZING BACK AT YOU!')
                        reveal_and_show((L,X,Y))
                        teleport_orb()
                        continue

                    if choice == 'ITEM':
                        # look for treasures/books/good food
                        candidates = []
                        for L in range(len(castlemap)):
                            for X in range(8):
                                for Y in range(8):
                                    r = castlemap[L][X][Y]
                                    if getattr(r,'treasure',''):
                                        candidates.append((L,X,Y,r.treasure))
                                    if getattr(r,'misc','') == 'BOOK':
                                        candidates.append((L,X,Y,'BOOK'))
                                    if getattr(r,'food',''):
                                        candidates.append((L,X,Y,r.food))
                        if not candidates:
                            print('The orb shows only emptiness.')
                            teleport_orb()
                            continue
                        L,X,Y,item = random.choice(candidates)
                        print('YOU SEE ' + str(item) + '!')
                        reveal_and_show((L,X,Y))
                        teleport_orb()
                        continue

                    if choice == 'POOL':
                        # show a pool and a random pool effect
                        pools = []
                        for L in range(len(castlemap)):
                            for X in range(8):
                                for Y in range(8):
                                    r = castlemap[L][X][Y]
                                    if getattr(r,'misc','') == 'POOL':
                                        pools.append((L,X,Y,r))
                        if not pools:
                            print('The orb shows only emptiness.')
                            teleport_orb()
                            continue
                        L,X,Y,r = random.choice(pools)
                        # Determine effect for message
                        if getattr(r,'pool', False):
                            stat, delta = r.pool
                            if stat == 'sex':
                                effect = 'sex-flip'
                            elif stat == 'race':
                                effect = f'transforming into {delta}'
                            else:
                                effect = ('stronger' if delta>0 else 'weaker') + ' (' + stat + ')'
                        else:
                            effect = 'some strange change'
                        print('YOURSELF DRINKING FROM A POOL AND BECOMING ' + str(effect).upper())
                        reveal_and_show((L,X,Y))
                        teleport_orb()
                        continue
                # Reveal all rooms (RV) or hide all rooms (RH) during gameplay
                if command == 'T':
                    # Teleport player using OrbOfZot and RuneStaff
                    self.teleport(castlemap, playerpos=playerpos, player=player, test_arg=test_arg, is_orb=False)
                    # teleport counts as movement, so decrement timed effects
                    self.decrement_timed_effects(player)
                    continue
                if command == 'RV':
                    self.reveal_map(castlemap, True)
                    print('All rooms revealed.')
                    continue
                if command == 'RH':
                    self.reveal_map(castlemap, False)
                    print('All rooms hidden.')
                    continue
            except ValueError:
                self.displayhelp(player, test_arg=test_arg)
                continue
            # Movement handling: move player and decrement movement-based timers
            try:
                lvl, rx, ry = playerpos
            except Exception:
                lvl, rx, ry = playerpos[0], playerpos[1], playerpos[2]
            try:
                room = self.get_room(castlemap, lvl, rx, ry)
            except Exception:
                room = None

            if command in ['N','S','E','W']:
                # basic bounded movement
                if command == 'N':
                    rx = max(0, rx - 1)
                elif command == 'S':
                    rx = min(7, rx + 1)
                elif command == 'W':
                    ry = max(0, ry - 1)
                elif command == 'E':
                    ry = min(7, ry + 1)
                playerpos[:] = [lvl, rx, ry]
                # decrement movement-based timed effects
                self.decrement_timed_effects(player)
                self.displaymap(castlemap, playerpos, player=player)
                self.displayroom(castlemap, playerpos, player=player)
                continue
            if command == 'U':
                if room and getattr(room, 'stairup', None):
                    playerpos[:] = list(room.stairup)
                    self.decrement_timed_effects(player)
                    self.displaymap(castlemap, playerpos, player=player)
                    self.displayroom(castlemap, playerpos, player=player)
                else:
                    print('There are no stairs up here.')
                continue
            if command == 'D':
                if room and getattr(room, 'stairdown', None):
                    playerpos[:] = list(room.stairdown)
                    self.decrement_timed_effects(player)
                    self.displaymap(castlemap, playerpos, player=player)
                    self.displayroom(castlemap, playerpos, player=player)
                else:
                    print('There are no stairs down here.')
                continue

            # I wish Python had a case keyword
            # Do Stuff
            self.atmosphere(player, monsters)

            # After atmospheric effects, check the player's current room for monsters/vendors
            try:
                lvl, rx, ry = playerpos
            except Exception:
                lvl, rx, ry = playerpos[0], playerpos[1], playerpos[2]
            try:
                room = self.get_room(castlemap, lvl, rx, ry)
            except Exception:
                room = None

            if room:
                # Auto-pickup food in the room (optional)
                if getattr(room, 'food', ''):
                    f = room.food
                    print(f'You see {f} here.')
                    try:
                        take = self.test_input(f'PICK UP {f}? (Y/N): ', ['Y','N'], None)
                    except ValueError:
                        take = 'N'
                    if take == 'Y':
                        player.setdefault('food', []).append(f)
                        room.food = ''
                        print(f'You picked up {f}.')

                # Offer to open chest if present
                if getattr(room, 'misc', '') == 'CHEST':
                    cmds_chest = ['OPEN','PICK','SMASH','LEAVE']
                    try:
                        action = self.test_input('THERE IS A CHEST HERE. (OPEN/PICK/SMASH/LEAVE): ', cmds_chest, None)
                    except ValueError:
                        action = 'LEAVE'
                    # helper to actually grant contents
                    def trigger_trap():
                        """Random chance for chest traps: explosion (10%) or gas (15%).
                        Returns 'exploded', 'gassed', 'dead', or None if no trap."""
                        r = random.random()
                        # Explosion: destroy contents, random 1d10 damage mitigated
                        if r < 0.10:
                            print('KABOOM! IT EXPLODES!!')
                            # roll 1d10
                            dmg = random.randint(1, 10)
                            # mitigation: armor type static value (as in combat) plus positive dexterity modifier
                            armor = player.get('armor', 'NO ARMOR')
                            armor_reduce = ARMOR_REDUCTION.get(armor, 0)
                            dex_mod = (player.get('dex', 10) - 10) // 2
                            dex_red = max(0, dex_mod)
                            mitig = armor_reduce + dex_red
                            taken = max(0, dmg - mitig)
                            player['hp'] = player.get('hp', player.get('max_hp', 0)) - taken
                            # degrade armor if it absorbed some damage (mirror combat behavior)
                            if armor != 'NO ARMOR' and taken > 0:
                                player['armorhealth'] = player.get('armorhealth', 1) - 1
                                if player['armorhealth'] <= 0:
                                    print(f'Your {armor} is destroyed by the blast!')
                                    player['armor'] = 'NO ARMOR'
                                    player['armortype'] = 'NO ARMOR'
                            # discard contents
                            try:
                                room.gold = 0
                                room.treasure = ''
                                room.potions = {}
                                room.misc = ''
                            except Exception:
                                pass
                            print(f'You take {taken} damage.')
                            if player.get('hp', 0) <= 0:
                                print('You are killed by the explosion!')
                                return 'dead'
                            return 'exploded'
                        # Gas: small damage and stagger to a random adjacent room
                        if r < 0.25:
                            print('GAS! YOU STAGGER FROM THE ROOM!')
                            # lethal gas: reduce you to 1 HP (perilous, but not instant death)
                            player['hp'] = 1
                            # choose a random adjacent room to stagger into
                            adj = []
                            for d in ['N','S','E','W']:
                                coords = self.get_adjacent_coords(lvl, rx, ry, d)
                                if coords:
                                    adj.append(coords)
                            if not adj:
                                print('You stagger but there is nowhere to go.')
                                return 'gassed'
                            nl, nx, ny = random.choice(adj)
                            playerpos[:] = [nl, nx, ny]
                            # moving counts as movement round
                            self.decrement_timed_effects(player)
                            self.displaymap(castlemap, playerpos, player=player)
                            self.displayroom(castlemap, playerpos, player=player)
                            return 'gassed'

                    def grant_contents():
                        if getattr(room, 'gold', 0):
                            g = room.gold
                            player['gold'] += g
                            print(f'You find {g} gold in the chest.')
                            room.gold = 0
                        if getattr(room, 'treasure', ''):
                            t = room.treasure
                            player['Treasures'].append(t)
                            room.treasure = ''
                            print(f'You find a treasure: {t}')
                            self.apply_treasure_effects(player, t)
                        if getattr(room, 'potions', None):
                            for k,v in list(room.potions.items()):
                                player['potions'][k] = player['potions'].get(k, 0) + v
                            print('You also find potions: ' + ', '.join([f"{k}:{v}" for k,v in room.potions.items()]))
                            room.potions = {}
                        room.misc = ''
                    if action == 'OPEN':
                        if getattr(room, 'locked', False):
                            print('The chest is locked.')
                        else:
                            outcome = trigger_trap()
                            if outcome == 'dead':
                                return
                            if outcome is None:
                                grant_contents()
                            else:
                                continue
                    elif action == 'PICK':
                        if not getattr(room, 'locked', False):
                            print('The chest is not locked; you open it.')
                            outcome = trigger_trap()
                            if outcome == 'dead':
                                return
                            if outcome is None:
                                grant_contents()
                            else:
                                continue
                        else:
                            # Lockpicking skill check
                            race = player.get('race','').upper()
                            race_mod = 0
                            if race == 'HOBBIT':
                                race_mod = 1
                            elif race == 'DWARF':
                                race_mod = -1
                            dex_mod = (player.get('dex',10) - 10) // 2
                            roll = random.randint(1,20) + dex_mod + race_mod
                            required = 10 + getattr(room,'lock_level',1) * 2
                            if roll >= required:
                                print('You successfully pick the lock.')
                                room.locked = False
                                outcome = trigger_trap()
                                if outcome == 'dead':
                                    return
                                if outcome is None:
                                    grant_contents()
                                else:
                                    continue
                            else:
                                print('You fail to pick the lock.')
                    elif action == 'SMASH':
                        # Smash attempt; strength-based with dwarf bonus
                        race = player.get('race','').upper()
                        smash_mod = 1 if race == 'DWARF' else 0
                        str_mod = (player.get('str',10) - 10) // 2
                        roll = random.randint(1,20) + str_mod + smash_mod
                        required = 10
                        if roll >= required:
                            print('You smash the chest open!')
                            outcome = trigger_trap()
                            if outcome == 'dead':
                                return
                            if outcome is None:
                                # gold is safe
                                if getattr(room, 'gold', 0):
                                    g = room.gold
                                    player['gold'] += g
                                    print(f'You find {g} gold in the chest.')
                                    room.gold = 0
                                # treasures and potions may be destroyed
                                if getattr(room, 'treasure', ''):
                                    if random.random() < 0.5:
                                        print('The treasure was crushed and destroyed!')
                                        room.treasure = ''
                                    else:
                                        t = room.treasure
                                        player['Treasures'].append(t)
                                        room.treasure = ''
                                        print(f'You salvage a treasure: {t}')
                                        self.apply_treasure_effects(player, t)
                                if getattr(room, 'potions', None):
                                    salvaged = {}
                                    for k,v in list(room.potions.items()):
                                        kept = 0
                                        for _ in range(v):
                                            if random.random() < 0.5:
                                                kept += 1
                                        if kept:
                                            salvaged[k] = kept
                                            player['potions'][k] = player['potions'].get(k,0) + kept
                                    if salvaged:
                                        print('You salvage some potions: ' + ', '.join([f"{k}:{v}" for k,v in salvaged.items()]))
                                    else:
                                        print('All potions were ruined in the smashing.')
                                    room.potions = {}
                                room.misc = ''
                        else:
                            print('You fail to smash the chest.')
                    else:
                        # LEAVE
                        pass

                if getattr(room, 'misc', '') == 'POOL':
                    pool_phrases = [
                        'The pool glows softly and the air above it seems warmer. It calls to you.',
                        'The water shimmers as if something alive is moving beneath the surface.',
                        'A delicious coolness rises from the pool; it looks like the answer to every ache.',
                        'The still pool seems almost too inviting, as though it wants to be touched.'
                    ]
                    print(random.choice(pool_phrases))
                    cmds_pool = ['DRINK','LEAVE']
                    try:
                        action = self.test_input('THERE IS A POOL HERE. (DRINK/LEAVE): ', cmds_pool, test_arg)
                    except ValueError:
                        action = 'LEAVE'
                    if action == 'DRINK':
                        self.drink_from_pool(player, room, test_arg=test_arg)
                    continue

                if getattr(room, 'misc', '') == 'BOOK':
                    book_phrases = [
                        'A dusty tome lies on the floor, its cover pulsing with a faint inner light.',
                        'You hear a whisper from the book that sounds almost like a promise.',
                        'The book seems to hum softly, as though it knows secrets you do not.',
                        'The leather cover of the book is warm to the touch and strangely inviting.'
                    ]
                    print(random.choice(book_phrases))
                    cmds_book = ['OPEN','LEAVE']
                    try:
                        action = self.test_input('THERE IS A BOOK HERE. (OPEN/LEAVE): ', cmds_book, test_arg)
                    except ValueError:
                        action = 'LEAVE'
                    if action == 'OPEN':
                        self.open_book(player, room, test_arg=test_arg)
                    continue

                mon = getattr(room, 'monster', '')
                if mon == 'VENDOR':
                    # Interact with vendor
                    self.vendor_interaction(player, test_arg=test_arg)
                    # continue main loop
                    continue
                elif mon and mon != '':
                    # Engage in combat with the monster
                    survived = self.combat(player, mon, room, test_arg=test_arg)
                    if not survived:
                        print('Game over.')
                        return
                    # after combat, continue game loop
                    continue

    def displaymap(self, castlemap, playerpos, player=None):
        # Backwards-compatible wrapper: display the level map containing playerpos
        return self.display(castlemap, playerpos=playerpos, show_room=False, detail=False, player=player)

    def displayroom(self, castlemap, playerpos, player=None):
        # Backwards-compatible wrapper: display the player's room in detail
        return self.display(castlemap, playerpos=playerpos, show_room=True, detail=True, player=player)

    def get_room(self, castlemap, level, x, y):
        """Return room object given 3D list castlemap (levels indexed 0..7)."""
        return castlemap[level][x][y]

    def display(self, castlemap, playerpos=None, show_room=False, detail=False, player=None):
        """Combined display: show level map or single room.
        - playerpos: tuple (level, x, y)
        - show_room: if True, print detailed room view for player's location
        - detail: when showing a single room, include verbose fields
        - player: optional player state used for blindness effects
        """
        if playerpos is None:
            print("No player position provided")
            return
        if player and player.get('blind', False):
            level, px, py = playerpos
            if show_room:
                print(f"Level {level} Room ({px},{py}): ?")
                print('You are blind and cannot see the room.')
            else:
                print(f"Level {level} (blind)")
                for _ in range(8):
                    print(' '.join('?' for _ in range(8)))
            return

        level, px, py = playerpos
        # mark player's room revealed
        try:
            prow = self.get_room(castlemap, level, px, py)
            prow.revealed = True
        except Exception:
            pass

        def glyph_for(room, is_player=False):
            if not getattr(room, 'revealed', True) and not is_player:
                return '?'
            if getattr(room, 'RuneStaff', False):
                return 'R'
            if getattr(room, 'OrbOfZot', False):
                return 'O'
            mon = getattr(room, 'monster', '')
            if mon:
                return 'V' if mon == 'VENDOR' else 'M'
            if getattr(room, 'treasure', ''):
                return 'T'
            if getattr(room, 'food', ''):
                return 'F'
            if getattr(room, 'misc', ''):
                m = room.misc
                return 'O' if m == 'CRYSTAL ORB' else m[0]
            if getattr(room, 'sinkhole', False):
                return 'S'
            if getattr(room, 'stairup', False):
                return '<'
            if getattr(room, 'stairdown', False):
                return '>'
            return '.'

        def color_for_char(ch, is_player=False):
            # Map glyphs to colors
            if is_player:
                return f"{C_GREEN}{ch}{C_RESET}"
            if ch == 'M':
                return f"{C_RED}{ch}{C_RESET}"
            if ch == 'V':
                return f"{C_CYAN}{ch}{C_RESET}"
            if ch in ('R', 'O'):
                return f"{C_MAGENTA}{ch}{C_RESET}"
            if ch == 'T':
                return f"{C_YELLOW}{ch}{C_RESET}"
            if ch == 'F':
                return f"{C_GREEN}{ch}{C_RESET}"
            if ch == 'S':
                return f"{C_RED}{ch}{C_RESET}"
            if ch in ('<', '>'):
                return f"{C_BLUE}{ch}{C_RESET}"
            if ch == '?':
                return f"{C_WHITE}{ch}{C_RESET}"
            # default
            return ch

        def room_detail(room):
            lines = []
            lines.append(f"Monster: {getattr(room,'monster','') or 'None'}")
            lines.append(f"Treasure: {getattr(room,'treasure','') or 'None'}")
            lines.append(f"Food: {getattr(room,'food','') or 'None'}")
            flags = []
            if getattr(room,'RuneStaff',False): flags.append('Runestaff')
            if getattr(room,'OrbOfZot',False): flags.append('OrbOfZot')
            if getattr(room,'sinkhole',False): flags.append('Sinkhole')
            if getattr(room,'stairup',False): flags.append('StairsUp')
            if getattr(room,'stairdown',False): flags.append('StairsDown')
            if getattr(room,'pool',False): flags.append('Pool')
            if getattr(room,'vendor',False): flags.append('Vendor')
            if getattr(room,'locked',False): flags.append('Locked')
            lines.append('Flags: ' + (', '.join(flags) if flags else 'None'))
            if getattr(room,'gold',None) is not None:
                lines.append(f"Gold: {room.gold}")
            if getattr(room,'misc', ''):
                lines.append(f"Misc: {room.misc}")
            return '\n'.join(lines)

        # If single room view requested
        if show_room:
            try:
                room = self.get_room(castlemap, level, px, py)
                base = glyph_for(room, True)
                print(f"Level {level} Room ({px},{py}): {color_for_char(base, True)}")
                if detail:
                    print(room_detail(room))
            except Exception:
                print("Unable to display room")
            return

        # Otherwise display the whole level map (8x8)
        print(f"Level {level}")
        for r in range(8):
            row_chars = []
            for c in range(8):
                try:
                    room = self.get_room(castlemap, level, r, c)
                except Exception:
                    # If lookup fails, print unknown
                    base = '?'
                else:
                    base = glyph_for(room, is_player=(r==px and c==py))
                if r == px and c == py:
                    ch = color_for_char('@', True)
                else:
                    ch = color_for_char(base, False)
                row_chars.append(ch)
            print(' '.join(row_chars))

    def get_adjacent_coords(self, level, x, y, direction):
        if direction == 'N' and x > 0:
            return level, x - 1, y
        if direction == 'S' and x < 7:
            return level, x + 1, y
        if direction == 'W' and y > 0:
            return level, x, y - 1
        if direction == 'E' and y < 7:
            return level, x, y + 1
        return None

    def describe_room(self, room):
        if not room:
            print('There is nothing there.')
            return
        print(f'Monster: {getattr(room,"monster","") or "None"}')
        print(f'Treasure: {getattr(room,"treasure","") or "None"}')
        print(f'Food: {getattr(room,"food","") or "None"}')
        flags = []
        if getattr(room,'RuneStaff',False): flags.append('Runestaff')
        if getattr(room,'OrbOfZot',False): flags.append('OrbOfZot')
        if getattr(room,'sinkhole',False): flags.append('Sinkhole')
        if getattr(room,'stairup',False): flags.append('StairsUp')
        if getattr(room,'stairdown',False): flags.append('StairsDown')
        if getattr(room,'pool',False): flags.append('Pool')
        if getattr(room,'monster','') == 'VENDOR': flags.append('Vendor')
        if getattr(room,'locked',False): flags.append('Locked')
        misc = getattr(room,'misc','')
        if misc and misc not in flags:
            flags.append(misc)
        print('Flags: ' + (', '.join(flags) if flags else 'None'))
        if getattr(room,'gold',None) is not None:
            print(f'Gold: {room.gold}')

    def teleport(self, castlemap, playerpos=None, player=None, test_arg=None, dest=None, is_orb=False):
        """Teleport helper: moves the player or the crystal orb.
        - If is_orb=True: moves the CRYSTAL ORB to `dest` or a random empty room.
        - If is_orb=False: teleports the player to coordinates (prompted or `dest`), with perilous consequences possible.
        """
        if is_orb:
            # clear any existing orb in the map
            try:
                for L in range(len(castlemap)):
                    for X in range(8):
                        for Y in range(8):
                            if getattr(castlemap[L][X][Y], 'misc', '') == 'CRYSTAL ORB':
                                castlemap[L][X][Y].misc = ''
            except Exception:
                pass
            if dest:
                nl, nx, ny = dest
            else:
                nl, nx, ny = self.get_random_empty_room(castlemap)
            castlemap[nl][nx][ny].misc = 'CRYSTAL ORB'
            return (nl, nx, ny)

        # Player teleport: require both OrbOfZot and RuneStaff per game rule
        if not player or not (player.get('OrbOfZot') and player.get('RuneStaff')):
            print("** YOU CAN'T TELEPORT WITHOUT THE RUNESTAFF AND ORB!")
            return None

        # If dest provided, use it, otherwise prompt for coordinates
        if dest:
            nl, nx, ny = dest
        else:
            try:
                sx = self.test_input('X-COORDINATE (0-7): ', None, test_arg)
                nx = int(sx)
            except Exception:
                print('Invalid X coordinate.')
                return None
            try:
                sy = self.test_input('Y-COORDINATE (0-7): ', None, test_arg)
                ny = int(sy)
            except Exception:
                print('Invalid Y coordinate.')
                return None
            try:
                sz = self.test_input('Z-COORDINATE (0-7): ', None, test_arg)
                nl = int(sz)
            except Exception:
                print('Invalid Z coordinate.')
                return None
        # clamp/validate
        if not (0 <= nl <= 7 and 0 <= nx <= 7 and 0 <= ny <= 7):
            print('Coordinates out of range.')
            return None
        
        # CRITICAL FAILURE: Small chance the teleport goes horribly wrong
        if random.random() < 0.10:
            print('THE TELEPORT ENERGY SURGES OUT OF CONTROL!')
            print('YOU ARE RIPPED APART BY PLANAR FORCES AND SCATTERED ACROSS THE DIMENSIONS!')
            player['hp'] = 0
            return None
        
        # Check if destination room is occupied (but allow sinkhole for peril)
        dest_room = castlemap[nl][nx][ny]
        blocked_by = []
        if getattr(dest_room, 'stairup', False):
            blocked_by.append('stairs')
        if getattr(dest_room, 'stairdown', False):
            blocked_by.append('stairs')
        if getattr(dest_room, 'exit', False):
            blocked_by.append('the exit')
        if getattr(dest_room, 'monster', ''):
            blocked_by.append('a monster')
        if getattr(dest_room, 'treasure', ''):
            blocked_by.append('treasure')
        if blocked_by:
            print(f'That room is occupied by {" and ".join(blocked_by)}.')
            return None
        
        # PERIL: Check for sinkhole - instant doom!
        if getattr(dest_room, 'sinkhole', False):
            print('YOU MATERIALIZE DIRECTLY OVER A SINKHOLE!')
            print('YOU PLUMMET INTO THE DARKNESS, FALLING FOREVER...')
            print('*** YOUR ADVENTURE HAS ENDED ***')
            player['hp'] = 0
            return None
        
        # PERIL: Check for SOAP trap - eternal imprisonment
        if getattr(dest_room, 'misc', '') == 'SOAP':
            print('YOU FIND YOURSELF TRAPPED INSIDE A TELEVISION SET!')
            print('THE SOAP OPERA PLAYS ON... AND ON... AND ON...')
            print('YOU ARE DOOMED TO WATCH IT FOR ALL ETERNITY!')
            print('*** YOUR ADVENTURE HAS ENDED ***')
            player['hp'] = 0
            return None
        
        # perform teleport
        playerpos[:] = [nl, nx, ny]
        # show new location
        self.displaymap(castlemap, playerpos, player=player)
        self.displayroom(castlemap, playerpos, player=player)
        return (nl, nx, ny)

    def use_light_source(self, castlemap, playerpos, player, test_arg=None, consume_flare=False):
        if consume_flare:
            if player.get('flares', 0) <= 0:
                print('You have no flares to use.')
                return
            player['flares'] -= 1
            print('You light a flare and wave it toward an adjacent room.')
        else:
            if not player.get('haslamp', False):
                print('You do not have a lamp.')
                return
            print('You lift your lamp and aim its glow into an adjacent room.')
        try:
            direction = self.test_input('Which direction? (N/S/E/W): ', ['N','S','E','W'], test_arg)
        except ValueError:
            print('You hesitate and decide not to look.')
            return
        try:
            lvl, rx, ry = playerpos
        except Exception:
            lvl, rx, ry = playerpos[0], playerpos[1], playerpos[2]
        coords = self.get_adjacent_coords(lvl, rx, ry, direction)
        if not coords:
            print('There is no adjacent room in that direction.')
            return
        _, nx, ny = coords
        room = self.get_room(castlemap, lvl, nx, ny)
        print('The light reveals the adjacent room:')
        self.describe_room(room)

    def isexit(self, index):
        if index == 4:
            return True
        else:
            return False
        
    def initmap(self, mapsize, sinkholes):
        """Initializes a 3D castle map (levels indexed 0..7).
        Returns castlemap[level][x][y] where level is 0..7 and x,y are 0..7.
        """
        print("ZOT'S CREATING THE CASTLE...")
        if getattr(self, 'debug', False):
            print(f"DEBUG: initializing castlemap (levels=8, level size=8x8)")
        # Build 0-based level list: levels 0..7
        castlemap = [
            [ [ Room() for _ in range(8) ] for _ in range(8) ]
            for _ in range(8)
        ]

        # Set the exit at level 0, row 0, col 4
        castlemap[0][0][4].exit = True
        if getattr(self, 'debug', False):
            print("DEBUG: exit set at level 0 (0,4)")

        # Set stairs: for level 0..6 create stairs down at a random (x,y)
        print('SETTING STAIRS...')
        for level in range(0, 7):
            rx = random.randint(0,7)
            ry = random.randint(0,7)
            # assign stairdown on current level and stairup on next level
            castlemap[level][rx][ry].stairdown = (level+1, rx, ry)
            castlemap[level+1][rx][ry].stairup = (level, rx, ry)
            print(f"level: {level} stair at ({rx},{ry}) -> level {level+1}")
            if getattr(self, 'debug', False):
                print(f"DEBUG: stairs assigned between {level} <-> {level+1} at ({rx},{ry})")

        # Set sinkholes (avoid level 0 and level 7)
        print('CREATING SINKHOLES...')
        sinks = random.randint(1, max(1, sinkholes))
        placed = 0
        attempts = 0
        while placed < sinks and attempts < 1000:
            attempts += 1
            level = random.randint(1,6)
            x = random.randint(0,7)
            y = random.randint(0,7)
            if not self.isoccupied(castlemap, level, x, y):
                castlemap[level][x][y].sinkhole = (level+1, x, y)
                placed += 1
                print(f"Sinkhole at level {level} ({x},{y}) -> level {level+1}")
                if getattr(self, 'debug', False):
                    print(f"DEBUG: sinkhole placed at level {level} ({x},{y})")

        return castlemap

    def populatemap(self, castlemap, monsters, treasures, food, misc):
        # Place RuneStaff
        level, x, y = self.get_random_empty_room(castlemap)
        castlemap[level][x][y].RuneStaff = True
        # But not with a vendor!
        rsmonster = random.choice(monsters)
        while rsmonster == 'VENDOR':
            rsmonster = random.choice(monsters)

        castlemap[level][x][y].monster = rsmonster
        if getattr(self, 'debug', False):
            print(f"DEBUG: RuneStaff placed at level {level} ({x},{y}) with monster {castlemap[level][x][y].monster}")

        # Place OrbOfZot
        level, x, y = self.get_random_empty_room(castlemap)
        castlemap[level][x][y].OrbOfZot = True
        if getattr(self, 'debug', False):
            print(f"DEBUG: OrbOfZot placed at level {level} ({x},{y})")

        # Place Vendors: One per floor (levels 0..7)
        for level in range(0, 8):
            x, y = random.randint(0, 7), random.randint(0, 7)
            while self.isoccupied(castlemap, level, x, y):
                x, y = random.randint(0, 7), random.randint(0, 7)
            castlemap[level][x][y].monster = 'VENDOR'
            if getattr(self, 'debug', False):
                print(f"DEBUG: Vendor placed at level {level} ({x},{y})")

        # Place monsters: one per floor (levels 0..7)
        for level in range(0, 8):
            x, y = random.randint(0, 7), random.randint(0, 7)
            while self.isoccupied(castlemap, level, x, y):
                x, y = random.randint(0, 7), random.randint(0, 7)
            castlemap[level][x][y].monster = monsters[level % len(monsters)]
            if getattr(self, 'debug', False):
                print(f"DEBUG: Monster {castlemap[level][x][y].monster} placed at level {level} ({x},{y})")

        # Big monsters on deeper levels (place a set number of big monsters)
        bigmonsters = ['GARGOYLE', 'CHIMERA', 'BALROG', 'DRAGON']
        ttemp = treasures.copy()
        # Repeat placement a small fixed number of times to populate deep areas
        for monster in bigmonsters:
            level, x, y = self.get_random_empty_room(castlemap, 4) # levels 4..7
            castlemap[level][x][y].monster = monster
            castlemap[level][x][y].gold = random.randint(300, 1000)
            castlemap[level][x][y].misc = 'CHEST'
            if ttemp:
                castlemap[level][x][y].treasure = ttemp.pop(random.randint(0, len(ttemp)-1))
            if getattr(self, 'debug', False):
                print(f"DEBUG: Big monster {monster} placed at level {level} ({x},{y}) with treasure {castlemap[level][x][y].treasure}")

        # Populate with food, misc, and treasures
        for _ in range(len(food)):
            level, x, y = self.get_random_empty_room(castlemap)
            castlemap[level][x][y].food = food.pop()
        for _ in range(len(misc)):
            level, x, y = self.get_random_empty_room(castlemap)
            val = misc.pop()
            castlemap[level][x][y].misc = val
            # If this is a pool, assign a hidden pool type (stat and delta)
            if val == 'POOL':
                # Pool flavors: stat +/- or race/sex transformations
                pool_options = [
                    ('str', 1), ('str', -1),
                    ('int', 1), ('int', -1),
                    ('dex', 1), ('dex', -1),
                    ('race', 'ELF'), ('race', 'DWARF'), ('race', 'HOBBIT'), ('race', 'HUMAN'),
                    ('sex', 'FLIP')
                ]
                castlemap[level][x][y].pool = random.choice(pool_options)
            # if it's a chest, possibly lock it
            if val == 'CHEST':
                if random.random() < 0.5:
                    castlemap[level][x][y].locked = True
                    castlemap[level][x][y].lock_level = random.randint(1,3)
        # Populate some chests with potions randomly
        for level in range(8):
            for x in range(8):
                for y in range(8):
                    room = castlemap[level][x][y]
                    if getattr(room, 'misc', '') == 'CHEST':
                        # random chance to include 0-2 potions of random types
                        pcount = random.randint(0,2)
                        if pcount > 0:
                            types = ['strength','intelligence','dexterity']
                            room.potions = {}
                            for _ in range(pcount):
                                t = random.choice(types)
                                room.potions[t] = room.potions.get(t, 0) + 1
                        # some chests may be locked (if not already set)
                        if not getattr(room, 'locked', False) and random.random() < 0.3:
                            room.locked = True
                            room.lock_level = random.randint(1,3)
        for _ in range(len(treasures)):
            level, x, y = self.get_random_empty_room(castlemap)
            castlemap[level][x][y].treasure = treasures.pop()
        return castlemap

    def makeplayer(self, races, weapons, armors, test_arg=None):
        # Set up player dictionary with default values
        # Works when races/weapons/armors are simple lists of strings
        playerone = {
            'race': 'HUMAN',
            'sex': 'MALE',
            'str': 12,
            'int': 11,
            'dex': 11,
            'armortype': 'NO ARMOR',
            'armorhealth': 1,
            'armor': 'NO ARMOR',
            'weapon': 'HANDS',
            'weapondamage': 1,
            'haslamp': False,
            'flares': 0,
            'gold': 60,
            'bookstuck': False,
            'blind': False,
            'OrbOfZot': False,
            'RuneStaff': False,
            'food': [],
            'Treasures': [],
            'potions': {'strength': 0, 'intelligence': 0, 'dexterity': 0},
            'max_hp': 10,
            'hp': 10,
            # timed movement-based effects: keys are 'str','int','dex' -> remaining moves
            'timed_effects': {},
            # temporary stat modifiers applied by pools { 'str': +1, 'int': -1 }
            'temp_mods': {},
        }

        print('\nALL RIGHT, BOLD ONE.\nYOU MAY BE AN ELF, DWARF, HUMAN, OR HOBBIT.\n')
        cmds = ['E', 'D', 'HU', 'HO']
        while True:
            try:
                command = self.test_input("ENTER E, D, HU, or HO: ", cmds, test_arg)
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
        elif command == 'HO':
            playerone['race'] = 'HOBBIT'
            playerone['str'] = 9
            playerone['int'] = 11
            playerone['dex'] = 14

        print(f"\nOK, {playerone['race']}, WHICH SEX DO YOU PREFER (M/F): ")
        cmds = ['M', 'F']
        while True:
            try:
                command = self.test_input("\nENTER M or F: ", cmds, test_arg)
                break
            except ValueError:
                print(f"** CUTE {playerone['race']}, REAL CUTE. TRY M OR F.")
                continue
        if command == 'F':
            playerone['sex'] = 'FEMALE'

        print(f"OK, {playerone['race']}, YOU HAVE THE FOLLOWING ATTRIBUTES: \n                STRENGTH = {playerone['str']} INTELLIGENCE = {playerone['int']} DEXTERITY = {playerone['dex']}")
        print('YOU HAVE 6 OTHER POINTS TO ALLOCATE AS YOU WISH.')

        # Allocate points
        points = 6
        commands = ['S', 'I', 'D']
        while points > 0:
            print(f'YOU HAVE {points} POINTS LEFT TO ALLOCATE.')
            try:
                command = self.test_input('\nWHICH ATTRIBUTE (S/I/D)? ', commands, test_arg)
                if command == 'S':
                    playerone['str'] += 1
                    print(f"\nSTRENGTH INCREASED TO {playerone['str']}\n")
                elif command == 'I':
                    playerone['int'] += 1
                    print(f"\nINTELLIGENCE INCREASED TO {playerone['int']}\n")
                elif command == 'D':
                    playerone['dex'] += 1
                    print(f"\nDEXTERITY INCREASED TO {playerone['dex']}\n")
                points -= 1
            except ValueError:
                print('\n** THAT WAS INCORRECT. PLEASE TYPE S, I, OR D.\n')
                continue

        # Buy gear - simple starting shop
        prices = {
            'ARMOR': {'PLATE':30, 'CHAINMAIL':20, 'LEATHER':10, 'NO ARMOR':0},
            'WEAPON': {'SWORD':30, 'MACE':20, 'DAGGER':10, 'HANDS':0},
            'LAMP': 20,
            'FLARE': 1
        }

        print(f"YOU HAVE {playerone['gold']} GOLD. YOU MAY BUY ARMOR, WEAPONS, A LAMP, OR FLARES.")
        shop_cmds = ['ARMOR','WEAPON','LAMP','FLARE','DONE']
        while True:
            try:
                cmd = self.test_input("BUY (ARMOR/WEAPON/LAMP/FLARE) OR DONE: ", shop_cmds, test_arg)
            except ValueError:
                print('PLEASE ENTER ARMOR, WEAPON, LAMP, FLARE, OR DONE.')
                continue
            if cmd == 'DONE':
                break
            if cmd == 'ARMOR':
                choices = list(prices['ARMOR'].keys())
                print('ARMOR OPTIONS: ' + ', '.join(choices))
                while True:
                    try:
                        a = self.test_input('CHOOSE ARMOR: ', choices, test_arg)
                        cost = prices['ARMOR'][a]
                        if cost > playerone['gold']:
                            print('YOU CANNOT AFFORD THAT ARMOR.')
                        else:
                            playerone['armortype'] = a
                            playerone['armor'] = a
                            playerone['gold'] -= cost
                            playerone['armorhealth'] = max(1, cost // 10)
                            print(f'BOUGHT {a} FOR {cost} GOLD.')
                            break
                    except ValueError:
                        print('INVALID CHOICE.')
                        continue
            if cmd == 'WEAPON':
                choices = list(prices['WEAPON'].keys())
                print('WEAPON OPTIONS: ' + ', '.join(choices))
                while True:
                    try:
                        w = self.test_input('CHOOSE WEAPON: ', choices, test_arg)
                        cost = prices['WEAPON'][w]
                        if cost > playerone['gold']:
                            print('YOU CANNOT AFFORD THAT WEAPON.')
                        else:
                            playerone['weapon'] = w
                            playerone['weapondamage'] = 1 + (cost // 10)
                            playerone['gold'] -= cost
                            print(f'BOUGHT {w} FOR {cost} GOLD.')
                            break
                    except ValueError:
                        print('INVALID CHOICE.')
                        continue
            if cmd == 'LAMP':
                if playerone['gold'] >= prices['LAMP']:
                    playerone['gold'] -= prices['LAMP']
                    playerone['haslamp'] = True
                    print('BOUGHT A LAMP.')
                else:
                    print('YOU CANNOT AFFORD A LAMP.')
            if cmd == 'FLARE':
                try:
                    amt_str = self.test_input('HOW MANY FLARES? ', None, test_arg)
                    amount = int(amt_str) if amt_str else 0
                except Exception:
                    print('INVALID NUMBER.')
                    continue
                cost = amount * prices['FLARE']
                if cost > playerone['gold']:
                    print('YOU CANNOT AFFORD THAT MANY FLARES.')
                else:
                    playerone['flares'] += amount
                    playerone['gold'] -= cost
                    print(f'BOUGHT {amount} FLARES FOR {cost} GOLD.')

        # finalize HP based on strength
        playerone['max_hp'] = 8 + max(0, playerone['str'] - 10)
        playerone['hp'] = playerone['max_hp']

        return playerone

    def displaystatus(self, player):
        print(f"STRENGTH = {player['str']} INTELLIGENCE = {player['int']} DEXTERITY = {player['dex']}")
        print(f"HP = {player.get('hp',0)}/{player.get('max_hp',0)}  FLARES = {player['flares']}  GOLD = {player['gold']}")
        print(f"WEAPON = {player['weapon']}  ARMOR = {player.get('armor','NO ARMOR')}")
        print(f"Treasures: {player['Treasures']}")
        if player.get('blind'):
            print('STATUS: You are BLIND.')
        if player.get('bookstuck'):
            print('STATUS: Your weapon is stuck and you cannot draw it.')
        # show timed movement-based effects
        te = player.get('timed_effects', {})
        if te:
            parts = []
            names = {'str':'STR','int':'INT','dex':'DEX'}
            for k,v in te.items():
                parts.append(f"{names.get(k,k)}:{v} moves")
            print('Timed effects: ' + ', '.join(parts))
        # show food and potions
        food = player.get('food', [])
        if food:
            print('Food: ' + ', '.join(food))
        potions = player.get('potions', {})
        if any(v>0 for v in potions.values()):
            print('Potions: ' + ', '.join([f"{k}:{v}" for k,v in potions.items() if v>0]))
        if player.get('haslamp'):
            print('\n...AND A LAMP.')

    def genrand(self, low, high):
        # Always skip the exit!
        index = random.randint(low, high)
        while index == 4:
            index = random.randint(low, high)
        return index
    
    def atmosphere(self, player, monsters):
        effects = [
            'A SCREAM!',
            'FOOTSTEPS!',
            'A WUMPUS!',
            'THUNDER!',
            'FAINT RUSTLING NOISES!',
            'A BAT FLY BY!',
            'FEEL LIKE YOU\'RE BEING WATCHED!',
            'STEPPED ON A FROG!',
            'SNEEZED!'
        ]
        atmos = "YOU "
        # Small chance to show an atmospheric message
        if random.randint(0, 20) <= 10:
            what = random.randint(0, len(effects) - 1)
            # player stores `blind` not `isblind` in the player dict
            if what == 5 and player.get('blind', False):
                print(atmos + 'HEAR ' + effects[what])
            else:
                print(atmos + 'SEE ' + effects[what])
            if what < 5:
                print(atmos + 'HEAR ' + effects[what])
            if 5 < what <= len(effects) - 2:
                print(atmos + effects[what])
            # use the last effect index to trigger a smell message
            if what == len(effects) - 1:
                print(atmos + f"SMELL {random.choice(monsters)} FRYING!")

            

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

    def vendor_interaction(self, player, test_arg=None):
        """Simple vendor/shop interaction. Sells armor, weapons, lamp, and flares."""
        prices = {
            'ARMOR': {'PLATE':30, 'CHAINMAIL':20, 'LEATHER':10, 'NO ARMOR':0},
            'WEAPON': {'SWORD':30, 'MACE':20, 'DAGGER':10, 'HANDS':0},
            'LAMP': 20,
            'FLARE': 1
        }
        print('A vendor greets you. You may BUY or QUIT.')
        # vendor has some potions randomly in stock
        potion_types = ['strength','intelligence','dexterity']
        vendor_potions = {}
        for _ in range(random.randint(0,3)):
            t = random.choice(potion_types)
            vendor_potions[t] = vendor_potions.get(t, 0) + 1
        cmds = ['ARMOR','WEAPON','LAMP','FLARE','POTION','QUIT']
        while True:
            try:
                cmd = self.test_input('WHAT DO YOU WANT TO BUY (ARMOR/WEAPON/LAMP/FLARE/POTION) OR QUIT: ', cmds, test_arg)
            except ValueError:
                print('Please choose ARMOR, WEAPON, LAMP, FLARE, POTION or QUIT.')
                continue
            if cmd == 'QUIT':
                print('The vendor nods and goes back to his wares.')
                break
            if cmd == 'ARMOR':
                choices = list(prices['ARMOR'].keys())
                print('ARMOR OPTIONS: ' + ', '.join(choices))
                try:
                    a = self.test_input('CHOOSE ARMOR: ', choices, test_arg)
                except ValueError:
                    print('Invalid armor choice.')
                    continue
                cost = prices['ARMOR'][a]
                if cost > player['gold']:
                    print('You cannot afford that armor.')
                    continue
                player['armortype'] = a
                player['armor'] = a
                player['gold'] -= cost
                player['armorhealth'] = max(1, cost // 10)
                print(f'Bought {a} for {cost} gold.')
            if cmd == 'WEAPON':
                choices = list(prices['WEAPON'].keys())
                print('WEAPON OPTIONS: ' + ', '.join(choices))
                try:
                    w = self.test_input('CHOOSE WEAPON: ', choices, test_arg)
                except ValueError:
                    print('Invalid weapon choice.')
                    continue
                cost = prices['WEAPON'][w]
                if cost > player['gold']:
                    print('You cannot afford that weapon.')
                    continue
                player['weapon'] = w
                player['weapondamage'] = 1 + (cost // 10)
                player['gold'] -= cost
                print(f'Bought {w} for {cost} gold.')
            if cmd == 'LAMP':
                if player['gold'] >= prices['LAMP']:
                    player['gold'] -= prices['LAMP']
                    player['haslamp'] = True
                    print('Bought a lamp.')
                else:
                    print('You cannot afford a lamp.')
            if cmd == 'POTION':
                if not vendor_potions:
                    print('Sorry, I have no potions right now.')
                    continue
                print('Vendor potions: ' + ', '.join([f"{k}:{v}" for k,v in vendor_potions.items()]))
                p = self.test_input('Which potion do you want? ', None, test_arg)
                if p:
                    p = p.strip().lower()
                else:
                    p = ''
                if p not in vendor_potions or vendor_potions[p] <= 0:
                    print('I do not have that potion.')
                    continue
                price = 10
                if player['gold'] < price:
                    print('You cannot afford that potion.')
                    continue
                vendor_potions[p] -= 1
                player['potions'][p] = player['potions'].get(p, 0) + 1
                player['gold'] -= price
                print(f'Bought a {p} potion for {price} gold.')
            if cmd == 'FLARE':
                try:
                    amt_str = self.test_input('How many flares? ', None, test_arg)
                    amount = int(amt_str) if amt_str else 0
                except Exception:
                    print('Invalid number.')
                    continue
                cost = amount * prices['FLARE']
                if cost > player['gold']:
                    print('You cannot afford that many flares.')
                else:
                    player['flares'] += amount
                    player['gold'] -= cost
                    print(f'Bought {amount} flares for {cost} gold.')

    def combat(self, player, monster_name, room=None, test_arg=None):
        """Run a simple turn-based combat between player and a monster.
        Returns True if player survives, False on death.
        """
        # Ensure player has hp
        if 'hp' not in player:
            player['max_hp'] = 8 + max(0, player.get('str', 10) - 10)
            player['hp'] = player['max_hp']

        # Basic monster stats table
        monster_stats = {
            'KOBOLD': {'hp':6, 'dmg':2, 'gold':5},
            'ORC': {'hp':8, 'dmg':3, 'gold':10},
            'WOLF': {'hp':6, 'dmg':2, 'gold':8},
            'GOBLIN': {'hp':6, 'dmg':2, 'gold':6},
            'OGRE': {'hp':12, 'dmg':4, 'gold':25},
            'TROLL': {'hp':14, 'dmg':5, 'gold':30},
            'BEAR': {'hp':10, 'dmg':4, 'gold':20},
            'MINOTAUR': {'hp':12, 'dmg':4, 'gold':40},
            'GARGOYLE': {'hp':16, 'dmg':5, 'gold':80},
            'CHIMERA': {'hp':18, 'dmg':6, 'gold':120},
            'BALROG': {'hp':22, 'dmg':7, 'gold':300},
            'DRAGON': {'hp':28, 'dmg':9, 'gold':500},
        }

        if monster_name not in monster_stats:
            stats = {'hp':8, 'dmg':3, 'gold':10}
        else:
            stats = monster_stats[monster_name].copy()

        m_hp = stats['hp']
        print(f'A {monster_name} appears!')

        # temporary buffs applied during combat
        player.setdefault('temp_buffs', {})

        while m_hp > 0 and player['hp'] > 0:
            # Player choice
            try:
                choice = self.test_input('F)ight, R)un, or U)se item? ', ['F','R','U'], test_arg)
                if choice:
                    choice = choice.strip().upper()
                else:
                    choice = 'F'
            except Exception:
                choice = 'F'
            if choice == 'R':
                # run chance based on dex
                roll = random.randint(1, 20) + (player.get('dex', 10) - 10)
                if roll >= 10:
                    print('You escape successfully!')
                    return True
                else:
                    print('You fail to escape!')
            if choice == 'U':
                used = self.use_consumable(player, in_combat=True, test_arg=test_arg)
                if used:
                    # continue to monster turn
                    pass
                else:
                    print('You fumble and lose your chance to act.')
                    # allow monster to attack below
                    pass

            # Player attacks (strength and temporary buff affect damage)
            str_buff = player.get('temp_buffs', {}).get('str', 0)
            dex_buff = player.get('temp_buffs', {}).get('dex', 0)
            attack_base = max(1, player.get('weapondamage', 1))
            if player.get('bookstuck', False):
                print('Your weapon is stuck; you fight with your fists!')
                attack_base = 1
            player_attack = random.randint(1, attack_base) + max(0, (player.get('str', 10) + str_buff - 10)//2) + (dex_buff//2)
            if player.get('blind', False):
                print('You swing blindly! Your attack is clumsy.')
                player_attack = max(1, player_attack - 2)
            m_hp -= player_attack
            print(f'You hit the {monster_name} for {player_attack} damage (monster hp {max(0,m_hp)}).')

            if m_hp <= 0:
                print(f'You defeated the {monster_name}!')
                # loot
                gained = stats.get('gold', 0) + room.gold if room and getattr(room, 'gold', 0) else stats.get('gold', 0)
                player['gold'] += gained
                print(f'You gain {gained} gold.')
                # collect treasure if present
                if room and getattr(room, 'treasure', ''):
                    t = room.treasure
                    player['Treasures'].append(t)
                    print(f'You picked up: {t}')
                    room.treasure = ''
                    self.apply_treasure_effects(player, t)
                # clear monster from room if provided
                if room:
                    room.monster = ''
                return True

            # Monster attacks
            # monster damage can vary; include random roll
            raw = random.randint(1, stats['dmg']) + random.randint(0,2)
            # armor reduction
            armor = player.get('armor', 'NO ARMOR')
            armor_reduce = ARMOR_REDUCTION.get(armor, 0)
            dmg = max(0, raw - armor_reduce)
            player['hp'] -= dmg
            print(f'The {monster_name} hits you for {dmg} damage (you have {max(0,player["hp"])} hp left).')
            # degrade armor if it absorbed damage
            if armor != 'NO ARMOR' and dmg > 0:
                player['armorhealth'] = player.get('armorhealth', 1) - 1
                if player['armorhealth'] <= 0:
                    print(f'Your {armor} is destroyed!')
                    player['armor'] = 'NO ARMOR'
                    player['armortype'] = 'NO ARMOR'

            if player['hp'] <= 0:
                print('YOU HAVE DIED!')
                # simple end: exit the program
                try:
                    sys.exit(0)
                except SystemExit:
                    return False

    def displayhelp(self, player, test_arg=None):
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
            ********************************************************
            '''
        )
        try:
            self.test_input(f"\nPRESS ENTER WHEN READY TO RESUME, {player['race']}.", None, test_arg)
        except (ValueError, TypeError):
            print(f"\n** SILLY {player['race']}, THAT WASN'T A VALID COMMAND!\n")
            pass

    def use_consumable(self, player, in_combat=False, test_arg=None):
        """Use a potion or food outside or inside combat.
        Returns True if something was used.
        """
        potions = player.get('potions', {})
        options = []
        if any(v>0 for v in potions.values()):
            options.append('POTION')
        if player.get('food'):
            options.append('FOOD')
        if not options:
            print('You have no consumables.')
            return False
        print('Consumable options: ' + ', '.join(options))
        choice = None
        try:
            choice = self.test_input('Use POTION or FOOD? ', options if options else None, test_arg)
            if choice:
                choice = choice.strip().upper()
            else:
                choice = ''
        except Exception:
            return False
        if choice == 'POTION' and any(v>0 for v in potions.values()):
            types = [k for k,v in potions.items() if v>0]
            print('Potions available: ' + ', '.join(types))
            p = self.test_input('Which potion? ', None, test_arg)
            if p:
                p = p.strip().lower()
            else:
                p = ''
            if p in potions and potions[p] > 0:
                potions[p] -= 1
                if p == 'strength':
                    if in_combat:
                        player.setdefault('temp_buffs', {})
                        player['temp_buffs']['str'] = player['temp_buffs'].get('str',0) + 2
                        print('You feel stronger! (+2 STR this combat)')
                    else:
                        player['str'] += 1
                        print('You feel permanently stronger (+1 STR).')
                elif p == 'intelligence':
                    if in_combat:
                        player.setdefault('temp_buffs', {})
                        player['temp_buffs']['int'] = player['temp_buffs'].get('int',0) + 2
                        print('Your mind sharpens! (+2 INT this combat)')
                    else:
                        player['int'] += 1
                        print('You feel permanently smarter (+1 INT).')
                elif p == 'dexterity':
                    if in_combat:
                        player.setdefault('temp_buffs', {})
                        player['temp_buffs']['dex'] = player['temp_buffs'].get('dex',0) + 2
                        print('You move more quickly! (+2 DEX this combat)')
                    else:
                        player['dex'] += 1
                        print('You feel permanently quicker (+1 DEX).')
                return True
            else:
                print('No such potion available.')
                return False
        elif choice == 'FOOD' and player.get('food'):
            item = player['food'].pop(0)
            heal_map = {'TACO':6, 'SANDWICH':5, 'STEW':4, 'SOUP':3, 'BURGER':6, 'ROAST':7, 'PIE':5, 'FILET':6}
            heal = heal_map.get(item.upper(), 3)
            old = player.get('hp', 0)
            player['hp'] = min(player.get('max_hp', 0), old + heal)
            print(f'You eat the {item} and restore {player["hp"]-old} HP.')
            return True
        else:
            print('No consumable used.')
            return False

    def apply_treasure_effects(self, player, treasure):
        if treasure == 'OPAL EYE' and player.get('blind', False):
            player['blind'] = False
            print('Your Opal Eye glows and cures your blindness!')
        if treasure == 'BLUE FLAME' and player.get('bookstuck', False):
            player['bookstuck'] = False
            print('The Blue Flame dissolves the book and frees your hands!')
        # Gems that cure temporary pool effects
        if treasure == 'PALE PEARL':
            # cures WEAKER (-1 STR)
            if player.get('temp_mods', {}).get('str', 0) < 0:
                delta = player['temp_mods'].pop('str')
                player['str'] -= delta  # delta is negative, subtracting reverts
                player.get('timed_effects', {}).pop('str', None)
                print('Your Pale Pearl glows and cures your weakness!')
        if treasure == 'GREEN GEM':
            if player.get('temp_mods', {}).get('int', 0) < 0:
                delta = player['temp_mods'].pop('int')
                player['int'] -= delta
                player.get('timed_effects', {}).pop('int', None)
                print('Your Green Gem glows and cures your stupidity!')
        if treasure == 'RUBY RED':
            if player.get('temp_mods', {}).get('dex', 0) < 0:
                delta = player['temp_mods'].pop('dex')
                player['dex'] -= delta
                player.get('timed_effects', {}).pop('dex', None)
                print('Your Ruby Red glows and restores your nimbleness!')

    def decrement_timed_effects(self, player):
        """Called on player movement to reduce remaining timed effects and revert when they expire."""
        if not player.get('timed_effects'):
            return
        names = {'str':'strength','int':'intelligence','dex':'dexterity'}
        for stat in list(player.get('timed_effects', {}).keys()):
            player['timed_effects'][stat] -= 1
            if player['timed_effects'][stat] <= 0:
                delta = player.get('temp_mods', {}).pop(stat, 0)
                # revert the stat change
                if delta:
                    player[stat] -= delta
                player['timed_effects'].pop(stat, None)
                print(f'Your {names.get(stat,stat)} returns to normal.')

    def drink_from_pool(self, player, room, test_arg=None):
        """Handle drinking from a magic pool: apply +/-1 to stats for 10 movement rounds."""
        # Prefer using the pool's assigned type if present
        if room and getattr(room, 'pool', False):
            stat, delta = room.pool
            msg_map = {
                ('str', 1): 'You drink from the pool and feel a surge of strength.',
                ('str', -1): 'You drink from the pool and suddenly feel weak.',
                ('int', 1): 'You drink from the pool and your thoughts sharpen.',
                ('int', -1): 'You drink from the pool and your mind goes foggy.',
                ('dex', 1): 'You drink from the pool and your body moves with uncanny ease.',
                ('dex', -1): 'You drink from the pool and your limbs feel sluggish.',
            }
            message = msg_map.get((stat, delta), 'You drink deeply; the water is ice-cold and strange.')
        else:
            options = [
                ('str', 1, 'You take a drink and feel stronger.'),
                ('str', -1, 'You take a drink and feel weaker.'),
                ('int', 1, 'You take a drink and feel smarter.'),
                ('int', -1, 'You take a drink and feel dumber.'),
                ('dex', 1, 'You take a drink and feel nimbler.'),
                ('dex', -1, 'You take a drink and feel clumsier.'),
            ]
            stat, delta, message = random.choice(options)
        print(message)
        # Map negative effects to curing treasures
        cure_map = {'str':'PALE PEARL', 'int':'GREEN GEM', 'dex':'RUBY RED'}
        # If pool is a stat change
        if stat in ('str','int','dex'):
            if delta < 0 and cure_map.get(stat) in player.get('Treasures', []):
                print(f'Your {cure_map[stat]} glows and protects you from the effect!')
                return
            # Revert any existing temporary mod on this stat before applying new
            existing = player.get('temp_mods', {}).get(stat, 0)
            if existing:
                player[stat] -= existing
            # Apply temporary modifier and set duration (10 movement rounds)
            player.setdefault('temp_mods', {})[stat] = delta
            player[stat] = player.get(stat, 0) + delta
            player.setdefault('timed_effects', {})[stat] = 10
            return

        # If pool changes race
        if stat == 'race':
            newrace = delta
            oldrace = player.get('race','HUMAN')
            if newrace == oldrace:
                print('A cold ripple passes through you, but you remain the same.')
                return
            # race base stats are forced on transformation
            race_bases = {'ELF':{'str':8,'int':13,'dex':13}, 'DWARF':{'str':14,'int':13,'dex':8}, 'HUMAN':{'str':12,'int':11,'dex':11}, 'HOBBIT':{'str':9,'int':11,'dex':14}}
            bases = race_bases.get(newrace, {'str':12,'int':11,'dex':11})
            temp = player.get('temp_mods', {})
            for s in ('str','int','dex'):
                player[s] = bases.get(s, player.get(s, 0)) + temp.get(s, 0)
            # adjust HP based on new effective strength
            new_max = 8 + max(0, player.get('str', 10) - 10)
            player['max_hp'] = new_max
            player['hp'] = min(player.get('hp', new_max), new_max)
            player['race'] = newrace
            print('A terrible tide surges through your bones — you have become a ' + newrace + '!')
            return

        # If pool flips sex
        if stat == 'sex':
            old = player.get('sex', 'MALE')
            new = 'FEMALE' if old.upper().startswith('M') else 'MALE'
            player['sex'] = new
            print('A strange warmth spreads through you, and when you look down the world has shifted. You are now ' + new + '.')
            return

    def open_book(self, player, room, test_arg=None):
        options = [
            ('blind', 'FLASH! OH NO! YOU ARE NOW BLIND!'),
            ('poetry', "IT'S ANOTHER VOLUME OF ZOT'S POETRY! - YECH!!"),
            ('play', f"IT'S AN OLD COPY OF PLAY{player['race']}"),
            ('bookstuck', 'THE BOOK STICKS TO YOUR HANDS - YOU ARE NOW UNABLE TO DRAW YOUR WEAPON!'),
            ('dex', "IT'S A MANUAL OF DEXTERITY!"),
            ('str', "IT'S A MANUAL OF STRENGTH!")
        ]
        kind, message = random.choice(options)
        print(message)
        if kind == 'blind':
            if 'OPAL EYE' in player.get('Treasures', []):
                print('Your Opal Eye flares brilliantly and shields you from the blindness!')
            else:
                player['blind'] = True
        elif kind == 'bookstuck':
            if 'BLUE FLAME' in player.get('Treasures', []):
                print('The Blue Flame ignites and dissolves the book binding before it can take hold!')
            else:
                player['bookstuck'] = True
        elif kind == 'dex':
            if player.get('dex', 0) < 18:
                player['dex'] = 18
            print('Your dexterity is now 18 for the rest of your quest.')
        elif kind == 'str':
            old_str = player.get('str', 10)
            if old_str < 18:
                player['str'] = 18
            new_max = 8 + max(0, player['str'] - 10)
            hp_diff = new_max - player.get('max_hp', new_max)
            player['max_hp'] = new_max
            player['hp'] = min(player.get('hp', new_max) + max(0, hp_diff), new_max)
            print('Your strength is now 18 for the rest of your quest.')
        room.misc = ''

    def reveal_map(self, castlemap, reveal=True):
        """Set `.revealed` for every room in the castlemap to `reveal`.
        Use `reveal=True` to unhide all rooms, `reveal=False` to hide them.
        """
        for level in range(len(castlemap)):
            for x in range(8):
                for y in range(8):
                    try:
                        castlemap[level][x][y].revealed = bool(reveal)
                    except Exception:
                        # ignore malformed cells
                        pass
        if getattr(self, 'debug', False):
            print(f"DEBUG: reveal_map set to {reveal} for all rooms")

if __name__ == "__main__":
    # If run with --test-display, initialize and show a single level and room for testing
    if '--test-display' in sys.argv:
        try:
            debug = '--debug' in sys.argv
            if debug:
                print('DEBUG mode enabled')
            wc = WizardsCastle(debug=debug)
            monsters = ['KOBOLD', 'ORC', 'WOLF', 'GOBLIN', 'OGRE', 'TROLL', 'BEAR', 'MINOTAUR', 'GARGOYLE', 'CHIMERA',
                        'BALROG', 'DRAGON', 'VENDOR']
            treasures = ['RUBY RED', 'NORN STONE', 'PALE PEARL', 'OPAL EYE', 'GREEN GEM', 'BLUE FLAME', 'PALANTIR',
                         'SILMARIL']
            misc = ['POOL', 'CHEST', 'FLARES', 'WARP', 'CRYSTAL ORB', 'BOOK', 'LAMP']
            food = ['SANDWICH', 'STEW', 'SOUP', 'BURGER', 'ROAST', 'FILET', 'TACO', 'PIE']

            # mapsize historically was 513 when levels were 1-based; with 0-based levels use 512
            mapsize = 512
            sinkholes = 4

            # Parse optional seed argument: `--seed N` to make test reproducible
            seed = None
            if '--seed' in sys.argv:
                try:
                    si = sys.argv.index('--seed')
                    seed = int(sys.argv[si + 1])
                except Exception:
                    print('Invalid --seed value; falling back to default seed 0')
                    seed = 0

            # Use provided seed if given, otherwise default to 0 for --test-display
            if seed is not None:
                random.seed(seed)
                print(f'Seeding RNG with {seed} for deterministic test')
            else:
                random.seed(0)
                print('Seeding RNG with 0 for deterministic test')

            print('Initializing map...')
            castlemap = wc.initmap(mapsize, sinkholes)
            print('Populating map...')
            wc.populatemap(castlemap, monsters.copy(), treasures.copy(), food.copy(), misc.copy())

            # Entrance is level 0, row 0, col 4 in 0-based indexing
            playerpos = (0, 0, 4)
            print('\nDisplaying level with player (compact):')
            wc.display(castlemap, playerpos=playerpos, show_room=False, detail=False)

            print('\nDisplaying player room (detailed):')
            wc.display(castlemap, playerpos=playerpos, show_room=True, detail=True)
        except KeyboardInterrupt:
            print('\nInterrupted by user')
    else:
        debug = '--debug' in sys.argv
        if debug:
            print('DEBUG mode enabled')
        game = WizardsCastle(debug=debug)
        game.play()