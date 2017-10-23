# StringQueryTool

Matches a string against a predefined query. Allows for and/or operators and brackets to modify the order of operations. 

Example usage:
```
from StringQueryTool import *

if __name__ == "__main__":
    qt = StringQueryTool("(this&that),(the&rest)")
    test = []
    test.append("this and that")                      # true
    test.append("this and the rest")                  # true
    test.append("that and this")                      # true
    test.append("that and the rest")                  # true
    test.append("this and that and the rest")         # true
    test.append("this and rest")                      # false
    test.append("this")                               # false
    test.append("that")                               # false
    test.append("the")                                # false
    test.append("rest")                               # false

    for i in test:
        print("Testing: %s" %i)
        print(qt.is_match(i))
```

is_match returns true for any strings that match the specified pattern. In the example, strings will evaluate to true if they contain either "this" and "that", or "the" and "rest".