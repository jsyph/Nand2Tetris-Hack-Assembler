from tqdm import tqdm
import click
from pathlib import Path
from typing import List

A0_ALU_OPERATIONS = {
    "0": "101010",
    "1": "111111",
    "-1": "111010",
    "D": "001100",
    "A": "110000",
    "!D": "001101",
    "!A": "110001",
    "-D": "001111",
    "-A": "110011",
    "D+1": "011111",
    "A+1": "110111",
    "D-1": "001110",
    "A-1": "110010",
    "D+A": "000010",
    "D-A": "010011",
    "A-D": "000111",
    "D&A": "000000",
    "D|A": "010101",
}

A1_ALU_OPERATIONS = {
    "M": "110000",
    "!M": "110001",
    "-M": "110011",
    "M+1": "110111",
    "M-1": "110010",
    "D+M": "000010",
    "D-M": "010011",
    "M-D": "000111",
    "D&M": "000000",
    "D|M": "010101",
}

DEST = {
    "": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "AMD": "111",
}

JUMP = {
    "": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}

BUILTIN_SYMBOLS = {
    "R0": "0",
    "R1": "1",
    "R2": "2",
    "R3": "3",
    "R4": "4",
    "R5": "5",
    "R6": "6",
    "R7": "7",
    "R8": "8",
    "R9": "9",
    "R10": "10",
    "R11": "11",
    "R12": "12",
    "R13": "13",
    "R14": "14",
    "R15": "15",
    "SCREEN": "16384",
    "KBD": "24576",
    "SP": "0",
    "LCL": "1",
    "ARG": "2",
    "THIS": "3",
    "THAT": "4",
}


def remove_non_code(lines: List[str]) -> List[str]:
    res = []
    for line in lines:
        value = line.split("//")[0]
        value = value.strip()

        if value == "":
            continue

        res.append(value)

    return res


def process_symbols(lines: List[str]) -> List[str]:
    symbol_map = BUILTIN_SYMBOLS

    # first, process labels
    line_no = -1
    for line in lines:
        line_no += 1

        if line[0] == "(":
            symbol = line.lstrip("(").rstrip(")")
            symbol_map[symbol] = str(line_no)
            line_no -= 1

    # second, process variables
    variable_address = 16
    for line in lines:
        if line[0] == "@":
            # check if number
            if line[1:].isdigit():
                continue

            # check if in symbol map
            if symbol_map.get(line[1:]):
                continue

            # is not in symbol map
            symbol_map[line[1:]] = str(variable_address)
            variable_address += 1

    # finally, put it all together
    res = []
    for line in lines:
        if line[0] == "@":
            # is normal number, do nothing
            if line[1:].isdigit():
                res.append(line)
                continue

            # is symbol
            value = symbol_map[line[1:]]
            res.append(f"@{value}")
            continue

        # line is label, do nothing
        if line[0] == "(":
            continue

        res.append(line)
    return res


def translate_code(lines: List[str]) -> List[str]:
    res = []

    for line in lines:
        if line[0] == "@":
            num = int(line[1:])
            res.append(f"0{num:015b}")
            continue

        dest = ""
        if "=" in line:
            dest = line.split("=")[0]
        dest_bin = DEST[dest]

        jump = ""
        if ";" in line:
            jump = line.split(";")[1]
        jump_bin = JUMP[jump]

        comp = line
        if "=" in line:
            comp = line.split("=")[1]
        if ";" in line:
            comp = comp.split(";")[0]

        if "M" in comp:
            a = 1
            comp_bin = A1_ALU_OPERATIONS[comp]
        else:
            a = 0
            comp_bin = A0_ALU_OPERATIONS[comp]

        res.append(f"111{a}{comp_bin}{dest_bin}{jump_bin}")

    return res


@click.command()
@click.argument("target")
@click.option("--output", "-o", help="Output file path. Defaults to TARGET filename + hack file extension")
def main(target: str, output: str):
    target_path = Path(target)
    if not target_path.exists():
        click.echo(f"Path `{target}` is not found.")
        return

    with open(target) as file:
        lines = file.readlines()

    pbar = tqdm(total=3)

    pbar.set_description(f"{'Removing Non-Code Elements': <26}")
    filtered_code = remove_non_code(lines)
    pbar.update(1)

    pbar.set_description(f"{'Processing Symbols': <26}")
    processed_symbols = process_symbols(filtered_code)
    pbar.update(1)

    pbar.set_description(f"{'Translating to Binary': <26}")
    translated_code = translate_code(processed_symbols)
    pbar.update(1)
    pbar.close()

    if not output:
        output = target_path.name.split(".")[0] + ".hack"

    with open(output, "w") as file:
        file.write("\n".join(translated_code))

    click.echo("Done")


if __name__ == "__main__":
    main()
