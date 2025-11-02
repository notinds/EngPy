# TinyLang Interpreter

TinyLang is a simple interpreted programming language implemented in Python. It features a Python-like syntax with indentation-based blocks, English-like keywords, and basic arithmetic and logical operations.

## Features

- **Variables**: Declare with `let`, `var`, `const`, or `set`.
- **Arithmetic**: `+`, `-`, `*`, `/` (integer division).
- **Comparisons**: `==`, `!=`, `<`, `>`, `<=`, `>=`, or English phrases like `is greater than`, `is not equal to`.
- **Boolean Logic**: `and`, `or`.
- **Control Flow**: `if` and `while` with colon and indentation.
- **Output**: `print` statements.

## Syntax Examples

### Basic Assignment and Print
```
let x = 10
print x
```

### Arithmetic
```
let a = 5
let b = 3
let sum = a + b
print sum
```

### Comparisons
```
let x = 10
if x > 5:
  print "x is greater than 5"
```

### Loops
```
let i = 0
while i < 5:
  print i
  i = i + 1
```

### Boolean Operations
```
let a = 1
let b = 0
if a and b:
  print "both true"
if a or b:
  print "at least one true"
```

## Running Programs

Save your TinyLang code in a file with a `.tl` extension, e.g., `program.tl`.

Run the interpreter:
```
python3 test.py program.tl
```

If no file is provided, it runs a sample factorial program.

## More Examples

### Factorial
```
let n = 5
let fact = 1
while n > 1:
  fact = fact * n
  n = n - 1
print fact
```

### FizzBuzz (simplified)
```
let i = 1
while i <= 10:
  if i % 3 == 0 and i % 5 == 0:
    print "FizzBuzz"
  if i % 3 == 0:
    print "Fizz"
  if i % 5 == 0:
    print "Buzz"
  print i
  i = i + 1
```

### Conditional Assignment
```
let x = 10
let y = 20
let max = x
if y > x:
  max = y
print max
```

## Implementation Details

- **Lexer**: Tokenizes input, handling indentation for blocks.
- **Parser**: Builds an AST using precedence climbing.
- **Evaluator**: Interprets the AST in a simple environment.
- **Error Handling**: Basic syntax and runtime errors.

## Extending TinyLang

To add new features:
1. Update the lexer for new tokens.
2. Modify the parser for new grammar rules.
3. Extend the evaluator for new operations.

Enjoy coding in TinyLang!
