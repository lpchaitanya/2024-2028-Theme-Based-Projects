"""
ImageShield Backend: Secure PNG/JPG Image Encryption Tool
BE CSE(IOT-CS-BCT) – Sem IV 2025 – 2026 Batch-No: 1

This module handles all backend operations including:
- Image encryption/decryption using AES (Fernet)
- Key management and derivation
- Database operations
- Security and lockout mechanisms
- File integrity verification
"""

import os
import io
import sqlite3
import hashlib
import hmac
import time
import threading
import re
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from PIL import Image
import base64
import json


# ==================== DATABASE MODULE ====================

class DatabaseModule:
    """Handles all SQLite database operations for storing encrypted files and metadata."""
    
    def __init__(self, db_path='imageshield.db'):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.conn = None
        self.lock = threading.Lock()  # Thread safety lock
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        try:
            # Allow connection to be used across threads, with check_same_thread=False
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # Create encrypted files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS encrypted_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    original_filename TEXT NOT NULL,
                    display_name TEXT,
                    file_format TEXT NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    file_size INTEGER NOT NULL,
                    encryption_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hmac_tag TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    tags TEXT
                )
            ''')
            
            # Create metadata index table for fast queries
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metadata_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    display_name TEXT,
                    format TEXT NOT NULL,
                    size INTEGER,
                    date TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES encrypted_files(file_id)
                )
            ''')
            
            # Add display_name column if it doesn't exist (for existing databases)
            cursor.execute("PRAGMA table_info(encrypted_files)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'display_name' not in columns:
                cursor.execute('ALTER TABLE encrypted_files ADD COLUMN display_name TEXT')
            
            cursor.execute("PRAGMA table_info(metadata_index)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'display_name' not in columns:
                cursor.execute('ALTER TABLE metadata_index ADD COLUMN display_name TEXT')
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
    
    def insert_encrypted_file(self, file_id, original_filename, file_format, 
                              encrypted_data, hmac_tag, salt, file_size, tags=None, display_name=None):
        with self.lock:  # Thread-safe database access
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO encrypted_files 
                    (file_id, original_filename, display_name, file_format, encrypted_data, 
                     hmac_tag, salt, file_size, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (file_id, original_filename, display_name, file_format, encrypted_data, 
                      hmac_tag, salt, file_size, tags))
                
                # Update metadata index
                cursor.execute('''
                    INSERT INTO metadata_index (file_id, filename, display_name, format, size, date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (file_id, original_filename, display_name, file_format, file_size, 
                      datetime.now().isoformat()))
                
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error inserting encrypted file: {e}")
                return False
    
    def retrieve_encrypted_file(self, file_id):
        """Retrieve encrypted file and metadata from database."""
        with self.lock:  # Thread-safe database access
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT file_id, original_filename, file_format, encrypted_data, 
                           hmac_tag, salt, file_size, encryption_date, tags
                    FROM encrypted_files
                    WHERE file_id = ?
                ''', (file_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'file_id': result[0],
                        'original_filename': result[1],
                        'file_format': result[2],
                        'encrypted_data': result[3],
                        'hmac_tag': result[4],
                        'salt': result[5],
                        'file_size': result[6],
                        'encryption_date': result[7],
                        'tags': result[8]
                    }
                return None
            except sqlite3.Error as e:
                print(f"Error retrieving file: {e}")
                return None
    
    def get_all_files_metadata(self):
        """Get metadata of all encrypted files (for gallery view)."""
        with self.lock:  # Thread-safe database access
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT file_id, filename, display_name, format, size, date
                    FROM metadata_index
                    ORDER BY date DESC
                ''')
                
                results = cursor.fetchall()
                files = []
                for row in results:
                    files.append({
                        'file_id': row[0],
                        'filename': row[1],
                        'display_name': row[2],
                        'format': row[3],
                        'size': row[4],
                        'date': row[5]
                    })
                return files
            except sqlite3.Error as e:
                print(f"Error retrieving metadata: {e}")
                return []
    
    def delete_encrypted_file(self, file_id):
        with self.lock:  # Thread-safe database access
            try:
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM encrypted_files WHERE file_id = ?', (file_id,))
                cursor.execute('DELETE FROM metadata_index WHERE file_id = ?', (file_id,))
                self.conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error deleting file: {e}")
                print(f"Error deleting file: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


# ==================== KEY MANAGEMENT MODULE ====================

class KeyManagementModule:
    """Handles password-based key derivation and key generation."""
    
    SALT_LENGTH = 16  # 16 bytes salt
    ITERATIONS = 100000  # PBKDF2 iterations
    
    @staticmethod
    def generate_salt():
        """Generate random salt for key derivation."""
        return os.urandom(KeyManagementModule.SALT_LENGTH)
    
    @staticmethod
    def derive_key_from_password(password, salt):
        """
        Derive 32-byte encryption key from password using PBKDF2.
        
        Args:
            password (str): User password
            salt (bytes): Random salt
            
        Returns:
            bytes: 32-byte derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=KeyManagementModule.ITERATIONS,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode())
        return key


# ==================== IMAGE INPUT/OUTPUT MODULE ====================

class ImageInputOutputModule:
    """Handles image file loading, saving, and format validation."""
    
    SUPPORTED_FORMATS = ['JPG', 'JPEG', 'PNG']
    
    @staticmethod
    def load_image(image_path):
        """
        Load image from file and convert to byte array.
        
        Args:
            image_path (str): Path to image file
            
        Returns:
            tuple: (image_bytes, format, filename) or (None, None, None) on error
        """
        try:
            if not os.path.exists(image_path):
                print(f"Image file not found: {image_path}")
                return None, None, None
            
            # Get file format
            file_ext = os.path.splitext(image_path)[1].upper().strip('.')
            if file_ext not in ImageInputOutputModule.SUPPORTED_FORMATS:
                print(f"Unsupported format: {file_ext}")
                return None, None, None
            
            # Load image with Pillow
            img = Image.open(image_path)
            
            # Normalize format for PIL (JPG -> JPEG)
            pil_format = 'JPEG' if file_ext == 'JPG' else file_ext

            # JPEG cannot store transparency or palette-based modes directly.
            # Convert to RGB first when needed so PNGs with alpha can be handled.
            if pil_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format=pil_format)
            image_bytes = img_byte_arr.getvalue()
            
            filename = os.path.basename(image_path)
            
            return image_bytes, file_ext, filename
        except Exception as e:
            print(f"Error loading image: {e}")
            return None, None, None
    
    @staticmethod
    def save_image(image_bytes, image_format, output_path):
        """
        Save image from byte array to file.
        
        Args:
            image_bytes (bytes): Image data
            image_format (str): Image format (JPG, PNG, etc.)
            output_path (str): Path to save image
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Normalize format for PIL (JPG -> JPEG)
            pil_format = 'JPEG' if image_format == 'JPG' else image_format

            # JPEG cannot store transparency or palette-based modes directly.
            # Convert to RGB before saving when the target format is JPEG.
            if pil_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            img.save(output_path, format=pil_format)
            return True
        except Exception as e:
            print(f"Error saving image: {e}")
            return False

    @staticmethod
    def build_encrypted_file_path(source_image_path, display_name=None):
        """Build a filesystem-safe .enc output path for an encrypted file."""
        source_dir = os.path.dirname(source_image_path) or os.getcwd()
        base_name = display_name or os.path.splitext(os.path.basename(source_image_path))[0]
        safe_name = re.sub(r'[^A-Za-z0-9._-]+', '_', base_name).strip('._-')
        if not safe_name:
            safe_name = os.path.splitext(os.path.basename(source_image_path))[0]
        return os.path.join(source_dir, f"{safe_name}.enc")

    @staticmethod
    def save_encrypted_file(encrypted_data, source_image_path, display_name=None):
        """Save encrypted payload and metadata to a standalone .enc file."""
        # Kept for backward compatibility; new code should use save_encrypted_package().
        print("Error saving encrypted file: use save_encrypted_package() for .enc exports")
        return None

    @staticmethod
    def save_encrypted_package(encrypted_data, salt, hmac_tag, source_image_path,
                               display_name=None, original_filename=None,
                               file_format=None, output_path=None):
        """Save a self-contained encrypted package as a .enc JSON file."""
        try:
            if output_path is None:
                output_path = ImageInputOutputModule.build_encrypted_file_path(
                    source_image_path,
                    display_name
                )
            package = {
                'version': 1,
                'original_filename': original_filename or os.path.basename(source_image_path),
                'display_name': display_name or original_filename or os.path.basename(source_image_path),
                'file_format': file_format or os.path.splitext(source_image_path)[1].upper().strip('.'),
                'salt': base64.b64encode(salt).decode(),
                'hmac_tag': hmac_tag,
                'encrypted_data': base64.b64encode(encrypted_data).decode(),
                'created_at': datetime.now().isoformat()
            }
            with open(output_path, 'w', encoding='utf-8') as file_handle:
                json.dump(package, file_handle, indent=2)
            return output_path
        except Exception as e:
            print(f"Error saving encrypted package: {e}")
            return None

    @staticmethod
    def load_encrypted_package(enc_path):
        """Load a self-contained encrypted package from a .enc file."""
        try:
            if not os.path.exists(enc_path):
                print(f"Encrypted file not found: {enc_path}")
                return None

            with open(enc_path, 'rb') as file_handle:
                raw_data = file_handle.read()

            try:
                package = json.loads(raw_data.decode('utf-8'))
            except Exception:
                print(f"Unsupported .enc format: {enc_path} (legacy binary file or non-JSON package)")
                return None

            required_keys = {'version', 'original_filename', 'file_format', 'salt', 'hmac_tag', 'encrypted_data'}
            if not required_keys.issubset(package.keys()):
                print(f"Invalid encrypted package: missing keys in {enc_path}")
                return None

            package['salt'] = base64.b64decode(package['salt'])
            package['encrypted_data'] = base64.b64decode(package['encrypted_data'])
            return package
        except Exception as e:
            print(f"Error loading encrypted package: {e}")
            return None
    
    @staticmethod
    def get_image_preview(image_bytes):
        """
        Generate thumbnail preview from image bytes.
        
        Args:
            image_bytes (bytes): Image data
            
        Returns:
            PIL.Image: Thumbnail image object
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail((150, 150))
            return img
        except Exception as e:
            print(f"Error creating preview: {e}")
            return None


# ==================== ENCRYPTION ENGINE ====================

class EncryptionEngine:
    """Handles image encryption using AES-128-CBC via Fernet."""
    
    @staticmethod
    def encrypt_image(image_bytes, encryption_key):
        """
        Encrypt image bytes using AES algorithm via Fernet.
        
        Args:
            image_bytes (bytes): Original image data
            encryption_key (bytes): 32-byte encryption key
            
        Returns:
            bytes: Encrypted image data
        """
        try:
            # Generate Fernet key from derived key
            fernet_key = base64.urlsafe_b64encode(encryption_key)
            fernet = Fernet(fernet_key)
            
            # Encrypt image bytes
            encrypted_data = fernet.encrypt(image_bytes)
            
            return encrypted_data
        except Exception as e:
            print(f"Encryption error: {e}")
            return None


# ==================== DECRYPTION ENGINE ====================

class DecryptionEngine:
    """Handles image decryption using AES algorithm via Fernet."""
    
    @staticmethod
    def decrypt_image(encrypted_data, encryption_key):
        """
        Decrypt image bytes using AES algorithm via Fernet.
        
        Args:
            encrypted_data (bytes): Encrypted image data
            encryption_key (bytes): 32-byte encryption key
            
        Returns:
            bytes: Decrypted image data or None on failure
        """
        try:
            # Generate Fernet key from derived key
            fernet_key = base64.urlsafe_b64encode(encryption_key)
            fernet = Fernet(fernet_key)
            
            # Decrypt image bytes
            decrypted_data = fernet.decrypt(encrypted_data)
            
            return decrypted_data
        except Exception as e:
            print(f"Decryption error: {e}")
            return None


# ==================== SECURITY CONTROLLER ====================

class SecurityController:
    """Manages password attempts, lockout mechanism, and integrity verification."""
    
    FAILED_ATTEMPTS_LIMIT = 3
    LOCKOUT_DURATION = 30  # seconds
    
    def __init__(self):
        """Initialize security controller."""
        self.failed_attempts = 0
        self.lockout_until = None
    
    def is_locked_out(self):
        """
        Check if system is currently locked out.
        
        Returns:
            bool: True if locked out, False otherwise
        """
        if self.lockout_until is None:
            return False
        
        if datetime.now() >= self.lockout_until:
            self.lockout_until = None
            self.failed_attempts = 0
            return False
        
        return True
    
    def get_remaining_lockout_time(self):
        """
        Get remaining lockout time in seconds.
        
        Returns:
            int: Seconds remaining, 0 if not locked out
        """
        if not self.is_locked_out():
            return 0
        
        remaining = (self.lockout_until - datetime.now()).total_seconds()
        return max(0, int(remaining))
    
    def record_failed_attempt(self):
        """Record a failed decryption attempt."""
        self.failed_attempts += 1
        
        if self.failed_attempts >= self.FAILED_ATTEMPTS_LIMIT:
            self.lockout_until = datetime.now() + timedelta(seconds=self.LOCKOUT_DURATION)
            return f"Too many failed attempts. Locked out for {self.LOCKOUT_DURATION} seconds."
        
        remaining_attempts = self.FAILED_ATTEMPTS_LIMIT - self.failed_attempts
        return f"Password incorrect. {remaining_attempts} attempts remaining."
    
    def reset_attempts(self):
        """Reset failed attempts on successful authentication."""
        self.failed_attempts = 0
        self.lockout_until = None
    
    @staticmethod
    def generate_hmac(data, key):
        """
        Generate HMAC for data integrity verification.
        
        Args:
            data (bytes): Data to authenticate
            key (bytes): Secret key
            
        Returns:
            str: HMAC tag (hex string)
        """
        hmac_obj = hmac.new(key, data, hashlib.sha256)
        return hmac_obj.hexdigest()
    
    @staticmethod
    def verify_hmac(data, key, hmac_tag):
        """
        Verify HMAC for data integrity.
        
        Args:
            data (bytes): Original data
            key (bytes): Secret key
            hmac_tag (str): HMAC tag to verify against
            
        Returns:
            bool: True if HMAC matches, False otherwise
        """
        calculated_hmac = SecurityController.generate_hmac(data, key)
        return hmac.compare_digest(calculated_hmac, hmac_tag)


# ==================== MAIN BACKEND COORDINATOR ====================

class ImageShieldBackend:
    """Main backend coordinator that orchestrates all operations."""
    
    def __init__(self, db_path='imageshield.db'):
        """Initialize backend modules."""
        self.db = DatabaseModule(db_path)
        self.image_io = ImageInputOutputModule()
        self.security = SecurityController()
        self.encryption = EncryptionEngine()
        self.decryption = DecryptionEngine()
    
    def encrypt_image_file(self, image_path, password, tags=None, display_name=None, output_path=None):
        """
        Complete encryption workflow: load image, derive key, encrypt, store in DB.
        
        Args:
            image_path (str): Path to image file
            password (str): User password
            tags (str): Optional tags for the encrypted file
            display_name (str): Optional custom name to display in gallery
            
        Returns:
            dict: Result dictionary with status and message
        """
        try:
            # Load image
            image_bytes, image_format, filename = self.image_io.load_image(image_path)
            if image_bytes is None:
                return {
                    'success': False,
                    'message': 'Failed to load image file'
                }
            
            # Generate salt and derive key
            salt = KeyManagementModule.generate_salt()
            encryption_key = KeyManagementModule.derive_key_from_password(password, salt)
            
            # Encrypt image
            encrypted_data = self.encryption.encrypt_image(image_bytes, encryption_key)
            if encrypted_data is None:
                return {
                    'success': False,
                    'message': 'Failed to encrypt image'
                }
            
            # Generate HMAC for integrity verification
            hmac_tag = SecurityController.generate_hmac(encrypted_data, encryption_key)

            # Save a standalone .enc file alongside the original image
            encrypted_file_path = self.image_io.save_encrypted_package(
                encrypted_data,
                salt,
                hmac_tag,
                image_path,
                display_name=display_name or filename,
                output_path=output_path
            )
            if not encrypted_file_path:
                return {
                    'success': False,
                    'message': 'Failed to create .enc file'
                }
            
            # Generate file ID
            file_id = hashlib.sha256(
                (filename + datetime.now().isoformat()).encode()
            ).hexdigest()[:16]
            
            # Store in database
            success = self.db.insert_encrypted_file(
                file_id=file_id,
                original_filename=filename,
                file_format=image_format,
                encrypted_data=encrypted_data,
                hmac_tag=hmac_tag,
                salt=base64.b64encode(salt).decode(),
                file_size=len(image_bytes),
                tags=tags,
                display_name=display_name or filename
            )
            
            if success:
                return {
                    'success': True,
                    'message': f'Image encrypted successfully. File ID: {file_id}',
                    'file_id': file_id,
                    'encrypted_size': len(encrypted_data),
                    'encrypted_file_path': encrypted_file_path
                }
            else:
                try:
                    if encrypted_file_path and os.path.exists(encrypted_file_path):
                        os.remove(encrypted_file_path)
                except OSError:
                    pass
                return {
                    'success': False,
                    'message': 'Failed to store encrypted file'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Encryption error: {str(e)}'
            }

    def decrypt_encrypted_package_file(self, enc_path, password, output_path=None, preview_only=False):
        """Decrypt a standalone .enc package file from disk."""
        try:
            if self.security.is_locked_out():
                remaining_time = self.security.get_remaining_lockout_time()
                return {
                    'success': False,
                    'message': f'System locked out. Try again in {remaining_time} seconds.',
                    'locked_out': True,
                    'remaining_time': remaining_time
                }

            package = self.image_io.load_encrypted_package(enc_path)
            if package is None:
                return {
                    'success': False,
                    'message': 'Invalid or unsupported .enc file'
                }

            encryption_key = KeyManagementModule.derive_key_from_password(password, package['salt'])

            if not SecurityController.verify_hmac(
                package['encrypted_data'],
                encryption_key,
                package['hmac_tag']
            ):
                error_msg = self.security.record_failed_attempt()
                return {
                    'success': False,
                    'message': error_msg,
                    'wrong_password': True
                }

            decrypted_bytes = self.decryption.decrypt_image(
                package['encrypted_data'],
                encryption_key
            )

            if decrypted_bytes is None:
                self.security.record_failed_attempt()
                return {
                    'success': False,
                    'message': 'Decryption failed - password incorrect'
                }

            self.security.reset_attempts()

            if preview_only:
                return {
                    'success': True,
                    'message': 'Preview generated successfully',
                    'image_bytes': decrypted_bytes,
                    'original_filename': package['original_filename'],
                    'display_name': package.get('display_name'),
                    'image_format': package['file_format']
                }

            if output_path:
                success = self.image_io.save_image(
                    decrypted_bytes,
                    package['file_format'],
                    output_path
                )
                if not success:
                    return {
                        'success': False,
                        'message': 'Failed to save decrypted image'
                    }

            return {
                'success': True,
                'message': 'Image decrypted successfully',
                'image_bytes': decrypted_bytes,
                'original_filename': package['original_filename'],
                'display_name': package.get('display_name'),
                'image_format': package['file_format']
            }

        except Exception as e:
            self.security.record_failed_attempt()
            return {
                'success': False,
                'message': f'Decryption error: {str(e)}'
            }
    
    def decrypt_image_file(self, file_id, password, output_path=None, preview_only=False):
        """
        Complete decryption workflow: retrieve from DB, verify, decrypt, save.
        
        Args:
            file_id (str): ID of encrypted file
            password (str): User password
            output_path (str): Optional path to save decrypted image
            preview_only (bool): If True, only return image bytes without saving
            
        Returns:
            dict: Result dictionary with status and decrypted image bytes
        """
        try:
            # Check lockout status
            if self.security.is_locked_out():
                remaining_time = self.security.get_remaining_lockout_time()
                return {
                    'success': False,
                    'message': f'System locked out. Try again in {remaining_time} seconds.',
                    'locked_out': True,
                    'remaining_time': remaining_time
                }
            
            # Retrieve from database
            file_data = self.db.retrieve_encrypted_file(file_id)
            if file_data is None:
                return {
                    'success': False,
                    'message': 'File not found in database'
                }
            
            # Derive key from password
            salt = base64.b64decode(file_data['salt'])
            encryption_key = KeyManagementModule.derive_key_from_password(password, salt)
            
            # Verify HMAC
            if not SecurityController.verify_hmac(
                file_data['encrypted_data'], 
                encryption_key, 
                file_data['hmac_tag']
            ):
                error_msg = self.security.record_failed_attempt()
                return {
                    'success': False,
                    'message': error_msg,
                    'wrong_password': True
                }
            
            # Decrypt image
            decrypted_bytes = self.decryption.decrypt_image(
                file_data['encrypted_data'], 
                encryption_key
            )
            
            if decrypted_bytes is None:
                self.security.record_failed_attempt()
                return {
                    'success': False,
                    'message': 'Decryption failed - password incorrect'
                }
            
            # Reset attempts on successful decryption
            self.security.reset_attempts()
            
            # If preview only, return the image bytes without saving
            if preview_only:
                return {
                    'success': True,
                    'message': 'Preview generated successfully',
                    'image_bytes': decrypted_bytes,
                    'original_filename': file_data['original_filename'],
                    'image_format': file_data['file_format']
                }
            
            # Save to file if output path provided
            if output_path:
                success = self.image_io.save_image(
                    decrypted_bytes,
                    file_data['file_format'],
                    output_path
                )
                if not success:
                    return {
                        'success': False,
                        'message': 'Failed to save decrypted image'
                    }
            
            return {
                'success': True,
                'message': 'Image decrypted successfully',
                'image_bytes': decrypted_bytes,
                'original_filename': file_data['original_filename'],
                'image_format': file_data['file_format']
            }
        
        except Exception as e:
            self.security.record_failed_attempt()
            return {
                'success': False,
                'message': f'Decryption error: {str(e)}'
            }
    
    def get_gallery_files(self):
        """
        Get metadata of all encrypted files for gallery view.
        
        Returns:
            list: List of file metadata dictionaries
        """
        return self.db.get_all_files_metadata()
    
    def delete_file(self, file_id):
        """
        Delete encrypted file from database.
        
        Args:
            file_id (str): ID of file to delete
            
        Returns:
            dict: Result dictionary
        """
        try:
            success = self.db.delete_encrypted_file(file_id)
            if success:
                return {
                    'success': True,
                    'message': 'File deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to delete file'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'Delete error: {str(e)}'
            }
    
    def encrypt_text_to_file(self, text, password, output_path, display_name=None):
        """
        Encrypt a text string and save it to a standalone .enc file package.
        
        Args:
            text (str): Input text string to encrypt
            password (str): User password
            output_path (str): File path to save the .enc package
            display_name (str): Optional display name for the text
            
        Returns:
            dict: Result dictionary with success/message status
        """
        try:
            if not text:
                return {
                    'success': False,
                    'message': 'Text is empty'
                }
            
            # Encode text to bytes
            text_bytes = text.encode('utf-8')
            
            # Generate salt and derive key
            salt = KeyManagementModule.generate_salt()
            encryption_key = KeyManagementModule.derive_key_from_password(password, salt)
            
            # Encrypt text bytes using Fernet AES
            encrypted_data = self.encryption.encrypt_image(text_bytes, encryption_key)
            if encrypted_data is None:
                return {
                    'success': False,
                    'message': 'Failed to encrypt text'
                }
            
            # Generate HMAC for integrity verification
            hmac_tag = SecurityController.generate_hmac(encrypted_data, encryption_key)
            
            # Save standalone JSON package with format "TXT"
            filename = os.path.basename(output_path)
            encrypted_file_path = self.image_io.save_encrypted_package(
                encrypted_data=encrypted_data,
                salt=salt,
                hmac_tag=hmac_tag,
                source_image_path=output_path,
                display_name=display_name or filename,
                original_filename=filename,
                file_format='TXT',
                output_path=output_path
            )
            
            if encrypted_file_path:
                return {
                    'success': True,
                    'message': 'Text encrypted and saved successfully',
                    'encrypted_file_path': encrypted_file_path
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to save encrypted text file'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Text encryption error: {str(e)}'
            }

    def decrypt_text_from_file(self, enc_path, password):
        """
        Decrypt a text string from a standalone .enc package file.
        
        Args:
            enc_path (str): Path to .enc file
            password (str): User password
            
        Returns:
            dict: Result dictionary with success, decrypted text string or error
        """
        try:
            # Check lockout status
            if self.security.is_locked_out():
                remaining_time = self.security.get_remaining_lockout_time()
                return {
                    'success': False,
                    'message': f'System locked out. Try again in {remaining_time} seconds.',
                    'locked_out': True,
                    'remaining_time': remaining_time
                }
            
            # Load package
            package = self.image_io.load_encrypted_package(enc_path)
            if package is None:
                return {
                    'success': False,
                    'message': 'Invalid or unsupported .enc file'
                }
            
            # Derive key
            encryption_key = KeyManagementModule.derive_key_from_password(password, package['salt'])
            
            # Verify HMAC integrity
            if not SecurityController.verify_hmac(
                package['encrypted_data'],
                encryption_key,
                package['hmac_tag']
            ):
                error_msg = self.security.record_failed_attempt()
                return {
                    'success': False,
                    'message': error_msg,
                    'wrong_password': True
                }
            
            # Decrypt bytes
            decrypted_bytes = self.decryption.decrypt_image(
                package['encrypted_data'],
                encryption_key
            )
            
            if decrypted_bytes is None:
                self.security.record_failed_attempt()
                return {
                    'success': False,
                    'message': 'Decryption failed - password incorrect'
                }
            
            # Reset security attempts
            self.security.reset_attempts()
            
            # Decode bytes back to UTF-8 text string
            decrypted_text = decrypted_bytes.decode('utf-8')
            
            return {
                'success': True,
                'message': 'Text decrypted successfully',
                'text': decrypted_text,
                'original_filename': package.get('original_filename'),
                'display_name': package.get('display_name'),
                'created_at': package.get('created_at')
            }
            
        except Exception as e:
            self.security.record_failed_attempt()
            return {
                'success': False,
                'message': f'Text decryption error: {str(e)}'
            }
    
    def close(self):
        """Close database connection."""
        self.db.close()


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Initialize backend
    backend = ImageShieldBackend()
    
    print("ImageShield Backend initialized successfully!")
    print("\nAvailable operations:")
    print("- encrypt_image_file(image_path, password, tags)")
    print("- decrypt_image_file(file_id, password, output_path)")
    print("- get_gallery_files()")
    print("- delete_file(file_id)")
    print("- close()")
