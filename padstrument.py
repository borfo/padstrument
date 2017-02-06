#!/usr/bin/python3
import mido, logging, time
from threading import Timer

# set up logging  - 50 CRITICAL 40 ERROR 30 WARNING 20 INFO 10 DEBUG 0 NOTSET
logging.basicConfig(level="DEBUG",  format='%(levelname)s - %(message)s')

# Global reference vars - notelookups
C=0; Db=Cs=1; D=2; Eb=Ds=3; E=4; F=5; Gb=Fs=6; G=7; Ab=Gs=8; A=9; Bb=As=10; B=11;
note2num = {"C":0, "Cs":1, "Db":1, "D":2, "Ds":3, "Eb":3, "E":4, "F":5, "Fs":6, "Gb":6, "G":7, "Gs":8, "Ab":8, "A":9, "As":10, "Bb":10, "B":11 }
num2note = {0:"C", 1:"Cs", 2:"D", 3:"Ds", 4:"E", 5:"F", 6:"Fs", 7:"G", 8:"Gs", 9:"A", 10:"As", 11:"B", }


class Bunch(dict):
    #simple object class that allows adding arbitrary attributes, also readable as dict
    def __init__(self,**kw):
        dict.__init__(self,kw)
        self.__dict__ = self

class Translate:
    '''Translates between the following
    note2grid(note, top/bottom)  - nanopad note to button grid coord
    grid2note(row, col) - grid coordinate to nanopad note
    '''

    notename2num_map = {"C":0, "Cs":1, "Db":1, "D":2, "Ds":3, "Eb":3, "E":4, "F":5, "Fs":6, "Gb":6, "G":7, "Gs":8, "Ab":8, "A":9, "As":10, "Bb":10, "B":11 }
    notenum2name_map = {0:"C", 1:"Cs", 2:"D", 3:"Ds", 4:"E", 5:"F", 6:"Fs", 7:"G", 8:"Gs", 9:"A", 10:"As", 11:"B", }

    grid2note_map = [ # maps grid coordinates to the midi notes the nanoPAD emits
        list( range( 64, 72, 1 ) ),
        list( range( 72, 80, 1 ) ),
        list( range( 79, 71, -1 ) ),
        list( range( 71, 63, -1 ) )
        ]

    # generate note2grid maps
    note2grid_map = { "top":{}, "bottom":{} }
    for row in range (0,2):
        for col in range (0,8):
            note2grid_map['top'][ grid2note_map[row][col] ] = (row, row, col,)
            note2grid_map['bottom'][ grid2note_map[row+2][col] ] = (row+2, row, col,)

    @classmethod
    def coord_exists(cls, row, col):
        '''check row/col coordinates'''
        if ( cls.row_exists(row) and cls.col_exists(col) ):
            return True
        else:
            raise Exception("Translate: coordinate doesn't exist")
            return False

    @classmethod
    def row_exists(cls, row):
        '''return True if row = 0-3, raise exception if not'''
        if ( row >= 0 and row <= 3 ):
            return True
        else:
            raise Exception( "Layout Error: Requested row "+str(row)+" does not exist" )
            return False

    @classmethod
    def col_exists(cls, col):
        '''return True if col = 0-7, raise exception if not'''
        if ( col >= 0 and col <= 7 ):
            return True
        else:
            raise Exception( "Layout Error: Requested row "+str(col)+" does not exist" )
            return False

    @classmethod
    def grid2note(cls, row, col):
        '''takes a grid coordinate, and returns the corresponding nanopad note number'''
        if (cls.coord_exists(row, col)):
            return cls.grid2note_map[row][col]
        else:
            return False

    @classmethod
    def bottom_grid2note(cls, row, col):
        '''takes a grid coordinate on the 2x8 bottom nanopad, and returns the corresponding nanopad note number'''
        if (row < 0 or row > 1):
            return False
        else:
            return cls.grid2note(row+2, col)

    @classmethod
    def top_grid2note(cls, row, col):
        '''takes a grid coordinate on the 2x8 bottom nanopad, and returns the corresponding nanopad note number'''
        if (row < 0 or row > 1):
            return False
        else:
            return cls.grid2note(row, col)

    @classmethod
    def notename2num(cls, notename):
        '''takes a grid coordinate, and returns the corresponding nanopad note number'''
        return cls.notename2num_map[notename]

    @classmethod
    def notenum2name(cls, notenum):
        '''takes a grid coordinate, and returns the corresponding nanopad note number'''
        return cls.notenum2name_map[notenum]




class Layouts:
    '''layouts are multidimensional (4x8) lists composed of tuples
    containing different info depending on what type of function the button serves
    most are standard notes, but there are special function buttons
    KWARGS allows passing arbitrary info with the layout
    NOTES( scale_degree (1-7), group(1-4), (KWARGS)  )
    scale_degree can go up or down past 1-7 as desired
    offsets will be translated into higher or lower notes, following the 1-7 scale degree thing
    4 x 4 layouts - split vertically

    4x4 layouts provide one model, which can be rotated and flipped. (TODO)
    User sets one side, which is either mirrored or repeated, with different octave groups on the other side
    '''

    # set default note and button layouts
    # don't change current play mode unless more play mode layouts are added
    # settings modes are retrieved by the main class by specifying the mode.

    current_button_mode = "play"
    current_note_layout = "hang_full"

    buttons = {}
    notes = {}

    # full size button function layouts - can be applied directly without
    # having to be assembled from layout pieces

    F = False
    N = "outnote"
    buttons['play'] = [
            [ (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,) ],
            [ (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,) ],
            [ (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,) ],
            [ (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,), (N,N,) ]
            ]

    buttons['bs0'] = [
            [ ('s4','s4',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s3','s3',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s2','s2',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s1','s1',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ]
            ]

    buttons['bs1'] = [
            [ ('s4','s4',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s3','s3',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s2','s2',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s1','s1',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ]
            ]

    buttons['bs2'] = [
            [ ('s4','s4',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s3','s3',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s2','s2',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s1','s1',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ]
            ]

    buttons['bs3'] = [
            [ ('s4','s4',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s3','s3',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s2','s2',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s1','s1',), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ]
            ]

    T = "set_tonic" # (T,notenum,)
    CC = "set_C_major"
    S = "set_scale" # (S,'harm' or 'nat',)
    M = "set_mode" # (M, modenum 1-7)
    buttons['bs4'] = [
            [ ('s4','s4',), ((T,1,),F,), ((T,3,),F,), (F,F,), ((T,6,),F,), ((T,8,),F,), ((T,10,),F,), (CC,F,) ],
            [ ('s3','s3',), ((T,0,),F,), ((T,2,),F,), ((T,4,),F,), ((T,5,),F,), ((T,7,),F,), ((T,9,),F,), ((T,11,),F,) ],
            [ ('s2','s2',), ((S,'nat',),F,), ((S,'harm',),F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,) ],
            [ ('s1','s1',), ((M,1,),F,), ((M,2,),F,), ((M,3,),F,), ((M,4,),F,), ((M,5,),F,), ((M,6,),F,), ((M,7,),F,) ]
            ]




    buttons['ts0'] = [
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s1','s1',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s2','s2',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s3','s3',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s4','s4',) ]
            ]

    buttons['ts1'] = [
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s1','s1',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s2','s2',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s3','s3',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s4','s4',) ]
            ]

    buttons['ts2'] = [
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s1','s1',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s2','s2',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s3','s3',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s4','s4',) ]
            ]

    buttons['ts3'] = [
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s1','s1',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s2','s2',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s3','s3',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s4','s4',) ]
            ]

    buttons['ts4'] = [
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s1','s1',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s2','s2',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s3','s3',) ],
            [ (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), (F,F,), ('s4','s4',) ]
            ]


    # full size note layouts - can be applied directly without
    # having to be assembled from layout pieces

    notes['hang_full'] = [
            [ (4,4), (6,4), (1,5), (7,4), (4,6), (6,6), (1,6), (7,6) ],
            [ (2,4), (3,3), (1,3), (5,4), (2,6), (3,5), (1,5), (5,6) ],
            [ (5,3), (1,4), (3,4), (2,3), (5,5), (1,6), (3,6), (2,5) ],
            [ (7,3), (1,2), (6,3), (4,3), (7,5), (1,4), (6,5), (4,5) ]
            ]

    notes['hang_mirror'] = [
            [ (4,4), (6,4), (1,5), (7,4), (7,6), (1,7), (6,6), (4,6) ],
            [ (2,4), (3,3), (1,3), (5,4), (5,6), (1,5), (3,5), (2,6) ],
            [ (5,3), (1,4), (3,4), (2,3), (2,5), (3,6), (1,6), (5,5) ],
            [ (7,3), (1,2), (6,3), (4,3), (4,5), (6,5), (1,4), (7,5) ]
            ]

    notes['lead'] = [
            [ (1,5), (3,5), (5,5), (7,5), (2,6), (4,6), (6,6), (1,7) ],
            [ (2,5), (4,5), (6,5), (1,6), (3,6), (5,6), (7,6), (2,7) ],
            [ (1,3), (3,3), (5,3), (7,3), (2,4), (4,4), (6,4), (1,5) ],
            [ (2,3), (4,3), (6,3), (1,4), (3,4), (5,4), (7,4), (2,5) ]
            ]


    @classmethod
    def button_layout_exists( cls, mode ):
        '''return True if mode exists, raise exception if not'''
        if ( mode in cls.buttons ):
            return cls.buttons[mode]
        else:
            raise Exception( "Layout Error: Button mode "+str(mode)+" does not exist" )
            return False

    @classmethod
    def note_layout_exists( cls, name ):
        '''return True if mode exists, raise exception if not'''
        if ( name in cls.notes ):
            return cls.notes[name]
        else:
            raise Exception( "Layout Error: Note layout "+str(name)+" does not exist" )
            return False

    @classmethod
    def coord_exists( cls, row, col ):
        '''check row/col coordinates'''
        if ( cls.row_exists(row) and cls.col_exists(col) ):
            return True
        else:
            raise Exception("Layout: coordinate doesn't exist")
            return False

    @classmethod
    def row_exists( cls, row ):
        '''return True if row = 0-3, raise exception if not'''
        if ( row >= 0 and row <= 3 ):
            return True
        else:
            raise Exception( "Layout Error: Requested row "+str(row)+" does not exist" )
            return False

    @classmethod
    def col_exists( cls, col ):
        '''return True if col = 0-7, raise exception if not'''
        if ( col >= 0 and col <= 7 ):
            return True
        else:
            raise Exception( "Layout Error: Requested row "+str(col)+" does not exist" )
            return False

    @classmethod
    def set_button_layout( cls, mode ):
        '''sets the current button mode
        '''
        if ( cls.button_layout_exists(mode) ):
            cls.current_button_mode = mode
            return True
        else:
            return False

    @classmethod
    def set_note_layout( cls, name ):
        '''sets the current note layout
        '''

        if ( cls.note_layout_exists(name) ):
            cls.current_note_layout = name
            return True
        else:
            return False

    @classmethod
    def get_button_layout( cls, mode=False ):
        '''returns a multidimensional layout list setting out the
        button on_press and button on_release functionality in
        a given pad mode.

        Functionality is specified as follows:
        buttons[row][col][0] = on_press
        buttons[row][col][1] = on_release

        on_press and on_release can be:
        - a keyword string, to be interpreted by a handler function
        - a tuple, containing:
        ---- keyword, args
        '''
        mode = mode if mode else cls.current_button_mode
        if ( cls.button_layout_exists(mode) ):
            return cls.buttons[ mode ]
        else:
            return False

    @classmethod
    def get_note_layout( cls, name=False ):
        '''returns a multidimensional layout list setting out the
        layout of the scale degrees (i-Vii) on the button pads.

        Notes are specified as follows:
        buttons[row][col][0] = scale_degree (1-7)
        buttons[row][col][1] = octave_offset

        oct offset can be a valid midi octave, or can be code for some other
        functionality if out of midi range
        '''
        name = name if name else cls.current_note_layout
        if ( cls.note_layout_exists(name) ):
            return cls.notes[name]
        else:
            return False

    @classmethod
    def get_button( cls, row, col, mode=False ):
        '''returns a tuple containing all the settings for a button
        (onpress, onpress_args, onrelease, onrelease_args) - each element is a string or False
        '''
        mode = mode if mode else cls.current_button_mode
        if ( cls.button_layout_exists(mode) and cls.coord_exists(row,col) ):
            button = cls.buttons[mode][row][col]
            if ( type(button[0]).__name__ == "tuple" ):
                onpress = button[0][0]
                onpress_args = button[0][1]
            else:
                onpress = button[0]
                onpress_args = False

            if ( type(button[1]).__name__ == "tuple" ):
                onrelease = button[0][0]
                onrelease_args = button[0][1]
            else:
                onrelease = button[0]
                onrelease_args = False

            return (onpress, onpress_args, onrelease, onrelease_args,)
        else:
            return False

    @classmethod
    def get_note( cls, row, col, name=False ):
        '''returns a tuple containing all the settings for a button
        (degree, octave) - each element is an int or False
        '''
        name = name if name else cls.current_note_layout
        if ( cls.note_layout_exists(name) and cls.coord_exists(row,col) ):
            # get note and octave, deal with notes above 7
            note = cls.notes[name][row][col][0] % 8
            octave = cls.notes[name][row][col][1] + ( cls.notes[name][row][col][0] // 8 )

            return (note, octave,)
        else:
            return False


class Scales:

    # settable class variables
    tonic = 0 # key root note - defaults to C
    mode = 1 # 1 based - will also accept mode names
    type = 'nat' # 'nat' or 'harm' for natural or harmonic minor scales as a basis for the mode calculations.

    # generate scales
    circle_5 = [C,G,D,A,E,B,Fs,Db,Ab,Eb,Bb,F]
    circle_m = [A,E,B,Fs,Cs,Gs,Eb,Bb,F,C,G,D] # minor scales - the inner wheel Aeolian stuff.  Used for navigation buttons to move around the circle to change key.
    circle_5ths = circle_5 + circle_5 # create a threepeat circle of fifths.  slice it to get scales.

    temp = [ ]
    for x in range(0,7):
        temp.append( circle_5ths[12-x:19-x] )
        temp[x].sort()

    # generate modes of C
    scaler = Bunch()
    scaler['nat'] = Bunch()
    scaler['nat'][C] = Bunch()
    scaler['nat'][C]['ionian'] = scaler['nat'][C]['i'] = scaler['nat'][C][1] = temp[1]
    scaler['nat'][C]['dorian'] = scaler['nat'][C]['ii'] = scaler['nat'][C][2] = temp[3]
    scaler['nat'][C]['phrygian'] = scaler['nat'][C]['iii'] = scaler['nat'][C][3] = temp[5]
    scaler['nat'][C]['lydian'] = scaler['nat'][C]['iv'] = scaler['nat'][C][4] = temp[0]
    scaler['nat'][C]['mixolydian'] = scaler['nat'][C]['v'] = scaler['nat'][C][5] = temp[2]
    scaler['nat'][C]['aeolian'] = scaler['nat'][C]['vi'] = scaler['nat'][C][6] = temp[4]
    scaler['nat'][C]['locrian'] = scaler['nat'][C]['vii'] = scaler['nat'][C][7] = temp[6]

    scaler['harm'] = Bunch()
    scaler['harm'][C] = Bunch()
    scaler['harm'][C]['aeolian7'] = scaler['harm'][C]['i'] = scaler['harm'][C][1] = [ x+1 if key == 6 else x for key, x in enumerate( scaler['nat'][C]['aeolian'] ) ]
    scaler['harm'][C]['locrian6'] = scaler['harm'][C]['ii'] = scaler['harm'][C][2] = [ x+1 if key == 6 else x for key, x in enumerate( scaler['nat'][C]['locrian'] ) ]
    scaler['harm'][C]['ionian5'] = scaler['harm'][C]['iii'] = scaler['harm'][C][3] = [ x+1 if key == 6 else x for key, x in enumerate( scaler['nat'][C]['ionian'] ) ]
    scaler['harm'][C]['dorian4'] = scaler['harm'][C]['iv'] = scaler['harm'][C][4] = [ x+1 if key == 6 else x for key, x in enumerate( scaler['nat'][C]['dorian'] ) ]
    scaler['harm'][C]['phrygian3'] = scaler['harm'][C]['v'] = scaler['harm'][C][5] = [ x+1 if key == 6 else x for key, x in enumerate( scaler['nat'][C]['phrygian'] ) ]
    scaler['harm'][C]['lydian2'] = scaler['harm'][C]['vi'] = scaler['harm'][C][6] = [ x+1 if key == 6 else x for key, x in enumerate( scaler['nat'][C]['lydian'] ) ]
    scaler['harm'][C]['mixolydian1'] = scaler['harm'][C]['vii'] = scaler['harm'][C][7] = [ x+1 if key == 6 else x for key, x in enumerate( scaler['nat'][C]['mixolydian'] ) ]

    # generate other scales
    global i # workaround for i not being in context for list comprehensions
    for i in range(1,12):
        scaler['nat'][i] = Bunch()
        scaler['nat'][i]['ionian'] = scaler['nat'][i]['i'] = scaler['nat'][i][1] = [ x+i for x in scaler['nat'][C][1] ]
        scaler['nat'][i]['dorian'] = scaler['nat'][i]['ii'] = scaler['nat'][i][2] = [ x+i for x in scaler['nat'][C][2] ]
        scaler['nat'][i]['phrygian'] = scaler['nat'][i]['iii'] = scaler['nat'][i][3] = [ x+i for x in scaler['nat'][C][3] ]
        scaler['nat'][i]['lydian'] = scaler['nat'][i]['iv'] = scaler['nat'][i][4] = [ x+i for x in scaler['nat'][C][4] ]
        scaler['nat'][i]['mixolydian'] = scaler['nat'][i]['v'] = scaler['nat'][i][5] = [ x+i for x in scaler['nat'][C][5] ]
        scaler['nat'][i]['aeolian'] = scaler['nat'][i]['vi'] = scaler['nat'][i][6] = [ x+i for x in scaler['nat'][C][6] ]
        scaler['nat'][i]['locrian'] = scaler['nat'][i]['vii'] = scaler['nat'][i][7] = [ x+i for x in scaler['nat'][C][7] ]

        scaler['harm'][i] = Bunch()
        scaler['harm'][i]['aeolian7'] = scaler['harm'][i]['i'] = scaler['harm'][i][1] = [ x+i for x in scaler['harm'][C][1] ]
        scaler['harm'][i]['locrian6'] = scaler['harm'][i]['ii'] = scaler['harm'][i][2] = [ x+i for x in scaler['harm'][C][2] ]
        scaler['harm'][i]['ionian5'] = scaler['harm'][i]['iii'] = scaler['harm'][i][3] = [ x+i for x in scaler['harm'][C][3] ]
        scaler['harm'][i]['dorian4'] = scaler['harm'][i]['iv'] = scaler['harm'][i][4] = [ x+i for x in scaler['harm'][C][4] ]
        scaler['harm'][i]['phrygian3'] = scaler['harm'][i]['v'] = scaler['harm'][i][5] = [ x+i for x in scaler['harm'][C][5] ]
        scaler['harm'][i]['lydian2'] = scaler['harm'][i]['vi'] = scaler['harm'][i][6] = [ x+i for x in scaler['harm'][C][6] ]
        scaler['harm'][i]['mixolydian1'] = scaler['harm'][i]['vii'] = scaler['harm'][i][7] = [ x+i for x in scaler['harm'][C][7] ]

    mode_names = Bunch()
    mode_names['nat'] = Bunch()
    mode_names['nat'][1] = Bunch( name='ionian', numeral='i' )
    mode_names['nat'][2] = Bunch( name='dorian', numeral='ii' )
    mode_names['nat'][3] = Bunch( name='phrygian', numeral='iii' )
    mode_names['nat'][4] = Bunch( name='lydian', numeral='iv' )
    mode_names['nat'][5] = Bunch( name='mixolydian', numeral='v' )
    mode_names['nat'][6] = Bunch( name='aeolian', numeral='vi'  )
    mode_names['nat'][7] = Bunch( name='locrian', numeral='vii'  )

    mode_names['harm'] = Bunch()
    mode_names['harm'][1] = Bunch( name='aeolian7', numeral='i'  )
    mode_names['harm'][2] = Bunch( name='locrian6', numeral='ii'  )
    mode_names['harm'][3] = Bunch( name='ionian5', numeral='iii'  )
    mode_names['harm'][4] = Bunch( name='dorian4', numeral='iv'  )
    mode_names['harm'][5] = Bunch( name='phrygian3', numeral='v'  )
    mode_names['harm'][6] = Bunch( name='lydian2', numeral='vi'  )
    mode_names['harm'][7] = Bunch( name='mixolydian1', numeral='vii'  )


    @classmethod
    def set_key(cls, tonic=0, mode=1, scale='nat' ):
        if ( int(tonic) >= 0 and int(tonic) <=11 and int(mode) >= 1 and int(mode) <= 7 and ( scale == 'nat' or scale == 'harm' ) ):
            cls.tonic = tonic # key root note
            cls.mode = 1 # 1 based - will also accept mode names
            cls.type = 'nat' # 'nat' or 'harm' for natural or harmonic minor scales as a basis for the mode calculations.
            return True
        else:
            return False

    @classmethod
    def get_key(cls):
        '''returns a tuple containing info on the current key/scale/mode
        ( int_tonic, int_mode, str_scale, )
        '''
        return ( cls.tonic, cls.mode, cls.scale, )

    @classmethod
    def get_note_by_degree(cls, degree, octave):
        '''retrieve note number by scale degree (1-7) and octave
        degree may be higher than 7 under some circumstances
        '''
        # deal with degrees higher than 7 - loop them around, forcing a number between 1 and 7.
        deg = degree % 8
        # but account for the octave offset
        octave += ( degree // 8 )

        notenum = cls.scaler[cls.type][cls.tonic][cls.mode][deg-1] + ( 12 * octave )
        return notenum

class Pad(Bunch):
    '''Pad object contains info about each nanopad button
    for the current pad settings - key/scale/mode
    - create with kwargs to set values
    '''
    # initialize all variables as False
    # coordinates
    grid_row = False    # row location in full 4x8 grid
    row = False         # row location in 2x8 nanopad grid
    col = False         # column location
    pad_note = False    # note emitted by nanopad button

    # out note information
    out_note = False    # note to be sent out when button is pressed
    out_degree = False  # scale degree of out_note
    out_octave = False

    # pad state information
    pressed = False

    # pad action information
    # onpress/release is false or a string to be parsed by a handler function
    # args can be a dict or a string or false
    onpress = False
    onpress_args = False
    onrelease = False
    onrelease_args = False

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            if hasattr( self, name ):
                setattr( self, name, value )
            else:
                raise Exception( "Pad has no attribute "+str(name) )

    def set(self, **kwargs):
        for name, value in kwargs.items():
            if hasattr( self, name ):
                setattr( self, name, value )
                return True
            else:
                raise Exception( "Pad has no attribute "+str(name) )

    def get(self, name):
        return setattr( self, name, value )

class Padstrument:
    '''main instrument class'''

    # sysex messages
    syx_prefix = [ 0x42,0x40,0x00,0x01,0x12,0x00 ] # set channel: syx_pre[1] += channelno
    syx_search = [ 0x42, 0x50, 0x00, 0x00 ] # send this to get response containing channel number
    syx_native_mode_on = [ 0x00,  0x00, 0x01 ]

    midi_out_channel=1
    def_button_mode = 'play'
#    def_note_layout = 'hang_full'
    def_note_layout = 'lead'

    scene = Bunch()
    scene[0] = Bunch()
    scene[1] = Bunch()
    scene[0]['pressed'] = False
    scene[1]['pressed'] = False
    scene[0].modes = ['ts0', 'ts1', 'ts2', 'ts3', 'ts4' ]
    scene[1].modes = ['bs0', 'bs1', 'bs2', 'bs3', 'bs4' ]

    def __init__(self):
        mido.set_backend('mido.backends.rtmidi/LINUX_ALSA')
        self.cur_mode = self.def_button_mode
        self.cur_note_layout = self.def_note_layout
        self.connect()  # connect nanopads
        self.make_padmaps()
        self.set_top_NP2(0)

        self.outport = mido.open_output("padstrument_out", virtual=True)

    def reset(self, top_pad_id=None):
        '''reset storage variables to defaults'''
        self.cur_mode = self.def_button_mode
        self.scene[0]['pressed'] = False
        self.scene[1]['pressed'] = False

    def connect(self, name_str="nanoPAD2"):
        '''connect two nanopads -- error if two are not connected
        '''
        logging.debug("Connecting nanoPADs")

        self.NP2 = Bunch() # initialize pad connection bunch
        ports = mido.get_ioport_names()
        logging.debug(ports)
        count=0

        for port in ports:
            if ( name_str in port ):
                logging.debug('connect first pad %s at self.NP2[%i]', port, count)
                self.port_open( count, port )
                count += 1

            if (count == 2):
                logging.debug("two nanopads connected - break")
                break

        if ( count < 2 ):
            raise Exception("Less than 2 nanoPAD2's connected.")
        else:
            return True

    def port_open( self, NP2num, id_str ):
        '''opens and configures a nanopad port'''
        callback=[ self.handler_0, self.handler_1 ]
        # open port
        self.NP2[NP2num] = mido.open_ioport( id_str, autoreset=True, callback = callback[NP2num] )
        self.NP2[NP2num].num = NP2num
        self.NP2[NP2num].id_str = id_str

        # send device search sysex - get device channel
        syxin = self.catch_sysex_reply( NP2num, mido.Message( 'sysex', data=self.syx_search ) )
        logging.debug("chan %s", syxin.data[3])
        self.NP2[NP2num].channel = syxin.data[3]

        # set sysex prefix
        self.NP2[NP2num].syx_prefix =  self.syx_prefix
        self.NP2[NP2num].syx_prefix[1] += self.NP2[NP2num].channel

        # Put pad in native mode
        syxdata = self.NP2[NP2num].syx_prefix + self.syx_native_mode_on
        syxin = self.catch_sysex_reply( NP2num, mido.Message( 'sysex', data=syxdata ) )

        return True

    def port_close( self ):
        '''close all midi ports'''
        for NP2num, port in self.NP2.items():
            if ( NP2num in self.NP2 ):
                if ( type(self.NP2[NP2num]).__name__ == "mido.ports" ):
                    logging.debug("goats goats ---------------------")
                    self.NP2[NP2num].reset()
                    self.NP2[NP2num].close()

    def set_top_NP2(self, topnum=0):
        '''Choose which NP2 is above the other.  Defaults to 0.
        Nothing should be necessary to switch top/bottom other than this function
        no reset should be required.'''
        logging.debug("SET TOP %i", topnum)
        bottomnum = 1 if topnum == 0 else 0
        # assign padmaps - these map notes to grid coordinates, with other
        self.NP2[topnum].padmap = self.padmap['top']
        self.NP2[bottomnum].padmap = self.padmap['bottom']

        # set top pad - defaults to pad 0
        self.NP2['top'] = self.NP2[topnum]
        self.NP2['bottom'] = self.NP2[bottomnum]
        self.connected = True

        return True

    def catch_sysex_reply( self, NP2num, msg ):
        '''sets a flag telling the callback to catch the next incoming sysex message
        for catching sysex replies.  Workaround for fucked up receive() locking'''
        self.NP2[NP2num].catch_next_sysex = True
        self.NP2[NP2num].caught_sysex = False

        self.NP2[NP2num].send( msg )
        while ( not self.NP2[NP2num].caught_sysex ):
            time.sleep(0.01)
        syxin = self.NP2[NP2num].caught_sysex
        self.NP2[NP2num].caught_sysex = False
        return syxin

    def make_padmaps(self):
        '''create top and bottom padmaps ( dict[NPnote]=Pad_object )
        these are later assigned to the NP2s ( NP2[num].map )
        depending on which is the top and which is the bottom.
        '''
        # initialize / reset
        self.padmap = {}
        self.padmap['top'] = {}
        self.padmap['bottom'] = {}

        for row in range (0,2):
            for col in range (0,8):
                topnote = Translate.top_grid2note( row, col )
                outnote = Layouts.get_note( row, col, self.cur_note_layout ) # tuple
                events = Layouts.get_button( row, col )

                self.padmap["top"][ topnote ] = Pad(
                    grid_row = row,    # row location in full 4x8 grid
                    row = row,         # row location in 2x8 nanopad grid
                    col = col,         # column location
                    pad_note = topnote,    # note emitted by nanopad button

                    # out note information
                    out_note = Scales.get_note_by_degree( outnote[0], outnote[1] ),    # note to be sent out when button is pressed
                    out_degree = outnote[0],  # scale degree of out_note
                    out_octave = outnote[1],

                    # pad state information
                    pressed = False,

                    # pad action information
                    # onpress/release is false or a string to be parsed by a handler function
                    # args can be a dict or a string or false
                    onpress = events[0],
                    onpress_args = events[1],
                    onrelease = events[2],
                    onrelease_args = events[3],
                    )

                bottomnote = Translate.bottom_grid2note( row, col )
                outnote = Layouts.get_note( row+2, col, self.cur_note_layout ) # tuple
                events = Layouts.get_button( row+2, col )

                self.padmap["bottom"][ bottomnote ] = Pad(
                    grid_row = row+2,    # row location in full 4x8 grid
                    row = row,         # row location in 2x8 nanopad grid
                    col = col,         # column location
                    pad_note = topnote,    # note emitted by nanopad button

                    # out note information
                    out_note = Scales.get_note_by_degree( outnote[0], outnote[1] ),    # note to be sent out when button is pressed
                    out_degree = outnote[0],  # scale degree of out_note
                    out_octave = outnote[1],

                    # pad state information
                    pressed = False,

                    # pad action information
                    # onpress/release is false or a string to be parsed by a handler function
                    # args can be a dict or a string or false
                    onpress = events[0],
                    onpress_args = events[1],
                    onrelease = events[2],
                    onrelease_args = events[3],
                    )
        return True

    def scene_pressed(self, NP2num ):
        '''a scene/settings button was pressed'''
        self.scene[NP2num].pressed = True
        if ( self.cur_mode == self.def_button_mode ):
            self.cur_mode = self.scene[NP2num].modes[0]
            self.set_all_scene_leds( NP2num, 0b1111 )


    def scene_released(self, NP2num ):
        '''a scene/settings button was pressed'''
        self.scene[NP2num].pressed = False
        if ( not self.cur_mode == self.def_button_mode ):
            self.cur_mode = self.def_button_mode
            self.set_all_scene_leds( NP2num, 0b0000 )


    def set_scene_led(self, NP2num=0, lednum=0, on=True):
        '''set all 4 leds on or off according to the binary flag passed to the function'''
        controls=[0x79, 0x7A, 0x7B, 0x7C ]
        value=127 if on else 0
        msg = mido.Message('control_change', channel=15, control=controls[lednum], value=value )
        self.NP2[NP2num].send( msg )


    def set_all_scene_leds(self, NP2num, bin_flags=0b1111):
        '''set all 4 leds on or off according to the binary flag passed to the function'''
        logging.debug("set led | NP2num %i | flags %s ", NP2num, bin(bin_flags) )
        masks = {0:0b0001, 1:0b0010, 2:0b0100, 3:0b1000}
        for lednum, mask in masks.items():
            if ( bin_flags & mask ):
                self.set_scene_led( NP2num, lednum, True )
            else:
                self.set_scene_led( NP2num, lednum, False )

    def handler_0( self, msg, NP2num=0 ):
        '''wrapper for handle_msgs() that plugs in the pad number.'''
        self.handle_msgs(msg, NP2num)

    def handler_1( self, msg, NP2num=1 ):
        '''wrapper for handle_msgs() that plugs in the pad number.'''
        self.handle_msgs(msg, NP2num)

    def handle_msgs(self, msg, NP2num):
        logging.debug("MSG %s - pad %i - hex %s ", msg, NP2num, msg.hex())

        if ( msg.type == "sysex" ):
            logging.debug("hex %s", msg.hex())

            if ( self.NP2[NP2num].catch_next_sysex == True ):
                self.NP2[NP2num].catch_next_sysex = False
                self.NP2[NP2num].caught_sysex = msg
            return True

        # handle noteon and noteoffs in default mode
        if ( self.cur_mode == self.def_button_mode and msg.channel == 1  and
        ( msg.type == "note_on" or msg.type == "note_off" ) and msg.note in self.NP2[NP2num].padmap ):
            logging.debug( "NOTE %i vel %i ch %i pad %i", msg.note, msg.velocity, msg.channel, NP2num )

            pad = self.NP2[NP2num].padmap[msg.note]

            if ( msg.type == "note_on" ):
                pad.pressed = True
                action = pad.onpress
                action_args = pad.onpress_args
                if (not action) or ( action != "outnote"):
                    return False
                else:
                    # send note message, copying the trigger message's velocity and type
                    outmsg = msg.copy( note=pad.out_note, channel=self.midi_out_channel )
                    logging.debug("out"+str(outmsg))
                    self.outport.send(outmsg)
            elif ( msg.type == "note_off" ):
                pad.pressed = False
                action = pad.onrelease
                action_args = pad.onrelease_args
                if (not action) or ( action != "outnote"):
                    return False
                else:
                    # send note message, copying the trigger message's velocity and type
                    outmsg = msg.copy( note=pad.out_note, channel=self.midi_out_channel )
                    logging.debug("out"+str(outmsg))
                    self.outport.send(outmsg)
            return True

        # get SCENE button presses - activate/deactivate SETTINGS modes
        if ( msg.type  == "control_change" and msg.channel == 15 and msg.control == 57 ):
            # a settings button was pressed or released
            if ( msg.value > 0 ):
                logging.debug("scene %s pressed", NP2num)
                self.scene_pressed(NP2num)
            else:
                logging.debug("scene %s released", NP2num)
                self.scene_released(NP2num)
                #self.reset(self.NP2[NP2num].id_str)
            return True

        otherNP2num = 0 if NP2num == 1 else 1
        if ( msg.type == "note_on" ):
            # deal with settings button presses
            pad = self.NP2[NP2num].padmap[msg.note]
            pad.pressed=True
            # if SCENE + all four s1-s4 buttons are pressed, then set this pad as top
            if ( self.scene[NP2num]['pressed'] and
                self.NP2[NP2num].padmap[71].pressed and
                self.NP2[NP2num].padmap[79].pressed
                ): # set this pad to top
                    self.set_top_NP2(NP2num)

        elif ( msg.type == "note_off" ):
            # deal with settings button releases
            pad = self.NP2[NP2num].padmap[msg.note]
            pad.pressed=False


        pad = self.NP2[NP2num].padmap[msg.note]
        logging.debug( "curmode: %s | button action: %s", self.cur_mode, Layouts.get_button(pad.grid_row, pad.col, self.cur_mode)[0] )

    def s1(self, press=True):
        pass

    def s2(self, press=True):
        pass

    def s3(self, press=True):
        pass

    def s4(self, press=True):
        pass




if __name__ == "__main__":
    pad = Padstrument()

    while True:
        time.sleep(0.02)


notes="""
- maps assigned to pads
- set button, note layouts
- set scale/key/mode
prior to making maps
"""
