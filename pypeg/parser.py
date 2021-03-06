from subprocess import check_output
from sys import argv
from os import chdir
from instruction import Instruction
from utils import runlpeg, charrange
from rpython.rlib.rstring import replace
from charlistelement import SingleChar, CharRange


def line_to_instruction(line):
    print line
    if "':'" in line:  # escape before split
        line = replace(line, "':'", "'#'")
        labelsplit = line.split(":")
        for i in range(len(labelsplit)):
            labelsplit[i] = replace(labelsplit[i], "'#'", "':'")
    else:
        labelsplit = line.split(":")
    label = int(labelsplit[0])
    line = labelsplit[1]
    charlist = []
    character = "\0"
    capturetype = "\0"
    goto = idx = size = behindvalue = -1
    if "->" in line:  # assuming format of "stuff -> int"
        gotosplit = line.split("->")
        goto = int(gotosplit[1])
        line = gotosplit[0]
    if "[" in line and "]" in line:
        #assuming format similar to "labelname [(stuff)(stuff)]"
        cut1 = line.find("[")
        cut2 = line.find("]") + 1
        assert cut1 >= 0
        assert cut2 >= 0
        bracketline = line[cut1:cut2]
        line = line[:cut1] + line[cut2:]
        bracketsplit = bracketline.split(")(")
        charlist = []
        for element in bracketsplit:
            element = (
                element.strip("()[]")
            )
            if "-" in element:  # describes a range of values
                sublist = []
                rangevalues = element.split("-")
                range1 = int(rangevalues[0], 16)
                range2 = int(rangevalues[1], 16)
                charlist.append(CharRange(chr(range1), chr(range2)))
            else:  # describes single value
                charlist.append(SingleChar(chr(int(element, 16))))
    if "(" in line:  # assuming format simillar to
        #"labelname (something = int) (somethingelse = int)"
        if "'('" in line:  # escape parent character as parameter before split
            line = replace(line, "'('", "'#'")
            parensplit = line.split("(")
            for i in range(len(parensplit)):
                parensplit[i] = replace(parensplit[i], "'#'", "'('")
        else:
            parensplit = line.split("(")
        line = parensplit[0]
        for element in parensplit:
            number = ""
            for x in element:
                if x.isdigit():
                    number += x
            if "idx" in element:
                idx = int(number)
            elif "size" in element:
                size = int(number)
            elif ")" in element:
                raise Exception("Unexpected bytecode parameter: " + element)

    if "\'" in line:  # assuming format of "bytecodename 'character'"
        character = line.split("'")[1]
        character = chr(int(character, 16))
    while line[-1] == " ":
        line = line[:-1]
    while line[0] == " ":
        line = line[1:]
    if " " in line:  # assuming format of "bytecodename extrainfo"
        behind_capture_split = line.split(" ")
        name = behind_capture_split[0]
        if behind_capture_split[1].isdigit():
            behindvalue = int(behind_capture_split[1])
        else:
            capturetype = behind_capture_split[1]
    else:
        name = line
    return Instruction(name, label, goto, charlist[:], idx, size,
                       character, behindvalue, capturetype)


def parse(lines):
    lines = replace(lines, "'\n'", "'###'")
    lines = lines.splitlines()
    instructionlist = []
    for line in lines:
        if line.strip():  # if line is not empty
            line = replace(line, "'###'", "'\n'")
            if line != "'":
                instruction = line_to_instruction(line)
                instructionlist.append(instruction)
    return instructionlist


def relabel(instructionlist):
    labeldict = {}
    for i in range(len(instructionlist)):
        #1st loop sets up the dictionary
        currentlabel = instructionlist[i].label
        if currentlabel in labeldict.keys():
            raise Exception("Multiple Bytecodes with Label "
                            + str(currentlabel))
        labeldict[currentlabel] = i
    for instruction in instructionlist:
        #2nd loop relabels the instructions
        currentlabel = instruction.label
        instruction.label = labeldict[currentlabel]
        if instruction.goto != -1:
            currentgoto = instruction.goto
            instruction.goto = labeldict[currentgoto]
    targets = findjumptargets(instructionlist)
    addjumptargets(instructionlist, targets)
    return instructionlist


def findjumptargets(instructionlist):
    targets = []  # list of numbers representing jumptargets by label
    for instruction in instructionlist:
        if instruction.goto != -1 and instruction.goto not in targets:
            targets.append(instruction.goto)
    return targets


def addjumptargets(instructionlist, targets):
    for instruction in instructionlist:
        if instruction.label in targets:
            instruction.isjumptarget = True


if __name__ == "__main__":
    bytecodestring = runlpeg(argv[1])
    instructionlist = parse(bytecodestring)
    instructionlist = relabel(instructionlist)
    for instruction in instructionlist:
        print(instruction)
