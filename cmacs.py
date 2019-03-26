#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2019 Nickolay Ilyushin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Pragma syntax
# All pragmas have form of '#pragma cmacs PRAGMA ARGUMENTS...' statement
# They are consumed by cmacs to generate corresponding header and implementation files

# Current pragmas
# - hppstart/includes: puts code in the block right after #pragma once, before namespace (if any)
# - hppbody/hpp: puts code in the block inside of header file body, inside of namespace (if any)
# - hppend: puts code in the block at the end of header file, after namespace (if any)
#
# - cppstart: puts code in the block right after header #include, before using namespace (if any)
# - cppbody/cpp: puts code in the block inside of implementation file body, inside of namespace (if any)
# - cppend: puts code in the block at the end of implementation file
#
# - namespace NS: sets namespace for the given file to NS
#
# - class: allows defining classnames in methods
# - method: method declaration is gone to the header file, implementation - to implementation file
# - main: same as method, but always generates static methods and also generates a global main function
#         which will call the method
# - constructor: allows defining class constructors
# - destructor: allows defining class destructors

import argparse
import os.path
import shlex
import re

# Args:
# #pragma cmacs namespace Foo
#                         0

SYM_STACK = []
CLASS_STACK = []

class CMacsPragma:
  def __init__(self, file):
    self.file = file
    pass

  def execute(self):
    pass
  
  def readblock(self):
    line = self.file.next()
    data = []
    if line[0] != '{':
      raise RuntimeError('Expected block, found something else')
    line = line[1:len(line)]
    while line != None:
      idx = 0
      while idx < len(line):
        c = line[idx]
        if c == '}':
          left = '' if idx == 0 else line[0:idx-1]
          right = '' if idx >= len(line) - 1 else line[idx+1:len(line)]
          data.append(left.strip() + '\n')
          self.file.insert(right.strip() + '\n')
          line = None
          break
        idx += 1
      if line != None:
        data.append(line.strip() + '\n')
        line = self.file.next()
    return data

  def readclass(self):
    line = self.file.peek_next().strip()
    c = re.compile(r'^class (.+?)(?:\s+{?|$)')
    m = c.match(line)
    self.classname = m.group(1)
    SYM_STACK.append(self)
    CLASS_STACK.append(self)
    return self

  def readmethod(self):
    mode_readtypews = 0
    mode_readtype = 1
    mode_readnamews = 2
    mode_readname = 3
    mode_readargslparenws = 4
    mode_readargslparen = 5
    mode_readargs = 6
    mode_readbodylbracews = 7
    mode_readbody = 8
    mode = mode_readtypews
    mtype = ''
    mname = ''
    margs = ''
    mbody = ''
    mvirtual = False
    mstatic = False
    SYM_STACK.append(self)
    try:
      line = self.file.next()
      while line != None:
        idx = 0
        while idx < len(line):
          nohandle = False
          c = line[idx]
          if mode == mode_readtypews:
            if not (c == ' ' or c == '\t' or c == '\r' or c == '\n'):
              mode = mode_readtype
              continue
          elif mode == mode_readnamews:
            if not (c == ' ' or c == '\t' or c == '\r' or c == '\n'):
              mode = mode_readname
              continue
          elif mode == mode_readargslparenws:
            if not (c == ' ' or c == '\t' or c == '\r' or c == '\n'):
              mode = mode_readargslparen
              continue
          elif mode == mode_readbodylbracews:
            if not (c == ' ' or c == '\t' or c == '\r' or c == '\n'):
              if c == '{':
                mode = mode_readbody
              else:
                raise RuntimeError('Expected whitespace or {, got ' + c)
          elif mode == mode_readtype:
            if (c == ' ' or c == '\t' or c == '\r' or c == '\n'):
              if type(SYM_STACK[len(SYM_STACK)-1]) is type(self):
                if mtype == 'virtual':
                  mvirtual = True
                  mtype = ''
                  mode = mode_readtypews
                elif mtype == 'static':
                  mstatic = True
                  mtype = ''
                  mode = mode_readtypews
                else:
                  mode = mode_readnamews
            else:
              mtype += c
          elif mode == mode_readname:
            if (c == ' ' or c == '\t' or c == '\r' or c == '\n'):
              if type(SYM_STACK[len(SYM_STACK)-1]) is type(self):
                mode = mode_readargslparenws
            elif c == '(':
              nohandle = True
              if type(SYM_STACK[len(SYM_STACK)-1]) is type(self):
                mode = mode_readargs
            else:
              mname += c
          elif mode == mode_readargslparen:
            nohandle = True
            if c == '(':
              mode = mode_readargs
            else:
              raise RuntimeError('Expected (, got ' + c)
          elif mode == mode_readargs:
            if c == ')' and type(SYM_STACK[len(SYM_STACK)-1]) is type(self):
              nohandle = True
              mode = mode_readbodylbracews
            else:
              margs += c
          elif mode == mode_readbody:
            if c == '}' and type(SYM_STACK[len(SYM_STACK)-2]) is type(self):
              SYM_STACK.pop()
              nohandle = True
              line = None
              break
            else:
              mbody += c
          if not nohandle: self.file.handle_char(c)
          idx += 1
        if line != None:
          line = self.file.next()
    finally:
      if not (True in [type(e) is type(self) for e in SYM_STACK]):
        raise RuntimeError('Invalid stack: no self')
      while type(SYM_STACK[len(SYM_STACK)-1]) is not type(self):
        SYM_STACK.pop()
      SYM_STACK.pop()
    return {
      'mtype': mtype,
      'mname': mname,
      'margs': margs,
      'mbody': mbody,
      'mvirtual': mvirtual,
      'mstatic': mstatic,
    }

pragmas = {}


class CMacsNOPPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)

pragmas['nop'] = lambda file, args: CMacsNOPPragma(file)


class CMacsHPPStartPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)
  
  def execute(self):
    self.file.hppstart = self.readblock() + self.file.hppstart

pragmas['hppstart'] = lambda file, args: CMacsHPPStartPragma(file)
pragmas['includes'] = pragmas['hppstart']


class CMacsHPPPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)
  
  def execute(self):
    self.file.hppbody = self.readblock() + self.file.hppbody

pragmas['hppbody'] = lambda file, args: CMacsHPPPragma(file)
pragmas['hpp'] = pragmas['hppbody']


class CMacsHPPEndPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)
  
  def execute(self):
    self.file.hppend = self.readblock() + self.file.hppend

pragmas['hppend'] = lambda file, args: CMacsHPPEndPragma(file)


class CMacsCPPStartPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)
  
  def execute(self):
    self.file.cppstart = self.readblock() + self.file.cppstart

pragmas['cppstart'] = lambda file, args: CMacsCPPStartPragma(file)


class CMacsCPPPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)
  
  def execute(self):
    self.file.cppbody = self.readblock() + self.file.cppbody

pragmas['cppbody'] = lambda file, args: CMacsCPPPragma(file)
pragmas['cpp'] = pragmas['cppbody']


class CMacsCPPEndPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)
  
  def execute(self):
    self.file.cppend = self.readblock() + self.file.cppend

pragmas['cppend'] = lambda file, args: CMacsCPPEndPragma(file)

class CMacsNamespacePragma(CMacsPragma):
  def __init__(self, file, namespace):
    super().__init__(file)
    self.namespace = namespace
  
  def execute(self):
    self.file.namespace = self.namespace

pragmas['namespace'] = lambda file, args: CMacsNamespacePragma(file, args[0])


class CMacsClassPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)

  def execute(self):
    self.readclass()

pragmas['class'] = lambda file, args: CMacsClassPragma(file)


class CMacsMethodPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)
  
  def execute(self):
    method = self.readmethod()
    classes = '::'.join(c.classname for c in CLASS_STACK)
    v = 'virtual ' if method['mvirtual'] else ''
    s = 'static ' if method['mstatic'] else ''
    self.file.hppbody.append(v + s + method['mtype'] + ' ' + method['mname'] + ' (' + method['margs'] + ');\n')
    self.file.cppbody.append(method['mtype'] + ' ' + classes + '::' + method['mname'] + ' (' + method['margs'] + ') {')
    self.file.cppbody.append(method['mbody'])
    self.file.cppbody.append('}\n')

pragmas['method'] = lambda file, args: CMacsMethodPragma(file)


class CMacsMainPragma(CMacsPragma):
  def __init__(self, file):
    super().__init__(file)

  def execute(self):
    method = self.readmethod()
    classes = '::'.join(c.classname for c in CLASS_STACK)
    self.file.hppbody.append('static ' + method['mtype'] + ' ' + method['mname'] + ' (' + method['margs'] + ');\n')
    self.file.cppbody.append(method['mtype'] + ' ' + classes + '::' + method['mname'] + ' (' + method['margs'] + ') {')
    self.file.cppbody.append(method['mbody'])
    self.file.cppbody.append('}\n')
    self.file.cppend.append('int ::main(int argc, char** argv) { return ::' + classes + '::' + method['mname'] + '(argc, argv); }')

pragmas['main'] = lambda file, args: CMacsMainPragma(file)


class CMacsFile:
  def __init__(self, path):
    self.path = path
    self.file = open(path, 'r')
    self.hpp = open(path + '.hpp', 'w')
    self.cpp = open(path + '.cpp', 'w')
    self.lines = self.file.readlines()
    self.line = 0
    self.namespace = None
    self.hppstart = []
    self.hppbody = []
    self.hppend = []
    self.cppstart = []
    self.cppbody = []
    self.cppend = []

  def close(self):
    self.hpp.write('#pragma once\n')
    self.hpp.writelines(self.hppstart)
    if self.namespace != None:
      self.hpp.write('namespace ' + self.namespace + ' {\n')
    self.hpp.writelines(self.hppbody)
    if self.namespace != None:
      self.hpp.write('}\n')
    self.hpp.writelines(self.hppend)
    self.cpp.write('#include "' + os.path.basename(self.path + '.hpp') + '"\n')
    self.cpp.writelines(self.cppstart)
    if self.namespace != None:
      self.cpp.write('using namespace ' + self.namespace + ';\n')
    self.cpp.writelines(self.cppbody)
    self.cpp.writelines(self.cppend)
    self.file.close()

  def current(self):
    if self.line >= len(self.lines):
      return None
    else:
      return self.lines[self.line]

  def next(self):
    if self.line >= len(self.lines):
      return None
    else:
      l = self.lines[self.line]
      self.line += 1
      return l

  def peek_next(self):
    if self.line >= len(self.lines):
      return None
    else:
      return self.lines[self.line]
  
  def insert(self, data):
    self.lines.insert(self.line+1, data)

  def process(self):
    line = self.next()
    while line != None:
      line = line.strip()
      self.process_line(line)
      line = self.next()
    if len(SYM_STACK) != 0:
      raise RuntimeError("Non-empty stack: " + str(SYM_STACK))

  def handle_char(self, c):
    if c == '{':
      SYM_STACK.append('}')
    elif c == '(':
      SYM_STACK.append(')')
    elif c == '[':
      SYM_STACK.append(']')
    elif c == '}':
      if SYM_STACK[len(SYM_STACK)-1] != '}':
        raise RuntimeError('Want } following a class, but got ' + str(SYM_STACK[len(SYM_STACK)-1]))  
      SYM_STACK.pop()
      if type(SYM_STACK[len(SYM_STACK)-1]) is CMacsClassPragma:
        SYM_STACK.pop()
    elif c == ')' or c == ']':
      if SYM_STACK[len(SYM_STACK)-1] != c:
        raise RuntimeError('Expected ' + SYM_STACK[len(SYM_STACK)-1] + ', got ' + c)
      else:
        SYM_STACK.pop() 

  def process_line(self, line):
    pragma = '#pragma cmacs'
    if line.startswith(pragma):
      self.process_pragma(line[len(pragma):len(line)].strip())
    elif len(line) > 0:
      for c in line:
        self.handle_char(c)
      self.hppbody.append(line + '\n')

  def process_pragma(self, pragma):
    args = shlex.split(pragma, True, True)
    p = args[0]
    args = args[1:len(args)]
    self.process_args(p, args)

  def process_args(self, pragma, args):
    if pragma in pragmas:
      pragmas[pragma](self, args).execute()
    else:
      print('invalid pragma: ' + pragma + ' ' + str(args))


parser = argparse.ArgumentParser(description='C++ code preprocessor')
parser.add_argument('file', metavar='FILE', type=str, help='input file')


args = parser.parse_args()


if not os.path.exists(args.file) and not os.path.isfile(args.file):
  raise RuntimeError("Invalid file")


f = CMacsFile(args.file)
f.process()
f.close()