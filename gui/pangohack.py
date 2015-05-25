# From
# https://bug646788.bugzilla-attachments.gnome.org/attachment.cgi?id=221735

from gi.repository import Pango

#Pango.AttrList
class AttrIterator():
    def __init__ (self, attributes=[]):
        self.attributes = attributes
        self.attribute_stack = []
        self.start_index = 0
        self.end_index = 0
        if not self.next():
            self.end_index = 2**32 -1

    def __next__(self):
        return self.next()

    def __iter__(self):
        return self

    def next(self):
        if len(self.attributes) == 0 and len(self.attribute_stack) == 0:
            return False
        self.start_index = self.end_index
        self.end_index = 2**32 - 1

        to_remove = []
        for attr in self.attribute_stack:
            if attr.end_index == self.start_index:
                to_remove.append(attr)
            else:
                self.end_index = min(self.end_index, attr.end_index)

        while len(to_remove) > 0:
            attr = to_remove[0]
            self.attribute_stack.remove(to_remove[0])
            try:
                to_remove.remove(attr)
            except:
                pass

        while len(self.attributes) != 0 and \
              self.attributes[0].start_index == self.start_index:
            if self.attributes[0].end_index > self.start_index:
                self.attribute_stack.append(self.attributes[0])
                self.end_index = min(self.end_index, self.attributes[0].end_index)
            self.attributes = self.attributes[1:]
        if len(self.attributes) > 0:
            self.end_index = min(self.end_index, self.attributes[0].start_index)
        return True

    def range(self):
        return (self.start_index, self.end_index)

    #Dont create pango.fontdesc as it should. But half working.
    def get_font(self):
        tmp_list1 = self.attribute_stack
        fontdesc = Pango.FontDescription()
        for attr in self.attribute_stack:
            if attr.klass.type == Pango.ATTR_FONT_DESC:
                tmp_list1.remove(attr)
                attr.__class__ = gi.repository.Pango.AttrFontDesc
                fontdesc = attr.desc
        return (fontdesc, None, self.attribute_stack)



def get_iterator(self):
    tmplist = []
    def fil(val, data):
        tmplist.append(val)
        return False
    self.filter(fil, None)
    return AttrIterator(tmplist)


setattr(Pango.AttrList, 'get_iterator', get_iterator)
class AttrFamily(Pango.Attribute):
   pass
Pango.AttrFamily = AttrFamily

class AttrStyle(Pango.Attribute):
   pass
Pango.AttrStyle = AttrStyle

class AttrVariant(Pango.Attribute):
   pass
Pango.AttrVariant = AttrVariant

class AttrWeight(Pango.Attribute):
   pass
Pango.AttrWeight = AttrWeight

class AttrVariant(Pango.Attribute):
   pass
Pango.AttrVariant = AttrVariant

class AttrStretch(Pango.Attribute):
   pass
Pango.AttrStretch = AttrStretch


# And to access values 
#  pango_type_table = {
#         pango.ATTR_SIZE: gi.repository.Pango.AttrInt,
#         pango.ATTR_WEIGHT: gi.repository.Pango.AttrInt,
#         pango.ATTR_UNDERLINE: gi.repository.Pango.AttrInt,
#         pango.ATTR_STRETCH: gi.repository.Pango.AttrInt,
#         pango.ATTR_VARIANT: gi.repository.Pango.AttrInt,
#         pango.ATTR_STYLE: gi.repository.Pango.AttrInt,
#         pango.ATTR_SCALE: gi.repository.Pango.AttrFloat,
#         pango.ATTR_FAMILY: gi.repository.Pango.AttrString,
#         pango.ATTR_FONT_DESC: gi.repository.Pango.AttrFontDesc,
#         pango.ATTR_STRIKETHROUGH: gi.repository.Pango.AttrInt,
#         pango.ATTR_BACKGROUND: gi.repository.Pango.AttrColor,
#         pango.ATTR_FOREGROUND: gi.repository.Pango.AttrColor,
#         pango.ATTR_RISE: gi.repository.Pango.AttrInt}

# def make_with_value(a):
#     type_ = a.klass.type
#     klass = a.klass
#     start_index = a.start_index
#     end_index = a.end_index
#     #Nasty workaround, but then python object gets value field.
#     a.__class__ = self.pango_type_table[type_]
#     a.type = type_
#     a.start_index = start_index
#     a.end_index = end_index
#     a.klass = klass
#     return a
