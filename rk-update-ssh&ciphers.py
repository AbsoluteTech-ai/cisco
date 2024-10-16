from radkit_client import ExecResultStatus, DeviceDict, Device
import regex as re

# Define ANSI color codes
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[37m"

# Define global regex patterns for encryption and MAC algorithms
encryption_regex = re.compile(r"Encryption Algorithms:\s*([^\n]+)")
mac_regex = re.compile(r"MAC Algorithms:\s*([^\n]+)")

def colorize(text, color):
    return f"{color}{text}{RESET}"

def format_algorithm_line(label, algorithms, algorithms_to_remove):
    # Determine color for the label based on the algorithms present
    label_color = RED if any(alg in algorithms_to_remove for alg in algorithms) else GREEN

    # Color the algorithms appropriately
    colored_algorithms = [colorize(alg.strip(), RED if alg in algorithms_to_remove else GREEN) for alg in algorithms]

    # Return the formatted line with the colored label and algorithms
    return colorize(label, label_color) + WHITE + ": " + ", ".join(colored_algorithms)

def extract_algorithms(output, regex_pattern):
    match = regex_pattern.search(output)
    return match.group(1).split(',') if match else []

def print_ssh_config_output(command_output, encryption_algorithms_to_remove, mac_algorithms_to_remove):
    # Initialize output to collect specific lines
    output_lines = []
    lines = command_output.split('\n')

    # Initialize flags to determine device status color
    device_has_red = False
    ssh_version_found = False

    for line in lines:
        if "SSH Enabled" in line:
            # Check the SSH version and color accordingly
            version = re.search(r"version (\S+)", line)
            version_color = GREEN if version and version.group(1) == "2.0" else RED
            output_lines.append(colorize(line, version_color))
            if version and version.group(1) == "2.0":
                ssh_version_found = True
        elif "Encryption Algorithms:" in line:
            encryption_algorithms = extract_algorithms(command_output, encryption_regex)
            line_output = format_algorithm_line("Encryption Algorithms", encryption_algorithms, encryption_algorithms_to_remove)
            output_lines.append(line_output)
            if RED in line_output:
                device_has_red = True
        elif "MAC Algorithms:" in line:
            mac_algorithms = extract_algorithms(command_output, mac_regex)
            line_output = format_algorithm_line("MAC Algorithms", mac_algorithms, mac_algorithms_to_remove)
            output_lines.append(line_output)
            if RED in line_output:
                device_has_red = True

    return output_lines, device_has_red, ssh_version_found

def check_and_update_ssh_algorithms(devices):
    if isinstance(devices, DeviceDict):
        ios_devices = devices.filter("device_type", "IOS")
    elif isinstance(devices, Device):
        if devices.device_type != 'IOS':
            raise ValueError("Device not of type IOS")
        ios_devices = devices.singleton()
    else:
        raise ValueError("'devices' must be of type Device or DeviceDict")

    updated_devices = []

    # Encryption and MAC algorithms to remove
    encryption_algorithms_to_remove = ['aes128-cbc', '3des-cbc', 'aes192-cbc', 'aes256-cbc']
    mac_algorithms_to_remove = ['hmac-sha1-96']

    for name, device in ios_devices.items():
        # Execute command to get SSH configuration
        ssh_config = device.exec("show ip ssh").wait()

        # Check if the command result object has 'result' and then check its status
        if not ssh_config or not hasattr(ssh_config, 'result') or ssh_config.result.status != ExecResultStatus.SUCCESS:
            print(colorize(f"Failed to execute 'show ip ssh' on {name}, status was {ssh_config.status if ssh_config else 'None'}", RED))
            continue

        # Access the actual result data from the ssh_config object
        command_result = ssh_config.result
        command_output = command_result.data if hasattr(command_result, 'data') else None

        if not command_output:
            print(colorize(f"No command output available for {name}.", RED))
            continue

        # Print the first SSH configuration output
        print(colorize(f"SSH server status for: ", YELLOW) + name)  # Device name in default white color
        output_lines, device_has_red, ssh_version_found = print_ssh_config_output(command_output, encryption_algorithms_to_remove, mac_algorithms_to_remove)
        for output_line in output_lines:
            print(output_line)

        # Determine device status color after first output
        device_color = RED if device_has_red else GREEN

        # Extract encryption algorithms and MAC algorithms
        encryption_algorithms_found = extract_algorithms(command_output, encryption_regex)
        mac_algorithms_found = extract_algorithms(command_output, mac_regex)

        commands_to_remove = []

        # Check and add commands to remove encryption algorithms
        for algorithm in encryption_algorithms_to_remove:
            if algorithm in encryption_algorithms_found:
                commands_to_remove.append(f"no ip ssh server algorithm encryption {algorithm}")

        # Check and add commands to remove MAC algorithms
        for algorithm in mac_algorithms_to_remove:
            if algorithm in mac_algorithms_found:
                commands_to_remove.append(f"no ip ssh server algorithm mac {algorithm}")

        # Check if SSH version 2 is not found, add the configuration to update it
        if not ssh_version_found:
            print(colorize(f"SSH version 2.0 not found on {name}, updating...", YELLOW))
            commands_to_remove.append("ip ssh version 2")

        if commands_to_remove:
            # Prepare full configuration command list
            config_commands = ["conf t"] + commands_to_remove + ["exit"]

            # Execute configuration changes
            config_result = device.exec("\n".join(config_commands)).wait()

            # Re-run 'show ip ssh' to validate changes
            recheck_config = device.exec("show ip ssh").wait()
            if recheck_config.result.status == ExecResultStatus.SUCCESS:
                recheck_output = recheck_config.result.data if hasattr(recheck_config.result, 'data') else None
                if recheck_output:
                    print(colorize(f"Device {name} updated with SSH configuration changes:", YELLOW))
                    recheck_lines, recheck_has_red, recheck_ssh_version_found = print_ssh_config_output(recheck_output, encryption_algorithms_to_remove, mac_algorithms_to_remove)
                    for recheck_line in recheck_lines:
                        print(recheck_line)

                    # Determine if the update was successful based on the absence of red regex algorithms
                    if recheck_has_red or not recheck_ssh_version_found:
                        print(colorize(f"Device {name} failed to update/insecure.", RED))
                    else:
                        print(colorize(f"Device {name} successfully updated/secure.", GREEN))
                        updated_devices.append(name)
                else:
                    print(colorize(f"No recheck output available for {name}.", RED))
            else:
                print(colorize(f"Failed to re-run 'show ip ssh' on {name}", RED))

    # Print the names of the updated devices
    if updated_devices:
        print(colorize("Devices updated with SSH configuration changes:", GREEN))
        for device in updated_devices:
            print(colorize(device, GREEN))
    else:
        print(colorize("No devices required SSH configuration changes.", RED))

# Call the function
service = direct_login()
check_and_update_ssh_algorithms(service.inventory)
