"""Basic pyKorf Usage Examples.
This example demonstrates the core functionality of pyKorf for working
with KORF hydraulic model files.

For comprehensive use case examples, see:
- 01_create_pump_circuit.py - Create hydraulic circuits
- 02_add_pms_from_excel.py - PMS management
- 03_add_fluid_properties.py - Fluid properties
- 04_multi_case_analysis.py - Multi-case workflows
- 05_export_and_visualize.py - Export and visualization
"""

from pykorf import CaseSet, Model, Query


def example_load_and_inspect(): -> None:
    """Load a model and inspect its contents."""
    print("=" * 60)
    print("Example: Load and Inspect")
    print("=" * 60)

    # Load an existing model
    model = Model("pykorf/library/Pumpcases.kdf")

    # Get summary information
    summary = model.summary()
    print(f"File: {summary['file']}")
    print(f"Version: {summary['version']}")
    print(f"Cases: {summary['cases']}")
    print(f"Pipes: {summary['num_pipes']}")
    print(f"Pumps: {summary['num_pumps']}")
    print()


def example_modify_parameters():
    """Modify element parameters."""
    print("=" * 60)
    print("Example: Modify Parameters")
    print("=" * 60)

    model = Model("pykorf/library/Pumpcases.kdf")

    # Get a pipe by name
    pipe = model["L1"]
    print(f"Before: {pipe.name}, length={pipe.length_m}m")

    # Update via model
    model.update_element("L1", {"LEN": 200})
    print(f"After: {pipe.name}, length={pipe.length_m}m")
    print()


def example_case_management():
    """Work with multi-case scenarios."""
    print("=" * 60)
    print("Example: Case Management")
    print("=" * 60)

    model = Model("pykorf/library/Pumpcases.kdf")
    cases = CaseSet(model)

    # List case names
    print(f"Available cases: {cases.names}")
    print(f"Case count: {cases.count}")

    # Get pipe flows for all cases
    table = cases.pipe_flows_table()
    print("Pipe flows:")
    for row in table[:3]:  # Show first 3
        print(f"  {row}")
    print()


def example_querying():
    """Query elements using the Query DSL."""
    print("=" * 60)
    print("Example: Querying")
    print("=" * 60)

    model = Model("pykorf/library/Pumpcases.kdf")
    q = Query(model)

    # Find all pipes
    pipes = q.pipes.all()
    print(f"Total pipes: {len(pipes)}")

    # Find elements by name pattern
    p_elements = q.by_name("P*").all()
    print(f"Elements starting with 'P': {[e.name for e in p_elements]}")

    # Complex query with conditions
    # Note: This is a demonstration; real queries would use actual attributes
    print()


def example_validation():
    """Validate a model."""
    print("=" * 60)
    print("Example: Validation")
    print("=" * 60)

    model = Model("pykorf/library/Pumpcases.kdf")

    # Run validation
    issues = model.validate()

    if issues:
        print(f"Found {len(issues)} issue(s):")
        for issue in issues[:5]:
            print(f"  - {issue}")
    else:
        print("Model is valid!")
    print()


def example_export():
    """Export model data."""
    print("=" * 60)
    print("Example: Export")
    print("=" * 60)

    from pykorf.types import ExportOptions

    model = Model("pykorf/library/Pumpcases.kdf")

    # Export to JSON
    options = ExportOptions(
        include_results=True,
        include_geometry=True,
        indent=2,
    )

    # Note: Uncomment to actually save
    # export_to_json(model, "output.json", options=options)
    print("Export example (would save to output.json)")
    print()


if __name__ == "__main__":
    example_load_and_inspect()
    example_modify_parameters()
    example_case_management()
    example_querying()
    example_validation()
    example_export()
