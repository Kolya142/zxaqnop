from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple
from lexer import lexer

class ParserState(Enum):
    SIMPLE = 0
    PARENTHES = 1
    SBRACES = 2
    CBRACES = 3

class AstAtomType(Enum):
    CHAR = 0
    STR = 1
    INT = 2
    WORD = 3
    PARENTHES = 4
    SBRACES = 5
    CBRACES = 6

@dataclass
class AstAtom:
    typ: AstAtomType
    value: List["Ast"] | str | int

Ast = List["Ast"] | AstAtom

def parser(toks: List[str | int], state: ParserState) -> Tuple[Ast, List[str | int]]:
    ast = []
    while len(toks):
        tok = toks[0]
        toks = toks[1:]
        if isinstance(tok, int):
            ast.append(AstAtom(AstAtomType.INT, str(tok)))
        elif tok[0] == '"':
            ast.append(AstAtom(AstAtomType.STR, tok[1:][:-1]))
        elif tok[0] == '\'':
            ast.append(AstAtom(AstAtomType.CHAR, tok[1:][:-1]))
        elif state == ParserState.PARENTHES and tok == ')':
            break
        elif state == ParserState.SBRACES and tok == ']':
            break
        elif state == ParserState.CBRACES and tok == '}':
            break
        elif tok == '(':
            i, toks = parser(toks, ParserState.PARENTHES)
            ast.append(AstAtom(AstAtomType.PARENTHES, i))
        elif tok == '[':
            i, toks = parser(toks, ParserState.SBRACES)
            ast.append(AstAtom(AstAtomType.SBRACES, i))
        elif tok == '{':
            i, toks = parser(toks, ParserState.CBRACES)
            ast.append(AstAtom(AstAtomType.CBRACES, i))
        else:
            ast.append(AstAtom(AstAtomType.WORD, tok))
    return ast, toks

if __name__ == "__main__":
    print(parser(lexer(open("main.zxq").read()), ParserState.SIMPLE)[0])
