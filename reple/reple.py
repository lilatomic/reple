#!/usr/bin/env python3

from __future__ import unicode_literals, annotations

import argparse
import json
import os
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from operator import add
from typing import List, Dict, Tuple

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import style_from_pygments_cls
from pygments.styles import get_style_by_name


class CompilationEnvironment:
    def __init__(self, compile, compile_args, user_cargs):
        self._compile = compile
        self.compile_args = defaultdict(str, compile_args)
        self.user_cargs = user_cargs

        assert(isinstance(self._compile, str))
        assert(isinstance(self.compile_args, dict))
        assert('{bin_fname}' in self._compile)
        assert('{code_fname}' in self._compile)

        self.code_suffix = self.compile_args['code_suffix']
        self.bin_suffix = self.compile_args['bin_suffix']

    # Construct a compile line
    def get_compile_line(self, code_fname, bin_fname):
        if '{user_cargs}' in self._compile:
            return self._compile.format(code_fname=code_fname,
                    bin_fname=bin_fname, user_cargs=self.user_cargs,
                    **self.compile_args)
        else:
            return self._compile.format(code_fname=code_fname,
                    bin_fname=bin_fname, **self.compile_args)

    # Given a code string and file name,
    # attempt to compile
    def compile(self, code_string, name, output_dir):
        code_fname = output_dir + name + self.code_suffix
        bin_fname = output_dir + name + self.bin_suffix
        compile_line = self.get_compile_line(code_fname, bin_fname)

        f = open(code_fname, 'w')
        f.write(code_string)
        f.close()

        os.system(compile_line)

        if os.path.isfile(bin_fname):
            return bin_fname
        else:
            return None

class RuntimeEnvironment:
    def __init__(self, runcommand, user_rargs):
        self.runcommand = runcommand
        self.user_rargs = user_rargs

    def get_run_line(self, bin_fname, output_fname):
        if '{user_rargs}' in self.runcommand:
            runcommand = self.runcommand.format(bin_fname=bin_fname,
                    user_rargs=self.user_rargs)
        else:
            runcommand = self.runcommand.format(bin_fname=bin_fname)
        return ' '.join([runcommand, bin_fname, '>', output_fname, '2>&1'])

    def run(self, bin_fname, output_fname):
        run_line = self.get_run_line(bin_fname, output_fname)
        os.system(run_line)

class CodeTemplate:
    def __init__(self, template, template_args):
        self.template = template
        self.template_args = template_args

        self.line_epilogue = self.template_args['line_epilogue']
        self.output_processor = self.template_args.get('output_processor')

        assert('prolog_lines' in self.template)
        assert('repl_lines' in self.template)

    def generate_code(self, prolog_lines, repl_lines):
        prolog_lines = '\n'.join(prolog_lines)
        repl_lines = ('\n' + self.line_epilogue + '\n').join(repl_lines)
        return self.template.format(prolog_lines=prolog_lines,
                repl_lines=repl_lines, **self.template_args)

    def make_output_processor(self) -> OutputProcessor:
        name_to_output_processor = {
               "simple": SimpleOutputProcessor,
               "demarcated": DemarcatedOutputProcessor,
       }
        if self.output_processor and self.output_processor.get("type"):
            return name_to_output_processor[self.output_processor["type"]](**self.output_processor)
        else:
            return SimpleOutputProcessor()


class OutputProcessor(ABC):
    def __init__(self, **_):
        ...

    """Process the output of executions to identify which input the lines should be associated with"""
    @abstractmethod
    def get_new_lines(self, executions, output_fname_nonce) -> List[str]:
        ...

    def wrap_lines(self, repl_lines: List[str], prolog_lines: List[str], output_fname_nonce: int) -> Tuple[List[str], List[str]]:
        return repl_lines, prolog_lines


class SimpleOutputProcessor(OutputProcessor):
    """Determine new lines by tracking the number of lines returned"""
    def get_new_lines(self, executions, output_fname_nonce) -> List[str]:
        nnew_lines = len(executions[output_fname_nonce]) - len(
            executions[output_fname_nonce - 1])
        if nnew_lines > 0:
            return executions[output_fname_nonce][-nnew_lines:]
        else:
            return []


class DemarcatedOutputProcessor(OutputProcessor):
    """Determine new lines by injecting fence lines"""
    start_str = "start:"
    end_str = "end:"

    def __init__(self, demarcater_template: str, supported=None, command_symbol="¶", **_):
        super().__init__(**_)
        self.demarcater_template = demarcater_template
        self.command_symbol = command_symbol
        if supported is None:
            supported = {
                "prolog": False,
                "repl": True
            }
        self.supported = supported

    def demarcate_lines(self, lines: List[str], output_fname_nonce: int) -> List[str]:
        if not lines or lines == ['']:
            return lines

        start = self.demarcater_template.format(
            demarcater=f'{self.command_symbol}{self.start_str}{output_fname_nonce}{self.command_symbol}'
        )
        end = self.demarcater_template.format(
            demarcater=f'{self.command_symbol}{self.end_str}{output_fname_nonce}{self.command_symbol}'
        )
        return [start] + lines + [end]

    def undemarcate_lines(self, lines: List[str]) -> Dict[int, List[str]]:
        current_nonce = None
        undemarcated_lines = defaultdict(list)

        def parse(line: str):
            nonlocal current_nonce

            command_start_index = line.find(self.command_symbol)
            if command_start_index == 0:  # at a command
                end_command_index = line.find(self.command_symbol, command_start_index+1)
                command = line[1:end_command_index]
                if command.startswith(self.start_str):
                    current_nonce = int(command.split(self.start_str)[1])
                elif command.startswith(self.end_str):
                    current_nonce = None
                remaining = line[end_command_index + 1:]
            elif command_start_index != -1:  # command appears later on the line
                undemarcated_lines[current_nonce].append(line[:command_start_index])
                remaining = line[command_start_index:]
            else:  # no command left on the line
                undemarcated_lines[current_nonce].append(line)
                remaining = None
            return remaining

        for line in lines:
            while line:
                line = parse(line)

        return undemarcated_lines

    def get_new_lines(self, executions, output_fname_nonce) -> List[str]:
        return self.undemarcate_lines(executions[output_fname_nonce])[output_fname_nonce]

    def wrap_lines(self, repl_lines: List[str], prolog_lines: List[str], output_fname_nonce: int) -> Tuple[List[str], List[str]]:
        if self.supported.get('repl'):
            wrapped_repl_lines = self.demarcate_lines(repl_lines, output_fname_nonce)
        else:
            wrapped_repl_lines = repl_lines

        if self.supported.get('prolog'):
            wrapped_prolog_lines = self.demarcate_lines(prolog_lines, output_fname_nonce)
        else:
            wrapped_prolog_lines = prolog_lines

        return wrapped_repl_lines, wrapped_prolog_lines


class Reple:
    def __init__(self, comp_env, runtime_env, code_templ, lexer=None,
            output_dir='/tmp/repl/', output_name='repl',
            enclosers = [('{', '}')], prolog_char='$'):
        assert(isinstance(comp_env, CompilationEnvironment))
        assert(isinstance(runtime_env, RuntimeEnvironment))
        assert(isinstance(code_templ, CodeTemplate))
        self.comp_env = comp_env
        self.runtime_env = runtime_env
        self.code_templ = code_templ

        self.lexer = None if lexer is None else PygmentsLexer(lexer)
        self.output_dir = output_dir

        self.prolog_lines = []
        self.repl_lines = []
        self.in_prolog = False

        self.executions = defaultdict(list)

        self.output_name = output_name
        self.output_fname_nonce = 0

        self.enclosers = enclosers
        self.prolog_char = prolog_char

        self.style = get_style_by_name('native')
        self.history = InMemoryHistory()
        self.output_processor = self.code_templ.make_output_processor()

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        os.system(' '.join(['rm -rf', self.output_dir + '*']))

    def count_enclosers(self, line, start, stop):
        return line.count(start) - line.count(stop)

    def get_fname(self):
        return self.output_name + str(self.output_fname_nonce)

    def append_lines(self, prolog_lines: List[str], repl_lines: List[str]):
        if prolog_lines:
            self.prolog_lines.extend(prolog_lines)
        if repl_lines:
            self.repl_lines.extend(repl_lines)

    def execute(self, repl_line, prolog_line=''):
        wrapped_repl_lines, wrapped_prolog_lines = self.output_processor.wrap_lines(
            [repl_line], [prolog_line], self.output_fname_nonce
        )

        cur_prolog_lines = self.prolog_lines + wrapped_prolog_lines
        cur_repl_lines = self.repl_lines + wrapped_repl_lines

        code = self.code_templ.generate_code(cur_prolog_lines, cur_repl_lines)
        bin_fname = self.comp_env.compile(code, self.get_fname(), self.output_dir)

        if bin_fname:
            output_fname = bin_fname + '.out'
            self.append_lines(wrapped_prolog_lines, wrapped_repl_lines)
            self.runtime_env.run(bin_fname, output_fname)

            self.executions[self.output_fname_nonce] = open(output_fname, 'r').readlines()
            new_lines = self.output_processor.get_new_lines(self.executions, self.output_fname_nonce)
            if len(new_lines) > 0:
                for l in [line.strip() for line in new_lines]:
                    print(l)
            self.output_fname_nonce += 1

    def process_line(self, line, repl_lines, prolog_lines, encloser_counts):
        if line == 'clear':
            self.prolog_lines.clear()
            self.repl_lines.clear()
            self.executions.clear()
        elif line == 'quit':
            return False
        elif len(line) <= 0:
            pass
        elif line[0] == self.prolog_char:
            if self.in_prolog:
                prolog_line = '\n'.join(prolog_lines)
                self.execute('', prolog_line)
                self.in_prolog = False
                prolog_lines.clear()
                self.process_line(line[1:], repl_lines, prolog_lines,
                    encloser_counts)
            else:
                self.in_prolog = True
                self.process_line(line[1:], repl_lines, prolog_lines,
                    encloser_counts)
        elif line[-1] == self.prolog_char:
            if self.in_prolog:
                prolog_lines.append(line[:-1])
                prolog_line = '\n'.join(prolog_lines)
                self.execute('', prolog_line)
                self.in_prolog = False
                prolog_lines.clear()
            else:
                self.process_line(line[:-1], repl_lines, prolog_lines,
                    encloser_counts)
                self.process_line(line[-1:], repl_lines, prolog_lines,
                    encloser_counts)
        elif self.in_prolog:
            prolog_lines.append(line)
        else:
            line_enclosers = [self.count_enclosers(line, x[0], x[1]) for x in self.enclosers]
            encloser_counts[:] = map(add, encloser_counts, line_enclosers)
            if sum(encloser_counts) <= 0:
                repl_lines.append(line)
                repl_line = '\n'.join(repl_lines)
                self.execute(repl_line)
                repl_lines.clear()
                encloser_counts = [0] * len(self.enclosers)
            else:
                repl_lines.append(line)
        return True

    def run(self):
        repl_lines = []
        prolog_lines = []
        encloser_counts = [0] * len(self.enclosers)
        while True:
            try:
                line = prompt('> ', lexer=self.lexer,
                              style=style_from_pygments_cls(get_style_by_name('native')),
                              history=self.history)
            except:
                break
            stat = self.process_line(line.rstrip(), repl_lines, prolog_lines,
                    encloser_counts)
            if not stat:
                break

def configure_terminal_opts(terminal_opts):
    rterm_opts= {}
    if 'lexer_class' in terminal_opts:
        import importlib
        lexer_class = importlib.import_module(terminal_opts['lexer_class'])
        lexer_fn = getattr(lexer_class, terminal_opts['lexer_fn'])
        rterm_opts['lexer'] = lexer_fn
    if 'prolog_char' in terminal_opts:
        rterm_opts['prolog_char'] = terminal_opts['prolog_char']
    if 'enclosers' in terminal_opts:
        rterm_opts['enclosers'] = [tuple(x) for x in terminal_opts['enclosers']]
    return rterm_opts

def get_config_fname(args):
    reple_path = os.path.dirname(os.path.realpath(__file__))
    fname = reple_path + '/configs/'
    if args.fname is not None:
        fname += args.fname
        return fname
    else:
        fname = reple_path + '/config/reple/' + args.env + '.json'
        if os.path.isfile(fname):
            return fname
        else:
            fname = reple_path + '/configs/' + args.env + '.json'
            return fname
    return fname


def reple_from_config(config, user_cargs, user_rargs):
    comp_env = CompilationEnvironment(config['compile'], config['compile_args'],
                                      user_cargs)
    runtime_env = RuntimeEnvironment(config['run'], user_rargs)
    code_templ = CodeTemplate(config['template'], config['template_args'])
    terminal_opts = configure_terminal_opts(config['terminal_opts'])
    reple = Reple(comp_env, runtime_env, code_templ, **terminal_opts)
    return reple


def run_reple(cmd_args):
    parser = argparse.ArgumentParser(description='reple, an interactive REPL \
            for executable-driven software toolchains.')
    config_group = parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('-env', dest='env', type=str, help='reple\
            environment to use.  See $INSTALL_DIR/configs for included\
            environments.')
    config_group.add_argument('-f', dest='fname', type=str, help='File name for\
            the json config file')
    parser.add_argument('--rargs', dest='user_rargs', type=str, help='User\
            options to forward at runtime', default='')
    parser.add_argument('--cargs', dest='user_cargs', type=str, help='User\
            options to forward at compile time', default='')
    args = parser.parse_args(cmd_args)

    fname = get_config_fname(args)
    config = json.load(open(fname, 'r'))

    assert(not (args.user_rargs != '' and '{user_rargs}' not in config['run']))
    assert(not (args.user_cargs != '' and '{user_cargs}' not in config['compile']))

    reple = reple_from_config(config, args.user_cargs, args.user_rargs)

    reple.run()


if __name__ == '__main__':
    run_reple(sys.argv[1:])
