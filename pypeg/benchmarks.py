
from time import time
from subprocess import check_output, CalledProcessError
from json import dumps
from os import chdir, listdir, getcwd
from collections import OrderedDict


#benchmarks all pypeg executables
#(files in path executable_path that start with pypeg_)
#also compares against lpeg
#uses pairs of patterns/inputs
#(files in path pattern_input_path that share a prefix
#and end with "pattern" and "input")
#writes result to file specified in output constant
executable_path = "/home/sktroost/PyPeg/pypeg/"
pattern_input_path = "/home/sktroost/PyPeg/pypeg/examples/"
lpeg_path = "/home/sktroost/PyPeg/pypeg/lpeg/"
repetitions = 100
output = "/home/sktroost/PyPeg/pypeg/benchmarks.txt"
blacklisted_executables = ["pypeg_180319_nochoicepointopt"]  # broken
blacklisted_patterns = ["verylongjson"]

lua_blacklist = ["5_mb_jsonpattern", "500_kb_jsonpattern",
                 "100_kb_jsonpattern", "80_mb_jsonpattern"]
#^they don't run on LUA and waste time trying


class TimeStamp():

    def __init__(self, filename, delta, patternname, inputname):
        self.filename = filename
        self.patternname = patternname
        self.inputname = inputname
        self.delta = delta


def get_executables():  # gets filenames of executables
    filelist = listdir(executable_path)
    ret = []
    for file in filelist:
        if file[:6] == "pypeg_":
            ret.append(file)
    return ret


def get_patterninputpairs():
    filelist = listdir(pattern_input_path)
    ret = []
    for file in filelist:
        if file[-5:] == "input":
            if file[:-5] + "pattern" in filelist:
                if file[:-5] not in blacklisted_patterns:
                    ret.append((file[:-5]+"pattern", file))
    return ret


def benchmark_exe(exe, pattern, input):
    print("Running "+exe+" on "+pattern)
    starttime = time()
    check_output([executable_path + exe,
                 pattern_input_path + pattern,
                 pattern_input_path + input])
    endtime = time()
    delta = endtime-starttime
    return TimeStamp(exe, delta, pattern, input)


def benchmark_all_exes():
    exes = get_executables()
    patterninputs = get_patterninputpairs()
    ret = []
    for exe in exes:
        if exe not in blacklisted_executables:
            for pattern, input in patterninputs:
                cwd = getcwd()
                try:
                    ret.append(benchmark_exe(exe, pattern, input))
                except OSError:
                    print(exe + " not executed due to an error.")
                chdir(cwd)
    return ret


def benchmark_shellscript(scriptname, inputname):
    print("Running "+scriptname+" on "+inputname)
    lastcwd = getcwd()
    chdir(executable_path)
    start = time()
    check_output([scriptname, "./examples/"+inputname])
    delta = time() - start
    chdir(lastcwd)
    return TimeStamp(scriptname, delta, scriptname, inputname)


def benchmark_lua(patternname, inputname):
    lastcwd = getcwd()
    chdir(pattern_input_path)
    pattern = open(patternname, "r").read().strip()
    input = ""
    for line in open(inputname, "r").readlines():
        input += line
    chdir(lastcwd)
    #input = input.replace("\n", "")
    #input = input.replace('"', "")  # TODO: better string escaping
    #input = input.replace('\\', "\\\\")
    #input = input.replace('"','\"')
    #input = input.replace("\n","")
    luacontent = ('local lpeg = require("lpeg"); lpeg.match('
                  + pattern + ',[====[' + input + ']====])')
    chdir(lpeg_path)
    luafile = open("temp.lua", "w")
    luafile.write(luacontent)
    luafile.close()
    start = time()
    check_output(["lua", "temp.lua"])
    delta = time() - start
    chdir(lastcwd)
    return TimeStamp("LPeg", delta, patternname, inputname)


def benchmark_all_lua():
    patterninputs = get_patterninputpairs()
    ret = []
    for pattern, input in patterninputs:
        if pattern not in lua_blacklist:
                try:
                    ret.append(benchmark_lua(pattern, input))
                except CalledProcessError:
                    print("Lua process for " + pattern + " on "
                          + input + " not executed.")
            #exit()
    return ret


def benchmark_all_shellscripts():
    #only shell script is urlgrep.sh.
    #in the future this will have to be refactored to be less hardcoded
    patterninputs = get_patterninputpairs()
    ret = []
    for pattern, input in patterninputs:
        if "url" in input:
            try:
                ret.append(benchmark_shellscript("./urlgrep.sh", input))
            except CalledProcessError:
                print("urlgrep.sh on "+input+" not executed.")
        elif "email" in input:
            try:
                ret.append(benchmark_shellscript("./emailgrep.sh", input))
            except CalledProcessError:
                print("emailgrep.sh on "+input+" not executed.")
    return ret


def benchmark_all():
    #ret = benchmark_all_shellscripts()
    ret = benchmark_all_exes()
    ret.extend(benchmark_all_lua())
    ret.extend(benchmark_all_shellscripts())
    return ret


def main():
    outputtext = "["
    timestamps = []  # list of lists of timestamps
    for i in range(repetitions):
        print(str(i)+" repetitions completed!")
        timestamps.append(benchmark_all())
    sums = []
    for i in range(len(timestamps[0])):
        sums.append([])  # i hate python for not being able to do [[]]*n
    maxvals = [0] * len(timestamps[0])
    minvals = [9999] * len(timestamps[0])
    for stamplist in timestamps:
        for i in range(len(stamplist)):
            timestamp = stamplist[i]
            sums[i].append(timestamp.delta)
            if maxvals[i] < timestamp.delta:
                maxvals[i] = timestamp.delta
            if minvals[i] > timestamp.delta:
                minvals[i] = timestamp.delta
    for i in range(len(timestamps[0])):
        timestamp = timestamps[0][i]
        name = timestamp.filename
        pattern = timestamp.patternname
        input = timestamp.inputname
        average = sum(sums[i]) / float(repetitions)
        maximum = maxvals[i]
        minimum = minvals[i]
        rawvals = sums[i]
        out = OrderedDict([("Name", name), ("Used Pattern", pattern),
                           ("Used Input", input),
                           ("Average time", average),
                           ("Longest Time", maximum),
                           ("Shortest Time", minimum),
                           ("# of repeats", repetitions),
                           ("raw values", rawvals)])
        outputtext += dumps(out, indent=4)+","
    outputtext = outputtext[:-1]  # remove last ","
    outputfile = open(output, "w")
    outputfile.write(outputtext+"]")
    outputfile.close
    print("Benchmarking complete!")


if __name__ == "__main__":
    print ("Beginning benchmarking! After completion results can be viewed in "
           + output)
    main()
