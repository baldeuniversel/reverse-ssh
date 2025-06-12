import os
import json
import signal
from pathlib import Path
import subprocess
import sys





class ReverseSSHRegistry:
    """
    @overview Manages a JSON-based registry of reverse SSH tunnels, allowing them to be listed,
    registered, terminated cleanly. Stores state in a file located at /tmp/.reverse-ssh/reverse_ssh.json.
    """


    def __init__(self, path:str="/tmp/.reverse-ssh/reverse_ssh.json"):
        """
        @overview Initializes the registry manager. Creates the directory and the JSON file if they don't exist.

        :param path {str}: Path to the JSON registry file.
        """

        self.registry_path = Path(path)
        self.registry_dir = self.registry_path.parent
        self.registry_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

        if not self.registry_path.exists():
            self._write_registry({})  # Create empty registry if file does not exist



    def _read_registry(self) -> dict:
        """
        @overview Loads and returns the JSON registry from disk.

        :return {dict}: Dictionary of active tunnels (by bind port).
        """

        try:
            with open(self.registry_path, "r") as f:
                return json.load(f)
            
        except (json.JSONDecodeError, FileNotFoundError):
            return {}  # Return empty registry if file is invalid or missing



    def _write_registry(self, data_dict:dict):
        """
        @overview Writes the given data to the JSON registry file.

        :param data_dict {dict}: Dictionary to write to the file.
        """

        with open(self.registry_path, "w") as f:
            json.dump(data_dict, f, indent=4)



    def register_tunnel(self, bind_port:int, remote_host:str, remote_user:str):
        """
        @overview Adds or updates a reverse SSH tunnel entry in the registry.

        :param bind_port {int}: Remote bind port used in the reverse tunnel.
        :param remote_host {str}: Remote SSH server address.
        :param remote_user {str}: Username used to connect to the remote server.
        """

        data_dict = self._read_registry()
        data_dict[str(bind_port)] = {
            "remote_host": remote_host,
            "remote_user": remote_user
        }

        self._write_registry(data_dict)



    def list_tunnel(self) -> dict:
        """
        @overview Returns the current list of registered reverse SSH tunnels,
        filtering out any tunnels whose process is no longer active.

        :return {dict}: Dictionary mapping active bind ports to tunnel metadata.
        """

        data_dict = self._read_registry()
        active_dict = {}


        for bind_port, metadata in data_dict.items():

            try:

                result = subprocess.run(
                    ["pgrep", "-f", f"{bind_port}:localhost"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                if result.stdout.strip():  # If there's a PID, the process exists
                    active_dict[bind_port] = metadata

            except subprocess.SubprocessError:
                print(f"[ ⚠️  ] Error checking status of port {bind_port}, assuming inactive")
                sys.exit(1)


        if active_dict != data_dict:
            self._write_registry(active_dict)

        else:
            return data_dict

        return active_dict



    def kill_tunnel(self, bind_port:int):
        """
        @overview Terminates the reverse SSH tunnel associated with the given bind port.
        Tries to use `PID` if available, otherwise falls back to searching the SSH process.
        """

        # Declaration variables
        data_dict = self._read_registry()
        bind_port = str(bind_port)
        the_pid = []


        try:

            result = subprocess.run(
                ["pgrep", "-f", f"{bind_port}:localhost"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )

            the_pid = result.stdout.decode().split()

            if not the_pid:
                print(f"[ ⚠️  ] No matching SSH process found for bind port {bind_port}")

            else:

                for found_pid in the_pid:

                    try:
                        os.kill(int(found_pid), signal.SIGTERM)
                        print(f"[✅] Killed tunnel with PID {found_pid} (bind port {bind_port})")

                    except ProcessLookupError:
                        print(f"[ ⚠️  ] Process with PID {found_pid} already gone")

        except subprocess.CalledProcessError:
            print(f"[ ⚠️  ] Failed to find or kill process for bind port {bind_port}")

        # In all cases, remove the entry from the registry
        if bind_port in data_dict:
            del data_dict[bind_port]

        self._write_registry(data_dict)
