"""
A GimpFu plugin
that:
tests ScriptFu binding
for Scheme constructs that call foreign functions i.e. PDB procedures.
I.E. test marshalling of args to a foreign function.
I.E. test script-fu/scheme-wrapper.c
I.E. test "language error" handling

Tests are all in the lisp form "(PDBprocedureName arg1 arg2)"

Evaluates a sequence of Scheme constructs.
Scheme constructs may have errors.
Tests many paths (the error paths) through scheme-wrapper.c logic.

To evaluate Scheme, calls plug-in-script-fu-eval

Checks the PDB status result and compare to expected,
print Pass or Fail to console.

To test:
open terminal
>export G_MESSAGES_DEBUG=scriptfu (optional, for debugging ScriptFu)
>gimp
File>New, choose OK
Choose menu Test>Scriptfu binding
Look for "Fail: expected ..."
You will also see error messages from GimpFu, since this is a GimpFu plugin.

TODO
Write a single PDB procedure that takes/return all GIMP types.
Use a template to call it.
Iterate, fuzz the template over edge cases for GIMP types.
"""

from gimpfu import *


# Note that a PDB procedure status is string "success" on success


def expect(expected_status):
    """
    Compare <status of last PDB call> to <expected_status>.
    """
    actual_status = pdb.get_last_error()
    if actual_status == expected_status:
        print("Pass")
    else:
        # print with repr() so whitespace visible
        print(f"Fail: expected:{repr(expected_status)}, actual:{repr(actual_status)}")

# !!! Some expected strings have trailing space and newline



def plugin_func(image, drawable):
      print("plugin_func called")

      """
      Basic sanity
      """

      # valid Scheme call to PDB
      # Here literal 1 where enum expected
      pdb.plug_in_script_fu_eval("(gimp-unit-get-factor 1)")
      expect("success")


      """
      Test known flaws in ScriptFu.
      These tests will change as ScriptFu is fixed.
      """

      # GIMP types unhandled
      # second arg is type ObjectArray
      # ScriptFu not handle yet, doesn't matter what we pass
      pdb.plug_in_script_fu_eval('(gimp-edit-copy 1 "foo")')
      expect("Error: Argument 2 for gimp-edit-copy is unhandled type GimpObjectArray \n")

      """
      Test bad actors: calling plugins that crash or fail semantically
      """
      # TODO: a plugin that we know crashes say with segfault
      # expect("in script, called procedure %s failed to return a status")

      # A plugin that doesn't like the values we pass
      # gimp-brush-get-hardness ( String ) => Float
      # Pass a non-existant brush name
      pdb.plug_in_script_fu_eval('(gimp-brush-get-hardness "Zed")')
      expect("Error: Procedure execution of gimp-brush-get-hardness failed on invalid input arguments: Brush 'Zed' not found \n")

      # TODO values out of range



      """
      procedure name tests
      """

      # invalid procedure name, not quoted
      pdb.plug_in_script_fu_eval('(foo)')
      expect( "Error: eval: unbound variable: foo \n")

      # invalid procedure name, quoted
      # ScriptFu allows you to quote, or not quote the first symbol??
      # in a list representing a call to PDB
      pdb.plug_in_script_fu_eval('("foo")')
      expect("Error: illegal function \n")

      # Excluded procedure
      # It takes a run mode (but why?), here 2 is NONINTERACTIVE
      pdb.plug_in_script_fu_eval('(script-fu-refresh 2)')
      expect("Error: A script cannot refresh scripts \n")



      """
      Test IN arg adaption: error cases
      """

      # error: missing arg
      pdb.plug_in_script_fu_eval("(gimp-unit-get-factor)")
      expect( "Error: in script, wrong number of arguments for gimp-unit-get-factor (expected 1 but received 0) \n")

      # error: arg has wrong type
      pdb.plug_in_script_fu_eval('(gimp-unit-get-factor "foo")')
      expect("Error: in script, expected type: numeric for argument 1 to gimp-unit-get-factor  \n")

      # valid float array having one element
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern 1 #(1.666))')
      expect("success")
      """
      If G_MESSAGES_DEBUG=scriptfu, console should print like:
      (script-fu:127): scriptfu-DEBUG: 15:31:59.612: vector has 1 elements
      (script-fu:127): scriptfu-DEBUG: 15:31:59.612: 1.666000
      """

      # error: array arg is not a container at all: 0 (some author's may mean empty list)
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern 2 0)')
      expect("Error: in script, expected type: vector for argument 2 to gimp-context-set-line-dash-pattern  \n")

      # Test what some novices might try, NIL is not a symbol in TinyScheme
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern 2 NIL)')
      expect("Error: eval: unbound variable: NIL \n")

      # Not an error (if PDB procedure handles it): array arg is empty vector
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern 0 #() )')
      expect("success")

      # error: array arg is empty list, expected vector
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern 2 () )')
      expect("Error: in script, expected type: vector for argument 2 to gimp-context-set-line-dash-pattern  \n")

      # TODO:
      # error: string array arg is empty: empty list
      # pdb.plug_in_script_fu_eval('''(??? 0 '() )''')
      # Hard to test, no PDB procedure (that we can test with) takes a string array

      # TODO:
      # error: string array arg is list of null string
      # pdb.plug_in_script_fu_eval('''(??? 1 '("") )''')
      # Hard to test, no PDB procedure (that we can test with) takes a string array

      # TODO:
      # valid string array passed as a list
      # Hard to test, no PDB procedure (that we can test with) takes a string array
      # pdb.plug_in_script_fu_eval('(??? 2 '("foo", "bar") )')
      """
       If G_MESSAGES_DEBUG=scriptfu, console should print like:
       (script-fu:127): scriptfu-DEBUG: 15:31:59.612: list has 2 elements
       (script-fu:127): scriptfu-DEBUG: 15:31:59.612: "foo"
       (script-fu:127): scriptfu-DEBUG: 15:31:59.612: "bar"
      """

      # error: array arg with wrong, longer length
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern 2 #(1.0))')
      expect("Error: in script, vector (argument 2) for function gimp-context-set-line-dash-pattern has length 1 but expected length 2 \n")

      # error: array arg with wrong, shorter length
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern 0 #(1.0))')
      # expect pass, although effect might not match author's expectation.
      # The effect is: scriptfu calls PDB procedure with empty array.
      # The PDB procedure accepts an empty pattern without complaint.
      # The PDB procedure sets the dash pattern in the context to an empty pattern?
      expect("success")

      # error: array arg with negative length
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern -1 #(1.0))')
      # When assigned by ScriptFu to a guint, will be interpreted by C
      # as a large number and should fail.
      expect("Error: in script, vector (argument 2) for function gimp-context-set-line-dash-pattern has length 1 but expected length 4294967295 \n")

      # error: array arg with wrong lisp container type
      # list literal given, vector literal expected
      # Note single quote is a lisp symbol for literal list
      pdb.plug_in_script_fu_eval("(gimp-context-set-line-dash-pattern 1 '(1.0))")
      # !!! Actual has two trailing spaces.
      expect("Error: in script, expected type: vector for argument 2 to gimp-context-set-line-dash-pattern  \n")

      # error: array arg with wrong contained element type
      # expected float array, received string in vector
      pdb.plug_in_script_fu_eval('(gimp-context-set-line-dash-pattern 1 #("foo"))')
      expect('''Error: in script, expected type: numeric for element 1 of argument 2 to gimp-context-set-line-dash-pattern  #("foo") \n''')

      # cases for arg is StringArray

      # !!! Only a few PDB procedure takes a StringArray
      #
      # !!! But we can't use extension-gimp-help with syntactically valid args
      # because it never returns (stops this test), even though passed garbage.
      # pdb.plug_in_script_fu_eval('''(extension-gimp-help 1 '("foo") 1 '("bar"))''')
      # expect pass ScriptFu parsing, but procedure execution error?

      # invalid container type
      pdb.plug_in_script_fu_eval('''(extension-gimp-help 1 #("foo") 1 '("bar"))''')
      expect("Error: in script, expected type: list for argument 2 to extension-gimp-help  \n")

      # invalid element type in container
      pdb.plug_in_script_fu_eval('''(extension-gimp-help 1 '(1.0) 1 '("bar"))''')
      expect("Error: in script, expected type: string for element 1 of argument 2 to extension-gimp-help  (1.0) \n")

      # Miscellaneous arg types

      # Parasite
      # Parasite repr in ScriptFu is list literal '(name string, flags numeric, data string)
      # gimp-attach-parasite ( Parasite ) =>
      pdb.plug_in_script_fu_eval('''(gimp-attach-parasite '("foo" 1 "bar"))''')
      expect("success")

      # Int8Array  Int8

      # RGB (aka color) : where arg is a literal tuple
      pdb.plug_in_script_fu_eval("(gimp-context-set-background '( 1 2 3))")
      expect("success")

      # RGB : where arg is a name of type string
      pdb.plug_in_script_fu_eval('(gimp-context-set-background "black")')
      expect("success")

      # Image (ScriptFu uses ID's i.e. type int )
      # Assuming there is an image open at time of testing, its ID should be 1?
      # gimp-image-get-active-drawable ( Image ) => Drawable
      pdb.plug_in_script_fu_eval('(gimp-image-get-active-drawable 1)')
      expect("success")

      # Wrong type where an ID of type numeric should be passed
      pdb.plug_in_script_fu_eval('(gimp-image-get-active-drawable "1")')
      expect("Error: in script, expected type: numeric for argument 1 to gimp-image-get-active-drawable  \n")

      # Not an error: passing a float literal for an ID usually type int
      # I suppose TinyScheme rounds it?
      pdb.plug_in_script_fu_eval('(gimp-image-get-active-drawable 1.01)')
      expect("success")




      """
      Test ScriptFu handles results.

      But plug_in_script_fu_eval does not return values from the evaluated string.
      IOW plug_in_script_fu_eval only offers side effects on images.

      No point in assigning the result of plug_in_script_fu_eval()
      because it is always an empty list.
      We can only check for errors in adapting the returned result.
      """

      # no in args, result is type int
      pdb.plug_in_script_fu_eval('(gimp-context-get-transform-direction)')
      expect("success")

      # enum arg and a double result
      pdb.plug_in_script_fu_eval('(gimp-unit-get-factor 1)')
      expect("success")

      # float array result
      pdb.plug_in_script_fu_eval('(gimp-context-get-line-dash-pattern)')
      expect("success")

      # string array result
      pdb.plug_in_script_fu_eval('(gimp-get-parasite-list)')
      expect("success")

      # image result.  1 is literal for image type enum
      pdb.plug_in_script_fu_eval('(gimp-image-new 10 30 1)')
      expect("success")

      # drawable result
      # Note each construct must create its own objects to pass to procedures.
      # In other words, nested calls to PDB procedures.
      # Each call to a PDB procedure returns a list, whose first element must be car'd
      pdb.plug_in_script_fu_eval('(gimp-image-get-active-drawable (car (gimp-image-new 10 30 1)))')
      expect("success")

      # Int8Array
      # gimp-image-get-color-profile ( Image ) => Int Int8Array
      # TODO gimp-image-set-colormap ( Image Int Int8Array ) =>

      # RGBArray
      # gimp-palette-get-colors ( String ) => Int RGBArray
      # Bears is a palette name
      pdb.plug_in_script_fu_eval('(gimp-palette-get-colors "Bears")')
      expect("success")

      # Int8Array
      # assert foo is a brush name (use a stock one)
      pdb.plug_in_script_fu_eval('(gimp-brush-get-pixels "foo")')
      expect("success")

      # TODO call a procedure that maliciously returns an array length
      # not matching the array size

      # TODO test a script that let * vars and (write vars)

      # TODO:
      # write a plugin that takes and returns all types
      # repetitively call it with fuzzed args


register(
      "python-fu-test-script-fu-errors",
      "Test ScriptFu binding to PDB",
      "A test program. Non-interactive.  Start in a console.  Search for Fail",
      "Lloyd Konneker",
      "copyright",
      "2021",
      "ScriptFu binding",
      "*",
      [
          (PF_IMAGE, "image", "Input image", None),
          (PF_DRAWABLE, "drawable", "Input drawable", None),
      ],
      [],
      plugin_func,
      menu="<Image>/Test")
main()
