from utils import charrange
from charlistelement import SingleChar, CharRange
from rpython.rlib import jit


class Instruction(object):

    _immutable_fields_ = ["name", "character",
                          "goto", "charlist[*]", "capturetype"]
    #indicates to jit that these variables are immutable. performance!

    def __init__(self, name, label,
                 goto=-1, charlist=[], idx=-1,
                 size=-1, character="\0",
                 behindvalue=-1, capturetype="\0"):
        self.name = name
        self.label = label
        self.goto = goto
        self.charlist = charlist
        self.idx = idx
        self.size = size
        self.character = character
        self.behindvalue = behindvalue
        self.capturetype = capturetype

    @jit.unroll_safe
    def incharlist(self, character):
        #for char in self.charlist:
        #    if char == character:
        #        return True
        #return False
        result = False
        #for char in self.charlist:
         #   result = result | (char == character)
        for element in self.charlist:
            result = result | element.is_match(character)
        return result

    def __str__(self):
        ret = "Instruction (name:"+self.name+", label:"+str(self.label)
        if self.charlist != []:
            #templist = []  # code to make the list look more pretty.
            #instead of outputting [a,b,c,...,z] it should output [a-z]
            #for sublist in self.charlist:
             #   if sublist == charrange("a", "z"):
              #      templist.append(["a-z"])
               # elif sublist == charrange("A", "Z"):
               #     templist.append(["A-Z"])
               # elif sublist == charrange("0", "9"):
                #    templist.append(["0-9"])
                #else:
                 #   templist.append(sublist)
            #ret += ", charlist:"+str(templist)
            ret += "charlist: "+str(self.charlist)
        if self.goto != -1:
            ret += ", goto:"+str(self.goto)
        if self.idx != -1:
            ret += ", idx:"+str(self.idx)
        if self.size != -1:
            ret += ", size:"+str(self.size)
        if self.character != "\0":
            ret += ", character:"+str(self.character)
        if self.behindvalue != -1:
            ret += ", behindvalue:"+str(self.behindvalue)
        if self.capturetype != "\0":
            ret += ", capturetype:"+str(self.capturetype)
        return ret+")"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return (self.name == other.name and self.label == other.label
                and self.goto == other.goto and self.charlist == other.charlist
                and self.idx == other.idx and self.size == other.size
                and self.character == other.character)

    def __ne__(self, other):
        return not __eq__(self, other)
