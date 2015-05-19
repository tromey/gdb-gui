/* Copyright (C) 2013, 2015 Tom Tromey <tom@tromey.com>

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <Python.h>
#include <signal.h>

static struct sigaction saved_action;

static PyObject *
save_sigchld (PyObject *self, PyObject *args)
{
  sigset_t set;

  sigaction (SIGCHLD, NULL, &saved_action);

  sigemptyset (&set);
  sigaddset (&set, SIGCHLD);
  pthread_sigmask (SIG_BLOCK, &set, NULL);

  Py_RETURN_NONE;
}

static PyObject *
restore_sigchld (PyObject *self, PyObject *args)
{
  sigset_t set;

  sigemptyset (&set);
  sigaddset (&set, SIGCHLD);
  pthread_sigmask (SIG_UNBLOCK, &set, NULL);

  sigaction (SIGCHLD, &saved_action, NULL);
  Py_RETURN_NONE;
}

static PyMethodDef methods[] =
{
  { "save", save_sigchld, METH_NOARGS, "Save SIGCHLD handler." },
  { "restore", restore_sigchld, METH_NOARGS, "Restores SIGCHLD handler." },
  { NULL, NULL, 0, NULL }
};

#if PY_MAJOR_VERSION >= 3

static struct PyModuleDef module =
{
  PyModuleDef_HEAD_INIT,
  "fix_signals",
  NULL,
  -1,
  methods,
  NULL,
  NULL,
  NULL,
  NULL
};

PyMODINIT_FUNC
PyInit_fix_signals (void)
{
  PyModule_Create (&module);
}

#else

PyMODINIT_FUNC
initfix_signals (void)
{
  Py_InitModule ("fix_signals", methods);
}

#endif
