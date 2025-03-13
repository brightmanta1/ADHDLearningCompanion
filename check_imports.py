#!/usr/bin/env python
"""
Скрипт для проверки опечаток в импортах.
"""

import os
import re


def check_files_for_typo(directory, typo="sqlachemy", correct="sqlalchemy"):
    """
    Проверяет все Python файлы в директории на наличие опечатки.

    Args:
        directory: Директория для проверки
        typo: Опечатка для поиска
        correct: Правильное написание
    """
    pattern = re.compile(r"import\s+" + typo + r"\b|from\s+" + typo + r"\b")

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        if matches:
                            print(f"Found typo in {file_path}:")
                            for match in matches:
                                print(f"  {match}")

                            # Исправляем опечатку
                            corrected = content.replace(typo, correct)
                            with open(file_path, "w", encoding="utf-8") as f_write:
                                f_write.write(corrected)
                            print(f"  Fixed in {file_path}")
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")


if __name__ == "__main__":
    check_files_for_typo("ADHDLOL")
    print("Finished checking files.")
