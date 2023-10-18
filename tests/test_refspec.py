# kas - setup tool for bitbake based projects
#
# Copyright (c) Siemens AG, 2019
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import pytest
import shutil
from kas import kas
from kas.libkas import run_cmd
from kas.repos import RepoRefError, Repo


def test_refspec_switch(changedir, tmpdir):
    """
        Test that the local git clone is correctly updated when switching
        between a commit hash refspec and a branch refspec.
    """
    tdir = str(tmpdir / 'test_refspec_switch')
    shutil.copytree('tests/test_refspec', tdir)
    os.chdir(tdir)

    kas.kas(['shell', 'test.yml', '-c', 'true'])
    (rc, output) = run_cmd(['git', 'symbolic-ref', '-q', 'HEAD'], cwd='kas',
                           fail=False, liveupdate=False)
    assert rc != 0
    assert output.strip() == ''
    (rc, output) = run_cmd(['git', 'rev-parse', 'HEAD'], cwd='kas',
                           fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == '907816a5c4094b59a36aec12226e71c461c05b77'
    (rc, output) = run_cmd(['git', 'symbolic-ref', '-q', 'HEAD'], cwd='kas2',
                           fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == 'refs/heads/master'
    (rc, output) = run_cmd(['git', 'tag', '--points-at', 'HEAD'], cwd='kas3',
                           fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == '3.0.1'

    kas.kas(['shell', 'test2.yml', '-c', 'true'])
    (rc, output) = run_cmd(['git', 'symbolic-ref', '-q', 'HEAD'], cwd='kas',
                           fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == 'refs/heads/master'
    (rc, output) = run_cmd(['git', 'symbolic-ref', '-q', 'HEAD'], cwd='kas2',
                           fail=False, liveupdate=False)
    assert rc != 0
    assert output.strip() == ''
    (rc, output) = run_cmd(['git', 'rev-parse', 'HEAD'], cwd='kas2',
                           fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == '907816a5c4094b59a36aec12226e71c461c05b77'
    (rc, output) = run_cmd(['git', 'symbolic-ref', '-q', 'HEAD'], cwd='kas3',
                           fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == 'refs/heads/master'
    (rc, output) = run_cmd(['git', 'tag', '--points-at', 'HEAD'], cwd='kas4',
                           fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == '2.6.3'


def test_refspec_absolute(changedir, tmpdir):
    """
        Test that the local git clone works when a absolute refspec
        is given.
    """
    tdir = str(tmpdir / 'test_refspec_absolute')
    shutil.copytree('tests/test_refspec', tdir)
    os.chdir(tdir)

    kas.kas(['shell', 'test3.yml', '-c', 'true'])
    (rc, output) = run_cmd(['git', 'symbolic-ref', '-q', 'HEAD'],
                           cwd='kas_abs', fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == 'refs/heads/master'
    (rc, output_kas_abs) = run_cmd(['git', 'rev-parse', 'HEAD'],
                                   cwd='kas_abs', fail=False, liveupdate=False)
    assert rc == 0
    (rc, output_kas_rel) = run_cmd(['git', 'rev-parse', 'HEAD'],
                                   cwd='kas_rel', fail=False, liveupdate=False)
    assert rc == 0
    assert output_kas_abs.strip() == output_kas_rel.strip()
    (rc, output) = run_cmd(['git', 'tag', '--points-at', 'HEAD'],
                           cwd='kas_tag_abs', fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == '3.0.1'


def test_url_no_refspec(changedir, tmpdir):
    """
        Test that a repository with url but no refspec raises an error.
    """
    tdir = str(tmpdir / 'test_url_no_refspec')
    shutil.copytree('tests/test_refspec', tdir)
    os.chdir(tdir)
    with pytest.raises(RepoRefError):
        kas.kas(['shell', 'test4.yml', '-c', 'true'])


def test_commit_refspec_mix(changedir, tmpdir):
    """
        Test that mixing legacy refspec with commit/branch raises errors.
    """
    tdir = str(tmpdir / 'test_commit_refspec_mix')
    shutil.copytree('tests/test_refspec', tdir)
    os.chdir(tdir)
    with pytest.raises(RepoRefError):
        kas.kas(['shell', 'test5.yml', '-c', 'true'])
    with pytest.raises(RepoRefError):
        kas.kas(['shell', 'test6.yml', '-c', 'true'])
    with pytest.raises(RepoRefError):
        kas.kas(['shell', 'test7.yml', '-c', 'true'])


def test_tag_commit_do_not_match(changedir, tmpdir):
    """
        Test that giving tag and commit that do not match raises an error.
    """
    tdir = str(tmpdir / 'test_tag_commit_do_not_match')
    shutil.copytree('tests/test_refspec', tdir)
    os.chdir(tdir)
    with pytest.raises(RepoRefError):
        kas.kas(['shell', 'test8.yml', '-c', 'true'])


def test_unsafe_tag_warning(capsys, changedir, tmpdir):
    """
        Test that using tag without commit issues a warning, but only once.
    """
    tdir = str(tmpdir / 'test_unsafe_tag_warning')
    shutil.copytree('tests/test_refspec', tdir)
    os.chdir(tdir)
    # needs to be reset in case other tests ran before
    Repo.__no_commit_tag_warned__ = []
    kas.kas(['shell', 'test2.yml', '-c', 'true'])
    assert capsys.readouterr().err.count(
        'Using tag without commit for repository "kas4" is unsafe as tags '
        'are mutable.') == 1


def test_tag_branch_same_name(capsys, changedir, tmpdir):
    """
        Test that kas uses the tag if a branch has the same name as the tag.
    """
    tdir = str(tmpdir / 'test_tag_branch_same_name')
    shutil.copytree('tests/test_refspec', tdir)
    os.chdir(tdir)

    # Checkout the repositories
    kas.kas(['shell', 'test.yml', '-c', 'true'])

    # In kas3: create a branch named "3.0.1" on master HEAD
    # A tag named "3.0.1" already exists on an old commit from 2022
    (rc, output) = run_cmd(['git', 'switch', 'master'], cwd='kas3',
                           fail=False, liveupdate=False)
    assert rc == 0
    (rc, output) = run_cmd(['git', 'branch', '3.0.1'], cwd='kas3',
                           fail=False, liveupdate=False)
    assert rc == 0

    # In kas4: create a tag named "master" on existing 2.6.3 tag
    (rc, output) = run_cmd(['git', 'checkout', '2.6.3'], cwd='kas4',
                           fail=False, liveupdate=False)
    assert rc == 0
    (rc, output) = run_cmd(['git', 'tag', 'master'], cwd='kas4',
                           fail=False, liveupdate=False)
    assert rc == 0

    # Checkout the repositories again
    kas.kas(['shell', 'test.yml', '-c', 'true'])

    # Check the commit hashes
    (rc, output) = run_cmd(['git', 'rev-parse', 'HEAD'], cwd='kas3',
                           fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == '229310958b17dc2b505b789c1cc1d0e2fddccc44'

    (rc, output) = run_cmd(['git', 'rev-parse', 'HEAD'], cwd='kas4',
                           fail=False, liveupdate=False)
    assert rc == 0

    (rc, output2) = run_cmd(['git', 'rev-parse', 'refs/heads/master'],
                            cwd='kas4', fail=False, liveupdate=False)
    assert rc == 0
    assert output.strip() == output2.strip()


def test_refspec_warning(capsys, changedir, tmpdir):
    """
        Test that using legacy refspec issues a warning, but only once.
    """
    tdir = str(tmpdir / 'test_refspec_warning')
    shutil.copytree('tests/test_refspec', tdir)
    os.chdir(tdir)
    # needs to be reset in case other tests ran before
    Repo.__legacy_refspec_warned__ = []
    kas.kas(['shell', 'test2.yml', '-c', 'true'])
    assert capsys.readouterr().err.count(
        'Using deprecated refspec for repository "kas2".') == 1
