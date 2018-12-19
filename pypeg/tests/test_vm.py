from pypeg.vm import run, runbypattern, processcaptures
from pypeg.parser import parse, relabel


def test_any():
    pattern = 'lpeg.P(1)'
    #matches any string of length 1
    assert runbypattern(pattern, "K") is not None
    assert runbypattern(pattern, "").fail 
    assert runbypattern(pattern, "AA").fail 


def test_char_end():
    pattern = 'lpeg.P"a"'
    #matches exactly the string "a"
    assert runbypattern(pattern, "a") is not None
    assert runbypattern(pattern, "b").fail 
    assert runbypattern(pattern, "").fail 


def test_char_end_2():
    pattern = 'lpeg.P"ab"'
    #matches exactly the string "ab"
    assert runbypattern(pattern, "ab") is not None
    assert runbypattern(pattern, "ac").fail 
    assert runbypattern(pattern, "b").fail 
    assert runbypattern(pattern, "").fail 


def test_set():
    pattern = 'lpeg.P"a"+lpeg.P"c"+lpeg.P"z"'
    #matches either of these 3 strings: "a","c","z"
    assert runbypattern(pattern, "a") is not None
    assert runbypattern(pattern, "c") is not None
    assert runbypattern(pattern, "z") is not None
    assert runbypattern(pattern, "b").fail 
    assert runbypattern(pattern, "").fail 


def test_testchar():
    pattern = 'lpeg.P"aa"+lpeg.P"bb"'
    #matches either of these 2 strings: "aa", "bb"
    assert runbypattern(pattern, "aa") is not None
    assert runbypattern(pattern, "bb") is not None
    assert runbypattern(pattern, "ab").fail 
    assert runbypattern(pattern, "ba").fail 
    assert runbypattern(pattern, "banana").fail 
    assert runbypattern(pattern, "").fail 


def test_choice_commit():
    pattern = 'lpeg.P"aa"+lpeg.P"ab"'
    #matches either of these 2 strings: "aa", "ab"
    assert runbypattern(pattern, 'aa') is not None
    assert runbypattern(pattern, 'ab') is not None
    assert runbypattern(pattern, 'aaa').fail 
    assert runbypattern(pattern, '').fail 


def test_testset_partial_commit():  # possible todo: find shorter example
    pattern = '(lpeg.P"aa"+lpeg.P"zz")^0'
    #matches arbitrarily many repetitions
    #of either of these 2 strings: "aa","zz"
    assert runbypattern(pattern, "") is not None
    assert runbypattern(pattern, "aazzaa") is not None
    assert runbypattern(pattern, "zzaazz") is not None
    assert runbypattern(pattern, "azazaz").fail 
    assert runbypattern(pattern, "aaaaaz").fail 
    assert runbypattern(pattern, "banana").fail 


def test_span():
    pattern = '(lpeg.P"a"+lpeg.P"b")^0'
    #matches arbitrarily many repetitions
    #of either of these 2 strings: "a", "b"
    assert runbypattern(pattern, "") is not None
    assert runbypattern(pattern, "aaaaa") is not None
    assert runbypattern(pattern, "b") is not None
    assert runbypattern(pattern, "aaac").fail 
    assert runbypattern(pattern, "abca").fail 


def test_behind():
    pattern = 'lpeg.B(lpeg.P"a")'
    #matches exactly the string "a" without consuming input
    assert runbypattern(pattern, "").fail 
    assert runbypattern(pattern, "a") is not None


def test_behind_2():
    pattern = '#lpeg.P(2)'
    #matches any 2 characters without consuming them
    assert runbypattern(pattern, "").fail 
    assert runbypattern(pattern, "z").fail 
    assert runbypattern(pattern, "ak") is not None
    assert runbypattern(pattern, "lol").fail 


def test_testany_fail():
    pattern = 'lpeg.P(-1)'
    # matches only on empty string
    assert runbypattern(pattern, "") is not None
    assert runbypattern(pattern, "a").fail 
    assert runbypattern(pattern, " ").fail 


def test_failtwice():
    pattern = 'lpeg.P(-2)'
    #Matches any String of length 1 or less
    assert runbypattern(pattern, "") is not None
    assert runbypattern(pattern, "a") is not None
    assert runbypattern(pattern, "aa").fail 
    assert runbypattern(pattern, "  ").fail 


def test_slow():
    bignumber = 1*10**4
    longstring = "c"*bignumber+"ab"
    pattern = 'lpeg.P{ lpeg.P"ab" + 1 * lpeg.V(1) }'
    #matches any string that ends with "ab"
    assert runbypattern(pattern,
                        longstring) is not None
    assert runbypattern(pattern,
                        longstring[0:1000]).fail 


def test_grammar_call_jmp_ret():
    grammar = """lpeg.P{
    "a";
    a =     lpeg.V("b") * lpeg.V("c"),
    b = lpeg.P("b"),
    c = lpeg.P("c")}"""
    #matches exactly the string "bc"
    assert runbypattern(grammar, "bc") is not None
    assert runbypattern(grammar, "").fail 
    assert runbypattern(grammar, "b").fail 


def test_fullcapture_simple():
    #fullcapture tests for captures of fixed length
    pattern = 'lpeg.C(lpeg.P("a"))'
    #captures exactly the string "a"
    assert runbypattern(pattern, "a") is not None
    assert runbypattern(pattern, "").fail


def test_fullcapture_simple_2():
    pattern = 'lpeg.C(lpeg.P("ab"))'
    #captures exactly the string "ab"
    assert runbypattern(pattern, "").fail 
    assert runbypattern(pattern, "a").fail 
    assert runbypattern(pattern, "ab") is not None
    assert runbypattern(pattern, "banana").fail 


def test_fullcapture_position():
    pattern = 'lpeg.P"a"^0*lpeg.Cp()'
    #captures the position of the end of a string of "a"s
    assert runbypattern(pattern, "a") is not None
    assert runbypattern(pattern, "b").fail 
    assert runbypattern(pattern, "") is not None


def test_opencapture_simple_closecapture():
    pattern = 'lpeg.C(lpeg.R("09")^0)'
    #captures a number
    captures = runbypattern(pattern, "123").captures
    assert captures is not None
    assert processcaptures(captures, "123") == ["123"]
    #TODO: more tests, figure out how to write this elegantly


def test_processcapture_open_simple():
    pattern = 'lpeg.R("09")^0 *  lpeg.C( lpeg.R("az")) * lpeg.R("09")^0'
    #captures a number
    #followed by a letter
    #followed by a number
    inputstring = "123a567"
    captures = runbypattern(pattern, inputstring).captures
    assert processcaptures(captures, inputstring) == ["a"]
    #TODO: more tests, figure out how to write this elegantly


def test_processcapture_full_position():
    pattern = 'lpeg.P"a"^0*lpeg.Cp()'
    #captures the position of the end of a string of "a"s
    inputstring = "aaaa"
    captures = runbypattern(pattern, inputstring).captures
    assert processcaptures(captures, inputstring) == ["POSITION: 4"]
