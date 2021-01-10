A plugin to test GIMP ScriptFu binding.

Target audience:
- GIMP developers
- possibly ScriptFu plugin developers, too see what constructs ScriptFu is intended to accept

Tests many cases.
Each case is a construct in TinyScheme language (Lisp dialect) of the form '(PDBprocedureName arg1 arg2)'

Kinds of cases:
- errors by authors of ScriptFu scripts i.e. plugins
- implementation errors in ScriptFu itself
- for each GIMP type or GType that ScriptFu is designed to handle (accept/return)

Only tests the binding, that is, that ScriptFu attempts (or not) to call a PDB procedure.
Understand the types procedures should return,
but not what values any given procedure should return.

Is a GimpFu plugin, requires GimpFu v3 repository.
(Could be translated to a GIMP v3 Python plugin using GI)

For Gimp v3 (not tested to work for GIMP 2.)
Loosely speaking, depends on a major and minor GIMP version, currently 2.99, a beta version.  
Should be updated as GIMP changes to v 3.0.

!!! Depends on patches to GIMP still in progress.

To install, copy testGimpScriptFuBinding.py
to a folder named testGimpScriptFuBinding
usually in  ~/.config/GIMP/2.0/plug-ins

Appears in GIMP menus as Test>ScriptFu binding
