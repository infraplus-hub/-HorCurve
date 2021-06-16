#
#
#
#
#
import subprocess
import sys,os
from pathlib import Path
import PySimpleGUI as sg
#import PySimpleGUIWeb as sg

TITLE = 'KML file of sampling points and points to be generated : '
def main():
    sg.theme('LightBrown3')
    layout = [ [sg.Image( filename='./CE_InfraMgmt.png') ],
               [sg.Text( TITLE )] ,
               [   sg.Input( default_text='CACHE/TestCurve.kml', 
                       key='_IN_' ) , sg.FileBrowse(),
                   sg.Button('Run'), sg.Button('Exit') ] , 
               [   sg.Input( default_text='10', key='_NUM_PNT_' ) ] , 
               [sg.Output(key='_OUTPUT_', size=(80,25), 
                    font=('courier', 12) )  ],
               [sg.Image( size=(1000,1000), key="_IMAGE_")],
             ]

    window = sg.Window('Estimate Horizontal Curve from  Sampling Alignment',  
                        layout)

    while True:             # Event Loop
        event, values = window.Read()
        # print(event, values)
        if event in (None, 'Exit'):
            break
        elif event == 'Run':
            KML_FILE = Path( values['_IN_'] )
            #import pdb; pdb.set_trace()
            NUM_PNT = int( values['_NUM_PNT_'] )
            KML_STEM = KML_FILE.parent.joinpath( KML_FILE.stem )
            OutPng = str(KML_STEM) + '_PLOT.png'
            OutTxt = str(KML_STEM) + '_REPORT.txt'
            CMD = 'python3 EstCircCurve.py {} {}'.format( KML_FILE,NUM_PNT )
            if 'PySimpleGUIWeb' in sys.modules.keys():
                os.system( CMD ) 
                window["_OUTPUT_"].update( open( OutTxt,'r' ).read()  )
            else:
                runCommand(cmd=CMD, window=window)
            if os.path.exists( OutPng ):
#                import pdb; pdb.set_trace()
                window["_IMAGE_"].update( filename=OutPng )
    window.Close()


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
