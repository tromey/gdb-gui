# Originally from https://github.com/wrhansen/MarkupToTextTag
# Then modified a bit to suit.
# This will be obsolete at some point in the future -- see
# https://bugzilla.gnome.org/show_bug.cgi?id=59390.

#    This package is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, Pango

import gui.pangohack

__author__ = "Wesley Hansen"
__date__ = "07/06/2012 11:29:17 PM"
'''
The markuptotexttag package contains the function `convertMarkup` that
will parse a string that is formatted with pango markup and convert
it into GtkTextTags that can be retrieved via the MarkupProps iterator.
'''

def convertMarkup(string):
    '''
    Parses the string and returns a MarkupProps instance
    '''
    attr_values = ('value', 'ink_rect', 'logical_rect', 'desc', 'color')
    # This seems like a rather lame API.
    ok, attr_list, text, accel = Pango.parse_markup( string, len(string), '\0' )
    
    props = MarkupProps()
    props.text = text
    
    val = True
    for attr in attr_list.get_iterator():
        name = attr.type
        start = attr.start_index
        end = attr.end_index
        name = Pango.AttrType(name).value_nick

        value = None
        for attr_value in attr_values:
            if hasattr( attr, attr_value ):
                value = getattr( attr, attr_value )
                break
        if name == 'font_desc':
            name = 'font'
        props.add( name, value, start, end )

    return props
        
class MarkupProps(object):
    '''
    Stores properties that contain indices and appropriate values for that property.
    Includes an iterator that generates GtkTextTags with the start and end indices to 
    apply them to
    '''
    def __init__(self):    
        '''
        properties = (    {    
                            'properties': {'foreground': 'green', 'background': 'red'}
                            'start': 0,
                            'end': 3
                        },
                        {
                            'properties': {'font': 'Lucida Sans 10'},
                            'start': 1,
                            'end':2,
                            
                        },
                    )
        '''
        self.properties = []#Sequence containing all the properties, and values, organized by like start and end indices
        self.text = ""#The raw text without any markup

    def add( self, label, value, start, end ):
        '''
        Add a property to MarkupProps. If the start and end indices are already in
        a property dictionary, then add the property:value entry into
        that property, otherwise create a new one
        '''
        for prop in self.properties:
            if prop['start'] == start and prop['end'] == end:
                prop['properties'].update({label:value})
        else:
            new_prop =     {
                            'properties': {label:value},
                            'start': start,
                            'end':end,
                        }
            self.properties.append( new_prop )
                         

    def __iter__(self):
        '''
        Yields (TextTag, start, end)
        '''
        for prop in self.properties:
            tag = Gtk.TextTag()
            tag.set_properties( **prop['properties'] )
            yield (tag, prop['start'], prop['end'])
