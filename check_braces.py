with open("script.js", "r") as f:
    text = f.read()

def check(t):
    stack = []
    line_nums = [1]
    for char in t:
        if char == '\n':
            line_nums.append(line_nums[-1] + 1)
        else:
            line_nums.append(line_nums[-1])
            
    for i, char in enumerate(t):
        if char in "({[":
            # ignore inside strings or regex? This simple parser might fail inside strings.
            stack.append((char, i, line_nums[i]))
        elif char in ")}]":
            if not stack:
                print(f"Extra closing {char} at line {line_nums[i]}")
                return
            last_char, last_i, last_line = stack.pop()
            matches = {"(": ")", "{": "}", "[": "]"}
            if matches[last_char] != char:
                print(f"Mismatch at line {line_nums[i]}: expected {matches[last_char]}, got {char}. Opened at line {last_line}")
                return
    if stack:
        print(f"Unclosed {stack[-1][0]} at line {stack[-1][2]}")

check(text)
