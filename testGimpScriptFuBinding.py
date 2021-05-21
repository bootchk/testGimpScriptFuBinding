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

To test:
open terminal
>export G_MESSAGES_DEBUG=scriptfu (optional, for debugging ScriptFu)
>gimp
File>New, choose OK
Choose menu Test>Scriptfu binding
Search console for "Fail:" (test sensitive) these are  failures.

You will also see:
- error messages from GimpFu, since this is a GimpFu plugin.
- error messages from Gimp
These do not mean the test failed
(since we test that errored scripts return error messages.)


Implementation notes:

1) a PDB procedure status is string "success" on success
2) tests use literal numerals:
   1 for an enum
   1 for the ID of image or drawable (usually exists)
3) use the ScriptFu constant RUN-NONINTERACTIVE where needed (calling plugins versus INTERNAL PROC)

TODO
Write a single PDB procedure that takes/return all GIMP types.
Use a template to call it.
Iterate, fuzz the template over edge tests for GIMP types.
"""

from gimpfu import *

failed_tests = {}

def test(description, construct, expected_status):
    """
    Test a scriptfu construct.

    description: informal string
    construct: Scriptfu Scheme text
    expected: expected text of PDB status result
    """
    global failure_count

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
        failed_tests[description] = 1

# !!! Some expected strings have trailing space and newline


def plugin_func(image, drawable):
    print("plugin_func called")

    """
    Order of  is important.
    Some tests depend on objects created by earlier tests,
    assuming a basic image was opened
    and not requiring the opened image to have any particular objects.
    Test assume image with ID 1 is used for most tests.
    """

    # Don't test a version of Scriptuf that does fixup for certain errors
    do_test_fixup = False

    # Some other tests that crash are commented out

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

    """ Circa 2020:
    criptFu not handle ObjectArray.
    "Error: Argument 2 for gimp-edit-copy is unhandled type GimpObjectArray \n")
    """



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

    # TODO separate test for "value is out of range"
    # It is covered by some tests below.



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

    error tests, where the script signature is wrong
    """

    # Formerly:
    # "Error: in script, wrong number of arguments for gimp-unit-get-factor (expected 1 but received 0) \n"
    # Now, should get warning in console, and procedure fails
    '''
    test("error: missing arg",
        "(gimp-unit-get-factor)",
        "Error: in script, expected type: numeric for argument 1 to gimp-unit-get-factor  \n")
    '''

    # Formerly: "Error: in script, wrong number of arguments for gimp-unit-get-factor (expected 1 but received 2) \n"
    # Now, should get warning in console, and but procedure not fail
    test("error: extra arg",
        "(gimp-unit-get-factor 1 2)",
        "success")

    test("error: arg has wrong type",
        '(gimp-unit-get-factor "foo")',
        "Error: in script, expected type: numeric for argument 1 to gimp-unit-get-factor  \n")


    """
    Array errors.
    """

    """
    If G_MESSAGES_DEBUG=scriptfu, console should print like:
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: vector has 1 elements
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: 1.666000
    """

    test("error: array arg is not a container at all: 0 (some author's may mean empty list)",
        '(gimp-context-set-line-dash-pattern 2 0)',
        "Error: in script, expected type: vector for argument 2 to gimp-context-set-line-dash-pattern  \n")

    test("error: what some novices might try, NIL is not a symbol in TinyScheme",
        '(gimp-context-set-line-dash-pattern 2 NIL)',
        "Error: eval: unbound variable: NIL \n")

    test("Not an error (if PDB procedure handles it): array arg is empty vector",
        '(gimp-context-set-line-dash-pattern 0 #() )',
        "success")

    test("error: array arg is empty list, expected vector",
        '(gimp-context-set-line-dash-pattern 2 () )',
        "Error: in script, expected type: vector for argument 2 to gimp-context-set-line-dash-pattern  \n")

    # The test plugintaking a GStrv must exist, it is not in the GIMP repository.
    # When the test plugin does not exist, these tests fail with a different error message.
    # The only other procedure in the GIMP PDB taking string array is file-gih-save, hard to call and its buggy.
    # 2 1 1 is runmode, image, drawable for the test plugin.

    # An unquoted list still is marshalled to an empty string array
    test("valid string array arg is empty, unquoted list",
        '(python-fu-test-take-string-array RUN-NONINTERACTIVE 1 1 () )',
        "success")

    # Valid, a quoted empty list yields a string array
    test("valid string array arg passed as empty quoted list",
        '''(python-fu-test-take-string-array RUN-NONINTERACTIVE 1 1 '() )''',
        "success")

    # Valid, a list of empty strings is an array of two empty strings
    test("valid string array arg passed as quoted list of empty count_strings",
        '''(python-fu-test-take-string-array RUN-NONINTERACTIVE 1 1 '("" "") )''',
        "success")

    # !!! Pass image ID, drawable ID, quoted list
    test("valid string array passed as a list",
        '''(python-fu-test-take-string-array RUN-NONINTERACTIVE 1 1 '("foo" "bar") )''',
        "success")

    """
    If G_MESSAGES_DEBUG=scriptfu, console should print like:
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: list has 2 elements
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: "foo"
    (script-fu:127): scriptfu-DEBUG: 15:31:59.612: "bar"
    """

    test("error: vector passed for string array",
        # pass a vector where list expected
        '''(python-fu-test-take-string-array RUN-NONINTERACTIVE 1 1 #("foo" "bar") )''',
        "execution error")  # OLD error message
        # NEW "Error: in script, expected type: list for argument 4 to python-fu-test-take-string-array  \n")

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
    # because it never returns (stops this test), even though passed garbage.
    # '''(extension-gimp-help 1 '("foo") 1 '("bar"))''')
    # expect pass ScriptFu parsing, but procedure execution error?

    test("error: invalid container type",
        # pass a vector where list expected
        '''(extension-gimp-help 1 #("foo") 1 '("bar"))''',
        "Error: in script, expected type: list for argument 2 to extension-gimp-help  \n")

    test("error: invalid element type in container",
        # pass a list of numeric where list of string expected
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

    """
    We don't test fundamental types separately.
    They are probably covered by other tests.
    They are also fundamentally the same: yield numeric type to a script.

    Int, UInt, UChar, Boolean, Enum,
    Double
    String
    """

    """
    Image, Item, Drawable, Layer, LayerMask, Channel, Display
    All similar, yield numeric for ID.
    We only test a few explicitly, others are probably incidentally covered other tests.
    """

    # Assuming there is an image open at test time, its ID should be 1?
    # gimp-image-get-active-drawable ( Image ) => Drawable
    test("Image : ScriptFu uses ID's i.e. type int",
        '(gimp-image-get-active-drawable 1)',
        "success")

    """
    Create and delete a display.
    gimp-display-new ( Image ) => Display
    gimp-display-delete ( Display ) =>
    1 is usually the image
    """
    test("Display",
        "(gimp-display-delete (car (gimp-display-new 1)))",
        "success")


    """ Arrays """

    test("Float array having one element",
        '(gimp-context-set-line-dash-pattern 1 #(1.666))',
        "success")

    test("Float array having two elements",
        '(gimp-context-set-line-dash-pattern 2 #(1.666 3.14))',
        "success")


    # gimp-image-set-colormap ( Image Int Int8Array ) =>
    # 1 is image ID, 3 is size of uchar array
    # one color, one 3-tuple for RGB
    # Can you set a colormap of one color?
    test("Int8Array",
        '(gimp-image-set-colormap 1 3 #(1 2 3))',
        "success")

    # TODO file-gih-save takes a StringArray
    # The only procedure that does.
    # Its seems obscure and probably not used.

    # file-pdf-load takes a Int32Array
    # It is the rare one that does.
    # file-pdf-load ( Int Object String Int Int32Array ) => Image
    # 1 is boolean for reverse order, 2 is page count, (3 4) is list of pages
    # We expect it to bind, but to fail to find the file.
    test("Int32Array",
        '(file-pdf-load RUN-NONINTERACTIVE  "/tmp/foo.pdf" "password" 1 2 #(3 4))',
        "Error: Procedure execution of file-pdf-load failed: Could not load '/tmp/foo.pdf': No such file or directory \n")

    # TODO RGBArray
    # I can't find a procedure that takes.


    """ Miscellaneous complicated GIMP types """

    # gimp-attach-parasite ( Parasite ) =>
    test("Parasite: repr in ScriptFu is list literal '(name string, flags numeric, data string)",
        '''(gimp-attach-parasite '("foo" 1 "bar"))''',
        "success")


    test("RGB aka color: where arg is a literal tuple",
        "(gimp-context-set-background '( 1 2 3))",
        "success")

    test("RGB : where arg is a name of type string",
        '(gimp-context-set-background "black")',
        "success")

    # Scriptfu expects a list of length 3
    test("error: RGB aka color: where arg is a too-short list",
        "(gimp-context-set-background '( 1 2 ))",
        "Error: in script, expected type: color string or list for argument 1 to gimp-context-set-background  \n")

    # Scriptfu expects a list of length 3 of numeric
    test("error: RGB aka color: where list is not of numeric",
        '''(gimp-context-set-background '( 1 2 "foo" ))''',
        "Error: in script, expected type: numeric for element 3 of argument 1 to gimp-context-set-background  \n")

    # Scriptfu clamps to 255 without complaint
    test("error: RGB aka color: where arg is a tuple of too-large integers",
        "(gimp-context-set-background '( 512 666  64456))",
        "success")


    # TODO move this
    test("Not an error: passing a float literal for an ID usually type int",
        # I suppose TinyScheme rounds it?
        '(gimp-image-get-active-drawable 1.01)',
        "success")


    """
    GimpDrawable
    """

    test("single GimpDrawable (a numeric ID in ScriptFu)",
        '(gimp-drawable-edit-clear (car (gimp-image-get-active-drawable  1)))',
        "success")


    """
    GimpObjectArray of GimpDrawable
    """

    """ Normal """
    # This is the new, multi-layer signature for gimp-edit-copy

    test("Second arg is type ObjectArray a vector of bound variables",
        '''(let*
             (
              (drawable 1)
             )
           (gimp-edit-copy 1 (vector drawable))
           )
        ''',
        "success")


    test("GimpObjectArray, passing length numeric and constant vector of ID's",
        # Here, '1' is usually a valid drawable ID
        "(gimp-edit-copy 1 '#(1))",
        "success")
    # alternative script
    #"(gimp-edit-copy 1 (list 1))",


    """ GimpObjectArray errors in script """

    test("Error: Second arg is type ObjectArray a quoted vector of bound variables",
        '''(let*
             (
              (drawable 1)
             )
           (gimp-edit-copy 1 '#(drawable))
           )
        ''',
        "Error: Expected numeric in drawable vector #(drawable) \n")

    test("Error: Second arg is type ObjectArray a quoted vector of strings",
        '''(gimp-edit-copy 1 '#("foo"))''',
        '''Error: Expected numeric in drawable vector #("foo") \n''')


    if do_test_fixup:
        """
        Enhanced v3 ScriptFu allows this changed signature from v2.
        The signature was changed for multi-layer.
        Expect ScriptFu to wrap the single GimpDrawable in a ObjectArray
        Before the enhancement:
        "Error: in script, wrong number of arguments for gimp-edit-copy (expected 2 but received 1) \n"
        """
        test("GimpObjectArray, passing a single drawable ID",
            '(gimp-edit-copy 1)',
            "success")
        # Alternative script: '(gimp-edit-copy (gimp-image-get-active-drawable  1))',
    else :
        # This should print a warning to the log, then call the procedure, which fails
        test("GimpObjectArray, passing a single drawable ID",
            '(gimp-edit-copy 1)',
            "Error: Procedure execution of gimp-edit-copy failed on invalid input arguments: "
            "Procedure 'gimp-edit-copy' returned no return values \n")




    if do_test_fixup:
        # With the fixup feature, Scriptfu will succeed here, discarding the "foo" as an extra arg
        # Without the fixup feature, "Error: in script, expected type: list for argument 2 to gimp-edit-copy  \n")
        test("Error: second arg is type ObjectArray but string passed",
            '(gimp-edit-copy 1 "foo")',
            "success")
    else:
        # Without the fixup feature, ")
        test("Error: second arg is type ObjectArray but string passed",
            '(gimp-edit-copy 1 "foo")',
            "Error: in script, expected type: vector for argument 2 to gimp-edit-copy  \n")


    test("Error: second arg is type ObjectArray but unquoted list passed",
        '(gimp-edit-copy 1 (1))',
        "Error: illegal function \n")

    test("Error: second arg is type ObjectArray but list of string passed",
        '(gimp-edit-copy 1 ("foo"))',
        "Error: illegal function \n")



    '''
    TODO currently crashes GIMP
    test("len 1, but empty list passed for GimpObjectArray",
    # binds wo error
    # procedure executes w error "bad args"
    "(gimp-edit-copy 1 ())",
    "success",
    '''

    test("len 0 and empty vector passed for GimpObjectArray",
        "(gimp-edit-copy 0 #())",
        "Error: Procedure execution of gimp-edit-copy failed on invalid input arguments:"\
             " Procedure 'gimp-edit-copy' has been called with value '0' for argument 'num-drawables' (#1, type gint). This value is out of range. \n")

    test("invalid drawable ID",
        '(gimp-drawable-edit-clear 666)',
        "Error: Invalid drawable ID (666) \n")

    # TODO: -1 for NULL drawable
    # TODO find a PDB procedure that takes a null drawable



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
    """
    For testing the binding,
    all GIMP object types can be covered by one case.
    Because there is only once case in scheme-wrapper.c.
    All have a numeric ID, which is what we return to the script.
    I.E. GimpImage and all subclasses of GimpItem can be covered by one case.
    I.E. we don't need a separate test for GimpLayer.
    """

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

    """ Special Gimp type (objects) results """
    """ These are separate cases in scheme-wrapper.c
    so for complete coverage, we test each.
    """

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
        # find parasite that doesn't exist. Evidently, the procedure fails.
        # GIMP inadequacy
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

    #TODO return a value if all tests passed

    print(">>>>>>>>>>> Test Gimp Scriptfu Binding: Summary <<<<<<<<<<<<<<<<")
    if failed_tests:
        print("Failed tests: ")
        print(failed_tests)
    else :
        print("All tests passed")


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
