from dataclasses import dataclass

@dataclass
class Component:
    sym: str
    mult: float

def tokenize(formula):
    i = 0
    tokens = []
    while i < len(formula):
        c = formula[i]

        if c in "()":
            tokens.append(c)
            i += 1
        elif c.isupper():
            if i+1 < len(formula) and formula[i + 1].islower():
                tokens.append(formula[i:i+2])
                if i+2 >= len(formula) or formula[i + 2] not in "1234567890":
                    tokens.append(1)
                i += 2
                continue
            elif i+1 >= len(formula) or formula[i + 1] not in "1234567890":
                tokens.append(formula[i])
                tokens.append(1)
                i += 1
            else:
                tokens.append(formula[i])
                i += 1
        elif c in "1234567890":
            cur = formula[i]
            chunk = ""
            index = i
            while cur in "1234567890.":
                chunk += cur
                index += 1 

                if index >= len(formula):
                    break

                cur = formula[index]

            tokens.append(float(chunk))
            i = index
        else:
            raise Exception(f"Invalid character '{c}'")
            print("Invalid character:", c)
             


    return tokens

def isfloating(string):
    try:
        float(string)
        return True
    except:
        return False

def tokens_to_elems(tokens):
    i = 0
    
    level = 0
    stack = [[]]
    while i < len(tokens):
        if tokens[i] == "(":
            level += 1
            i += 1
            stack.append([])
            continue
        elif tokens[i] == ")":
            # End of level, unwind one level
            # Check for multiplier after parenthesis
            # Add unwound elems to above stack frame
            mult = 1
            if i + 1 < len(tokens) and isinstance(tokens[i+1], (int, float)):
                mult = tokens[i+1]

            cur = stack.pop()
            for x in cur:
                stack[-1].append([x[0], x[1] * mult])

            level -= 1
        elif isinstance(tokens[i], (str)):
            # Token is an element
            if i+1 < len(tokens) and isinstance(tokens[i+1], (float, int)):
                stack[-1].append([tokens[i], tokens[i+1]])
                i += 2
                continue
            else:
                stack[-1].append([tokens[i], 1])
                i += 1
                continue
        # The below code should never be triggered. Can be used to indicate error
        #elif isfloating(tokens[i]):
        #    print(tokens[i])
        #    i += 1
        #    continue
        
        
        i += 1

    return stack[0]

def parse_formula(formula):
    return tokens_to_elems(tokenize(formula))


if __name__ == "__main__":
    hto = "Ho2.2Ti2O7"
    comp = "(Ho0.5Gd0.2Dy0.3)2Ti2O7"
    extra = "(Ho0.6(Gd0.1Dy0.1)2)2Ti2O7"
    extra_2 = "(Ho0.6(Gd0.1Dy0.1)2)2(Ti0.5Zr0.25Sn0.25)2O7"
    print(tokens_to_elems(tokenize(hto)))
    print(tokens_to_elems(tokenize(comp)))
    print(tokens_to_elems(tokenize(extra)))
    print(tokens_to_elems(tokenize(extra_2)))



