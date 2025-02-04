import os
import time
import stat
import subprocess
import requests
from typing import Optional

from log.LogInterface import LogInterface


class SSHHandler:
    """
    Refactored SSH handler that retrieves and saves SSH keys from a remote master node.
    Uses shared helper functions to remove code duplication.
    """

    def __init__(
        self,
        master_ip: str,
        master_port: int,
        public_key_path: str = "/get_ssh_public_key",
        private_key_path: str = "/get_ssh_private_key",
    ):
        """
        Args:
            master_ip (str): The IP address of the master node.
            master_port (int): The port on the master node.
            public_key_path (str): Endpoint for retrieving the public key.
            private_key_path (str): Endpoint for retrieving the private key.
        """
        self.log = LogInterface(verbose=True)
        self.master_ip = master_ip
        self.master_port = master_port
        self.public_key_endpoint = f"http://{master_ip}:{master_port}{public_key_path}"
        self.private_key_endpoint = f"http://{master_ip}:{master_port}{private_key_path}"

    # -------------------------------------------------------------------------
    # Main entry point: register both keys + import private key into ssh-agent
    # -------------------------------------------------------------------------
    def register_ssh_keys(self, max_retries: int = 3) -> bool:
        """Fetch public and private keys, save them, then import private key into SSH agent."""
        # 1) Fetch & save public key
        pub_key = self._fetch_key_data(
            endpoint=self.public_key_endpoint,
            key_type="public_key",
            max_retries=max_retries
        )
        if not pub_key:
            self.log.error("Failed to retrieve the public key after multiple attempts.")
            return False
        self._save_public_key(pub_key)

        # 2) Fetch & save private key
        priv_key = self._fetch_key_data(
            endpoint=self.private_key_endpoint,
            key_type="private_key",
            max_retries=max_retries
        )
        if not priv_key:
            self.log.error("Failed to retrieve the private key after multiple attempts.")
            return False
        self._save_private_key(priv_key)

        # 3) Import private key into SSH agent
        self._import_private_key()
        return True

    # -------------------------------------------------------------------------
    # Shared helper: fetch key data via HTTP GET with retries
    # -------------------------------------------------------------------------
    def _fetch_key_data(self, endpoint: str, key_type: str, max_retries: int) -> Optional[str]:
        """
        Generic key fetching with retry logic. Expects JSON response with 'public_key' or 'private_key'.
        """
        attempt = 0
        while attempt < max_retries:
            attempt += 1
            self.log.info(f"Attempt {attempt} to fetch {key_type} from {endpoint}...")
            try:
                response = requests.get(endpoint, timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    key_value = data.get(key_type, "").strip()
                    if key_value:
                        self.log.info(f"{key_type.capitalize()} retrieved successfully.")
                        return key_value
                    else:
                        self.log.error(f"No '{key_type}' field found in the response.")
                else:
                    self.log.error(
                        f"Failed to fetch {key_type}. HTTP {response.status_code}: {response.text}"
                    )
            except requests.exceptions.RequestException as err:
                self.log.error(f"Exception while fetching {key_type}: {err}")

            self.log.warning("Retrying in 2 seconds...")
            time.sleep(2)

        return None

    # -------------------------------------------------------------------------
    # Public key saving
    # -------------------------------------------------------------------------
    def _save_public_key(self, key_data: str) -> None:
        """
        Always overwrite ~/.ssh/id_rsa.pub and update authorized_keys (remove duplicates first).
        """
        ssh_dir = self._ensure_ssh_dir()
        # 1) Overwrite id_rsa.pub
        pub_key_path = os.path.join(ssh_dir, "id_rsa.pub")
        self._write_file(pub_key_path, key_data)
        self.log.info("Public key has been overwritten in id_rsa.pub.")

        # 2) Update authorized_keys (remove duplicates, then append)
        auth_keys_path = os.path.join(ssh_dir, "authorized_keys")
        self._remove_existing_lines(auth_keys_path, key_data)
        with open(auth_keys_path, "a") as f:
            f.write(key_data + "\n")
        self.log.info("Public key added to authorized_keys (duplicates removed).")

    # -------------------------------------------------------------------------
    # Private key saving
    # -------------------------------------------------------------------------
    def _save_private_key(self, key_data: str) -> None:
        """
        Always overwrite ~/.ssh/id_rsa with the new private key, set 600 permissions.
        """
        ssh_dir = self._ensure_ssh_dir()
        priv_key_path = os.path.join(ssh_dir, "id_rsa")

        # Overwrite the private key file
        self._write_file(priv_key_path, key_data, file_mode=stat.S_IRUSR | stat.S_IWUSR)
        self.log.info("Private key has been overwritten in id_rsa with 600 permissions.")

    # -------------------------------------------------------------------------
    # Import private key into SSH agent (optional)
    # -------------------------------------------------------------------------
    def _import_private_key(self) -> None:
        """
        Ensure an SSH agent is running, then load the private key into it.
        This function will attempt to:
        1) Find an existing agent via SSH_AUTH_SOCK.
        2) If none is found, start a new agent and set SSH_AUTH_SOCK and SSH_AGENT_PID.
        3) Run `ssh-add` to load the private key.
        """
        ssh_dir = os.path.expanduser("~/.ssh")
        priv_key_path = os.path.join(ssh_dir, "id_rsa")

        if not os.path.exists(priv_key_path):
            self.log.warning("No private key found at ~/.ssh/id_rsa; cannot import into SSH agent.")
            return

        # 1) Check if an SSH agent is already running.
        if "SSH_AUTH_SOCK" not in os.environ:
            self.log.warning("No SSH agent detected. Attempting to start one...")
            if not self._start_ssh_agent():
                self.log.error("Failed to start SSH agent. Cannot import private key.")
                return

        # 2) Now that an agent should be running, attempt to add the key.
        try:
            subprocess.run(["ssh-add", priv_key_path], check=True)
            self.log.info("Successfully imported the private key into the SSH agent.")
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to add the private key to SSH agent: {e}")
        except FileNotFoundError:
            self.log.error("ssh-add command not found. Make sure you have OpenSSH client installed.")


    def _start_ssh_agent(self) -> bool:
        """
        Attempt to start a new ssh-agent and set the environment variables
        (SSH_AUTH_SOCK, SSH_AGENT_PID) for the current process.

        Returns:
            bool: True if the agent was started successfully, False otherwise.
        """
        try:
            # Start an ssh-agent in "single run" mode; it will print environment variables to stdout.
            proc = subprocess.Popen(["ssh-agent", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()

            if proc.returncode != 0:
                self.log.error(f"ssh-agent failed to start: {err.decode().strip()}")
                return False

            # Parse the output lines to extract SSH_AUTH_SOCK and SSH_AGENT_PID.
            for line in out.decode().split("\n"):
                if line.startswith("SSH_AUTH_SOCK") or line.startswith("SSH_AGENT_PID"):
                    # Example line: SSH_AUTH_SOCK=/tmp/ssh-oH45SWPEmDCa/agent.12345; export SSH_AUTH_SOCK;
                    key_val = line.split(";")[0]  # e.g., SSH_AUTH_SOCK=/tmp/ssh-agent...
                    if "=" in key_val:
                        env_key, env_val = key_val.split("=", 1)
                        os.environ[env_key] = env_val
                        self.log.info(f"Set {env_key}={env_val}")

            return True

        except FileNotFoundError:
            # ssh-agent is not installed.
            self.log.error("ssh-agent command not found. Make sure you have the OpenSSH client installed.")
            return False
        except Exception as e:
            self.log.error(f"Unexpected error while starting ssh-agent: {e}")
            return False


    # -------------------------------------------------------------------------
    # Helper: ensure ~/.ssh directory exists
    # -------------------------------------------------------------------------
    def _ensure_ssh_dir(self) -> str:
        """Create ~/.ssh if it doesn't exist and return the path."""
        ssh_dir = os.path.expanduser("~/.ssh")
        os.makedirs(ssh_dir, exist_ok=True)
        return ssh_dir

    # -------------------------------------------------------------------------
    # Helper: remove any lines containing 'key_data' from a file
    # -------------------------------------------------------------------------
    def _remove_existing_lines(self, file_path: str, key_data: str) -> None:
        """Remove all lines containing key_data from file_path (if it exists)."""
        if not os.path.exists(file_path):
            return
        with open(file_path, "r") as f:
            lines = f.readlines()

        new_lines = [line for line in lines if key_data not in line]
        with open(file_path, "w") as f:
            f.writelines(new_lines)

    # -------------------------------------------------------------------------
    # Helper: write content to a file, optionally changing permissions
    # -------------------------------------------------------------------------
    def _write_file(self, file_path: str, content: str, file_mode: Optional[int] = None) -> None:
        """Overwrite the file with 'content' and set permissions if provided."""
        with open(file_path, "w") as f:
            f.write(content + "\n")
        if file_mode is not None:
            os.chmod(file_path, file_mode)
