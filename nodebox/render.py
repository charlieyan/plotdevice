#!/usr/bin/env python
# encoding: utf-8
"""
render.py

Run nodebox scripts from the command line
"""

import sys
import os
import argparse
import xmlrpclib
import socket
import json
from time import sleep

PORT = 9000

def connect(retry=12, delay=0):
  if delay:
    sleep(delay)
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  try:
    sock.connect(("localhost", PORT))
  except socket.error, e:
    if not retry:
      return None
    return connect(retry-1, delay=.2)
  return sock

def exec_command(opts):  
  sock = connect(0)
  if not sock:
    os.system('open -a "%s" "%s"'%(app_name(), opts.file))
    sock = connect()
  if not sock:
    print "Couldn't connect to the NodeBox application"
    sys.exit(1)

  try:
    sock.sendall(json.dumps(vars(opts)) + "\n")
    try:
      while read_and_echo(sock): pass
    except KeyboardInterrupt:
      sock.sendall('STOP\n')
      print "\n",
      while read_and_echo(sock): pass
  finally:
    sock.close()

def app_name():
  parent = os.path.dirname(__file__)
  if os.path.islink(__file__):
    parent = os.path.dirname(os.path.realpath(__file__))
  if parent.endswith('NodeBox.app/Contents/SharedSupport/bin'):
    return os.path.abspath('%s/../../..'%parent)
  return 'NodeBox.app'

def read_and_echo(sock):
  response = sock.recv(80)
  if response:
    print response,
  return response

def main():
  parser = argparse.ArgumentParser(description='Run python scripts in NodeBox.app', add_help=False)
  o = parser.add_argument_group("Options", None)
  o.add_argument('-h','--help', dest='helpscreen', action='store_const', const=True, default=False, help='show this help message and exit')
  o.add_argument('-f', dest='fullscreen', action='store_const', const=True, default=False, help='run full-screen')
  o.add_argument('-b', dest='activate', action='store_const', const=False, default=True, help='run NodeBox in the background')
  o.add_argument('--virtualenv', metavar='PATH', help='path to virtualenv whose libraries you want to use (this should point to the top-level virtualenv directory; a folder containing a lib/python2.7/site-packages subdirectory)')
  o.add_argument('--export', metavar='FILE', help='a destination filename ending in pdf, eps, png, tiff, jpg, gif, or mov')
  o.add_argument('--frames', metavar='N or M-N', help='number of frames to render or a range specifying the first and last frames (default "1-")')
  o.add_argument('--fps', metavar='N', default=30, help='frames per second in exported video (default 30)')
  o.add_argument('--loop', metavar='N', default=0, nargs='?', const=-1, help='number of times to loop an exported animated gif (omit N to loop forever)')
  o.add_argument('--live', action='store_const', const=True, help='re-render graphics each time the file is saved')
  o.add_argument('--args', nargs='*', default=[], metavar=('a','b'), help='remainder of command line will be passed to the script as sys.argv')
  i = parser.add_argument_group("NodeBox Script File", None)
  i.add_argument('file', help='the python script to be rendered')
  parser.print_help()
  # print dir(parser)
  sys.exit(0)  
  opts = parser.parse_args()
  
  if opts.virtualenv:
    libdir = '%s/lib/python2.7/site-packages'%opts.virtualenv
    if os.path.exists(libdir):
      opts.virtualenv = os.path.abspath(libdir)
    else:
      parser.exit(1, "bad argument [--virtualenv]\nvirtualenv site-packages dir not found: %s\n"%libdir)

  if opts.file:
    opts.file = os.path.abspath(opts.file)
    if not os.path.exists(opts.file):
      parser.exit(1, "file not found: %s\n"%opts.file)

  if opts.frames:
    try:
      frames = [int(f) if f else None for f in opts.frames.split('-')]
    except ValueError:
      parser.exit(1, 'bad argument [--frame]\nmust be a single integer ("42") or a hyphen-separated range ("33-66").\ncouldn\'t make sense of "%s"\n'%opts.frames)

    if len(frames) == 1:
      opts.first, opts.last = (1, frames[0])
    elif len(frames) == 2:
      if frames[1] is not None and frames[1]<frames[0]:
        parser.exit(1, "bad argument [--frame]\nfinal-frame number is less than first-frame\n")
      opts.first, opts.last = frames
      del opts.frames
  else:
    opts.first, opts.last = (1, None)

  if opts.fps:
    opts.fps = int(opts.fps)

  if opts.loop:
    opts.loop = int(opts.loop)

  if opts.export:
    basename, ext = opts.export.rsplit('.',1)
    if ext.lower() not in ('pdf', 'eps', 'png', 'tiff', 'jpg', 'gif', 'mov'):
      parser.exit(1, 'bad argument [--export]\nthe output filename must end with a supported format:\npdf, eps, png, tiff, jpg, gif, or mov\n')
    if '/' in opts.export:
      export_dir = os.path.dirname(opts.export)
      if not os.path.exists(export_dir):
        parser.exit(1,'export directory not found: %s\n'%os.path.abspath(export_dir))
    opts.export = os.path.abspath(opts.export)

  exec_command(opts)

if __name__ == "__main__":
  main()