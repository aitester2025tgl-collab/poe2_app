# utils/backup.py - Automatic Backup System
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class BackupManager:
    """Manages automatic backups of critical data files"""
    
    def __init__(self, backup_dir: str = "backups", max_backups: int = 10):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.max_backups = max_backups
    
    def create_backup(self, file_path: Path, prefix: str = "") -> Optional[Path]:
        """
        Create a timestamped backup of a file.
        
        Args:
            file_path: Path to the file to backup
            prefix: Optional prefix for the backup filename
            
        Returns:
            Path to the created backup file, or None if failed
        """
        if not file_path.exists():
            logger.warning(f"File not found for backup: {file_path}")
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{prefix}{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            logger.info(f"✅ Backup created: {backup_path}")
            
            # Clean old backups
            self._cleanup_old_backups(file_path.stem)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup of {file_path}: {e}")
            return None
    
    def _cleanup_old_backups(self, file_stem: str):
        """Remove old backups, keeping only max_backups most recent"""
        try:
            # Find all backups for this file
            backups = sorted(
                [f for f in self.backup_dir.glob(f"*{file_stem}_*") if f.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups
            for old_backup in backups[self.max_backups:]:
                old_backup.unlink()
                logger.info(f"🗑️  Removed old backup: {old_backup.name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old backups: {e}")
    
    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restore a backup file.
        
        Args:
            backup_path: Path to the backup file
            target_path: Path where to restore the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create backup of current file before restoring
            if target_path.exists():
                self.create_backup(target_path, prefix="pre_restore_")
            
            shutil.copy2(backup_path, target_path)
            logger.info(f"✅ Backup restored: {backup_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to restore backup: {e}")
            return False
    
    def list_backups(self, file_stem: Optional[str] = None) -> list:
        """List all backups, optionally filtered by file stem"""
        pattern = f"*{file_stem}_*" if file_stem else "*"
        backups = sorted(
            self.backup_dir.glob(pattern),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        return backups

# Convenience function
def safe_save_json(data, file_path: Path, create_backup: bool = True):
    """
    Safely save JSON data with automatic backup.
    
    Args:
        data: Data to save
        file_path: Path to save to
        create_backup: Whether to create backup before saving
    """
    file_path = Path(file_path)
    backup_mgr = BackupManager()
    
    try:
        # Create backup of existing file
        if create_backup and file_path.exists():
            backup_mgr.create_backup(file_path)
        
        # Write to temporary file first
        temp_path = file_path.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Atomic rename
        temp_path.replace(file_path)
        logger.info(f"✅ Data saved successfully to {file_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save data to {file_path}: {e}")
        raise

if __name__ == '__main__':
    # Test backup system
    logging.basicConfig(level=logging.INFO)
    
    backup_mgr = BackupManager()
    
    # List existing backups
    backups = backup_mgr.list_backups()
    print(f"\n📦 Found {len(backups)} backups:")
    for backup in backups[:5]:  # Show first 5
        print(f"  - {backup.name}")
