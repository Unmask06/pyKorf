# User Workflow through pyKorf

## File Handling

`pykorf` does not rely on the KORF EXE to read and write KDF files. Users should be able
to create a basic model programmatically and save it to a KDF file.

- A user can create a new model with `pykorf.Model()`. This creates a new model with
  default values from [text](../../library/New.kdf). A user can also load an existing KDF
  file with `pykorf.Model('path/to/file.kdf')`, which reads the KDF file and creates a
  model with values from that file.
- A user can save the model to a KDF file with `model.save()`. This writes the model to a
  KDF file with the same format as the input file. The user can also specify a different
  file name with `model.save('path/to/newfile.kdf')`.
- There should be a method to validate the KDF file format using `model.validate()`. This
  should check whether the model has all required fields and whether values are in the
  correct format. If there are any errors, it should raise an exception with a message
  indicating what is wrong. Because the KDF format is strict, any missing or incorrect
  field can cause the KORF EXE to fail, so this validation step is important before saving
  or running the model.

## Model Manipulation

Once a model is loaded or created, users can manipulate it by changing field values.

- Users can access model fields with `model.fieldname`; this should return the requested
  field value.
- Users should have an option to get the list of all elements and their fields with
  `model.elements`, which returns all elements in the model and their fields. Users can
  also filter by type with `model.get_elements_by_type('PIPE')`, which returns all PIPE
  elements.
- Users should be able to change parameter values by passing the element name, parameters,
  and values to `model.update_element('PIPE1', {'L': 10, 'D': 0.5})`. This updates the
  length and diameter of PIPE1 to 10 and 0.5. Users can also update multiple elements at
  once with
  `model.update_elements({'PIPE1': {'L': 10, 'D': 0.5}, 'PUMP1': {'PZPRES': 100}})`.
- Users should be able to add new elements with
  `model.add_element('PIPE', 'PIPE2', {'L': 5, 'D': 0.3})`, which adds a new PIPE element
  named PIPE2 with the specified parameters. Users can also add multiple elements at once
  with
  `model.add_elements([('PIPE', 'PIPE2', {'L': 5, 'D': 0.3}), ('PUMP', 'PUMP2', {'PZPRES': 100})])`.
  Even without parameters, new elements should be created with default values from
  [text](../../library/New.kdf), and users can update them later.
- Users should be able to delete elements with `model.delete_element('PIPE1')`, which
  deletes PIPE1 from the model. Users can also delete multiple elements at once with
  `model.delete_elements(['PIPE1', 'PUMP1'])`.
- Users should be able to copy elements with `model.copy_element('PIPE1', 'PIPE3')`, which
  creates a new element PIPE3 with the same type and parameters as PIPE1. Users can also
  copy multiple elements at once with
  `model.copy_elements([('PIPE1', 'PIPE3'), ('PUMP1', 'PUMP3')])`.
- Users should be able to move elements with `model.move_element('PIPE1', 'PIPE2')`, which
  moves PIPE1 to the position of PIPE2. Users can also move multiple elements at once with
  `model.move_elements([('PIPE1', 'PIPE2'), ('PUMP1', 'PUMP2')])`.

### Connectivity

Users should be able to connect and disconnect elements in the model.

- Users should be able to connect elements with `model.connect_elements('PIPE1', 'PUMP1')`,
  which connects PIPE1 to PUMP1. Users can also connect multiple elements at once with
  `model.connect_elements([('PIPE1', 'PUMP1'), ('PIPE2', 'PUMP2')])`, which connects PIPE1
  and PIPE2 to PUMP1 and PUMP2 respectively.
- Users should be able to disconnect elements with
  `model.disconnect_elements('PIPE1', 'PUMP1')`, which disconnects PIPE1 from PUMP1. Users
  can also disconnect multiple elements at once with
  `model.disconnect_elements([('PIPE1', 'PUMP1'), ('PIPE2', 'PUMP2')])`, which disconnects
  those pairs.
- These operations can lead to errors, for example if a user tries to connect incompatible
  elements or disconnect elements that are not connected. In such cases, the method should
  raise an exception with a clear message indicating what is wrong.
- Users should be able to check model connectivity with `model.check_connectivity()`. This
  should verify all element connections and raise an exception if any connectivity errors
  exist.
- Before every connection or disconnection, the model should validate the operation to
  ensure it does not create an invalid state. For example, connecting a PIPE to a PUMP is
  valid, but connecting a PIPE to another PIPE may not be valid depending on context. If
  an invalid connection is attempted, the method should raise an exception with a clear
  message.

### Layout and Positioning

- By default, elements in the model should have a default position and layout based on
  values from [text](../../library/New.kdf).
- The model should check for clashes and offset positions when X and Y are not provided by
  the user.
- When new elements are added, they should be placed in a default position that does not
  overlap existing elements. If there is a clash, the new element should be automatically
  offset to a nearby position to avoid overlap. Users should also be able to specify X and
  Y coordinates directly. If X and Y are not provided, automatic non-overlapping placement
  should be applied.
- Users should be able to change element position and layout with
  `model.update_element('PIPE1', {'X': 10, 'Y': 5})`, which updates PIPE1 to X=10 and Y=5.
  Users can also update multiple element positions with
  `model.update_elements({'PIPE1': {'X': 10, 'Y': 5}, 'PUMP1': {'X': 20, 'Y': 10}})`.
- Users should be able to check layout and positioning with `model.check_layout()`, which
  verifies placement and raises an exception if clashes or overlaps are found.
- Users should be able to visualize layout with `model.visualize()`, which creates a visual
  representation of elements and their connections. Users can customize this visualization
  with different colors, shapes, and sizes to better understand layout and connectivity.

## Splitting the Responsibilities

To manage complexity, the model should split responsibilities into different classes or modules. For example:

- A `Model` class that handles overall model management, file handling, and high-level operations.
- An `Element` class that represents individual elements (PIPE, PUMP, etc.) and their parameters.
- A `Connectivity` module that manages connections between elements and checks for connectivity errors.
- A `Layout` module that manages element positioning, checks for clashes, and visualizes the model.
- A `Validation` module that checks for KDF format compliance and raises exceptions for any issues.
  This separation allows for better organization, easier maintenance, and clearer code structure. Each module can focus on its specific responsibilities while the `Model` class orchestrates interactions between them.
