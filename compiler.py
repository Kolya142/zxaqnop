from dataclasses import dataclass
import sys
from typing import Dict, Tuple
from parser import Ast, AstAtomType, AstAtom, parser, ParserState
from lexer import lexer

def get_c_type(r: str) -> str:
    i = 0
    while r[-1] == '*':
        r = r[:-1]
        i += 1
    r, *R = r
    if r in functypes:
        t = functypes[r]
    else:
        match r:
            case "i8":
                t = "char"
            case "i16":
                t = "short"
            case "i32":
                t = "int"
            case "i64":
                t = "long long"
            case "u0":
                t = "void"
            case "u8":
                t = "unsigned char"
            case "u16":
                t = "unsigned short"
            case "u32":
                t = "unsigned int"
            case "u64":
                t = "unsigned long long"
            case "f32":
                t = "float"
            case "f64":
                t = "double"
            case "str":
                t = "char*"
            case _:
                t = r
    return t + '*' * i, ''.join(R)

@dataclass
class CompilerState:
    lvars: Dict[str, str]
    current: str | None
    ret: str
    indent: int
    def dup(self) -> "CompilerState":
        return CompilerState(self.lvars.copy(), self.current, self.ret, self.indent + 4)

functypes: Dict[str, str] = {}
macros: Dict[str, str] = {}

def par2type(par: AstAtom) -> str:
    t = []
    for i in par.value:
        if isinstance(i.value, list):
            t.append('[')
            t.extend(par2type(i))
            t.append(']')
        else:
            t.append(i.value)
    return t

def compiler(ast: Ast, cstate: CompilerState) -> Tuple[object, CompilerState]:
    global functypes, macros
    if isinstance(ast, list):
        i = 0
        code = ""
        defer = ""
        while i < len(ast):
            atom = ast[i]
            if isinstance(atom, list):
                code += compiler(atom, cstate)[0]
                i += 1
                continue
            elif isinstance(atom, str):
                code += atom
                i += 1
                continue
            elif isinstance(atom, int):
                code += str(atom)
                i += 1
                continue
            match atom.typ:
                case AstAtomType.WORD:
                    match atom.value:
                        case "use":
                            i += 1
                            name = []
                            while ast[i].value != ';':
                                name.append(ast[i].value)
                                i += 1
                            if name[0] == 'std':
                                match name[2]:
                                    case 'io':
                                        code += "#include <stdio.h>\n"
                                    case 'std':
                                        code += "#include <stdlib.h>\n"
                                    case 'math':
                                        code += "#include <math.h>\n"
                            elif name[0] == 'glob':
                                code += f"#include <{name[2]}.h>\n"
                            elif name[0] == 'loc':
                                code += f"#include \"{name[2]}.h\"\n"
                            elif name[0] == 'there':
                                code += compiler(parser(lexer(open({name[2]+".zxq"}).read()), ParserState.SIMPLE)[0], cstate)[0]
                        case "defer":
                            defer = compiler([ast[i + 1]], cstate)[0]
                            i += 1
                        case "loop":
                            if ast[i + 1].value == "until":
                                code += "while (!" + compiler(ast[i + 2].value, cstate)[0] + ")"
                                i += 2
                            elif ast[i + 1].value == "range":
                                v = compiler([ast[i + 2].value], cstate)[0]
                                l = compiler([ast[i + 3].value], cstate)[0]
                                r = compiler([ast[i + 4].value], cstate)[0]
                                code += f"for (long long {v} = {l}; {v} < {r}; ++{v})"
                                i += 4
                            else:
                                code += "for (;;)"
                        case "class":
                            inner = ""
                            j = 0
                            while j < len(ast[i + 2].value):
                                t = get_c_type(par2type(ast[i + 2].value[j + 1]))
                                inner += t[0] + " " + ast[i + 2].value[j].value + t[1] + ";"
                                j += 2
                            code += f"typedef struct {ast[i + 1].value} {ast[i + 1].value}; typedef struct {ast[i + 1].value} {"{\n"}{inner}{"\n}\n"} {ast[i + 1].value};"
                            functypes[ast[i + 1].value] = ast[i + 1].value
                            i += 2
                        case "enum":
                            inner = ""
                            j = 0
                            while j < len(ast[i + 2].value):
                                inner += ast[i + 1].value + "_" + ast[i + 2].value[j].value + ","
                                j += 1
                            code += f"typedef enum {ast[i + 1].value} {ast[i + 1].value}; typedef enum {ast[i + 1].value} {"{\n"}{inner}{"\n}\n"} {ast[i + 1].value};"
                            functypes[ast[i + 1].value] = ast[i + 1].value
                            i += 2
                        case "fn":
                            args = ""
                            j = 0
                            cstate0 = cstate.dup()
                            cstate0.current = ast[i + 2].value
                            while j < len(ast[i + 3].value):
                                arg = ast[i + 3].value[j].value
                                t = get_c_type(par2type(ast[i + 3].value[j + 1]))
                                cstate0.lvars[arg] = t
                                args += t[0] + " " + arg + t[1]
                                if j + 2 < len(ast[i + 3].value):
                                    args += ", "
                                j += 2
                            t = get_c_type(par2type(ast[i + 1]))
                            code += t[0] + " " + ast[i + 2].value + "(" + args + ")" + '{\n' + (compiler(macros["on_func_enter"], cstate0)[0] if "on_func_enter" in macros else "") + compiler(ast[i + 4].value, cstate0)[0] + (compiler(macros["on_func_exit"], cstate0)[0] if "on_func_exit" in macros else "") + '\n}\n'
                            if ast[i + 2].value in functypes:
                                sys.stderr.write(f"Function {ast[i + 2].value} already exists\n")
                                sys.exit(1)
                            functypes[ast[i + 2].value] = get_c_type(par2type(ast[i + 1]))
                            i += 4
                        case "extfn":
                            if ast[i + 2].value in functypes:
                                sys.stderr.write(f"Function {ast[i + 2].value} already exists\n")
                                sys.exit(1)
                            functypes[ast[i + 2].value] = get_c_type(par2type(ast[i + 1]))
                            i += 2
                        case "let":
                            if ast[i + 1].value == "stat":
                                code += "static "
                                i += 1
                            if ast[i + 1].value == "hardware":
                                code += "volatile "
                                i += 1
                            if ast[i + 1].value == "readonly":
                                code += "const "
                                i += 1
                            cstate0 = cstate.dup()
                            cstate0.current = ast[i + 2].value
                            t = get_c_type(par2type(ast[i + 1]))
                            if ast[i + 3].value == ";":
                                code += t[0] + " " + ast[i + 2].value + t[1] + ';'
                                cstate.lvars[ast[i + 2].value] = t
                                i += 2
                            else:
                                if ast[i + 1].value[0].value == "auto":
                                    s = compiler([ast[i + 4]], cstate0)
                                    code += s[1].ret + " " + ast[i + 2].value + "=" + s[0] + ';'
                                    cstate.lvars[ast[i + 2].value] = s[1].ret
                                else:
                                    code += t[0] + " " + ast[i + 2].value + t[1] + "=" + compiler([ast[i + 4]], cstate0)[0] + ';'
                                    cstate.lvars[ast[i + 2].value] = t
                                i += 5
                        case "typeof":
                            code += ''.join(cstate.lvars[ast[i + 1].value[0].value])
                            i += 1
                        case "thisof":
                            code += cstate.current
                        case ";":
                            code += ";\n"
                        case "strize":
                            code += '"' + compiler(ast[i + 1].value, cstate)[0] + '"'
                            cstate.ret = "char*"
                            i += 1
                        case "return":
                            code += "return "
                        case "case":
                            code += "case "
                        case "else":
                            code += "else "
                        case "macro":
                            macros[compiler([ast[i + 1].value], cstate)[0]] = ast[i + 2].value
                            i += 2
                        case "static_format":
                            a = tuple([compiler([i.value], cstate)[0] for i in ast[i + 2].value])
                            sys.stderr.write(str(a))
                            f = compiler([ast[i + 1].value], cstate)[0]
                            sys.stderr.write("\nFormat: " + str(f) + "\n")
                            code += '"' + (
                                f % a
                            ) + '"'
                            i += 2
                        case "static_append":
                            code += compiler([ast[i + 1].value], cstate)[0][1:][:-1]
                            i += 1
                        case "static_print":
                            sys.stderr.write(compiler([ast[i + 1].value], cstate)[0])
                            i += 1
                        case "undef":
                            del macros[ast[i + 1].value]
                            i += 1
                        case _:
                            if atom.value in macros:
                                sys.stderr.write(str(macros[atom.value]) + "\n")
                                code += compiler(macros[atom.value], cstate)[0]
                            else:
                                if atom.value in functypes:
                                    cstate.ret = functypes[atom.value]
                                code += atom.value
                case AstAtomType.INT:
                    if atom.value[0] == '-':
                        cstate.ret = 'long long'
                    else:
                        cstate.ret = 'unsigned long long'
                    code += atom.value
                case AstAtomType.PARENTHES:
                    s = compiler(atom.value, cstate)
                    code += '(' + s[0] + ')'
                case AstAtomType.SBRACES:
                    s = compiler(atom.value, cstate)
                    code += '[\n' + s[0] + '\n]\n'
                case AstAtomType.CBRACES:
                    s = compiler(atom.value, cstate)
                    code += '{\n' + s[0] + '\n}\n'
                case AstAtomType.STR:
                    cstate.ret = 'char*'
                    code += '"' + atom.value + '"'
                case AstAtomType.CHAR:
                    cstate.ret = 'char'
                    code += '\'' + atom.value + '\''
            i += 1
        return (code + defer, cstate)
    return ('', cstate)

if __name__ == "__main__":
    print(compiler(parser(lexer(open(sys.argv[1]).read()), ParserState.SIMPLE)[0], CompilerState({}, "toplevel", "toplevel", 0))[0])
