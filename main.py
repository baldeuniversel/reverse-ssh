import argparse
from ssh_util.reverse_ssh import ReverseSSH
from ssh_util.reverse_ssh_registry import ReverseSSHRegistry
import sys





def main():
    """
    @overview Command-line interface to configure and start a reverse SSH tunnel.
    """

    parser = argparse.ArgumentParser(description="Reverse SSH Tunnel Setup Tool")

    parser.add_argument("--host", help="Remote SSH host (e.g., ssh.example.com)")
    parser.add_argument("--user", help="Username to connect to the remote host")
    parser.add_argument("--remote-port", type=int, default=1248, help="Remote SSH server port (default: 1248)")
    parser.add_argument("--bind-port", type=int, default=8421, help="Remote bind port for the tunnel (default: 8421)")
    parser.add_argument("--local-port", type=int, default=1632, help="Local port to forward to (default: 1632)")

    # For the PID associated with the remote bind
    parser.add_argument("--list-tunnels", action="store_true", help="List active reverse SSH tunnels")
    parser.add_argument("--kill-tunnel", type=int, help="Kill a reverse SSH tunnel by bind port")


    args = parser.parse_args()


    if args.list_tunnels:

        registry = ReverseSSHRegistry()
        tunnels = registry.list_tunnels()

        if not tunnels:
            print("[❗] No active reverse tunnel found")

        else:

            print("🔁 Active Reverse Tunnels : ")

            for bind_port, info in tunnels.items():
                print(f"    - Bind Port: {bind_port}; Remote: {info['remote_user']}@{info['remote_host']}")
        
        sys.exit(0)


    if args.kill_tunnel is not None:

        registry = ReverseSSHRegistry()
        registry.kill_tunnel(args.kill_tunnel)
        
        sys.exit(0)


    # Normal tunnel setup flow
    if not (args.host and args.user):
        parser.error(f"⛔ The following arguments are required for tunnel creation : --host and --user")


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

        print("[✅] Reverse SSH tunnel established successfully\n")

    except Exception as err:
        print(f"[❗] Error : {err}\n")



if __name__ == "__main__":
    main()
