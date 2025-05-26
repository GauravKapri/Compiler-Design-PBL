import re
import os


class ProgramConverter:
    """
    A class to convert a LISP-like S-expression string into 3-address code.
    It handles assignments, arithmetic operations, for loops, and if-else statements.
    """

    def __init__(self):
        self.temp_count = 0  # Counter for temporary variables
        self.label_count = 0  # Counter for labels
        self.three_address_code = []  # List to store generated 3-address instructions

    def new_temp(self):
        """Generates a new unique temporary variable name."""
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        """Generates a new unique label name."""
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, op, arg1=None, arg2=None, result=None):
        """
        Emits a single 3-address code instruction.
        Args:
            op (str): The operation (e.g., 'ASSIGN', 'ADD', 'IF_FALSE', 'GOTO', 'LABEL').
            arg1 (str, optional): The first argument. Defaults to None.
            arg2 (str, optional): The second argument. Defaults to None.
            result (str, optional): The result variable. Defaults to None.
        """
        # Ensure consistent structure for different instruction types
        if op in [
            "ASSIGN",
            "ADD",
            "SUB",
            "MUL",
            "DIV",
            ">",
            "<",
            "<=",
            ">=",
            "==",
            "!=",
            "IF_FALSE",
        ]:
            # These operations typically have 4 fields: op, arg1, arg2, result
            # We explicitly include None for arg2 if it's not provided, to maintain structure.
            instruction = [op, arg1, arg2, result]
        elif op in ["GOTO", "LABEL"]:
            # These operations typically have 2 fields: op, target_label
            instruction = [op, arg1]  # arg1 is the label here
        else:
            # Fallback for unexpected operations or operations with variable arguments.
            # This part should ideally not be hit if all operations are handled.
            instruction = [op]
            if arg1 is not None:
                instruction.append(arg1)
            if arg2 is not None:
                instruction.append(arg2)
            if result is not None:
                instruction.append(result)

        self.three_address_code.append(instruction)

    def tokenize(self, s_expr_str):
        """
        Tokenizes the input S-expression string.
        It adds spaces around parentheses and then splits the string by whitespace.
        """
        # Add spaces around parentheses to ensure they are split as separate tokens
        s_expr_str = s_expr_str.replace("(", " ( ").replace(")", " ) ")
        tokens = s_expr_str.split()
        return tokens

    def parse_s_expression(self, token_list):
        """
        Recursively parses a list of tokens into an S-expression (Abstract Syntax Tree).
        Handles nested parentheses to build the tree structure.
        """
        sexpr = []
        while token_list:
            token = token_list.pop(0)
            if token == "(":
                # If an opening parenthesis, recursively parse the sub-expression
                sexpr.append(self.parse_s_expression(token_list))
            elif token == ")":
                # If a closing parenthesis, return the current S-expression list
                return sexpr
            else:
                # Otherwise, it's a literal or identifier
                sexpr.append(token)
        return sexpr  # Should not be reached if parentheses are balanced

    def convert_expression(self, expr):
        """
        Converts an S-expression representing an expression into 3-address code.
        Returns the variable (or literal) that holds the result of the expression.
        """
        if not isinstance(expr, list):  # Not a list, e.g., 'x' or '5'
            return expr  # Return the literal/variable itself
        if not expr:  # Empty list []
            # This case should ideally not happen for valid expressions,
            # but if it does, returning None to avoid immediate IndexError.
            return None

        op = expr[0]
        if op == "=":
            # Assignment: (= target value)
            target = expr[1]
            value_expr = expr[2]
            if isinstance(value_expr, list):
                # If value is another expression, convert it first
                temp_result = self.convert_expression(value_expr)
                self.emit("ASSIGN", temp_result, None, target)
                return target
            else:
                # If value is a literal or variable
                self.emit("ASSIGN", value_expr, None, target)
                return target
        elif op in ["+", "-", "*", "/", ">", "<", "<=", ">=", "==", "!="]:
            # Binary operations: (op arg1 arg2)
            arg1_val = self.convert_expression(expr[1])
            arg2_val = self.convert_expression(expr[2])
            temp = self.new_temp()
            # Use appropriate operation name for emit
            if op == "+":
                self.emit("ADD", arg1_val, arg2_val, temp)
            elif op == "-":
                self.emit("SUB", arg1_val, arg2_val, temp)
            elif op == "*":
                self.emit("MUL", arg1_val, arg2_val, temp)
            elif op == "/":
                self.emit("DIV", arg1_val, arg2_val, temp)
            else:
                self.emit(
                    op, arg1_val, arg2_val, temp
                )  # For comparisons like <=, >= etc.
            return temp
        elif op == "++":
            # Increment operation: ( ++ ( <= i x ) i )
            # Based on desired output, we only care about incrementing the last argument 'i'.
            var = expr[-1]  # 'i' in this case
            temp = self.new_temp()
            self.emit("ADD", var, "1", temp)  # tX = var + 1
            self.emit("ASSIGN", temp, None, var)  # var = tX
            return var
        elif op == "if":
            # Conditional expression: (if condition true_branch false_branch)
            condition_expr = expr[1]
            true_branch_val = self.convert_expression(expr[2])
            false_branch_val = (
                self.convert_expression(expr[3]) if len(expr) > 3 else None
            )

            result_temp = (
                self.new_temp()
            )  # Temporary variable to store the result of the if expression

            label_false = self.new_label()
            label_end = self.new_label()

            # Evaluate the condition
            cond_result = self.convert_expression(condition_expr)
            self.emit(
                "IF_FALSE", cond_result, None, label_false
            )  # If condition is false, jump to false branch

            # True branch
            self.emit(
                "ASSIGN", true_branch_val, None, result_temp
            )  # Assign true branch result to temp
            self.emit("GOTO", label_end)  # Jump to end of if

            # False branch
            self.emit("LABEL", label_false)  # Label for the false branch
            if false_branch_val is not None:
                self.emit(
                    "ASSIGN", false_branch_val, None, result_temp
                )  # Assign false branch result to temp

            self.emit("LABEL", label_end)  # Label for the end of the if expression
            return result_temp  # Return the temporary variable holding the result
        else:
            # If an unrecognized operation, treat the entire list as a single entity
            # (e.g., a function call or an unrecognized keyword)
            return expr

    def convert_statement(self, stmt):
        """
        Converts an S-expression representing a statement or block of statements
        into 3-address code.
        """
        if not isinstance(stmt, list):  # Not a list, e.g., 'Dc' or 'i'
            return  # Do nothing for non-list statements
        if not stmt:  # Empty list []
            return  # Do nothing for empty statements

        op = stmt[0]
        if op == "stmt":
            # A sequence of statements: (stmt statement1 statement2 ...)
            for sub_stmt in stmt[1:]:
                self.convert_statement(sub_stmt)
        elif op == "main":
            # The main program block: (main statement1 statement2 ...)
            for sub_stmt in stmt[1:]:
                self.convert_statement(sub_stmt)
        elif op == "for":
            # For loop: (for init_stmt condition_expr increment_stmt body_stmt)
            # Based on user's desired output, we re-interpret the S-expression structure.
            # Original S-expr for for: (for init_block condition_assignment increment_expr body_block)
            # init_block = stmt[1]  -> (stmt (stmt (= x 5) (= p 1)) Dc i)
            # condition_assignment = stmt[2] -> (= i 1)  <-- This is now treated as initialization
            # increment_expr = stmt[3] -> (++ (<= i x) i) <-- (<= i x) is the actual condition, 'i' is incremented
            # body_block = stmt[4] -> (stmt (= p (* x i)) (= j 7))

            # 1. Process initial assignments before the loop starts
            # This handles (= x 5) and (= p 1)
            self.convert_statement(stmt[1])
            # This handles (= i 1) which was originally in the condition_expr slot
            self.convert_expression(stmt[2])

            label_loop_start = self.new_label()
            label_loop_end = self.new_label()

            # 2. Loop start label
            self.emit("LABEL", label_loop_start)

            # 3. Condition check: Extract (<= i x) from the increment_expr part (stmt[3][1])
            actual_condition_expr = stmt[3][1]  # This is (<= i x)
            cond_result = self.convert_expression(
                actual_condition_expr
            )  # Generates t_cond = i <= x
            self.emit(
                "IF_FALSE", cond_result, None, label_loop_end
            )  # If condition is false, exit loop

            # 4. Loop body
            self.convert_statement(stmt[4])  # This is the body_block

            # 5. Increment part: Process ( ++ ( <= i x ) i )
            # The '++' operator is handled in convert_expression, generating tX = i + 1; i = tX
            self.convert_expression(stmt[3])

            # 6. Jump back to loop start
            self.emit("GOTO", label_loop_start)
            self.emit("LABEL", label_loop_end)  # Label for loop exit
        elif op == "Dc":
            # Declaration: (Dc variable_name)
            # Declarations typically don't generate 3-address code directly,
            # as they are handled during symbol table creation.
            pass
        else:
            # If it's not a recognized statement keyword, treat it as an expression
            # that might have side effects (like an assignment).
            self.convert_expression(stmt)

    def convert(self, s_expr_str):
        """
        Main method to convert the S-expression string to 3-address code.
        """
        tokens = self.tokenize(s_expr_str)

        # Parse the token list into an Abstract Syntax Tree (AST).
        # The result will be a list containing the 'main' block as its first element.
        parsed_ast = self.parse_s_expression(tokens)

        # Start the conversion process from the main program block.
        if (
            parsed_ast
            and isinstance(parsed_ast[0], list)
            and parsed_ast[0][0] == "main"
        ):
            self.convert_statement(parsed_ast[0])
        else:
            print("Error: Input does not start with a 'main' block or is malformed.")

        return self.three_address_code


# --- Main execution block for file input ---
if __name__ == "__main__":
    # Define the path to ast_output.txt relative to the current script's location
    # Assuming ast_to_tac.py is in main-compiler/3. ICG/
    # and ast_output.txt is in main-compiler/2. AST/
    script_dir = os.path.dirname(__file__)
    ast_output_path = os.path.join(script_dir, "..", "2. AST", "ast_output.txt")

    s_expression_input = ""
    try:
        with open(ast_output_path, "r") as f:
            s_expression_input = f.read().strip()
        if not s_expression_input:
            print(
                f"Error: {ast_output_path} is empty. Please ensure it contains the S-expression."
            )
            exit()
    except FileNotFoundError:
        print(f"Error: The file '{ast_output_path}' was not found.")
        print("Please ensure your directory structure is:")
        print("main-compiler/")
        print("  ├── 2. AST/")
        print("  │   └── ast_output.txt")
        print("  └── 3. ICG/")
        print("      └── ast_to_tac.py (this program)")
        exit()
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        exit()

    converter = ProgramConverter()
    three_address_code = converter.convert(s_expression_input)

    # Print the generated 3-address code in the desired format
    for instruction in three_address_code:
        op = instruction[0]
        if op == "ASSIGN":
            # Handles assignments like 'x = 5' or 'x = t1'
            # instruction format: [ASSIGN, source, None, destination]
            print(f"{instruction[3]} = {instruction[1]}")
        elif op in ["ADD", "SUB", "MUL", "DIV", ">", "<", "<=", ">=", "==", "!="]:
            # Handles binary operations like 't3 = i <= x' or 't4 = x * i'
            # instruction format: [OP, arg1, arg2, result]
            # For comparison operators like <=, >, etc., the op is already the symbol.
            # For arithmetic ops, map to the symbol.
            print_op = op
            if op == "ADD":
                print_op = "+"
            elif op == "SUB":
                print_op = "-"
            elif op == "MUL":
                print_op = "*"
            elif op == "DIV":
                print_op = "/"
            print(f"{instruction[3]} = {instruction[1]} {print_op} {instruction[2]}")
        elif op == "IF_FALSE":
            # Handles conditional jumps like 'ifFalse t_cond goto L2'
            # instruction format: [IF_FALSE, condition_var, None, target_label]
            print(f"ifFalse {instruction[1]} goto {instruction[3]}")
        elif op == "GOTO":
            # Handles unconditional jumps like 'goto L1'
            # instruction format: [GOTO, target_label]
            print(f"goto {instruction[1]}")
        elif op == "LABEL":
            # Handles labels like 'L1:'
            # instruction format: [LABEL, label_name]
            print(f"{instruction[1]}:")
        else:
            # Fallback for any unhandled instruction types, print as raw list for debugging
            print(f"UNHANDLED_INSTRUCTION: {instruction}")
