import os

from pathlib import Path
from Log.LogInterface import LogInterface  

class SSHKeyManager:
    def __init__(self, log_interface: LogInterface):
        self.ssh_dir = Path.home() / '.ssh'
        self.auth_keys_file = self.ssh_dir / 'authorized_keys'
        self.logger = log_interface
        self.logger.info("Initializing SSHKeyManager")

    def add_public_key(self, public_key: str) -> bool:
        """
        Add a public SSH key to the authorized_keys file
        
        Args:
            public_key (str): The SSH public key to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Adding public key to authorized keys: {public_key}")
            self.ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            if not self.auth_keys_file.exists():
                self.auth_keys_file.touch(mode=0o600)
            
            clean_key = public_key.strip()
            
            existing_keys = set()
            if self.auth_keys_file.exists():
                with open(self.auth_keys_file, 'r') as f:
                    existing_keys = set(f.read().splitlines())
            
            if clean_key not in existing_keys:
                with open(self.auth_keys_file, 'a') as f:
                    f.write(f"{clean_key}\n")
            
            os.chmod(self.auth_keys_file, 0o600)
             
            self.logger.info("Public key added successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add public key: {str(e)}")
            return False