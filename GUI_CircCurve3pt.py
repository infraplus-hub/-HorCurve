#
#
# GUI_Curve3ptAlign.py : Calculate circular curve parameter (PC,PI,PT,
#                        degree of curve, lenght of curve from a 3-point
#                        alignment in WKT format.
# Release v.1.0 : Phisan Santitamnont ( phisan.chula@gmail.com )
#                 29 Mar 2021
#
#
import subprocess
import sys,os
from shapely.geometry import Point, LineString
from shapely import wkt
from CircCurve3pt import *
import PySimpleGUI as sg
#import PySimpleGUIWeb as sg

TITLE = 'Calculate Horizontal Curve from 3-point Alignment'
CMD_CircCurve3pt = 'python3 CircCurve3pt.py' 
ARGS =  "'LINESTRING (0 5000, 10000 7000, 13000 -4000)' 3550 15 "

INPUT_STR = 'Input 1)"WKT of 3-points alignment" 2)RADIUS 3)NUMBER_OF_POINTS '

#################################################################
def main():
    OutPng = 'CACHE/GENCIRCCURVE3pt_CURVE.png'
    OutTxt = 'CACHE/GENCIRCCURVE3pt_REPORT.txt'
    sg.theme('DarkBlue3')
    layout = [ [sg.Image( filename='./CE_InfraMgmt.png') ],
               [sg.Text( INPUT_STR )] ,
               [   sg.Input( default_text=ARGS ,size=(70,1), 
                           font=('courier', 14), key='_ARGS_' ) ,
                   sg.Button('Run'), 
                   sg.Button('Exit') ] , 
               [sg.Output(key='_OUTPUT_', size=(80,25), 
                    font=('courier', 14) )  ],
               [sg.Image( size=(1000,1000), key="_IMAGE_")],
             ]
    window = sg.Window( TITLE,  layout)
    while True:             # Event Loop
        event, values = window.Read()
        #print(event, values)
        if event in (None, 'Exit'):
            break
        elif event == 'Run':
            #import pdb; pdb.set_trace()
            CMD = '{} {}'.format( CMD_CircCurve3pt, values['_ARGS_'] )
            print( CMD )
            if 'PySimpleGUIWeb' in sys.modules.keys():
                os.system( CMD ) 
                window["_OUTPUT_"].update( open( OutTxt,'r' ).read()  )
                pass
            else:
                runCommand(cmd=CMD, window=window)
            window["_IMAGE_"].update( filename=OutPng ) # same for web/html
    window.Close()

#################################################################
def runCommand(cmd, timeout=None, window=None):
    """ run shell command
    @param cmd: command to execute
    @param timeout: timeout for command execution
    @param window: the PySimpleGUI window that the output is going to (needed to do refresh on)
    @return: (return code from command, command output)
    """
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
    output = ''
    for line in p.stdout:
        line = line.decode( errors='replace' 
           if (sys.version_info) < (3, 5) else 'backslashreplace').rstrip()
        output += line
        print(line)
        window.Refresh() if window else None  # yes, a 1-line if, so shoot me
    retval = p.wait(timeout)
    return (retval, output)

#################################################################
main()
#import pdb; pdb.set_trace()
