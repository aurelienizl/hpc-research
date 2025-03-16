import sqlite3
import os

from Log.LogInterface import LogInterface

class DatabaseInterface:
    def __init__(self, logger: LogInterface, db_path="files.db"):
        """
        Initialize the Database instance.

        :param db_path: The SQLite database file name.
        """
        self.logger = logger
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

        self.logger.info(f"Database connected: {self.db_path}")

    def create_table(self):
        """
        Create the 'files' table if it doesn't already exist.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id TEXT,
                file_path TEXT,
                content TEXT
            )
        ''')
        self.conn.commit()

    def insert_file(self, file_id, file_path, content=None):
        """
        Insert a single file entry for a given ID.
        If 'content' is not provided, the method tries to read from the file.
        
        :param file_id: The identifier for grouping files.
        :param file_path: Path to the file.
        :param content: Optional pre-read content for the file.
        """
        # Convert Path object to string to avoid PosixPath not supported error
        file_path = str(file_path)
        if content is None:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                except Exception as e:
                    content = f"Error reading file: {e}"
            else:
                content = f"File {file_path} not found."
        
        self.cursor.execute(
            "INSERT INTO files (id, file_path, content) VALUES (?, ?, ?)",
            (file_id, file_path, content)
        )
        self.conn.commit()

    def insert_files_for_id(self, file_id, paths):
        """
        Insert multiple file entries for a given ID.

        :param file_id: The identifier for grouping files.
        :param paths: A list of file paths.
        """
        self.logger.info(f"Inserting files for ID {file_id}")
        self.logger.info(f"Paths: {paths}")
        for path in paths:
            self.insert_file(file_id, path)

    def get_files_by_id(self, file_id):
        """
        Retrieve all file paths and their contents for the given ID.

        :param file_id: The identifier to search for.
        :return: A list of tuples (file_path, content).
        """
        self.cursor.execute("SELECT file_path, content FROM files WHERE id=?", (file_id,))
        return self.cursor.fetchall()
    
    def clear_database(self):
        """
        Clear all data from the database.
        """
        self.cursor.execute("DELETE FROM files")
        self.conn.commit()

    def close(self):
        """
        Close the SQLite connection.
        """
        if self.conn:
            self.conn.close()

    def __del__(self):
        """
        Ensure the connection is closed when the instance is destroyed.
        """
        try:
            self.close()
        except Exception:
            pass

