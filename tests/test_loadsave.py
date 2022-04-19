from reple.reple import Reple, RepleState, CompilationEnvironment, RuntimeEnvironment, CodeTemplate


prolog_char = "%"


def default_reple() -> Reple:
    return Reple(
        CompilationEnvironment(
            "{compiler} {code_fname} {bin_fname}",
            {
                "compiler": "cp",
                "code_suffix": ".sh"
            },
            {},
        ),
        RuntimeEnvironment("bash {bin_fname}", {}),
        CodeTemplate(
            "{template_begin}\n#--\n{prolog_lines}\n#--\n{repl_lines}\n",
            {
                "template_begin": "#! /bin/bash",
                "line_epilogue": ""
            },
        ),
        prolog_char=prolog_char
    )


def prologify(cmd: str, prolog_char: str = prolog_char):
    return prolog_char + cmd + prolog_char


class TestLoadSave:
    def test_cyclic(self):
        """Test that state can be restored and dumped and comes back the same"""
        reple = default_reple()
        state = RepleState(
            ["prolog0", "prolog1"],
            ["repl0", "repl1"]
            )

        reple.load_state(state)
        result = reple.dump_state()

        assert result == state

    def test_adding_repl_appear_in_state(self):
        reple = default_reple()
        cmd = "echo '5'"
        reple.process_line(cmd, [], [], [])

        state = reple.dump_state()
        assert state == RepleState([], [cmd])

    def test_adding_prolog_appear_in_state(self):
        reple = default_reple()
        cmd = f"echo '5'"
        reple.process_line(prologify(cmd), [], [], [])

        state = reple.dump_state()
        assert state == RepleState([cmd], [])
