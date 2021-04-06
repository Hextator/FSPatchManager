# File System Patch Manager
#### FSPatchManager.py
For managing applications and removals of modular file overwrites of an application's resources, when they are represented by a file tree.

## Usage

### Application Argument(s)

The **FSPM** provides a command line interface with the following syntax:

`"path/to/python.exe" "path/to/FSPatchManager.py" "path/to/settings.ini"`

where `settings.ini` is a plain text file with the structure shown in the **Configuration File** section.

### Configuration File

```
APP_DATA_DIR    = path/to/directory/of/the/Data Dir
LOG_PATH        = path/to/directory/of/your/choice/patch.log
PATCH_PATH      = path/to/directory/of/your/choice/Active Mods/Repository
REVERT_PATH     = path/to/directory/of/your/choice/Revert Patch/Repository
GEN_PATCH_PATH  = path/to/directory/of/your/choice/Generated Patch/Repository
GEN_REVERT_PATH = path/to/directory/of/your/choice/Generated Revert Patch/Repository
```

Here, the `APP_DATA_DIR` is the directory you want to apply patches to, the `LOG_PATH` is where you want to save log messages from using the tool, the `PATCH_PATH` is the directory you plan to place your mods in, and the other directories specified are for the tool to appropriately maintain backups of original files and apply patch files.

It is recommended that an extra subfolder, like those named `Repository` in the previous example, be the leaves for each of the configured paths used by the tool for patch management. This allows the parent of those directories to hold version control meta data, for auditing whether the tool has behaved as expected, without interfering with program functionality. Beyond this recommendation, any path may be chosen - the names like `Active Mods`, `Revert Patch`, and `Repository` are merely guides, and are not required directory names.

### Adding Mods

The `PATCH_PATH` directory, specified in the config file discussed in the **Configuration File** section, should have directories of "mods" placed in it. These are folders with files to overwrite the contents of the `APP_DATA_DIR` with, organized with the same tree structure as the `APP_DATA_DIR` itself - to overwrite a file called `Sub File 2.txt` located at `APP_DATA_DIR/Sub Dir 2`, a file called `Sub File 2.txt` would need to be located at `PATCH_PATH/Mod Name/Sub Dir 2`. More visualized:

`PATCH_PATH/Mod Name/Sub Dir 2/Sub File 2.txt`
would overwrite
`APP_DATA_DIR/Sub Dir 2/Sub File 2.txt`

In this example, `Mod Name` can be any name, and should both designate what the mod does and what its priority is.

If more than one mod folder contains a patch file for the same target file in the `APP_DATA_DIR`, then the highest priority file takes precedence:

`PATCH_PATH/Test Mod 1/Sub Dir 2/Sub File 2.txt`
supersedes
`PATCH_PATH/Test Mod 2/Sub Dir 2/Sub File 2.txt`

because `Test Mod 1` is ordered lexicographically before `Test Mod 2`. A reasonable sorting method might be to prepend all mod folder names with an 8 digit hexadecimal order designation, with 00000000 indicating a mod with the highest priority.

### Applying Mods

Running the tool with the previously defined command line syntax, after appropriately configuring the settings file and the folder of mods, will result in the `APP_DATA_DIR` being patched appropriately. Backup copies of the original files will be maintained automatically.

**Any changes to the contents of `APP_DATA_DIR` after using the tool, which are not made by the tool itself, will be detected by the tool as important updates to the original files, and new backup files will be obtained.**

To prevent unexpected program behavior, never modify the contents of the `APP_DATA_DIR` manually after beginning use of this tool, except to manually restore the original files.

### Removing Mods

Simply run the tool again after moving mod folders out of the `PATCH_PATH` to restore the original files, or to allow lower priority modifications to those files to be applied (if applicable).

### Recovery

If the tool seems dysfunctional, manually moving the contents of the `GEN_REVERT_PATH` to the `APP_DATA_DIR` should restore all of the original files that were patched from their backup location, at which point clearing the `REVERT_PATH`, the `GEN_PATCH_PATH`, and the `GEN_REVERT_PATH` folders' contents should reset the tool's state.
