"""
Gestor de configuración persistente.
"""
"""
Persistent configuration manager.
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.logger import logger


class ConfigManager:
    """JSON persistent configuration manager."""
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / 'config' / 'default_config.json'
    USER_CONFIG_DIR = Path.home() / '.config' / 'input-locker'
    USER_CONFIG_FILE = USER_CONFIG_DIR / 'config.json'
    
    def __init__(self):
        """Inicializa el gestor de configuración."""
        self.config: Dict[str, Any] = {}
        self._ensure_config_dir()
        self.load()
    
    def _ensure_config_dir(self):
        """Crea el directorio de configuración si no existe."""
        try:
            self.USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorio de configuración: {self.USER_CONFIG_DIR}")
        except Exception as e:
            logger.error(f"Error creando directorio de configuración: {e}")
    
    def load(self) -> bool:
        """
        Carga la configuración desde archivo.
        
        Returns:
            bool: True si se cargó exitosamente.
        """
        try:
            # Si no existe config de usuario, copiar default
            if not self.USER_CONFIG_FILE.exists():
                logger.info("Creando configuración inicial desde default")
                self._copy_default_config()
            
            # Cargar configuración
            with open(self.USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            logger.info("Configuración cargada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            # Cargar default como fallback
            return self._load_default()
    
    def _copy_default_config(self):
        """Copia la configuración por defecto al directorio de usuario."""
        try:
            shutil.copy(self.DEFAULT_CONFIG_PATH, self.USER_CONFIG_FILE)
        except Exception as e:
            logger.error(f"Error copiando config default: {e}")
    
    def _load_default(self) -> bool:
        """Carga la configuración por defecto."""
        try:
            with open(self.DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info("Configuración default cargada")
            return True
        except Exception as e:
            logger.critical(f"Error cargando config default: {e}")
            return False
    
    def save(self) -> bool:
        """
        Guarda la configuración actual en archivo.
        
        Returns:
            bool: True si se guardó exitosamente.
        """
        try:
            with open(self.USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info("Configuración guardada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            return False
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            section: Sección del config (ej: 'general', 'devices', 'ui')
            key: Clave dentro de la sección
            default: Valor por defecto si no existe
            
        Returns:
            El valor configurado o default
        """
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception as e:
            logger.warning(f"Error obteniendo config {section}.{key}: {e}")
            return default
    
    def set(self, section: str, key: str, value: Any):
        """
        Establece un valor de configuración.
        
        Args:
            section: Sección del config
            key: Clave dentro de la sección
            value: Nuevo valor
        """
        if section not in self.config:
            self.config[section] = {}
        
        self.config[section][key] = value
        logger.debug(f"Config actualizado: {section}.{key} = {value}")
    
    def get_hotkey(self) -> str:
        """Obtiene el hotkey configurado."""
        hotkey = self.get('general', 'hotkey', 'Ctrl+Alt+L')

        # Normalizar combinaciones con caracteres no ASCII (p.ej. "Ç")
        try:
            parts = [p.strip() for p in hotkey.split('+') if p.strip()]
            if parts:
                last = parts[-1]
                # Si la última parte no es una letra ASCII simple, forzar valor por defecto
                if not (last.isascii() and last.isalpha()):
                    logger.warning(
                        f"Hotkey inválido en config ('{hotkey}'), usando valor por defecto Ctrl+Alt+L"
                    )
                    hotkey = 'Ctrl+Alt+L'
                    # Persistir corrección para futuras ejecuciones
                    try:
                        self.set_hotkey(hotkey)
                    except Exception:
                        pass
        except Exception:
            hotkey = 'Ctrl+Alt+L'

        return hotkey

    def set_hotkey(self, hotkey: str):
        """Establece el hotkey en la configuración y lo persiste."""
        self.set('general', 'hotkey', hotkey)
        self.save()
    
    def get_theme(self) -> str:
        """Obtiene el tema configurado."""
        return self.get('ui', 'theme', 'dark')
    
    def set_theme(self, theme: str) -> bool:
        """Establece el tema configurado."""
        try:
            if 'ui' not in self.config:
                self.config['ui'] = {}
            self.config['ui']['theme'] = theme
            return self.save()
        except Exception as e:
            logger.error(f"Error setting theme: {e}")
            return False
    
    def should_block_keyboards(self) -> bool:
        """Verifica si se deben bloquear teclados."""
        return self.get('devices', 'block_keyboards', True)
    
    def should_block_mice(self) -> bool:
        """Verifica si se deben bloquear ratones."""
        return self.get('devices', 'block_mice', True)
    
    def should_allow_touchscreens(self) -> bool:
        """Verifica si se deben permitir touchscreens."""
        return self.get('devices', 'allow_touchscreens', True)
    
    def get_whitelist(self) -> list:
        """Obtiene la lista de dispositivos en whitelist."""
        return self.get('devices', 'whitelist', [])
    
    def add_to_whitelist(self, device_path: str):
        """Agrega un dispositivo a la whitelist."""
        whitelist = self.get_whitelist()
        if device_path not in whitelist:
            whitelist.append(device_path)
            self.set('devices', 'whitelist', whitelist)
            self.save()
    
    def remove_from_whitelist(self, device_path: str):
        """Remueve un dispositivo de la whitelist."""
        whitelist = self.get_whitelist()
        if device_path in whitelist:
            whitelist.remove(device_path)
            self.set('devices', 'whitelist', whitelist)
            self.save()
    
    def export_config(self, path: Path) -> bool:
        """Exporta la configuración a un archivo."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuración exportada a: {path}")
            return True
        except Exception as e:
            logger.error(f"Error exportando configuración: {e}")
            return False
    
    def import_config(self, path: Path) -> bool:
        """Importa configuración desde un archivo."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            
            # Validar estructura básica
            required_sections = ['general', 'devices', 'ui']
            if not all(section in imported for section in required_sections):
                raise ValueError("Estructura de config inválida")
            
            self.config = imported
            self.save()
            logger.info(f"Configuración importada desde: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importando configuración: {e}")
            return False

    # --- Logging rotation helpers ---
    def get_log_rotation(self) -> dict:
        """Return dict with logging rotation settings."""
        logging_cfg = self.get('logging', 'rotation', {}) or {}
        # Provide defaults
        return {
            'max_bytes': logging_cfg.get('max_bytes', 10 * 1024 * 1024),
            'backup_count': logging_cfg.get('backup_count', 5)
        }

    def set_log_rotation(self, max_bytes: int, backup_count: int):
        """Persist rotation settings in configuration."""
        if 'logging' not in self.config:
            self.config['logging'] = {}
        self.config['logging']['rotation'] = {
            'max_bytes': int(max_bytes),
            'backup_count': int(backup_count)
        }
        self.save()