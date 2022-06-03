from lrparsing import *
import sys

KEYWORD_IF = "যদি"
KEYWORD_ELSE = "অথবা"
KEYWORD_WHILE = "যখন"
KEYWORD_PRINT = "দেখাও"

class ExprParser(Grammar):

    class T(TokenRegistry):
        integer = Token(re="[\u09e6-\u09ef]+")
        ident = Token(re="[\u0980-\u09e3A-Za-z_][\u0980-\u09e3A-Za-z_0-9]*")
        string = Token(re="\"(?:[^\"\\\\]|\\.)*\"")
    expr = Ref("expr")                # Forward reference
    print_call = Keyword(KEYWORD_PRINT) + '(' + List(expr, ',') + ')'
    grouping = '(' + expr + ')'
    atom = T.ident | T.integer | grouping | print_call | T.string
    binary_mult = atom | atom << Tokens("* / %") << atom
    binary_add = binary_mult | binary_mult << Tokens("+ -") << binary_mult
    binary_cond = binary_add | binary_add << Tokens("< >") << binary_add
    binary_equality = binary_cond | binary_cond << Tokens("== !=") << binary_cond
    expr = binary_equality * 1
    """
    expr = Prio(
        atom,
        Tokens("+ - ~") >> THIS,      # >> means right associative
        THIS << Tokens("* / // %") << THIS,
        THIS << Tokens("+ -") << THIS,# THIS means "expr" here
        THIS << Tokens("< >") << THIS,
        THIS << Tokens("== !=") << THIS)
        """
    stmt = Ref("stmt")
    stmt_block = "{" + Repeat(stmt) + "}"
    stmt_assign = T.ident + "=" + expr
    block_if = Keyword(KEYWORD_IF) + "(" + expr + ")" + stmt_block
    stmt_if = block_if + Repeat(Keyword(KEYWORD_ELSE) + block_if, min=0, max=None)
    stmt_while = Keyword(KEYWORD_WHILE) + "(" + expr + ")" + stmt_block
    stmt = stmt_if | stmt_while | stmt_assign | expr
    root = Repeat(stmt, min=1)
    START = root                      # Where the grammar must start
    COMMENTS = (                      # Allow C and Python comments
        Token(re="#(?:[^rn]*(?:rn?|nr?))") |
        Token(re="/[*](?:[^*]|[*][^/])*[*]/"))

VARIABLES = {}

BENGALI_DIGITS = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯']

def to_bengali_value(number):
    string = str(number)
    ret = ""
    if string[0] == '-':
        ret = '-'
        string = string[1:]
    for s in string:
        ret += BENGALI_DIGITS[int(s)]
    return ret

def to_value(bengali_number):
    num = 0
    for b in bengali_number:
        num = num * 10 + BENGALI_DIGITS.index(b)
    return num

def run_print(expr):
    # print(expr)
    count = 0
    for val in expr[3:-1:2]:
        val = run_expr(val[1])
        if type(val) == int:
            val = to_bengali_value(val)
        print(val, end='')
        count += 1
    print()
    return count

def run_expr_atom(expr):
    # print(expr)
    expr = expr[1]
    if expr[0] == ExprParser.T.integer:
        return to_value(expr[1])
    elif expr[0] == ExprParser.T.ident:
        var = expr[1]
        if var in VARIABLES:
            return VARIABLES[expr[1]]
        else:
            print("[Warn] Variable", var, "used before declaration!")
            return 0
    elif expr[0] == ExprParser.grouping:
        return run_expr(expr[2])
    elif expr[0] == ExprParser.T.string:
        return expr[1][1:-1]
    elif expr[0] == ExprParser.print_call:
        return run_print(expr)
    else:
        print("[Err] Unknown expression:", expr[1])

def run_expr_mult(expr):
    # print(expr)
    left = run_expr_atom(expr[1])
    if len(expr) > 2:
        right = run_expr_atom(expr[3])
        if expr[2][1] == '*':
            left *= right
        elif expr[2][1] == '/':
            left //= right
        else:
            left %= right
    return left

def run_expr_add(expr):
    # print(expr)
    left = run_expr_mult(expr[1])
    if len(expr) > 2:
        right = run_expr_mult(expr[3])
        # print(expr[2])
        if expr[2][1] == '+':
            left += right
        else:
            left -= right
    return left

def run_expr_cond(expr):
    left = run_expr_add(expr[1])
    if len(expr) > 2:
        right = run_expr_add(expr[3])
        if expr[2][1] == '>':
            return left > right
        else:
            return left < right
    return left

def run_expr_equality(expr):
    # print(expr)
    left = run_expr_cond(expr[1])
    if len(expr) > 2:
        right = run_expr_cond(expr[3])
        if expr[2][1] == '==':
            return left == right
        else:
            return left != right
    return left

def run_expr(expr):
    # print(expr)
    return run_expr_equality(expr)

def run_assign(stmt):
    var = stmt[1][1]
    value = run_expr(stmt[3][1])
    VARIABLES[var] = value
    # print(VARIABLES)

def run_if(stmt):
    cond = run_expr(stmt[1][3][1])
    if cond:
        run_block(stmt[1][5])

def run_while(stmt):
    cond = run_expr(stmt[3][1])
    while cond:
        run_block(stmt[5])
        cond = run_expr(stmt[3][1])

def run_block(stmt):
    for s in stmt[2:-1]:
        run_stmt(s[1])
        # print(s)

def run_stmt(stmt):
    # print(stmt)
    if stmt[0] == ExprParser.stmt_assign:
        # print("assignment")
        run_assign(stmt)
    elif stmt[0] == ExprParser.stmt_if:
        # print("if")
        run_if(stmt)
    elif stmt[0] == ExprParser.stmt_while:
        # print("while")
        run_while(stmt)
    elif stmt[0] == ExprParser.expr:
        run_expr(stmt[1])
    else:
        print("[Err]: Invalid statement:", stmt)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please enter a filename to run!")
        sys.exit()
    source = open(sys.argv[1]).readlines()
    parse_tree = ExprParser.parse("".join(source))
    # print(parse_tree[1][1][1])
    for stmt in parse_tree[1][1:]:
        run_stmt(stmt[1])
    # print(ExprParser.repr_parse_tree(parse_tree))
