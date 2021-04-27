"""
A GimpFu plugin
that:
Tests ScriptFu binding
for Scheme constructs that call foreign functions i.e. PDB procedures.
I.E.  marshalling of args to a foreign function.
I.E.  script-fu/scheme-wrapper.c
I.E.  "language error" handling

Tested scripts are all in the lisp form "(PDBprocedureName arg1 arg2)"

Evaluates a sequence of Scheme constructs.
Scheme constructs may have errors.
Tests many paths (the error paths) through scheme-wrapper.c logic.

To evaluate Scheme, calls plug-in-script-fu-eval

Checks the PDB status result and compare to expected,
print Pass or Fail to console.

To :
open terminal
>export G_MESSAGES_DEBUG=scriptfu (optional, for debugging ScriptFu)
>gimp
File>New, choose OK
Choose menu Test>Scriptfu binding
Search console for "Fail:" (test sensitive) these are  failures.

You will also see:
- error messages from GimpFu, since this is a GimpFu plugin.
- error messages from Gimp
These do not mean the  failed (since we  error tests.)


TODO
Write a single PDB procedure that takes/return all GIMP types.
Use a template to call it.
Iterate, fuzz the template over edge tests for GIMP types.
"""

from gimpfu import *


# Note that a PDB procedure status is string "success" on success

def test(description, construct, expected_status):
    """
    Test a scriptfu construct.

    description: informal string
    construct: Scriptfu Scheme text
    expected: expected text of PDB status result
    """

    print(f"\nCase: {description}")

    # scriptfu evaluate
    pdb.plug_in_script_fu_eval(construct)

    # Compare <status of last PDB call> to <expected_status>.
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
    Order of  is important.
    Some s depend on objects created by earlier s,
    assuming a basic image was opened
    and not requiring the opened image to have any particular objects.
    Test assume image with ID 1 is used for most s.
    """

    """
    Basic sanity
    ============
    """


    test("Basic valid Scheme call to PDB",
        # literal 1 where enum expected
        "(gimp-unit-get-factor 1)",
        "success")


    """
    Test known flaws in ScriptFu.
    ============================
    These tests will change as ScriptFu is fixed.
    """

    # GIMP types that ScriptFu does not handle

    # ScriptFu not handle yet, doesn't matter what we pass
    # Circa 2020: "Error: Argument 2 for gimp-edit-copy is unhandled type GimpObjectArray \n")
    test("second arg is type ObjectArray",
        '(gimp-edit-copy 1 "foo")',
        "Error: in script, expected type: list or numeric for argument 2 to gimp-edit-copy  \n")



    """
    Test bad actors: calling plugins that crash or fail semantically
    """
    # TODO: a plugin that we know crashes say with segfault
    # "in script, called procedure %s failed to return a status")

    # gimp-brush-get-hardness ( String ) => Float
    # Pass a non-existant brush name
    test("Called procedure rejects arguments as invalid",
        '(gimp-brush-get-hardness "Zed")',
        "Error: Procedure execution of gimp-brush-get-hardness failed on invalid input arguments: Brush 'Zed' not found \n")

    # TODO values out of range



    """
    Test basic ScriptFu calling mechanism.
    ======================================

    An evaluated list whose car is an unquoted name of a PDB procedure
    should result in a call to the PDB.
    """

    test("invalid procedure name, not quoted",
        '(foo)',
         "Error: eval: unbound variable: foo \n")

    # ScriptFu allows you to quote, or not quote the first symbol??
    # in a list representing a call to PDB
    test("invalid procedure name, quoted",
        '("foo")',
        "Error: illegal function \n")

    test("Excluded procedure: script-fu-refresh",
        '(script-fu-refresh RUN-NONINTERACTIVE)',
        "Error: A script cannot refresh scripts \n")

    # Each call to a PDB procedure returns a list, whose first element must be car'd
    test("Nested calls",
        '(gimp-image-get-active-drawable (car (gimp-image-new 10 30 1)))',
        "success")


    """
    Test ScriptFu binding of args to PDB procedures, i.e. binding in forward direction
    ==================================================================================

    error tests
    """

    test("error: missing arg",
        "(gimp-unit-get-factor)",
        "Error: in script, wrong number of arguments for gimp-unit-get-factor (expected 1 but received 0) \n")

    test("error: extra arg",
        "(gimp-unit-get-factor 1 2)",
        "Error: in script, wrong number of arguments for gimp-unit-get-factor (expected 1 but received 2) \n")

    test("error: arg has wrong type",
        '(gimp-unit-get-factor "foo")',
        "Error: in script, expected type: numeric for argument 1 to gimp-unit-get-factor  \n")

    test("valid float array having one element",
        '(gimp-context-set-line-dash-pattern 1 #(1.666))',
        "success")

    """
    If G_MESSAGES_DEBUG=scriptfu, console should print like:
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: vector has 1 elements
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: 1.666000
    """

    test("error: array arg is not a container at all: 0 (some author's may mean empty list)",
        '(gimp-context-set-line-dash-pattern 2 0)',
        "Error: in script, expected type: vector for argument 2 to gimp-context-set-line-dash-pattern  \n")

    test("what some novices might try, NIL is not a symbol in TinyScheme",
        '(gimp-context-set-line-dash-pattern 2 NIL)',
        "Error: eval: unbound variable: NIL \n")

    test("Not an error (if PDB procedure handles it): array arg is empty vector",
        '(gimp-context-set-line-dash-pattern 0 #() )',
        "success")

    test("error: array arg is empty list, expected vector",
        '(gimp-context-set-line-dash-pattern 2 () )',
        "Error: in script, expected type: vector for argument 2 to gimp-context-set-line-dash-pattern  \n")

    # TODO:
    # error: string array arg is empty: empty list
    # '''(??? 0 '() )''')
    # Hard to , no PDB procedure (that we can  with) takes a string array

    # TODO:
    # error: string array arg is list of null string
    # '''(??? 1 '("") )''')
    # Hard to , no PDB procedure (that we can  with) takes a string array

    # TODO:
    # valid string array passed as a list
    # Hard to , no PDB procedure (that we can  with) takes a string array
    # '(??? 2 '("foo", "bar") )',
    """
    If G_MESSAGES_DEBUG=scriptfu, console should print like:
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: list has 2 elements
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: "foo"
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: "bar"
    """

    test("error: array arg with wrong, longer length",
        '(gimp-context-set-line-dash-pattern 2 #(1.0))',
        "Error: in script, vector (argument 2) for function gimp-context-set-line-dash-pattern has length 1 but expected length 2 \n")

    test("error: array arg with wrong, shorter length",
        '(gimp-context-set-line-dash-pattern 0 #(1.0))',
        # expect pass, although effect might not match author's expectation.
        # The effect is: scriptfu calls PDB procedure with empty array.
        # The PDB procedure accepts an empty pattern without complaint.
        # The PDB procedure sets the dash pattern in the context to an empty pattern?
        "success")

    test("error: array arg with negative length",
        '(gimp-context-set-line-dash-pattern -1 #(1.0))',
        # When assigned by ScriptFu to a guint, will be interpreted by C
        # as a large number and should fail.
        "Error: in script, vector (argument 2) for function gimp-context-set-line-dash-pattern has length 1 but expected length 4294967295 \n")

    test("error: array arg with wrong lisp container type",
        # list literal given, vector literal expected
        # Note single quote is a lisp symbol for literal list
        "(gimp-context-set-line-dash-pattern 1 '(1.0))",
        # !!! Actual has two trailing spaces.
        "Error: in script, expected type: vector for argument 2 to gimp-context-set-line-dash-pattern  \n")

    test("error: array arg with wrong contained element type",
        # expected float array, received string in vector
        '(gimp-context-set-line-dash-pattern 1 #("foo"))',
        '''Error: in script, expected type: numeric for element 1 of argument 2 to gimp-context-set-line-dash-pattern  #("foo") \n''')

    # tests for arg is StringArray

    # !!! Only a few PDB procedure takes a StringArray
    #
    # !!! But we can't use extension-gimp-help with syntactically valid args
    # because it never returns (stops this ), even though passed garbage.
    # '''(extension-gimp-help 1 '("foo") 1 '("bar"))''')
    # expect pass ScriptFu parsing, but procedure execution error?

    test("invalid container type",
        '''(extension-gimp-help 1 #("foo") 1 '("bar"))''',
        "Error: in script, expected type: list for argument 2 to extension-gimp-help  \n")

    test("invalid element type in container",
        '''(extension-gimp-help 1 '(1.0) 1 '("bar"))''',
        "Error: in script, expected type: string for element 1 of argument 2 to extension-gimp-help  (1.0) \n")

    test("error: wrong type where an image ID of type numeric should be passed",
        '(gimp-image-get-active-drawable "1")',
        "Error: in script, expected type: numeric for argument 1 to gimp-image-get-active-drawable  \n")

    """
    Test ScriptFu binding of args to PDB procedures, i.e. binding in forward direction
    ==================================================================================

    non error tests
    """
    # Miscellaneous arg types

    test("Parasite: repr in ScriptFu is list literal '(name string, flags numeric, data string)",
        # gimp-attach-parasite ( Parasite ) =>
        '''(gimp-attach-parasite '("foo" 1 "bar"))''',
        "success")

    # Int8Array  Int8

    test("RGB aka color: where arg is a literal tuple",
        "(gimp-context-set-background '( 1 2 3))",
        "success")

    test("RGB : where arg is a name of type string",
        '(gimp-context-set-background "black")',
        "success")

    test("Image : ScriptFu uses ID's i.e. type int",
        # Assuming there is an image open at time of ing, its ID should be 1?
        # gimp-image-get-active-drawable ( Image ) => Drawable
        '(gimp-image-get-active-drawable 1)',
        "success")

    test("Not an error: passing a float literal for an ID usually type int",
        # I suppose TinyScheme rounds it?
        '(gimp-image-get-active-drawable 1.01)',
        "success")


    """
    GimpDrawable and GimpObjectArray of GimpDrawable
    """

    test("single GimpDrawable (which is a numeric in ScriptFu)",
        '(gimp-drawable-edit-clear (car (gimp-image-get-active-drawable  1)))',
        "success")

    test("GimpObjectArray, passing a single drawable ID",
        # FUTURE: enhance ScriptFu to allow this
        '(gimp-edit-copy 1)',
        "Error: in script, wrong number of arguments for gimp-edit-copy (expected 2 but received 1) \n")

    # Expect ScriptFu to wrap the single GimpDrawable
    # '(gimp-edit-copy (gimp-image-get-active-drawable  1))',

    test("GimpObjectArray, passing length numeric and list of ID's",
        # Here, '1' is usually a valid drawable ID
        "(gimp-edit-copy 1 '(1))",
        "success")
    # alternative script
    #"(gimp-edit-copy 1 (list 1))",


    '''
    TODO currently crashes GIMP
    test("len 1, but empty list passed for GimpObjectArray",
    # binds wo error
    # procedure executes w error "bad args"
    "(gimp-edit-copy 1 ())",
    "success",
    '''

    test("len 0 and empty list passed for GimpObjectArray",
        "(gimp-edit-copy 0 ())",
        "Error: Procedure execution of gimp-edit-copy failed on invalid input arguments:"\
             " Procedure 'gimp-edit-copy' has been called with value '0' for argument 'num-drawables' (#1, type gint). This value is out of range. \n")

    test("invalid drawable ID",
        '(gimp-drawable-edit-clear 666)',
        "Error: Invalid drawable ID (666) \n")

    # TODO: -1 for NULL drawable



    test("GFile",
        # GIMP 3, a ScriptFu script passes one string (which ScriptFu converts to a GFile)
        # GIMP 2 used two strings
        # The filename is bad, expect no errors in binding, but error in procedure
        '(gimp-file-load RUN-NONINTERACTIVE "/tmp/foo")',
        "Error: Procedure execution of gimp-file-load failed: Error opening file /tmp/foo: No such file or directory \n")


    """
    Test ScriptFu binding of results, i.e. binding in backward direction
    ====================================================================

    But plug_in_script_fu_eval does not return values from the evaluated string.
    IOW plug_in_script_fu_eval only offers side effects on images.

    No point in assigning the result of plug_in_script_fu_eval()
    because it is always an empty list.
    We can only check for errors in adapting the returned result.
    """

    """ Fundamental/primitive results """

    test("Int result",
        # no IN arg
        '(gimp-context-get-transform-direction)',
        "success")

    test("Double result",
        # enum arg
        '(gimp-unit-get-factor 1)',
        "success")

    test("String result",
        '(gimp-item-get-name 1)',
        "success")

    """ Gimp type (objects) results """

    test("image result.",
        # 1 is literal for image type enum
        '(gimp-image-new 10 30 1)',
        "success")

    test("Drawable result: NULL i.e. -1",
        # Note each construct must create its own objects to pass to procedures.
        # In other words, nested calls to PDB procedures.
        # Each call to a PDB procedure returns a list, whose first element must be car'd
        # There is no active drawable for a new image, this returns -1
        # TODO therefore need a different script
        '(gimp-image-get-active-drawable (car (gimp-image-new 10 30 1)))',
        "success")

    test("GimpItem result",
        # gimp-item-get-parent ( Item ) => Item
        '(gimp-item-get-parent 1)',
        "success")

    test("GimpVectors result",
        # image 1.  Put vectors in it before .
        '(gimp-image-get-active-vectors 1)',
        "success")

    test("RGB result",
        # gimp-channel-get-color ( Channel ) => RGB
        # channel 1
        # Result should be a list of 3 numerics
        '(gimp-channel-get-color 1)',
        "success")

    test("Parasite result",
        # gimp-parasite-find ( String ) => Parasite
        # find parasite we attached earlier?
        '(gimp-get-parasite "foo")',
        "success")

    test("Parasite result: none",
        # gimp-get-parasite ( String ) => Parasite
        # find parasite that doesn't exist. Evidently, the procedure fails
        '(gimp-get-parasite "zed")',
        "Error: Procedure execution of gimp-get-parasite failed \n")



    """ GLib type results """

    test("GFile result is empty string",
        # Since new image not exported, should return empty string
        '(gimp-image-get-exported-file (car (gimp-image-new 10 30 1)))',
        "success")

    test("GFile result is nonempty string",
        '(gimp-temp-file "txt")',
        "success")


    """ GimpFooArray results """

    test("float array result",
        '(gimp-context-get-line-dash-pattern)',
        "success")

    test("string array result",
        '(gimp-get-parasite-list)',
        "success")

    test("RGBArray result",
        # gimp-palette-get-colors ( String ) => Int RGBArray
        # Bears is a palette name
        '(gimp-palette-get-colors "Bears")',
        "success")

    test("Int8Array result",
        # gimp-brush-get-pixels ( String ) => Int Int Int Int Int8Array Int Int Int8Array
        # assert foo is a brush name (use a stock one)
        '(gimp-brush-get-pixels "foo")',
        "success")

    # gimp-image-get-color-profile ( Image ) => Int Int8Array
    # '(gimp-image-get-color-profile (car (gimp-image-new 10 30 1)))',

    test("ObjectArray result",
        # get layers of a new image
        '(gimp-image-get-layers (car (gimp-image-new 10 30 1)))',
        "success")

    '''
    Sidebar:  writing to console.

    test("TinyScheme write",
        '(write "Written to console")',
        "success")

    test("TinyScheme display",
        '(display "Written to console")',
        "success")
    '''



    # TODO call a procedure that maliciously returns an array length
    # not matching the array size

    # TODO Not related to binding:  a script that let * vars and (write vars)

    # TODO:
    # write a plugin that takes and returns all types
    # repetitively call it with fuzzed args

    #TODO return a value if all s passed


register(
    "python-fu--script-fu-binding",
    "Test ScriptFu binding to PDB",
    "A  program. Non-interactive.  Start in a console.  Search for Fail",
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
