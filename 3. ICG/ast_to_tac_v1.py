import re
import os


class ProgramConverter:
    def __init__(self):
        self.temp_count = 0
        self.label_count = 0
        self.three_address_code = []

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def emit(self, op, arg1=None, arg2=None, result=None):
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
        ]:
            instruction = [op, arg1, arg2, result]
        elif op in ["GOTO", "LABEL"]:
            instruction = [op, arg1]
        else:
            instruction = [op]
            if arg1 is not None:
                instruction.append(arg1)
            if arg2 is not None:
                instruction.append(arg2)
            if result is not None:
                instruction.append(result)
        self.three_address_code.append(instruction)

    def tokenize(self, s_expr_str):
        s_expr_str = s_expr_str.replace("(", " ( ").replace(")", " ) ")
        tokens = s_expr_str.split()
        return tokens

    def parse_s_expression(self, token_list):
        sexpr = []
        while token_list:
            token = token_list.pop(0)
            if token == "(":
                sexpr.append(self.parse_s_expression(token_list))
            elif token == ")":
                return sexpr
            else:
                sexpr.append(token)
        return sexpr

    def convert_expression(self, expr):
        if not isinstance(expr, list):
            return expr
        if not expr:
            return None
        op = expr[0]
        if op == "=":
            target = expr[1]
            value_expr = expr[2]
            if isinstance(value_expr, list):
                temp_result = self.convert_expression(value_expr)
                self.emit("ASSIGN", temp_result, None, target)
                return target
            else:
                self.emit("ASSIGN", value_expr, None, target)
                return target
        elif op in ["+", "-", "*", "/", ">", "<", "<=", ">=", "==", "!="]:
            arg1_val = self.convert_expression(expr[1])
            arg2_val = self.convert_expression(expr[2])
            temp = self.new_temp()
            if op == "+":
                self.emit("ADD", arg1_val, arg2_val, temp)
            elif op == "-":
                self.emit("SUB", arg1_val, arg2_val, temp)
            elif op == "*":
                self.emit("MUL", arg1_val, arg2_val, temp)
            elif op == "/":
                self.emit("DIV", arg1_val, arg2_val, temp)
            else:
                self.emit(op, arg1_val, arg2_val, temp)
            return temp
        elif op == "++":
            var = expr[-1]
            temp = self.new_temp()
            self.emit("ADD", var, "1", temp)
            self.emit("ASSIGN", temp, None, var)
            return var
        elif op == "if":
            condition_expr = expr[1]
            true_branch_val = self.convert_expression(expr[2])
            false_branch_val = (
                self.convert_expression(expr[3]) if len(expr) > 3 else None
            )
            result_temp = self.new_temp()
            label_false = self.new_label()
            label_end = self.new_label()
            cond_result = self.convert_expression(condition_expr)
            self.emit("IF_FALSE", cond_result, None, label_false)
            self.emit("ASSIGN", true_branch_val, None, result_temp)
            self.emit("GOTO", label_end)
            self.emit("LABEL", label_false)
            if false_branch_val is not None:
                self.emit("ASSIGN", false_branch_val, None, result_temp)
            self.emit("LABEL", label_end)
            return result_temp
        else:
            return expr

    def convert_statement(self, stmt):
        if not isinstance(stmt, list):
            return
        if not stmt:
            return
        op = stmt[0]
        if op == "stmt":
            for sub_stmt in stmt[1:]:
                self.convert_statement(sub_stmt)
        elif op == "main":
            for sub_stmt in stmt[1:]:
                self.convert_statement(sub_stmt)
        elif op == "for":
            self.convert_statement(stmt[1])
            self.convert_expression(stmt[2])
            label_loop_start = self.new_label()
            label_loop_end = self.new_label()
            self.emit("LABEL", label_loop_start)
            actual_condition_expr = stmt[3][1]
            cond_result = self.convert_expression(actual_condition_expr)
            self.emit("IF_FALSE", cond_result, None, label_loop_end)
            self.convert_statement(stmt[4])
            self.convert_expression(stmt[3])
            self.emit("GOTO", label_loop_start)
            self.emit("LABEL", label_loop_end)
        elif op == "Dc":
            pass
        else:
            self.convert_expression(stmt)

    def convert(self, s_expr_str):
        tokens = self.tokenize(s_expr_str)
        parsed_ast = self.parse_s_expression(tokens)
        if (
            parsed_ast
            and isinstance(parsed_ast[0], list)
            and parsed_ast[0][0] == "main"
        ):
            self.convert_statement(parsed_ast[0])
        else:
            print("Error: Input does not start with a 'main' block or is malformed.")
        return self.three_address_code


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    ast_output_path = os.path.join(script_dir, "..", "2. AST", "ast_output.txt")
    s_expression_input = ""
    try:
        with open(ast_output_path, "r") as f:
            s_expression_input = f.read().strip()
        if not s_expression_input:
            print(f"Error: {ast_output_path} is empty.")
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

    for instruction in three_address_code:
        op = instruction[0]
        if op == "ASSIGN":
            print(f"{instruction[3]} = {instruction[1]}")
        elif op in ["ADD", "SUB", "MUL", "DIV", ">", "<", "<=", ">=", "==", "!="]:
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
            print(f"ifFalse {instruction[1]} goto {instruction[3]}")
        elif op == "GOTO":
            print(f"goto {instruction[1]}")
        elif op == "LABEL":
            print(f"{instruction[1]}:")
        else:
            print(f"UNHANDLED_INSTRUCTION: {instruction}")
