"""Small shared compiler adapter; MSVC runs inside an x64 developer prompt."""
from pathlib import Path
import os
import subprocess
from contextlib import contextmanager
import shutil
import uuid

@contextmanager
def temporary_directory():
    # Inherit the workspace ACL. Python 3.13's private Windows temp ACL does
    # not include the restricted token used by the Codex Windows sandbox.
    root=(Path(__file__).resolve().parents[1]/'.validation'/'temp').resolve()
    root.mkdir(parents=True,exist_ok=True)
    directory=root/uuid.uuid4().hex
    directory.mkdir()
    try:
        yield str(directory)
    finally:
        assert directory.resolve().parent == root
        shutil.rmtree(directory)

def compile_cpp(source, executable, includes=()):
    source, executable = Path(source), Path(executable)
    if os.name == 'nt':
        executable = executable.with_suffix('.exe')
        command = ['cl', '/nologo', '/std:c++20', '/EHsc', '/utf-8', '/W4',
                   '/DWIN32_LEAN_AND_MEAN', '/DNOMINMAX',
                   '/Fe:' + str(executable), '/Fo:' + str(executable.with_suffix('.obj'))]
        command += ['/I' + str(p) for p in includes]
        command += [str(source)]
    else:
        command = ['g++', '-std=c++20', '-Wall', '-Wextra']
        command += ['-I' + str(p) for p in includes]
        command += [str(source), '-o', str(executable)]
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(result.stdout)
    return executable
