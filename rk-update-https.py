from radkit_client import ExecResultStatus, DeviceDict, Device
import regex as re

# Define ANSI color codes
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
WHITE = "\033[37m"

# Define regex patterns for HTTP and HTTPS statuses
http_status_regex = re.compile(r"HTTP server status:\s*(\S+)")
https_status_regex = re.compile(r"HTTP secure server status:\s*(\S+)")

def colorize(text, color):
    return f"{color}{text}{RESET}"

def extract_status(output, regex_pattern):
    match = regex_pattern.search(output)
    return match.group(1) if match else None

def print_http_config_output(command_output):
    output_lines = []
    lines = command_output.split('\n')

    # Initialize flags to track the HTTP/HTTPS status
    http_enabled = False
    https_enabled = False

    for line in lines:
        if "HTTP server status:" in line:
            http_status = extract_status(command_output, http_status_regex)
            status_color = RED if http_status == "Enabled" else GREEN
            output_lines.append(colorize(line, status_color))
            http_enabled = http_status == "Enabled"
        elif "HTTP secure server status:" in line:
            https_status = extract_status(command_output, https_status_regex)
            status_color = RED if https_status == "Enabled" else GREEN
            output_lines.append(colorize(line, status_color))
            https_enabled = https_status == "Enabled"

    return output_lines, http_enabled, https_enabled

def check_and_update_http_servers(devices):
    if isinstance(devices, DeviceDict):
        ios_devices = devices.filter("device_type", "IOS")
    elif isinstance(devices, Device):
        if devices.device_type != 'IOS':
            raise ValueError("Device not of type IOS")
        ios_devices = devices.singleton()
    else:
        raise ValueError("'devices' must be of type Device or DeviceDict")

    updated_devices = []

    for name, device in ios_devices.items():
        # Execute command to get HTTP/HTTPS server status
        http_config = device.exec("show ip http server status").wait()

        if not http_config or not hasattr(http_config, 'result') or http_config.result.status != ExecResultStatus.SUCCESS:
            print(colorize(f"Failed to execute 'show ip http server status' on {name}, status was {http_config.status if http_config else 'None'}", RED))
            continue

        # Access the actual result data from the http_config object
        command_result = http_config.result
        command_output = command_result.data if hasattr(command_result, 'data') else None

        if not command_output:
            print(colorize(f"No command output available for {name}.", RED))
            continue

        # Print the current HTTP/HTTPS configuration output
        print(colorize(f"HTTP/HTTPS server status for: ", YELLOW) + name)  # Device name in default white color
        output_lines, http_enabled, https_enabled = print_http_config_output(command_output)
        for output_line in output_lines:
            print(output_line)

        commands_to_configure = []

        # If HTTP is enabled, disable it
        if http_enabled:
            commands_to_configure.append("no ip http server")

        # If HTTPS is enabled, disable it
        if https_enabled:
            commands_to_configure.append("no ip http secure-server")

        if commands_to_configure:
            # Prepare full configuration command list
            config_commands = ["conf t"] + commands_to_configure + ["exit"]

            # Execute configuration changes
            config_result = device.exec("\n".join(config_commands)).wait()

            if config_result.result.status == ExecResultStatus.SUCCESS:
                # Re-run 'show ip http server status' to validate changes
                recheck_config = device.exec("show ip http server status").wait()
                if recheck_config.result.status == ExecResultStatus.SUCCESS:
                    recheck_output = recheck_config.result.data if hasattr(recheck_config.result, 'data') else None
                    if recheck_output:
                        print(colorize(f"Device {name} updated with HTTP/HTTPS configuration changes:", YELLOW))
                        recheck_lines, recheck_http_enabled, recheck_https_enabled = print_http_config_output(recheck_output)
                        for recheck_line in recheck_lines:
                            print(recheck_line)

                        # Determine if the update was successful
                        if recheck_http_enabled:
                            print(colorize(f"Device {name} failed to disable HTTP.", RED))
                        elif recheck_https_enabled:
                            print(colorize(f"Device {name} failed to disable HTTPS.", RED))
                        else:
                            print(colorize(f"Device {name} successfully updated.", GREEN))
                            updated_devices.append(name)
                    else:
                        print(colorize(f"No recheck output available for {name}.", RED))
            else:
                print(colorize(f"Failed to apply configuration changes on {name}.", RED))

    # Print the names of the updated devices
    if updated_devices:
        print(colorize("Devices updated with HTTP/HTTPS configuration changes:", GREEN))
        for device in updated_devices:
            print(colorize(device, GREEN))
    else:
        print(colorize("No devices required HTTP/HTTPS configuration changes.", RED))

# Call the function
service = direct_login()
check_and_update_http_servers(service.inventory)
