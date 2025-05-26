import re
import os


class Instruction:
    def __init__(self, raw_line):
        self.raw_line = raw_line.strip()
        self.type = None
        self.target = None
        self.op1 = None
        self.operator = None
        self.op2 = None
        self.label = None
        self.condition_var = None
        self.jump_target = None
        self.is_removed = False
        self._parse()

    def _parse(self):
        line = self.raw_line
        match = re.match(r"^(L\d+):$", line)
        if match:
            self.type = "label"
            self.label = match.group(1)
            return
        match = re.match(r"^ifFalse (\w+) goto (L\d+)$", line)
        if match:
            self.type = "ifFalse"
            self.condition_var = match.group(1)
            self.jump_target = match.group(2)
            return
        match = re.match(r"^goto (L\d+)$", line)
        if match:
            self.type = "goto"
            self.jump_target = match.group(1)
            return
        match = re.match(
            r"^(\w+)\s*=\s*([a-zA-Z_][\w]*|\d+(?:\.\d+)?|True|False)\s*([+\-*/]|<=|>)\s*([a-zA-Z_][\w]*|\d+(?:\.\d+)?|True|False)$",
            line,
        )
        if match:
            self.type = "expression_assignment"
            self.target = match.group(1)
            self.op1 = match.group(2)
            self.operator = match.group(3)
            self.op2 = match.group(4)
            return
        match = re.match(
            r"^(\w+)\s*=\s*([a-zA-Z_][\w]*|\d+(?:\.\d+)?|True|False)$", line
        )
        if match:
            self.type = "simple_assignment"
            self.target = match.group(1)
            self.op1 = match.group(2)
            return
        raise ValueError(f"Could not parse instruction: {line}")

    def __str__(self):
        if self.is_removed:
            return ""
        if self.type == "label":
            return f"{self.label}:"
        if self.type == "ifFalse":
            return f"ifFalse {self.condition_var} goto {self.jump_target}"
        if self.type == "goto":
            return f"goto {self.jump_target}"
        if self.type == "expression_assignment":
            return f"{self.target} = {self.op1} {self.operator} {self.op2}"
        if self.type == "simple_assignment":
            return f"{self.target} = {self.op1}"
        return self.raw_line


def is_numeric(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def evaluate_expression(op1, operator, op2):
    try:
        val1 = (
            float(op1)
            if is_numeric(op1)
            else (True if op1 == "True" else (False if op1 == "False" else None))
        )
        val2 = (
            float(op2)
            if is_numeric(op2)
            else (True if op2 == "True" else (False if op2 == "False" else None))
        )
        if val1 is None or val2 is None:
            return None
        if operator == "+":
            return str(val1 + val2)
        if operator == "-":
            return str(val1 - val2)
        if operator == "*":
            return str(val1 * val2)
        if operator == "/":
            if val2 == 0:
                return None
            return str(val1 / val2)
        if operator == "<=":
            return str(val1 <= val2)
        if operator == ">":
            return str(val1 > val2)
        return None
    except Exception:
        return None


def optimize_code(code_string):
    lines = [line.strip() for line in code_string.strip().split("\n") if line.strip()]
    instructions = [Instruction(line) for line in lines]
    optimization_log = []
    constant_propagation_map = {}
    copy_propagation_map = {}
    # Times variables are assigned to detect mutability
    assign_counts = {}
    # First pass: count assignments per variable
    for instr in instructions:
        if instr.type in ("simple_assignment", "expression_assignment"):
            assign_counts[instr.target] = assign_counts.get(instr.target, 0) + 1
    # Variables assigned more than once are mutable, so can't be constants
    mutable_vars = {var for var, count in assign_counts.items() if count > 1}
    for i, instr in enumerate(instructions):
        if instr.is_removed:
            continue
        # Propagate constants or copies for operands before processing
        if instr.type == "expression_assignment":
            if instr.op1 in constant_propagation_map and instr.op1 not in mutable_vars:
                old = instr.op1
                instr.op1 = constant_propagation_map[instr.op1]
                optimization_log.append(
                    f"Constant propagated: '{old}' -> '{instr.op1}' in instruction {i+1}"
                )
            elif instr.op1 in copy_propagation_map:
                old = instr.op1
                instr.op1 = copy_propagation_map[instr.op1]
                optimization_log.append(
                    f"Copy propagated: '{old}' -> '{instr.op1}' in instruction {i+1}"
                )
            if instr.op2 in constant_propagation_map and instr.op2 not in mutable_vars:
                old = instr.op2
                instr.op2 = constant_propagation_map[instr.op2]
                optimization_log.append(
                    f"Constant propagated: '{old}' -> '{instr.op2}' in instruction {i+1}"
                )
            elif instr.op2 in copy_propagation_map:
                old = instr.op2
                instr.op2 = copy_propagation_map[instr.op2]
                optimization_log.append(
                    f"Copy propagated: '{old}' -> '{instr.op2}' in instruction {i+1}"
                )
            # Fold only if operands are constants and target var NOT mutable
            if (
                (is_numeric(instr.op1) or instr.op1 in ("True", "False"))
                and (is_numeric(instr.op2) or instr.op2 in ("True", "False"))
                and instr.target not in mutable_vars
            ):
                result = evaluate_expression(instr.op1, instr.operator, instr.op2)
                if result is not None:
                    optimization_log.append(
                        f"Constant folded: '{instr.op1} {instr.operator} {instr.op2}' -> '{result}' in instruction {i+1}"
                    )
                    instr.type = "simple_assignment"
                    instr.op1 = result
                    instr.operator = None
                    instr.op2 = None
                    constant_propagation_map[instr.target] = result
                    if instr.target in copy_propagation_map:
                        del copy_propagation_map[instr.target]
                    continue
        elif instr.type == "simple_assignment":
            original_op1 = instr.op1
            # Only treat as constant if source is constant and target is not mutable
            if (
                is_numeric(original_op1) or original_op1 in ("True", "False")
            ) and instr.target not in mutable_vars:
                constant_propagation_map[instr.target] = original_op1
                optimization_log.append(
                    f"Constant propagated: '{instr.target}' assigned constant '{original_op1}' in instruction {i+1}"
                )
                if instr.target in copy_propagation_map:
                    del copy_propagation_map[instr.target]
            elif (
                original_op1 in constant_propagation_map
                and original_op1 not in mutable_vars
                and instr.target not in mutable_vars
            ):
                instr.op1 = constant_propagation_map[original_op1]
                constant_propagation_map[instr.target] = instr.op1
                optimization_log.append(
                    f"Constant propagated: '{original_op1}' -> '{instr.op1}' for '{instr.target}' in instruction {i+1}"
                )
                if instr.target in copy_propagation_map:
                    del copy_propagation_map[instr.target]
            elif (
                original_op1 in copy_propagation_map
                and instr.target not in mutable_vars
            ):
                instr.op1 = copy_propagation_map[original_op1]
                copy_propagation_map[instr.target] = instr.op1
                optimization_log.append(
                    f"Copy propagated: '{original_op1}' -> '{instr.op1}' for '{instr.target}' in instruction {i+1}"
                )
                if instr.target in constant_propagation_map:
                    del constant_propagation_map[instr.target]
            else:
                copy_propagation_map[instr.target] = original_op1
                optimization_log.append(
                    f"Copy relationship established: '{instr.target}' copies '{original_op1}' in instruction {i+1}"
                )
                if instr.target in constant_propagation_map:
                    del constant_propagation_map[instr.target]
        elif instr.type == "ifFalse":
            orig_var = instr.condition_var
            if orig_var in constant_propagation_map and orig_var not in mutable_vars:
                instr.condition_var = constant_propagation_map[orig_var]
                optimization_log.append(
                    f"Constant propagated: '{orig_var}' -> '{instr.condition_var}' in instruction {i+1}"
                )
                # Only simplify jumps if condition is literal and target not mutable
                if instr.condition_var.lower() == "false":
                    instr.type = "goto"
                    instr.condition_var = None
                    optimization_log.append(
                        f"Conditional jump simplified: 'ifFalse False' -> 'goto {instr.jump_target}' in instruction {i+1}"
                    )
                elif instr.condition_var.lower() == "true":
                    instr.is_removed = True
                    optimization_log.append(
                        f"Dead code eliminated: 'ifFalse True' removed in instruction {i+1}"
                    )
            elif orig_var in copy_propagation_map:
                instr.condition_var = copy_propagation_map[orig_var]
                optimization_log.append(
                    f"Copy propagated: '{orig_var}' -> '{instr.condition_var}' in instruction {i+1}"
                )
        # Invalidate const/copy if assigned var is mutable or re-assigned non-constant
        if instr.type in ("expression_assignment", "simple_assignment"):
            if instr.target in mutable_vars:
                if instr.target in constant_propagation_map:
                    del constant_propagation_map[instr.target]
                    optimization_log.append(
                        f"Variable '{instr.target}' marked mutable; constant invalidated at instruction {i+1}"
                    )
                if instr.target in copy_propagation_map:
                    del copy_propagation_map[instr.target]
                    optimization_log.append(
                        f"Variable '{instr.target}' marked mutable; copy invalidated at instruction {i+1}"
                    )
    optimized_code = "\n".join(
        str(instr) for instr in instructions if not instr.is_removed
    )
    return optimized_code, optimization_log


def main():
    # Construct paths relative to the current script's location
    script_dir = os.path.dirname(__file__)

    input_path = os.path.join(script_dir, "..", "3. ICG", "icg_output.txt")
    output_code_path = os.path.join(script_dir, "optimized_code.txt")
    output_log_path = os.path.join(script_dir, "optimization_log.txt")

    # Read input code from file
    with open(input_path, "r") as f:
        input_code = f.read()

    optimized_code, log = optimize_code(input_code)

    with open(output_code_path, "w") as f:
        f.write(optimized_code)

    with open(output_log_path, "w") as f:
        for entry in log:
            f.write(entry + "\n")

    print(
        f"Optimization complete.\nOptimized code saved to '{output_code_path}'.\nLog saved to '{output_log_path}'."
    )


if __name__ == "__main__":
    main()
