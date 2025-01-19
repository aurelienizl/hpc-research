import os
from flask import Flask, request, jsonify
from menu_handler import MenuHandler



def create_app(menu_handler: MenuHandler) -> Flask:
    app = Flask(__name__)

    @app.route("/register", methods=["POST"])
    def register_node():
        node_data = request.get_json() or {}
        node_ip = request.remote_addr  # Directly obtain the client's IP
        print(f"Received registration request from IP: {node_ip}")
        node_entry = menu_handler.register_node(node_ip, node_data)
        return jsonify({"status": "registered", "node": node_entry}), 200

    @app.route("/get_ssh_public_key", methods=["GET"])
    def get_ssh_public_key():
        """
        Return the public key content from ~/.ssh/id_rsa.pub.
        """
        home_dir = os.path.expanduser("~")
        public_key_path = os.path.join(home_dir, ".ssh", "id_rsa.pub")

        if not os.path.exists(public_key_path):
            return jsonify({"error": "No public key found on the server"}), 404

        with open(public_key_path, "r") as f:
            pubkey_data = f.read().strip()

        return jsonify({"public_key": pubkey_data}), 200
    
    @app.route("/get_ssh_private_key", methods=["GET"])
    def get_ssh_private_key():
        """
        Return the private key content from ~/.ssh/id_rsa.
        """
        home_dir = os.path.expanduser("~")
        private_key_path = os.path.join(home_dir, ".ssh", "id_rsa")

        if not os.path.exists(private_key_path):
            return jsonify({"error": "No private key found on the server"}), 404

        with open(private_key_path, "r") as f:
            private_data = f.read().strip()

        return jsonify({"private_key": private_data}), 200


    return app
