import paramiko
import json
import os
import sys

def get_mgmt_and_ilo_info(store_id):
    try:
        json_file_path = f'/opt/airflow/artifacts/{store_id}.json'
        with open(json_file_path, 'r') as json_file:
            store_data = json.load(json_file)
            mgmt_and_ilo_info = {
                "esxi_host": store_data["servers"][0]["mgmtIP"],
                "ilo_host": store_data["servers"][0]["ilohostname"],
                "new_timezone": store_data["StoreInfo"]["edgecpconfigdata"]["ntpinfo"]["timezone"]
            }
            return mgmt_and_ilo_info

    except FileNotFoundError:
        print(f"JSON file not found for store ID {store_id}")
        return None

def update_timezone_ssh(host, new_timezone):
    try:
        # Create an SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Specify the common credentials for both iLO and ESXi
        username = 'root'
        password = 'Password!234'

        # Connect to the host
        ssh.connect(
            host,
            username=username,
            password=password,
            # Add other necessary parameters here (e.g., key_filename='/path/to/private/key')
        )

        # Run a command to update the timezone
        command = f"esxcli hardware clock set --year {new_timezone}"
        stdin, stdout, stderr = ssh.exec_command(command)

        # Check if the command ran successfully
        if stderr.read().decode():
            print(f"Failed to update timezone for host {host}. Error: {stderr.read().decode()}")
        else:
            print(f"Timezone updated successfully for host {host} to {new_timezone}")

    except Exception as e:
        print(f"Failed to update timezone for host {host}. Error: {str(e)}")

    finally:
        # Close the SSH connection
        ssh.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 timezone_update_script.py <store_id>")
        sys.exit(1)

    store_id = sys.argv[1]

    # Get ESXi and iLO information from JSON file based on store ID
    info = get_mgmt_and_ilo_info(store_id)

    if info:
        # Update timezone for ESXi host using SSH
        update_timezone_ssh(info["esxi_host"], info["new_timezone"])

        # Update timezone for iLO using SSH
        update_timezone_ssh(info["ilo_host"], info["new_timezone"])
    else:
        print(f"Failed to retrieve information for store ID {store_id}.")
