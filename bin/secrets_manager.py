#!/usr/bin/env python3
"""
Secrets Manager for HA AI Gen Workflow
Handles encryption, storage and restoration of sensitive data.
"""

import os
import sys
import json
import base64
import hashlib
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Try to import cryptography, fall back to basic encoding if not available
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠ cryptography not installed. Using base64 encoding (not secure for production)")


class SecretsManager:
    """Manages encryption and storage of secrets with labeled placeholders."""
    
    def __init__(self, secrets_dir: str = "./secrets", label_prefix: str = "HA_SECRET"):
        """Initialize secrets manager.
        
        Args:
            secrets_dir: Directory to store encrypted secrets
            label_prefix: Prefix for secret labels
        """
        self.secrets_dir = Path(secrets_dir)
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        
        self.label_prefix = label_prefix
        self.secrets_file = self.secrets_dir / "secrets_vault.enc"
        self.mapping_file = self.secrets_dir / "secrets_mapping.json"
        self.key_file = self.secrets_dir / ".encryption_key"
        
        self._fernet = None
        self._secrets: Dict[str, Any] = {}
        self._mapping: Dict[str, Dict] = {}  # label -> {type, description, hash}
        self._counter = 0
        
        self._init_encryption()
        self._load_existing()
    
    def _init_encryption(self):
        """Initialize or load encryption key."""
        if not CRYPTO_AVAILABLE:
            return
        
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)  # Restrict permissions
            print(f"✓ New encryption key generated: {self.key_file}")
        
        self._fernet = Fernet(key)
    
    def _load_existing(self):
        """Load existing secrets and mapping if available."""
        # Load mapping (unencrypted - contains only labels and metadata)
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r') as f:
                    data = json.load(f)
                    self._mapping = data.get('mapping', {})
                    self._counter = data.get('counter', 0)
                print(f"✓ Loaded {len(self._mapping)} secret mappings")
            except Exception as e:
                print(f"⚠ Error loading mapping: {e}")
        
        # Load encrypted secrets
        if self.secrets_file.exists() and self._fernet:
            try:
                with open(self.secrets_file, 'rb') as f:
                    encrypted = f.read()
                decrypted = self._fernet.decrypt(encrypted)
                self._secrets = json.loads(decrypted.decode())
                print(f"✓ Loaded {len(self._secrets)} encrypted secrets")
            except Exception as e:
                print(f"⚠ Error loading secrets: {e}")
    
    def _generate_label(self, secret_type: str) -> str:
        """Generate unique label for a secret.
        
        Args:
            secret_type: Type of secret (PASSWORD, TOKEN, API_KEY, etc.)
            
        Returns:
            Unique label like HA_SECRET_PASSWORD_001
        """
        self._counter += 1
        return f"{self.label_prefix}_{secret_type.upper()}_{self._counter:03d}"
    
    def _hash_value(self, value: str) -> str:
        """Create hash of value for duplicate detection.
        
        Args:
            value: Value to hash
            
        Returns:
            SHA256 hash of value
        """
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def _detect_secret_type(self, key: str, value: str) -> str:
        """Detect type of secret based on key name and value.
        
        Args:
            key: Configuration key name
            value: Secret value
            
        Returns:
            Secret type string
        """
        key_lower = key.lower()
        
        type_patterns = {
            'PASSWORD': ['password', 'passwd', 'pass', 'pwd'],
            'TOKEN': ['token', 'access_token', 'bearer', 'jwt'],
            'API_KEY': ['api_key', 'apikey', 'api-key', 'key'],
            'SECRET': ['secret', 'client_secret'],
            'CREDENTIAL': ['credential', 'auth', 'login'],
            'EMAIL': ['email', 'mail'],
            'PHONE': ['phone', 'mobile', 'tel'],
            'LATITUDE': ['latitude', 'lat'],
            'LONGITUDE': ['longitude', 'lon', 'lng'],
            'IP_ADDRESS': ['ip', 'host', 'address'],
            'URL': ['url', 'uri', 'endpoint'],
            'CERTIFICATE': ['cert', 'certificate', 'pem', 'crt'],
            'PRIVATE_KEY': ['private_key', 'privkey', 'ssh_key'],
        }
        
        for secret_type, patterns in type_patterns.items():
            if any(p in key_lower for p in patterns):
                return secret_type
        
        # Check value patterns
        if re.match(r'^[\w-]+\.[\w-]+\.[\w-]+$', value):  # JWT pattern
            return 'TOKEN'
        if re.match(r'^[a-f0-9]{32,}$', value.lower()):  # Hash/key pattern
            return 'API_KEY'
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):  # IP pattern
            return 'IP_ADDRESS'
        if '@' in value and '.' in value:  # Email pattern
            return 'EMAIL'
        
        return 'SECRET'
    
    def add_secret(self, key: str, value: str, description: str = "") -> str:
        """Add a secret and return its label.
        
        Args:
            key: Original configuration key
            value: Secret value to encrypt
            description: Optional description for documentation
            
        Returns:
            Label placeholder to use in exported config
        """
        if not value or not isinstance(value, str):
            return value
        
        # Check if value already exists (by hash)
        value_hash = self._hash_value(value)
        for label, meta in self._mapping.items():
            if meta.get('hash') == value_hash:
                return f"<<{label}>>"
        
        # Detect secret type and generate label
        secret_type = self._detect_secret_type(key, value)
        label = self._generate_label(secret_type)
        
        # Store encrypted value
        self._secrets[label] = value
        
        # Store mapping metadata (no actual secret value)
        self._mapping[label] = {
            'type': secret_type,
            'original_key': key,
            'description': description or f"Secret from {key}",
            'hash': value_hash,
            'created': datetime.now().isoformat(),
        }
        
        return f"<<{label}>>"
    
    def get_secret(self, label: str) -> Optional[str]:
        """Retrieve decrypted secret by label.
        
        Args:
            label: Secret label (with or without << >>)
            
        Returns:
            Decrypted secret value or None
        """
        # Strip << >> if present
        clean_label = label.replace('<<', '').replace('>>', '').strip()
        return self._secrets.get(clean_label)
    
    def save(self):
        """Save secrets and mapping to files."""
        # Save mapping (metadata only - safe to include in repo with caution)
        mapping_data = {
            'counter': self._counter,
            'mapping': self._mapping,
            'updated': datetime.now().isoformat()
        }
        with open(self.mapping_file, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        # Save encrypted secrets
        if self._fernet:
            secrets_json = json.dumps(self._secrets).encode()
            encrypted = self._fernet.encrypt(secrets_json)
            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted)
            os.chmod(self.secrets_file, 0o600)
            print(f"✓ Saved {len(self._secrets)} encrypted secrets")
        else:
            # Fallback: base64 encoding (NOT secure!)
            encoded = base64.b64encode(json.dumps(self._secrets).encode())
            with open(self.secrets_file, 'wb') as f:
                f.write(encoded)
            print("⚠ Saved secrets with base64 encoding (install cryptography for encryption)")
    
    def get_mapping_for_ai(self) -> Dict[str, Dict]:
        """Get mapping info suitable for AI context (no actual secrets).
        
        Returns:
            Dictionary with label metadata for AI
        """
        ai_mapping = {}
        for label, meta in self._mapping.items():
            ai_mapping[label] = {
                'type': meta['type'],
                'description': meta['description'],
                'placeholder': f"<<{label}>>"
            }
        return ai_mapping
    
    def restore_secrets_in_text(self, text: str) -> str:
        """Replace all secret labels in text with actual values.
        
        Args:
            text: Text containing <<LABEL>> placeholders
            
        Returns:
            Text with secrets restored
        """
        pattern = r'<<(' + re.escape(self.label_prefix) + r'_[A-Z]+_\d{3})>>'
        
        def replace_match(match):
            label = match.group(1)
            secret = self._secrets.get(label)
            if secret:
                return secret
            return match.group(0)  # Keep original if not found
        
        return re.sub(pattern, replace_match, text)
    
    def restore_secrets_in_file(self, file_path: str, output_path: Optional[str] = None) -> bool:
        """Restore secrets in a file.
        
        Args:
            file_path: Path to file with placeholders
            output_path: Optional different output path
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            restored = self.restore_secrets_in_text(content)
            
            out_path = output_path or file_path
            with open(out_path, 'w') as f:
                f.write(restored)
            
            return True
        except Exception as e:
            print(f"✗ Error restoring secrets in {file_path}: {e}")
            return False
    
    def export_for_ai(self, output_file: str):
        """Export secrets mapping for AI context.
        
        Args:
            output_file: Path to output JSON file
        """
        ai_data = {
            'secrets_info': {
                'total_secrets': len(self._mapping),
                'label_prefix': self.label_prefix,
                'instruction': (
                    "These placeholders represent sensitive data that has been removed. "
                    "When generating code, preserve these placeholders exactly as shown. "
                    "They will be automatically restored during import."
                )
            },
            'secret_labels': self.get_mapping_for_ai()
        }
        
        with open(output_file, 'w') as f:
            json.dump(ai_data, f, indent=2)
        
        print(f"✓ AI secrets mapping exported to: {output_file}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored secrets.
        
        Returns:
            Dictionary with secret statistics
        """
        type_counts = {}
        for meta in self._mapping.values():
            t = meta['type']
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            'total_secrets': len(self._secrets),
            'by_type': type_counts,
            'encryption': 'Fernet (AES-128-CBC)' if CRYPTO_AVAILABLE else 'Base64 (not secure)'
        }
    
    def print_summary(self):
        """Print summary of secrets."""
        stats = self.get_statistics()
        
        print("\n" + "=" * 50)
        print("🔐 Secrets Summary")
        print("=" * 50)
        print(f"Total secrets: {stats['total_secrets']}")
        print(f"Encryption: {stats['encryption']}")
        print("\nBy type:")
        for secret_type, count in stats['by_type'].items():
            print(f"  {secret_type}: {count}")
        print("=" * 50)


class SecretsSanitizer:
    """Sanitizes configuration files by replacing secrets with labels."""
    
    SENSITIVE_PATTERNS = {
        'password': r'(password|passwd|pass|pwd)\s*[:=]\s*["\']?([^"\'\n]+)["\']?',
        'token': r'(token|access_token|bearer_token)\s*[:=]\s*["\']?([^"\'\n]+)["\']?',
        'api_key': r'(api_key|apikey|api-key)\s*[:=]\s*["\']?([^"\'\n]+)["\']?',
        'secret': r'(secret|client_secret)\s*[:=]\s*["\']?([^"\'\n]+)["\']?',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'ip_address': r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        'latitude': r'(latitude|lat)\s*[:=]\s*(-?\d+\.?\d*)',
        'longitude': r'(longitude|lon|lng)\s*[:=]\s*(-?\d+\.?\d*)',
    }
    
    SKIP_VALUES = ['example', 'placeholder', 'your_', 'xxx', '***', 'none', 'null', 'true', 'false']
    
    def __init__(self, secrets_manager: SecretsManager):
        """Initialize sanitizer with secrets manager.
        
        Args:
            secrets_manager: SecretsManager instance
        """
        self.secrets_manager = secrets_manager
    
    def should_skip(self, value: str) -> bool:
        """Check if value should be skipped (placeholder/example).
        
        Args:
            value: Value to check
            
        Returns:
            True if value should not be sanitized
        """
        if not value or len(value) < 3:
            return True
        
        value_lower = value.lower()
        return any(skip in value_lower for skip in self.SKIP_VALUES)
    
    def sanitize_yaml_content(self, content: str) -> str:
        """Sanitize YAML content by replacing secrets.
        
        Args:
            content: YAML file content
            
        Returns:
            Sanitized content with labels
        """
        lines = content.split('\n')
        sanitized_lines = []
        
        for line in lines:
            sanitized_line = line
            
            # Skip comments
            if line.strip().startswith('#'):
                sanitized_lines.append(line)
                continue
            
            # Check each pattern
            for pattern_type, pattern in self.SENSITIVE_PATTERNS.items():
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    if pattern_type in ['email', 'ip_address']:
                        value = match.group(0)
                        key = pattern_type
                    else:
                        try:
                            key = match.group(1)
                            value = match.group(2)
                        except:
                            continue
                    
                    if not self.should_skip(value):
                        label = self.secrets_manager.add_secret(key, value.strip())
                        sanitized_line = sanitized_line.replace(value, label)
            
            sanitized_lines.append(sanitized_line)
        
        return '\n'.join(sanitized_lines)
    
    def sanitize_file(self, file_path: str, output_path: Optional[str] = None) -> bool:
        """Sanitize a file.
        
        Args:
            file_path: Path to file
            output_path: Optional output path
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            sanitized = self.sanitize_yaml_content(content)
            
            out_path = output_path or file_path
            with open(out_path, 'w') as f:
                f.write(sanitized)
            
            return True
        except Exception as e:
            print(f"✗ Error sanitizing {file_path}: {e}")
            return False


if __name__ == '__main__':
    # Demo/test
    manager = SecretsManager()
    
    # Add some test secrets
    label1 = manager.add_secret('db_password', 'super_secret_123', 'Database password')
    label2 = manager.add_secret('api_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9', 'API token')
    label3 = manager.add_secret('latitude', '52.5200', 'Home location')
    
    print(f"Label 1: {label1}")
    print(f"Label 2: {label2}")
    print(f"Label 3: {label3}")
    
    manager.save()
    manager.print_summary()
    
    # Test restoration
    test_text = f"password: {label1}\ntoken: {label2}"
    restored = manager.restore_secrets_in_text(test_text)
    print(f"\nRestored text:\n{restored}")
