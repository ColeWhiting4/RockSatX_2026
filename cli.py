#! /usr/bin/env python3

#
# Built-in modules.
#

import types, sys, shlex, pathlib, shutil, subprocess, time



#
# The PXD module.
#

try:
    import deps.pxd.ui
    import deps.pxd.metapreprocessor
    import deps.pxd.cite
    from deps.pxd.log   import log
    from deps.pxd.utils import *
except ModuleNotFoundError as error:
    print(f'[ERROR] Could not import "{error.name}"; maybe the Git submodules need to be initialized/updated? Try doing:')
    print(f'        > git submodule update --init --recursive')
    print(f'        If this still doesn\'t work, please raise an issue.')
    sys.exit(1)



#
# Common definitions with the meta-preprocessor.
#

from electrical.src.Common import TARGET, TARGETS



#
# Import handler for PySerial.
#

def import_pyserial():

    try:
        import serial
        import serial.tools.list_ports
    except ModuleNotFoundError as error:
        with log(ansi = 'fg_red'):
            log(f'[ERROR] Python got {type(error).__name__} ({error}); try doing:')
            log(f'        > pip install pyserial', ansi = 'bold')
        sys.exit(1)

    return serial, serial.tools.list_ports



#
# Routine for ensuring the user has the required programs on their machine (and provide good error messages if not).
#

def require(*needed_programs):

    missing_program = next((program for program in needed_programs if shutil.which(program) is None), None)

    if not missing_program:
        return # The required programs were found on the machine.

    # PowerShell.
    if missing_program in (roster := [
        'pwsh',
    ]):
        with log(ansi = 'fg_red'):
            log(f'[ERROR] Python couldn\'t find "pwsh" in your PATH; have you installed PowerShell yet?')
            log(f'        > https://apps.microsoft.com/detail/9MZ1SNWT0N5D', ansi = 'bold')
            log(f'        Installing PowerShell via Windows Store is the most convenient way.')

    # STM32CubeCLT.
    elif missing_program in (roster := [
        'STM32_Programmer_CLI',
        'ST-LINK_gdbserver'
    ]):
        with log(ansi = 'fg_red'):
            log(f'[ERROR] Python couldn\'t find "{missing_program}" in your PATH; have you installed STM32CubeCLT yet?')
            log(f'        > https://www.st.com/en/development-tools/stm32cubeclt.html', ansi = 'bold')
            log(f'        Install and then make sure all of these commands are available in your PATH:')
            for program in roster:
                if shutil.which(program) is not None:
                    log(f'            - [located] {program}', ansi = 'fg_green')
                else:
                    log(f'            - [missing_program] {program}')

    # Arm GNU Toolchain.
    elif missing_program in (roster := [
        'arm-none-eabi-gcc',
        'arm-none-eabi-cpp',
        'arm-none-eabi-objcopy',
        'arm-none-eabi-gdb',
    ]):
        with log(ansi = 'fg_red'):
            log(f'[ERROR] Python couldn\'t find "{missing_program}" in your PATH; have you installed the Arm GNU toolchain (version 14.2.Rel1, December 10, 2024) yet?')
            log(f'        > website : https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads', ansi = 'fg_bright_red')
            for platform, url in (
                ('win32', 'https://armkeil.blob.core.windows.net/developer/Files/downloads/gnu/14.2.rel1/binrel/arm-gnu-toolchain-14.2.rel1-mingw-w64-x86_64-arm-none-eabi.exe'),
                ('linux', 'https://armkeil.blob.core.windows.net/developer/Files/downloads/gnu/14.2.rel1/binrel/arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi.tar.xz'       ),
            ):
                log(f'        > {platform.ljust(len('website'))} : {url}', ansi = ('bold', 'fg_bright_red') if sys.platform == platform else 'fg_bright_red')
            log(f'        Install/unzip and then make sure all of these commands are available in your PATH:')
            for program in roster:
                if shutil.which(program) is not None:
                    log(f'            - [located] {program}', ansi = 'fg_green')
                else:
                    log(f'            - [missing_program] {program}')

    # Picocom.
    elif missing_program in (roster := [
        'picocom'
    ]):
        with log(ansi = 'fg_red'):
            log(f'[ERROR] Python couldn\'t find "{missing_program}" in your PATH; have you installed it yet?')
            log(f'        If you\'re on a Debian-based distro, this is just simply:')
            log(f'        > sudo apt install picocom', ansi = 'bold')
            log(f'        Otherwise, you should only be getting this message on some other Linux distribution, ')
            log(f'        to which I have faith in you to figure this out on your own.')

    # Make.
    elif missing_program in (roster := [
        'make'
    ]):
        with log(ansi = 'fg_red'):
            log(f'[ERROR] Python couldn\'t find "{missing_program}" in your PATH; have you installed it yet?')
            log(f'        If you\'re on a Windows system, run the following command and restart your shell:')
            log(f'        > winget install ezwinports.make', ansi = 'bold')

    # Not implemented.
    else:
        with log(ansi = 'fg_red'):
            log(f'[ERROR] Python couldn\'t find "{missing_program}" in your PATH; have you installed it yet?')

    sys.exit(1)



################################################################################################################################

#
# Routine for logging out ST-Links as a table.
#

def log_stlinks(stlinks):

    header, rows = ljusts(({
        'Probe Index'   : stlink.probe_index,
        'Board Name'    : stlink.board_name,
        'Device'        : stlink.comport.device,
        'Description'   : stlink.comport.description,
        'Serial Number' : stlink.serial_number,
    } for stlink in stlinks), include_keys = True)

    log(f'| {' | '.join(header)} |')
    for row in rows:
        log(f'| {' | '.join(row.values())} |')



#
# Routine for finding ST-Links.
#

def request_stlinks(
    *,
    specific_one         = False,
    specific_probe_index = None,
):

    # Parse output of STM32_Programmer_CLI's findings.
    #
    # e.g.
    #     ST-Link Probe 0 :
    #        ST-LINK SN  : 003F00493133510F37363734
    #        ST-LINK FW  : V3J15M7
    #        Access Port Number  : 2
    #        Board Name  : NUCLEO-H7S3L8

    require('STM32_Programmer_CLI')

    listing_lines = subprocess.check_output(['STM32_Programmer_CLI', '--list', 'st-link']).decode('utf-8').splitlines()
    stlinks       = [
        types.SimpleNamespace(
            probe_index        = int(listing_lines[i + 0].removeprefix(prefix).removesuffix(':')),
            serial_number      =     listing_lines[i + 1].split(':')[1].strip(),
            firmware           =     listing_lines[i + 2].split(':')[1].strip(),
            access_port_number = int(listing_lines[i + 3].split(':')[1].strip()),
            board_name         =     listing_lines[i + 4].split(':')[1].strip(),
        )
        for i in range(len(listing_lines))
        if listing_lines[i].startswith(prefix := 'ST-Link Probe ')
    ]



    # Find each ST-Link's corresponding serial port.

    serial, list_ports = import_pyserial()

    comports = list_ports.comports()

    for stlink in stlinks:
        stlink.comport, = [comport for comport in comports if comport.serial_number == stlink.serial_number]



    # If a specific probe index was given, give back that specific ST-Link.

    if specific_probe_index is not None:

        if not stlinks:
            log(f'[ERROR] No ST-Links found.', ansi = 'fg_red')
            sys.exit(1)

        if not (matches := [stlink for stlink in stlinks if stlink.probe_index == specific_probe_index]):
            log_stlinks(stlinks)
            log()
            log(f'[ERROR] No ST-Links found with probe index of "{specific_probe_index}".', ansi = 'fg_red')
            sys.exit(1)

        stlink, = matches

        return stlink



    # If the caller is assuming there's only one ST-Link, then give back the only one.

    if specific_one:

        if not stlinks:
            log(f'[ERROR] No ST-Links found.', ansi = 'fg_red')
            sys.exit(1)

        if len(stlinks) >= 2:
            log_stlinks(stlinks)
            log()
            log(f'[ERROR] Multiple ST-Links found; I don\'t know which one to use.', ansi = 'fg_red')
            sys.exit(1)

        stlink, = stlinks

        return stlink



    # Otherwise, give back the list of the ST-Links we found (if any).

    return stlinks



#
# Routine for executing shell commands.
#

def execute(
    default               = None,  # Typically for when the command for cmd.exe and bash are the same (e.g. "echo hello!").
    *,
    bash                  = None,
    cmd                   = None,  # PowerShell is slow to invoke, so cmd.exe would be used if its good enough.
    powershell            = None,  # "
    keyboard_interrupt_ok = False,
    nonzero_exit_code_ok  = False
):

    # Determine the shell command we'll be executing based on the operating system.

    if cmd is not None and powershell is not None:
        raise RuntimeError(
            f'CMD and PowerShell commands cannot be both provided; '
            f'please raise an issue or patch the script yourself.'
        )

    match sys.platform:

        case 'win32':
            use_powershell = cmd is None
            command        = powershell if use_powershell else cmd

        case _:
            command        = bash
            use_powershell = False

    if command is None:
        command = default

    if command is None:
        raise RuntimeError(
            f'Missing shell command for platform "{sys.platform}"; '
            f'please raise an issue or patch the script yourself.'
        )

    if use_powershell:
        require('pwsh')



    # Carry out the shell command.

    lexer                  = shlex.shlex(command)
    lexer.quotes           = '"'
    lexer.whitespace_split = True
    lexer.commenters       = ''
    lexer_parts            = list(lexer)
    command                = ' '.join(lexer_parts)

    log(f'$ {lexer_parts[0]}'    , end = '', ansi = 'fg_bright_green')
    log(' '                      , end = ''                          )
    log(' '.join(lexer_parts[1:]),                                   )

    if use_powershell:
        command = ['pwsh', '-Command', command]

    try:
        exit_code = subprocess.call(command, shell = True)
    except KeyboardInterrupt:
        if keyboard_interrupt_ok:
            exit_code = None
        else:
            raise

    if exit_code and not nonzero_exit_code_ok:
        log()
        log(f'[ERROR] Shell command exited with a non-zero code of {exit_code}.', ansi = 'fg_red')
        sys.exit(exit_code)

    return exit_code



#
# This Python script's user-interface constructor.
#

def ui_hook(subcmd_name):

    start = time.time()
    yield
    end = time.time()

    if (elapsed := end - start) >= 0.5:
        log()
        log(f'> "{subcmd_name}" took: {elapsed :.3f}s')

ui = deps.pxd.ui.UI(
    f'{root(pathlib.Path(__file__).name)}',
    f'The command line program (pronounced "clippy").',
    ui_hook,
)



################################################################################################################################



@ui(f'Delete all build artifacts.')
def clean():

    directories = root('''
        ./electrical/build
    ''')

    for directory in directories:
        execute(
            bash = f'''
                rm -rf {repr(str(directory))}
            ''',
            cmd = f'''
                if exist {repr(str(directory))} rmdir /S /Q {repr(str(directory))}
            ''',
        )



################################################################################################################################



@ui('Compile and generate the binary for flashing.')
def build(
    specific_target_name : ([target.name for target in TARGETS], 'Target program to build; otherwise, build entire project.') = None,
    metapreprocess_only  : (bool                               , 'Run the meta-preprocessor; no compiling and linking.'     ) = False
):

    # Determine the targets we're building for.

    if specific_target_name is None:
        targets = TARGETS
    else:
        targets = [TARGET(specific_target_name)]



    # Logging routine for outputting nice dividers in stdout.

    def log_header(header):
        log()
        log(f'{'>' * 32} {header} {'<' * 32}', ansi = ('bold', 'fg_bright_black'))
        log()



    # Determine the files for the meta-preprocessor to scan through.

    metapreprocessor_file_paths = [
        pathlib.Path(root, file_name)
        for root, dirs, file_names in root('./electrical/src').walk()
        for file_name in file_names
        if file_name.endswith(('.c', '.h', '.py', '.ld', '.S'))
    ]



    # Callback of things to do before and after the execution of a meta-directive.

    elapsed = 0

    def metadirective_callback(info):

        nonlocal elapsed



        # Log information about the meta-directive that we're about to evaluate.

        export_preview = ', '.join(info.exports)

        if export_preview:

            if len(export_preview) > (cutoff := 64): # This meta-directive is exporting a lot of stuff, so we trim the list.
                export_preview = ', '.join(export_preview[:cutoff].rsplit(',')[:-1] + ['...'])

            export_preview = ' ' + export_preview


        log('| {nth}/{count} | {src} : {line} |{export_preview}'.format(
            count          = len(info.meta_directives),
            export_preview = export_preview,
            **ljusts({
                'nth'  : meta_directive_i + 1,
                'src'  : meta_directive.source_file_path,
                'line' : meta_directive.header_line_number,
            } for meta_directive_i, meta_directive in enumerate(info.meta_directives))[info.index],
        ))



        # Record how long it took to run this meta-directive.

        start  = time.time()
        output = yield
        end    = time.time()
        delta  = end - start

        if delta > 0.050:
            log(f'^ {delta :.3}s', ansi = 'fg_yellow') # Warn that this meta-directive took quite a while to execute.

        elapsed += delta




    # Begin meta-preprocessing!

    log_header('Meta-preprocessing')

    try:
        deps.pxd.metapreprocessor.do(
            output_dir_path   = root('./electrical/build/meta/'),
            source_file_paths = metapreprocessor_file_paths,
            callback          = metadirective_callback,
        )
    except deps.pxd.metapreprocessor.MetaError as err:
        sys.exit(err)

    log()
    log(f'# Meta-preprocessor : {elapsed :.3f}s.', ansi = 'fg_magenta')

    if metapreprocess_only:
        return



    # Compile each source.

    require(
        'arm-none-eabi-gcc',
    )

    for target in targets:

        log_header(f'Compiling "{target.name}"')

        for src in target.srcs:

            obj = root('./electrical/build', target.name, src.stem + '.o')

            obj.parent.mkdir(parents = True, exist_ok = True)

            execute(f'''
                arm-none-eabi-gcc
                    -o {repr(str(obj))}
                    -c {repr(str(src))}
                    {target.compiler_flags}
            ''')



    # Link the firmware.

    require(
        'arm-none-eabi-cpp',
        'arm-none-eabi-objcopy',
        'arm-none-eabi-gdb',
    )

    for target in targets:

        log_header(f'Linking "{target.name}"')

        # Preprocess the linker file.
        execute(f'''
            arm-none-eabi-cpp
                {target.compiler_flags}
                -E
                -x c
                -o {repr(str(root('./electrical/build', target.name, 'link.ld')))}
                {repr(str(root('./electrical/src/link.ld')))}
        ''')

        # Link object files.
        execute(f'''
            arm-none-eabi-gcc
                -o {repr(str(root('./electrical/build', target.name, target.name + '.elf')))}
                -T {repr(str(root('./electrical/build', target.name, 'link.ld')))}
                {' '.join(
                    repr(str(root('./electrical/build', target.name, src.stem + '.o')))
                    for src in target.srcs
                )}
                {target.linker_flags}
        ''')

        # Turn ELF into raw binary.
        execute(f'''
            arm-none-eabi-objcopy
                -S
                -O binary
                {repr(str(root('./electrical/build', target.name, target.name + '.elf')))}
                {repr(str(root('./electrical/build', target.name, target.name + '.bin')))}
        ''')



    # Done!

    log_header(f'Hip-hip hooray! Built {', '.join(f'"{target.name}"' for target in targets)}!')
    for target in targets:
        log(f'# {target.name.ljust(max(len(t.name) for t in targets))}', ansi = 'fg_magenta')



################################################################################################################################



@ui('Flash the binary to the MCU.')
def flash():

    require('STM32_Programmer_CLI')

    stlink   = request_stlinks(specific_one = True)
    attempts = 0

    while True:

        # Maxed out attempts?
        if attempts == 3:
            log()
            with log(ansi = 'fg_red'):
                log('[ERROR] Failed to flash; this might be because...')
                log('        - the binary file haven\'t been built yet.')
                log('        - the ST-Link is being used by a another program.')
                log('        - the ST-Link has disconnected.')
                log('        - ... or something else entirely!')
            sys.exit(1)

        # Not the first try?
        elif attempts:
            log()
            log('[WARNING] Failed to flash (maybe due to verification error); trying again...', ansi = 'fg_yellow')
            log()

        # Try flashing.
        exit_code = execute(f'''
            STM32_Programmer_CLI
                --connect port=SWD index={stlink.probe_index}
                --download {repr(str(root('./electrical/build/NucleoH7S3L8/NucleoH7S3L8.bin')))} 0x08000000
                --verify
                --start
        ''', nonzero_exit_code_ok = True)

        # Try again if needed.
        if exit_code:
            attempts += 1
        else:
            break



################################################################################################################################



@ui('Set up a debugging session.')
def debug(
    just_gdbserver : (bool, 'Just set up the GDB-server and nothing else; mainly used for Visual Studio Code.') = False
):

    require(
        'ST-LINK_gdbserver',
        'STM32_Programmer_CLI',
    )

    apid = 1 # TODO This is the core ID, which varies board to board... Maybe we just hardcode it?

    gdbserver = f'''
        ST-LINK_gdbserver
            --stm32cubeprogrammer-path {repr(str(pathlib.Path(shutil.which('STM32_Programmer_CLI')).parent))}
            --swd
            --apid {apid}
            --verify
            --attach
    '''

    if just_gdbserver:
        execute(gdbserver, keyboard_interrupt_ok = True)
        return

    require('arm-none-eabi-gdb')

    gdb_init = f'''
        file {repr(str(root('./electrical/build/NucleoH7S3L8/NucleoH7S3L8.elf').as_posix()))}
        target extended-remote localhost:61234
        with pagination off -- focus cmd
    '''

    gdb = f'''
        arm-none-eabi-gdb -q {' '.join(f'-ex "{inst.strip()}"' for inst in gdb_init.strip().splitlines())}
    '''

    execute(
        bash                  = f'set -m; {gdbserver} > /dev/null & {gdb}',
        powershell            = f'{gdbserver} & {gdb}',
        keyboard_interrupt_ok = True, # Whenever we halt execution in GDB using CTRL-C, a KeyboardInterrupt exception is raised, but this is a false-positive.
    )



################################################################################################################################



@ui('Search and list for any ST-Links connected to the computer.', name = 'stlinks')
def _():
    if stlinks := request_stlinks():
        log_stlinks(stlinks)
    else:
        log('No ST-Link detected by STM32_Programmer_CLI.')



################################################################################################################################



exit(ui.invoke(sys.argv[1:]))
