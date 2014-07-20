#! /usr/bin/env python
'''
Generates Inkscape SVG file containing box components needed to create several different
types of laser cut tabbed boxes.

Derived from original version authored by elliot white - elliot@twot.eu

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
__version__ = "0.1" ### please report bugs at https://github.com/zackurtz/box-maker/issues ###

import sys
import inkex, simplestyle, gettext

_ = gettext.gettext

def drawS(XYstring):         # Draw lines from a list
  name='part'
  style = { 'stroke': '#000000', 'fill': 'none' }
  drw = { 'style':simplestyle.formatStyle(style), inkex.addNS('label','inkscape'):name, 'd':XYstring}
  inkex.etree.SubElement(parent, inkex.addNS('path','svg'), drw )
  return


  
class BoxMaker(inkex.Effect):
  def __init__(self):
      # Call the base class constructor.
      inkex.Effect.__init__(self)
      # Define options
      self.OptionParser.add_option('--unit',action='store',type='string',
        dest='unit',default='mm',help='Measure Units')
      self.OptionParser.add_option('--inside',action='store',type='int',
        dest='inside',default=0,help='Int/Ext Dimension')
      self.OptionParser.add_option('--length',action='store',type='float',
        dest='length',default=100,help='Length of Box')
      self.OptionParser.add_option('--width',action='store',type='float',
        dest='width',default=100,help='Width of Box')
      self.OptionParser.add_option('--depth',action='store',type='float',
        dest='height',default=100,help='Height of Box')
      self.OptionParser.add_option('--tab',action='store',type='float',
        dest='tab',default=25,help='Nominal Tab Width')
      self.OptionParser.add_option('--equal',action='store',type='int',
        dest='equal',default=0,help='Equal/Prop Tabs')
      self.OptionParser.add_option('--thickness',action='store',type='float',
        dest='thickness',default=10,help='Thickness of Material')
      self.OptionParser.add_option('--kerf',action='store',type='float',
        dest='kerf',default=0.5,help='Kerf (width) of cut')
      self.OptionParser.add_option('--clearance',action='store',type='float',
        dest='clearance',default=0.01,help='Clearance of joints')
      self.OptionParser.add_option('--style',action='store',type='int',
        dest='style',default=25,help='Layout/Style')
      self.OptionParser.add_option('--spacing',action='store',type='float',
        dest='spacing',default=25,help='Part Spacing')

  def tabbed_side(self, (rx,ry), (sox,soy), (eox,eoy), tabVec, length, (dirx,diry), isTab):
    #       root    startOffset endOffset tabVec  length  direction    isTab
    num_divisions = int(length/nomTab)  # divisions

    if num_divisions % 2 == 0: 
      num_divisions -= 1   # make divs odd

    num_divisions = float(num_divisions)
    tabs = (num_divisions-1)/2          # tabs for side
    
    if equalTabs:
      gapWidth = tabWidth = length/num_divisions
    else:
      tabWidth = nomTab
      gapWidth = (length-tabs*nomTab)/(num_divisions-tabs)
      
    # kerf correction
    if isTab:                 
      gapWidth -= correction
      tabWidth += correction
      first = correction/2
    else:
      gapWidth += correction
      tabWidth -= correction
      first =- correction/2
      
    s = [] 
    firstVec = 0 
    secondVec = tabVec

    # used to select operation on x or y
    dirxN = 0 if dirx else 1 
    diryN = 0 if diry else 1
    (Vx, Vy) = (rx+sox*self.thickness,ry+soy*self.thickness)
    s = 'M ' + str(Vx) + ',' + str(Vy) + ' '

    if dirxN: 
      Vy = ry # set correct line start
    if diryN:
      Vx = rx

    # generate line as tab or hole using:
    #   last co-ord:Vx,Vy ; tab dir:tabVec  ; direction:dirx,diry ; thickness:thickness
    #   divisions:num_divisions ; gap width:gapWidth ; tab width:tabWidth

    for n in range(1, int(num_divisions)):
      if n % 2 == 1:
        Vx = Vx + dirx*gapWidth + dirxN*firstVec + first*dirx
        Vy = Vy + diry*gapWidth + diryN*firstVec + first*diry
        s += 'L ' + str(Vx) + ',' + str(Vy) + ' '
        Vx = Vx + dirxN*secondVec
        Vy = Vy + diryN*secondVec
        s += 'L ' + str(Vx) + ',' + str(Vy) + ' '
      else:
        Vx = Vx+dirx*tabWidth+dirxN*firstVec
        Vy = Vy+diry*tabWidth+diryN*firstVec
        s += 'L ' + str(Vx) + ',' + str(Vy) + ' '
        Vx = Vx + dirxN*secondVec
        Vy = Vy + diryN*secondVec
        s += 'L ' + str(Vx) + ',' + str(Vy) + ' '
      (secondVec,firstVec) = (-secondVec,-firstVec) # swap tab direction
      first = 0
    s += 'L ' + str(rx+eox*self.thickness+dirx*length) + ',' + str(ry+eoy*self.thickness+diry*length) + ' '
    return s

  def flat_side(self, root, start_offset, end_offset, direction, length):
    current_x = root[0] + start_offset[0]*self.thickness
    current_y = root[1] + start_offset[1]*self.thickness
    draw_cmd = 'M' + str(current_x) + ',' + str(current_y) + ' '
    draw_cmd += 'L ' + str(root[0] + end_offset[0]*self.thickness+direction[0]*length) + ',' 
                     + str(root[1] + end_offset[1]*self.thickness+direction[1]*length) + ' '

    return draw_cmd


  def draw_pieces(self, pieces, thickness, spacing):
    for piece in pieces: # generate and draw each piece of the box
      (xs,xx,xy,xz) = piece[0]
      (ys,yx,yy,yz) = piece[1]
      x = xs*spacing + xx*self.x_dim + xy*self.y_dim + xz*self.z_dim  # root x co-ord for piece
      y = ys*spacing + yx*self.x_dim  +yy*self.y_dim + yz*self.z_dim  # root y co-ord for piece
      dx = piece[2]
      dy = piece[3]
      tabs = piece[4]
      
      # extract tab status for each side
      a = tabs>>3 & 1
      b= tabs>>2 & 1
      c= tabs>>1 & 1
      d= tabs & 1 
      # generate and draw the sides of each piece
      drawS(self.tabbed_side((x,y), (d,a), (-b,a), -thickness if a else thickness, dx, (1,0), a))          # side a
      drawS(self.tabbed_side((x+dx,y), (-b,a), (-b,-c), thickness if b else -thickness, dy, (0,1), b))     # side b
      drawS(self.tabbed_side((x+dx,y+dy), (-b,-c), (d,-c), thickness if c else -thickness, dx, (-1,0), c)) # side c
      drawS(self.tabbed_side((x,y+dy), (d,-c), (d,a), -thickness if d else thickness, dy, (0,-1), d))      # side d


  def effect(self):
    global parent, nomTab, equalTabs, correction
    
    # Get access to main SVG document element and get its dimensions.
    svg = self.document.getroot()
    
    # Get the attibutes:
    widthDoc  = inkex.unittouu(svg.get('width'))
    heightDoc = inkex.unittouu(svg.get('height'))

    # Create a new layer.
    layer = inkex.etree.SubElement(svg, 'g')
    layer.set(inkex.addNS('label', 'inkscape'), 'newlayer')
    layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
    
    parent = self.current_layer
    
    # Get script's option values.
    unit = self.options.unit
    inside = self.options.inside
    self.x_dim = inkex.unittouu( str(self.options.length) + unit )
    self.y_dim = inkex.unittouu( str(self.options.width) + unit )
    self.z_dim = inkex.unittouu( str(self.options.height) + unit )

    thickness = inkex.unittouu( str(self.options.thickness) + unit )
    nomTab = inkex.unittouu( str(self.options.tab) + unit )
    equalTabs = self.options.equal
    kerf = inkex.unittouu( str(self.options.kerf) + unit )
    clearance = inkex.unittouu( str(self.options.clearance) + unit )
    layout = self.options.style
    spacing = inkex.unittouu( str(self.options.spacing) + unit )
    
    self.thickness = thickness

    if inside: 
      # convert inside dimension to outside dimension
      self.x_dim += thickness*2
      self.y_dim += thickness*2
      self.z_dim += thickness*2

    correction = kerf - clearance

    # check input values mainly to avoid python errors
    # TODO restrict values to *correct* solutions
    error = 0
    
    X = self.x_dim
    Y = self.y_dim
    Z = self.z_dim

    if min(X,Y,Z) == 0:
      inkex.errormsg(_('Error: Dimensions must be non zero'))
      error = 1
    if max(X,Y,Z) > max(widthDoc,heightDoc)*10: # crude test
      inkex.errormsg(_('Error: Dimensions Too Large'))
      error = 1
    if min(X,Y,Z) < 3*nomTab:
      inkex.errormsg(_('Error: Tab size too large'))
      error = 1
    if nomTab < thickness:
      inkex.errormsg(_('Error: Tab size too small'))
      error = 1	  
    if thickness == 0:
      inkex.errormsg(_('Error: Thickness is zero'))
      error = 1	  
    if thickness > min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Material too thick'))
      error = 1	  
    if correction > min(X,Y,Z)/3: # crude test
      inkex.errormsg(_('Error: Kerf/Clearence too large'))
      error = 1	  
    if spacing > max(X,Y,Z)*10: # crude test
      inkex.errormsg(_('Error: Spacing too large'))
      error = 1	  
    if spacing < kerf:
      inkex.errormsg(_('Error: Spacing too small'))
      error = 1	  

    if error: exit()
   
    # layout format:(rootx),(rooty),Xlength,Ylength,tabInfo
    # root= (spacing,X,Y,Z) * values in tuple
    # tabInfo= <abcd> 0=holes 1=tabs
    if layout==1: # Diagramatic Layout
      pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1010], [(1,0,0,0),(2,0,0,1),Z,Y,0b1111],
              [(2,0,0,1),(2,0,0,1),X,Y,0b0000], [(3,1,0,1),(2,0,0,1),Z,Y,0b1111],
              [(4,1,0,2),(2,0,0,1),X,Y,0b0000], [(2,0,0,1),(1,0,0,0),X,Z,0b1010]]
    elif layout==2: # 3 Piece Layout
      pieces=[[(2,0,0,1),(2,0,1,0),X,Z,0b1010], [(1,0,0,0),(1,0,0,0),Z,Y,0b1111],
              [(2,0,0,1),(1,0,0,0),X,Y,0b0000]]
    elif layout==3: # Inline(compact) Layout
      pieces=[[(1,0,0,0),(1,0,0,0),X,Y,0b0000], [(2,1,0,0),(1,0,0,0),X,Y,0b0000],
              [(3,2,0,0),(1,0,0,0),Z,Y,0b0101], [(4,2,0,1),(1,0,0,0),Z,Y,0b0101],
              [(5,2,0,2),(1,0,0,0),X,Z,0b1111], [(6,3,0,2),(1,0,0,0),X,Z,0b1111]]
    elif layout==4: # Diagramatic Layout with Alternate Tab Arrangement
      pieces=[[(2,0,0,1),(3,0,1,1),X,Z,0b1001], [(1,0,0,0),(2,0,0,1),Z,Y,0b1100],
              [(2,0,0,1),(2,0,0,1),X,Y,0b1100], [(3,1,0,1),(2,0,0,1),Z,Y,0b0110],
              [(4,1,0,2),(2,0,0,1),X,Y,0b0110], [(2,0,0,1),(1,0,0,0),X,Z,0b1100]]

    self.draw_pieces(pieces, thickness, spacing)





# Create effect instance and apply it.
effect = BoxMaker()
effect.affect()
