import os
import time
import stat
import subprocess
import requests
from typing import Optional

from log.LogInterface import LogInterface


class SSHHandler:
    """
    Handles fetching and saving of the SSH keys (public and private) from the master node.
    """

    def __init__(
        self,
        master_ip: str,
        master_port: int,
        public_key_path: str = "/get_ssh_public_key",
        private_key_path: str = "/get_ssh_private_key"
    ):
        """
        Args:
            master_ip (str): The IP address of the master node.
            master_port (int): The port of the master node.
            public_key_path (str): The endpoint path to get the SSH public key (default "/get_ssh_public_key").
            private_key_path (str): The endpoint path to get the SSH private key (default "/get_ssh_private_key").
        """
        self.log = LogInterface(verbose=True)  # Adjust verbosity as needed
        self.master_ip = master_ip
        self.master_port = master_port

        # Full endpoint URLs
        self.public_key_endpoint = f"http://{master_ip}:{master_port}{public_key_path}"
        self.private_key_endpoint = f"http://{master_ip}:{master_port}{private_key_path}"

    # -------------------------------------------------------------------------
    # High-Level Method: Retrieve both keys and import them
    # -------------------------------------------------------------------------
    def register_ssh_keys(self, max_retries: int = 5) -> bool:
        """
        Retrieves both the public and private keys from the master node, saves them locally,
        and imports the private key into the SSH agent.

        Args:
            max_retries (int): Number of attempts before giving up on each key.

        Returns:
            bool: True if both keys were successfully retrieved and saved, False otherwise.
        """
        # 1) Retrieve & Save Public Key
        if not self.register_ssh_public_key(max_retries):
            self.log.error("Failed to retrieve and save SSH public key.")
            return False

        # 2) Retrieve & Save Private Key
        if not self.register_ssh_private_key(max_retries):
            self.log.error("Failed to retrieve and save SSH private key.")
            return False

        # 3) Import the private key into the local SSH agent
        self.import_private_key()

        self.log.info("SSH public and private keys successfully registered and imported.")
        return True

    # -------------------------------------------------------------------------
    # Public Key Retrieval
    # -------------------------------------------------------------------------
    def register_ssh_public_key(self, max_retries: int = 5) -> bool:
        """
        Attempt to fetch the SSH public key from the master node multiple times.

        - Saves the public key to authorized_keys (if not already present).
        - Also saves it to ~/.ssh/id_rsa.pub (overwrites any existing file).

        Args:
            max_retries (int): Number of attempts before giving up.

        Returns:
            bool: True if the public key was fetched and saved at any attempt, False otherwise.
        """
        attempt = 0
        while attempt < max_retries:
            success = self._attempt_fetch_ssh_public_key()
            if success:
                return True
            attempt += 1
            self.log.warning(f"Public key fetch attempt {attempt} failed. Retrying in 2 seconds...")
            time.sleep(2)

        self.log.error("All attempts to fetch SSH public key failed.")
        return False

    def _attempt_fetch_ssh_public_key(self) -> bool:
        """
        Single attempt to fetch and save the SSH public key from the master node.

        Returns:
            bool: True on success, False on failure.
        """
        try:
            self.log.info(f"Fetching public key from {self.public_key_endpoint}...")
            response = requests.get(self.public_key_endpoint, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                public_key = data.get("public_key", "").strip()
                if not public_key:
                    self.log.error("No 'public_key' field found in server response.")
                    return False

                # Save public key to authorized_keys and id_rsa.pub
                self.save_ssh_key(public_key)
                self.save_public_key_file(public_key)
                return True
            else:
                self.log.error(
                    f"Failed to fetch SSH public key. "
                    f"Status Code: {response.status_code}, Response: {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            self.log.error(f"Exception during public key fetch: {e}")
            return False

    def save_ssh_key(self, key: str) -> None:
        """
        Saves the given SSH key into the authorized_keys file (if not already present).
        Creates the ~/.ssh folder if needed.
        """
        ssh_dir = os.path.expanduser("~/.ssh")
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, exist_ok=True)

        authorized_keys_path = os.path.join(ssh_dir, "authorized_keys")

        # Check if the key is already present
        existing_keys = ""
        if os.path.exists(authorized_keys_path):
            with open(authorized_keys_path, "r") as ak_file:
                existing_keys = ak_file.read()

        if key not in existing_keys:
            with open(authorized_keys_path, "a") as ak_file:
                ak_file.write(key + "\n")
            self.log.info("Public key has been added to authorized_keys.")
        else:
            self.log.info("Public key already present in authorized_keys. Skipping addition.")

    def save_public_key_file(self, key: str) -> None:
        """
        Overwrite ~/.ssh/id_rsa.pub with the given key.
        """
        pubkey_path = os.path.expanduser("~/.ssh/id_rsa.pub")
        with open(pubkey_path, "w") as pk_file:
            pk_file.write(key + "\n")
        self.log.info("Public key has been written to ~/.ssh/id_rsa.pub.")

    # -------------------------------------------------------------------------
    # Private Key Retrieval
    # -------------------------------------------------------------------------
    def register_ssh_private_key(self, max_retries: int = 5) -> bool:
        """
        Attempt to fetch the SSH private key from the master node multiple times.

        - Saves the private key to ~/.ssh/id_rsa (overwrites any existing file).
        - Sets file permissions to 600.

        Args:
            max_retries (int): Number of attempts before giving up.

        Returns:
            bool: True if the private key was fetched and saved, False otherwise.
        """
        attempt = 0
        while attempt < max_retries:
            success = self._attempt_fetch_ssh_private_key()
            if success:
                return True
            attempt += 1
            self.log.warning(f"Private key fetch attempt {attempt} failed. Retrying in 2 seconds...")
            time.sleep(2)

        self.log.error("All attempts to fetch SSH private key failed.")
        return False

    def _attempt_fetch_ssh_private_key(self) -> bool:
        """
        Single attempt to fetch and save the SSH private key from the master node.

        Returns:
            bool: True on success, False on failure.
        """
        try:
            self.log.info(f"Fetching private key from {self.private_key_endpoint}...")
            response = requests.get(self.private_key_endpoint, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                private_key = data.get("private_key", "").strip()
                if not private_key:
                    self.log.error("No 'private_key' field found in server response.")
                    return False

                # Save private key locally
                self.save_private_key_file(private_key)
                return True
            else:
                self.log.error(
                    f"Failed to fetch SSH private key. "
                    f"Status Code: {response.status_code}, Response: {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            self.log.error(f"Exception during private key fetch: {e}")
            return False

    def save_private_key_file(self, key: str) -> None:
        """
        Writes the given private key into ~/.ssh/id_rsa (overwriting if necessary),
        sets file permissions to 600, and logs the action.
        """
        ssh_dir = os.path.expanduser("~/.ssh")
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, exist_ok=True)

        private_key_path = os.path.join(ssh_dir, "id_rsa")

        with open(private_key_path, "w") as pk_file:
            pk_file.write(key + "\n")

        # Set file permissions to 600 (-rw-------)
        os.chmod(private_key_path, stat.S_IRUSR | stat.S_IWUSR)

        self.log.info("Private key has been written to ~/.ssh/id_rsa with permissions 600.")

    # -------------------------------------------------------------------------
    # Optional: Import the Private Key Into the SSH Agent
    # -------------------------------------------------------------------------
    def import_private_key(self) -> None:
        """
        Attempts to import the private key into the local SSH agent,
        allowing password-less SSH sessions. This step requires that
        'ssh-agent' is running and 'ssh-add' is available on the system.
        """
        private_key_path = os.path.expanduser("~/.ssh/id_rsa")

        # Only attempt if the file exists
        if not os.path.exists(private_key_path):
            self.log.warning("No private key found at ~/.ssh/id_rsa; cannot import to SSH agent.")
            return

        try:
            subprocess.run(["ssh-add", private_key_path], check=True)
            self.log.info("Successfully imported the private key into the SSH agent.")
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to add the private key to SSH agent: {e}")
        except FileNotFoundError:
            self.log.error("ssh-add not found. Ensure that OpenSSH client is installed.")
