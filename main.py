import argparse
from ssh_util.reverse_ssh import ReverseSSH





def main():
    """
    Command-line interface to configure and start a reverse SSH tunnel.
    """

    parser = argparse.ArgumentParser(description="Reverse SSH Tunnel Setup Tool")

    parser.add_argument("--host", required=True, help="Remote SSH host (e.g., ssh.example.com)")
    parser.add_argument("--user", required=True, help="Username to connect to the remote host")
    parser.add_argument("--remote-port", type=int, default=1248, help="Remote SSH server port (default: 1248)")
    parser.add_argument("--bind-port", type=int, default=8421, help="Remote bind port for the tunnel (default: 8421)")
    parser.add_argument("--local-port", type=int, default=1632, help="Local port to forward to (default: 1632)")

    args = parser.parse_args()

    ssh_client = ReverseSSH(
        remote_user=args.user,
        remote_host=args.host,
        remote_bind_port=args.bind_port,
        remote_port=args.remote_port,
        local_port=args.local_port
    )

    print("\n--- Reverse SSH Setup ---\n")

    try:
        ssh_client.ensure_ssh_server()
        ssh_client.generate_ssh_key()
        ssh_client.push_key()
        ssh_client.start_reverse_tunnel()

        print("\n[✅] Reverse SSH tunnel established successfully\n")

    except Exception as e:
        print(f"\n[!] Error : {e}\n")

if __name__ == "__main__":
    main()
