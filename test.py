from __future__ import annotations

import os
import subprocess
import sys
import random
import shutil
import time

from argparse import ArgumentParser
from enum import Enum, auto
from glob import glob
from typing import NamedTuple, Optional, Union
import re

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

TEST_ROUND = 1
TIMEOUT = 120

# NOTE: 在这里修改你的编译器路径和参数。此处的默认值对应着gcc
compiler_path = "riscv64-unknown-elf-gcc"
compiler_args = "-O2 -march=rv64gc -mabi=lp64f -S"
# compiler_args = "-O2 -march=rv32gc -mabi=ilp32f -S"

# 调用gcc进行链接的参数
gcc_args_rv64 = "-march=rv64gc -mabi=lp64f"
gcc_args_rv32 = "-march=rv32gc -mabi=ilp32f"
gcc_args = gcc_args_rv64


class Config(NamedTuple):
    compiler: str
    testcases: str
    compiler_args: str
    tempdir: str
    parallel: bool
    timing: bool


class Result(Enum):
    LINKER_ERROR = auto()
    PASSED = auto()
    WRONG_ANSWER = auto()
    TIME_LIMIT_EXCEEDED = auto()
    GCC_ERROR = auto()

def arithmetic_mean(numbers):
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def get_config(argv: list[str]) -> Config:
    parser = ArgumentParser('performance.py')
    parser.add_argument('-t', '--testcases', metavar='<testcases>', help='path to the directory containing testcases')
    parser.add_argument('-p', '--parallel', action='store_true', default=False, help='run parallely')
    parser.add_argument('-b', '--benchmark', action='store_true', default=False, help='benchmark time')
    index: int
    try:
        index = argv.index('--')
    except ValueError:
        index = len(argv)
    args = parser.parse_args(argv[:index])
    return Config(compiler=compiler_path,
                  testcases=args.testcases,
                  compiler_args=compiler_args,
                  tempdir='temp',
                  parallel=args.parallel,
                  timing=args.benchmark,
                  )


def get_testcases(config: Config) -> list[str]:
    testcases = [os.path.splitext(os.path.basename(file))[0]
                 for file in glob(os.path.join(config.testcases, '*.c'))]
    testcases.sort()
    return testcases


def get_answer(file: str) -> tuple[list[str], int]:
    content = [line.strip() for line in open(file).read().splitlines()]
    return content[:-1], int(content[-1])


def get_time(file: str) -> Optional[int]:
    content = open(file).read().splitlines()
    if not content:
        return None
    content = content[-1]
    pattern = r'TOTAL:\s*(\d+)H-(\d+)M-(\d+)S-(\d+)us'
    matches = re.match(pattern, content)
    h, m, s, us = map(int, (matches.group(1), matches.group(2), matches.group(3), matches.group(4)))
    return ((h * 60 + m) * 60 + s) * 1_000_000 + us


def run(
    workdir: str,
    assembly: str,
    input: str,
    answer_exitcode: int,
    answer_content: str,
    round: int = 1,
    timing: bool = False,
) -> Union[Result, float]:
    name_body = os.path.basename(assembly).split('.')[0]
    executable = os.path.join(workdir, name_body + '.exec')
    output = os.path.join(workdir, name_body + '.stdout')
    outerr = os.path.join(workdir, name_body + '.stderr')
    if os.system(f'riscv64-unknown-elf-gcc {gcc_args} {assembly} testcases/lib/libsysy.c'
                 f' -o {executable}') != 0:
        return Result.LINKER_ERROR
    total_time = 0
    for _ in range(round):
        start_time = time.time()
        proc = subprocess.Popen(
            executable,
            stdin=open(input) if os.path.exists(input) else None,
            stdout=open(output, 'w'), stderr=open(outerr, 'w'))
        try:
            proc.wait(TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            return Result.TIME_LIMIT_EXCEEDED
        end_time = time.time()
        output_content = [line.strip()
                          for line in open(output).read().splitlines()]
        if proc.returncode != answer_exitcode \
                or output_content != answer_content:
            return Result.WRONG_ANSWER
        # if round > 1:
        #     print('.', end='', flush=True)
        t = end_time - start_time
        if t is None:
            timing = False
        else:
            total_time += t
    if timing:
        return total_time * 1_000 / round
    else:
        return Result.PASSED


def run_gcc(
    workdir: str,
    assembly: str,
    input: str,
    round: int = 1,
):
    name_body = os.path.basename(assembly).split('.')[0]
    executable = os.path.join(workdir, name_body + '.exec')
    output = os.path.join(workdir, name_body + '.stdout')
    outerr = os.path.join(workdir, name_body + '.stderr')
    if os.system(f'riscv64-unknown-elf-gcc {gcc_args} {assembly} testcases/lib/libsysy.c'
                 f' -o {executable}') != 0:
        return Result.LINKER_ERROR
    total_time = 0
    for _ in range(round):
        start_time = time.time()
        proc = subprocess.Popen(
            executable,
            stdin=open(input) if os.path.exists(input) else None,
            stdout=open(output, 'w'), stderr=open(outerr, 'w'))
        try:
            proc.wait(TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            return Result.TIME_LIMIT_EXCEEDED
        end_time = time.time()
        output_content = [line.strip()
                          for line in open(output).read().splitlines()]
        # if round > 1:
        #     print('.', end='', flush=True)
        t = end_time - start_time
        total_time += t
            
    return (total_time * 1_000 / round, proc.returncode, output_content)


def test(config: Config, testcase: str, score_callback = None) -> bool:
    source = os.path.join(config.testcases, f'{testcase}.c')
    input = os.path.join(config.testcases, f'{testcase}.in')


    ident = '%04d' % random.randint(0, 9999)
    assembly = os.path.join(config.tempdir, f'{testcase}-{ident}.s')
    gcc_assembly = os.path.join(config.tempdir, f'{testcase}-gcc.s')
    
    if os.system(f'riscv64-unknown-elf-gcc -O2 -S {gcc_args}' f' {source} -o {gcc_assembly} ') == 0:
        gcc_result, answer_exitcode, answer_content = run_gcc(config.tempdir, gcc_assembly, input, TEST_ROUND)
    else:
        gcc_result = Result.GCC_ERROR
    
    # NOTE: 你可以在这里修改调用你的编译器的方式
    command = (f'{config.compiler} {config.compiler_args} {source}'
                f' -o {assembly}')
    proc = subprocess.Popen(command, shell=True)
    try:
        proc.wait(TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        print(testcase, '\033[0;31mCompiler TLE\033[0m')
        return False
    if proc.returncode != 0:
        print(testcase, '\033[0;31mCompiler Error\033[0m')
        return False
    result = run(config.tempdir, assembly, input, answer_exitcode, answer_content, TEST_ROUND, config.timing)
    if result == Result.LINKER_ERROR:
        print(testcase, '\033[0;31mLinker Error\033[0m')
        return False
    elif result == Result.WRONG_ANSWER:
        print(testcase, '\033[0;31mWrong Answer\033[0m')
        return False
    elif result == Result.TIME_LIMIT_EXCEEDED:
        print(testcase, '\033[0;31mTime Limit Exceeded\033[0m')
        return False
    else:
        runtime = result
    # print(' ', end='')
    if not isinstance(runtime, float) or runtime == 0:
        print(testcase, '\033[0;32mPassed\033[0m')
        return True
    
    if isinstance(gcc_result, Result):
        print(testcase, '\033[0;31mGCC Error\033[0m')
    else:
        print(testcase, f'\033[0;32m{runtime :.3f}ms / {gcc_result :.3f}ms'
                f' => {gcc_result / runtime :.2%}\033[0m')
        
        score = min(gcc_result / runtime * 125, 100)
        if score_callback is not None:
            score_callback(testcase, score)
    return True


if __name__ == '__main__':
    config = get_config(sys.argv[1:])
    testcases = get_testcases(config)

    if os.path.exists(config.tempdir):
        shutil.rmtree(config.tempdir)
    os.mkdir(config.tempdir)

    score_info = []
    scores_lock = Lock()
    def add_score(testcase, score):
        scores_lock.acquire()
        score_info.append((testcase, score))
        scores_lock.release()
    score_callback = add_score if config.timing else None

    failed = []
    if config.parallel:
        futures = []
        f = lambda t: (t, test(config, t, score_callback))
        with ThreadPoolExecutor() as executor:
            for testcase in testcases:
                futures.append(executor.submit(f, testcase))
            for future in as_completed(futures):
                testcase, ok = future.result()
                if not ok:
                    failed.append(testcase)
        failed.sort()
    else:
        for testcase in testcases:
            if not test(config, testcase, score_callback):
                failed.append(testcase)
    info = '\033[0;34m[info]\033[0m {}'
    if not failed:
        print(info.format('All Passed'))

        if config.timing:
            print('scores of testcases:')
            for testcase, score in score_info:
                print(testcase, score)

            mean_score = arithmetic_mean([t[1] for t in score_info])
            print("final score:", mean_score)
    else:
        for testcase in failed:
            print(info.format(f'`{testcase}` Failed'))
