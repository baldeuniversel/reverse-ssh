import subprocess
import platform
from pathlib import Path
import shutil
import sys
from ssh_util.reverse_ssh_registry import ReverseSSHRegistry





class ReverseSSH:
    """
    A client for setting up reverse SSH tunnels from the local host to a remote host.
    This includes checking SSH server installation, generating SSH keys, pushing keys to the remote server,
    starting the reverse SSH tunnel.
    """


    def __init__(self, remote_user:str, remote_host:str, remote_bind_port:int, remote_port:int, local_port:int):
        """
        @overview Initializes the client with connection parameters.

        :param remote_user {str}: SSH username for the remote host.
        :param remote_host {str}: SSH hostname or IP.
        :param remote_bind_port {int}: Port to bind on the remote SSH server — acts as the public entry point of the reverse tunnel (used in -R).
        :param remote_port {int}: Port on the remote SSH server that the client connects to (SSH service port, typically 22 but may be customized).
        :param local_port {int}: Local port to forward to (typically 22 for SSH).
        """
        
        self.remote_user = remote_user
        self.remote_host = remote_host
        self.remote_bind_port = remote_bind_port
        self.remote_port = remote_port
        self.local_port = local_port
        self.key_path = Path.home() / ".ssh" / "id_rsa"
        self.pub_key_path = self.key_path.with_suffix(".pub")
        self.system = platform.system()



    def run_cmd(self, cmd:list, shell:bool=False, check=True, return_process=False) -> subprocess.CompletedProcess | str:
        """
        @overview Runs a system command and returns its output.

        :param cmd {list}: List or string of the command to run.
        :param shell {bool}: Whether to use shell mode.
        :param check {bool}: To manage the raised errors (the exceptions).
        :param return_process {bool}: If True, return CompletedProcess object, else return stdout string.

        :return {str}: stdout output as string
        """

        result = subprocess.run(cmd, shell=shell, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if return_process:
            return result
        
        return result.stdout.decode().strip()



    def ensure_ssh_server(self):
        """
        @overview Ensures that the SSH server is installed and running on the local host.
        Supports Linux (apt), macOS, and Windows (PowerShell).
        """

        print(f"[+] Checking SSH server installation on the local host {self.system}...")

        if self.system == "Linux":

            # Check if openssh-server is installed
            if not shutil.which("sshd"):

                print(f"[*] Installing OpenSSH server on the local host {self.system}...")

                try: 

                    self.run_cmd(["sudo", "apt", "update"])
                    self.run_cmd(["sudo", "apt", "install", "-y", "openssh-server"])

                    print(f"[✅] OpenSSH server installed successfully on the local host {self.system}")

                except Exception as err:
                    print(f"[❌] Failed to install the dependencies on the local host {self.system} : {err}")
                    sys.exit(1)

            else:
                print(f"[✅] OpenSSH server installation detected on the local host {self.system}")

            print(f"\n[+] Checking SSH status on the local host {self.system}...")

            # Check if ssh service is active
            result = self.run_cmd(["systemctl", "is-active", "--quiet", "ssh"], check=False, return_process=True)

            if result.returncode != 0:

                print(f"[*] SSH service is not active. Enabling and starting on the local host {self.system}...")

                try:
                    self.run_cmd(["sudo", "systemctl", "enable", "--now", "ssh"])
                    print(f"[✅] SSH service enabled and started successfully on the local host {self.system}")

                except Exception as err:
                    print(f"[❌] Failed to enable/start SSH service on the local host {self.system} : {err}")
                    sys.exit(1)

            else:
                print(f"[✅] SSH service is running on the local host {self.system}")

        else:
            print(f"[❌] Unsupported OS : {self.system}")
            sys.exit(1)



    def validate_ssh_key_pair(self):
        """
        @overview Uses `ssh-keygen -l` to compare fingerprints of private and public SSH keys.
        """

        # Declaration variables
        priv_fingerprint = ""
        pub_fingerprint = ""


        print(f"\n[+] Checking SSH key pair on the local host {self.system}...")
        
        if self.key_path.exists() and self.pub_key_path.exists():
   
            print(f"[✅] SSH key pair detected on the local host {self.system}")
   
            try:
                priv_fingerprint = self.run_cmd(["ssh-keygen", "-l", "-f", str(self.key_path)])
                pub_fingerprint = self.run_cmd(["ssh-keygen", "-l", "-f", str(self.pub_key_path)])

            except Exception as err:
                raise RuntimeError(f"[❌] Could not read fingerprint from SSH keys on the local host {self.system} : {err}")

            # Extract just the SHA256 fingerprint
            priv_fp = priv_fingerprint.split()[1]
            pub_fp = pub_fingerprint.split()[1]

            if priv_fp != pub_fp:
                raise ValueError(f"[❌] SSH Key pair fingerprint mismatched on the local host {self.system} : \nPrivate: {priv_fp}\nPublic: {pub_fp}")
            
            print(f"[✅] SSH key pair fingerprint matched on the local host {self.system}")

        else:
            raise FileNotFoundError(f"[❌] SSH key pair missing on the local host {self.system}")



    def generate_ssh_key(self):
        """
        @overview Generates an SSH key pair if this one doesn't already exist (local host).
        Uses RSA 4096 bits and stores keys in ~/.ssh/ .
        """

        try:
            self.validate_ssh_key_pair()

        except (ValueError, FileNotFoundError) as err:

            print(f"[*] Generating SSH key pair on the local host {self.system}...")

            try:

                self.key_path.parent.mkdir(parents=True, exist_ok=True)

                self.run_cmd([
                    "ssh-keygen", "-t", "rsa", "-b", "4096",
                    "-f", str(self.key_path), "-N", ""
                ])

                print(f"[✅] SSH key pair generated successfully on the local host {self.system}")

            except Exception as err:
                print(f"[❌] Failed to generate SSH key pair on the local host {self.system} : {err}")
                sys.exit(1)

        except RuntimeError as err:
            print(f"[❌] Could not read fingerprint from SSH keys on the local host {self.system} : {err}")
            sys.exit(1)



    def push_key(self):
        """
        @overview Pushes the local public key to the remote server's authorized_keys, if not already present.
        Ensures proper permissions on the remote server's .ssh directory.
        """

        public_key = ""
        check_cmd = ""
        result = ""
        remote_cmd = ""


        if not self.pub_key_path.exists():
            raise RuntimeError(f"[❌] Public key not found on the local host {self.system}")

        with open(self.pub_key_path) as f:
            public_key = f.read().strip()

        print("\n[+] Checking if key is already authorized on remote host...")

        check_cmd = f'grep -Fxq "{public_key}" ~/.ssh/authorized_keys'

        result = subprocess.run(
            ["ssh", f"{self.remote_user}@{self.remote_host}", "-p", str(self.remote_port), check_cmd],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        if result.returncode == 0:
            print("[✅] Key already authorized on the remote host")
            return

        print(f"\n[+] Copying public key from local host {self.system} to remote host...")

        remote_cmd = (
            f'mkdir -p ~/.ssh 2> /dev/null ; '
            f'echo "{public_key}" >> ~/.ssh/authorized_keys && '
            f'chmod 600 ~/.ssh/authorized_keys && chmod 700 ~/.ssh'
        )

        self.run_cmd(["ssh", f"{self.remote_user}@{self.remote_host}", "-p", str(self.remote_port), remote_cmd])



    def start_reverse_tunnel(self):
        """
        @overview Starts the reverse SSH tunnel from the remote host back to the local host.
        Example: ssh -fNR <remote_bind_port>:localhost:<local_port> user@host -p <:remote_port>.
        """

        print(f"\n[+] Starting reverse tunnel : remote_bind_port:{self.remote_bind_port} → local_port:{self.local_port}")

        cmd = [
            "ssh", "-fNR",
            f"{self.remote_bind_port}:localhost:{self.local_port}",
            f"{self.remote_user}@{self.remote_host}",
            "-p", str(self.remote_port),
            "-o", "ExitOnForwardFailure=yes",
            "-o", "StrictHostKeyChecking=no"
        ]

        try:

            # Start the SSH reverse tunnel in the background
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Register in registry
            registry = ReverseSSHRegistry()
            registry.register_tunnel(
                bind_port=self.remote_bind_port,
                remote_host=self.remote_host,
                remote_user=self.remote_user
            )
            
        except subprocess.CalledProcessError as e:
            print(f"[❌] Failed to start reverse tunnel.\n[stderr] : {e.stderr.decode().strip()}")
            raise RuntimeError(f"Reverse SSH tunnel could not be established")
