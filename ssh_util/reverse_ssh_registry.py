import json
import os
import signal
from pathlib import Path





class ReverseSSHRegistry:
    """
    @overview Manages a JSON-based registry of reverse SSH tunnels, allowing them to be listed,
    registered, terminated cleanly. Stores state in a file located at /tmp/.reverse-ssh/reverse_ssh.json.
    """


    def __init__(self, path="/tmp/.reverse-ssh/reverse_ssh.json"):
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



    def _write_registry(self, data_dict):
        """
        @overview Writes the given data to the JSON registry file.

        :param data_dict {dict}: Dictionary to write to the file.
        """

        with open(self.registry_path, "w") as f:
            json.dump(data_dict, f, indent=4)



    def register_tunnel(self, bind_port:int, remote_host:str, remote_user:str, pid:int):
        """
        @overview Adds or updates a reverse SSH tunnel entry in the registry.

        :param bind_port {int}: Remote bind port used in the reverse tunnel.
        :param remote_host {str}: Remote SSH server address.
        :param remote_user {str}: Username used to connect to the remote server.
        :param pid {int}: PID of the local SSH process maintaining the tunnel.
        """

        data_dict = self._read_registry()
        data_dict[str(bind_port)] = {
            "remote_host": remote_host,
            "remote_user": remote_user,
            "pid": pid
        }

        self._write_registry(data_dict)



    def list_tunnels(self):
        """
        @overview Returns the current list of registered reverse SSH tunnels.

        :return {dict}: Dictionary mapping bind ports to tunnel metadata.
        """

        return self._read_registry()



    def kill_tunnel(self, bind_port:int):
        """
        @overview Terminates the reverse SSH tunnel associated with the given bind port.

        :param bind_port {int}: The bind port whose associated tunnel should be terminated.
        """

        data_dict = self._read_registry()
        bind_port = str(bind_port)

        if bind_port not in data_dict:
            print(f"[!] No active tunnel found for bind port {bind_port}")
            return

        pid = data_dict[bind_port]["pid"]

        try:

            os.kill(pid, signal.SIGTERM)  # Attempt to terminate the SSH process
            print(f"[✅] Killed tunnel with PID {pid} (bind port {bind_port})")

            del data_dict[bind_port]  # Remove entry from registry

            self._write_registry(data_dict)

        except ProcessLookupError:

            # Process may already be gone — clean up stale entry
            print(f"[⚠️] Process with PID {pid} not found. Removing from registry")

            del data_dict[bind_port]

            self._write_registry(data_dict)
