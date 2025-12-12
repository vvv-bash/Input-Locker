"""
Privilege management and elevation utilities.
"""
import os
import sys
import subprocess
import tempfile
from typing import Optional
from pathlib import Path
from .logger import logger


class PrivilegeManager:
    """Root privilege manager for access to input devices."""
    
    @staticmethod
    def is_root() -> bool:
        """Check if the process has root privileges."""
        return os.geteuid() == 0
    
    @staticmethod
    def get_app_root() -> Path:
        """Get the application's root directory."""
        if getattr(sys, 'frozen', False):
            # Si está empaquetado con PyInstaller
            return Path(sys.executable).parent
        else:
            # In development: /opt/input-locker/src/utils/privileges.py -> /opt/input-locker
            current_file = Path(__file__).resolve()
            return current_file.parent.parent.parent
    
    @staticmethod
    def elevate_privileges() -> bool:
        """
        Attempt to elevate privileges using pkexec or sudo.

        Returns:
            bool: True if privileges were successfully elevated.
        """
        if PrivilegeManager.is_root():
            return True
        
        logger.warning("Root privileges are required")

        # Get paths
        app_root = PrivilegeManager.get_app_root()
        python_exec = sys.executable
        
        # Environment variables to preserve
        display = os.environ.get('DISPLAY', ':0')
        xauthority = os.environ.get('XAUTHORITY', '')
        
        # Try pkexec (PolicyKit)
        try:
            # Create a temporary wrapper script in /tmp (user-writable)
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                prefix='input-locker-',
                delete=False
            ) as f:
                wrapper_script = Path(f.name)
                wrapper_content = f"""#!/bin/bash
cd "{app_root}"
export PYTHONPATH="{app_root}"
export DISPLAY="{display}"
export XAUTHORITY="{xauthority}"
exec "{python_exec}" -c "import sys; sys.path.insert(0, '{app_root}'); from src.main import main; sys.exit(main())"
"""
                f.write(wrapper_content)
            
            # Make it executable
            wrapper_script.chmod(0o755)
            
            args = [
                'pkexec',
                str(wrapper_script)
            ]
            
            logger.info("Attempting to elevate privileges with pkexec")
            logger.debug(f"Temporary wrapper script: {wrapper_script}")
            logger.debug(f"Command: {' '.join(args)}")
            
            # Ejecutar y esperar
            result = subprocess.run(args)
            
            # Clean up temporary script
            try:
                wrapper_script.unlink()
            except:
                pass
            
            # If pkexec executed, exit (child process will continue)
            sys.exit(result.returncode)
            
        except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            logger.warning(f"pkexec failed: {e}")
            # Clean up temporary script if exists
            try:
                if 'wrapper_script' in locals() and wrapper_script.exists():
                    wrapper_script.unlink()
            except:
                pass
        
        # Try sudo
        try:
            # Método directo sin script temporal
            args = [
                'sudo',
                '-E',  # Preservar variables de entorno
                'env',
                f'PYTHONPATH={app_root}',
                f'DISPLAY={display}',
                f'XAUTHORITY={xauthority}',
                python_exec,
                '-c',
                f"import sys; sys.path.insert(0, '{app_root}'); from src.main import main; sys.exit(main())"
            ]
            
            logger.info("Attempting to elevate privileges with sudo")
            logger.debug(f"Command: {' '.join(args[:6])}... [python code]")
            
            result = subprocess.run(args)
            sys.exit(result.returncode)
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"sudo failed: {e}")
        
        return False
    
    @staticmethod
    def check_device_access() -> bool:
        """
        Verify access to /dev/input/.

        Returns:
            bool: True if read access is available.
        """
        try:
            input_dir = '/dev/input'
            
            # Search for the first available event file
            event_files = [f for f in os.listdir(input_dir) if f.startswith('event')]
            
            if not event_files:
                logger.warning("No event files found in /dev/input/")
                return False
            
            test_file = os.path.join(input_dir, event_files[0])
            
            # Try opening for read
            with open(test_file, 'rb') as f:
                pass
            
            return True

        except PermissionError:
            logger.error("No permission to access input devices")
            return False
        except Exception as e:
            logger.error(f"Error checking device access: {e}")
            return False
    
    @staticmethod
    def get_user_info() -> dict:
        """Return information about the current user."""
        return {
            'uid': os.getuid(),
            'euid': os.geteuid(),
            'gid': os.getgid(),
            'egid': os.getegid(),
            'username': os.getenv('USER', 'unknown'),
            'is_root': PrivilegeManager.is_root()
        }