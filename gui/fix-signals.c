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

PyMODINIT_FUNC
initfix_signals (void)
{
  Py_InitModule ("fix_signals", methods);
}
