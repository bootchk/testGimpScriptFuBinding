A plugin to test GIMP ScriptFu binding.

# Target audience

   - GIMP developers
   - possibly ScriptFu plugin developers, too see what constructs ScriptFu is intended to accept

# Test Cases

Each case is a construct in TinyScheme language (Lisp dialect) of the form '(PDBprocedureName arg1 arg2)'

Kinds of cases:
- errors by authors of ScriptFu scripts i.e. plugins
- implementation errors in ScriptFu itself
- for each GIMP type or GType that ScriptFu is designed to handle (accept/return)

Only tests the binding, that is, that ScriptFu attempts (or not) to call a PDB procedure.
Understands the types procedures should return, but not what values any given procedure should return.


# Is GimpFu

Is a GimpFu plugin, requires GimpFu v3 repository.
(Could be translated to a GIMP v3 Python plugin using GI)

# GIMP version

Tests Gimp v3 (not for GIMP 2.)
Loosely speaking, depends on a major and minor GIMP version, currently 2.99, a beta version.  
Should be updated as GIMP changes to v 3.0.

!!! Depends on patches to GIMP still in progress.

# Installation

To install, copy testGimpScriptFuBinding.py
to a folder named testGimpScriptFuBinding
usually in  ~/.config/GIMP/2.0/plug-ins

Appears in GIMP menus as Test>ScriptFu binding

# Running

   - Start GIMP in a console.
   - Open some image file
   - Choose Test>ScriptFu binding...

Expect no dialog, there are no choices for you to make.

Expect many error dialogs, but those are usually from failed procedures, not failed bindings.

Expect a sequence of all "Pass" to print on the console.
"Pass" means the test succeeded and the binding behaves as expected.

You will also see interspersed log messages, from GIMP and GimpFu
(WARNING and CRITICAL log messages cannot be supressed.)

A "Fail" demands action.
When GIMP has changed, eliminating a deficiency of GIMP,
then update this plugin to expect the new behavior of GIMP.

It is also possible that the support machinery (GimpFu) has changed,
giving a false "Fail".
Then also update this plugin.


# See also

Comments in code.
