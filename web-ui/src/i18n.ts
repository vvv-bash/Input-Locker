import { useSettings } from './context';

const messages = {
  en: {
    // Settings dialog
    'settings.title': 'Settings',
    'settings.tab.general': 'General',
    'settings.tab.notifications': 'Notifications',
    'settings.tab.security': 'Security',
    'settings.tab.appearance': 'Appearance',
    'settings.tab.diagnostics': 'Diagnostics',
    // Security
    'security.emergency.title': 'Enable Emergency Unlock Pattern',
    'security.emergency.subtitle': 'Use ↑↑↓↓ + Enter to emergency unlock all devices',
    'diagnostics.title': 'Diagnostics',
    'diagnostics.copy': 'Copy Diagnostics',
    'security.backend.title': 'Backend settings',
    'security.backend.description': 'Global hotkey and emergency pattern managed by the core service.',
    'security.backend.hotkey': 'Current hotkey',
    'security.backend.pattern': 'Current emergency pattern',
    'security.backend.hotkey.helper': 'Use keys separated by + (e.g. Ctrl + Alt + L). Avoid special characters like Ç, ñ, ¡, etc.; prefer letters A–Z.',
    'security.backend.pattern.helper': 'Use steps separated by spaces (e.g. Up Up Down Down Enter).',
    'security.backend.behavior': 'Backend behavior',
    'security.backend.autoBlock.title': 'Lock on start',
    'security.backend.autoBlock.desc': 'Automatically block devices when the backend service starts',
    'security.backend.notifications.title': 'Backend notifications',
    'security.backend.notifications.desc': 'Allow the core service to trigger desktop notifications',
    'security.backend.touchscreen.title': 'Allow touchscreen unlock',
    'security.backend.touchscreen.desc': 'Let trusted touchscreens bypass the global lock',
    'diagnostics.summaryTitle': 'Diagnostics summary',
    'diagnostics.copied': 'Diagnostics copied to clipboard',
    'diagnostics.copyError': 'Could not copy diagnostics',

    // Header
    'header.title': 'Input Device Blocker',
    'header.subtitle': 'Secure your Linux input devices',
    'header.refresh': 'Refresh devices',
    'header.settings': 'Settings',

    // Dashboard main
    'dashboard.loading.connecting': 'Connecting to API server...',
    'dashboard.loading.waiting': 'Waiting for API server...',
    'dashboard.loading.passwordHint': 'Enter your password in the system dialog if prompted',
    'dashboard.actions.lockAll': 'Lock All',
    'dashboard.actions.unlockAll': 'Unlock All',
    'dashboard.actions.refresh': 'Refresh',
    'dashboard.section.devicesTitle': 'Input Devices',
    'dashboard.noDevices.title': 'No input devices found',
    'dashboard.noDevices.subtitle': 'Make sure you have the necessary permissions',
    'dashboard.section.securityProfilesTitle': 'Security Profiles',
    'dashboard.profile.activeLabel': 'Active',
    'dashboard.systemHealth.title': 'System Health',
    'dashboard.systemHealth.apiStatus': 'API Status',
    'dashboard.systemHealth.devicesDetected': 'Devices Detected',
    'dashboard.systemHealth.activeLocks': 'Active Locks',
    'dashboard.activity.title': 'Activity Log',
    'dashboard.activity.emptyTitle': 'No activity yet',
    'dashboard.activity.emptySubtitle': 'Actions will appear here',
    'dashboard.statistics.title': 'Statistics',

    // Security profiles (names & descriptions)
    'profile.focus.name': 'Focus Mode',
    'profile.focus.description': 'Block all except essential mouse',
    'profile.child.name': 'Child Lock',
    'profile.child.description': 'Block all input devices',
    'profile.gaming.name': 'Gaming Mode',
    'profile.gaming.description': 'Block touchpad only',
    'profile.presentation.name': 'Presentation',
    'profile.presentation.description': 'Block keyboard only',

    // General tab texts
    'settings.general.startupTitle': 'Startup Options',
    'settings.general.startOnBoot.title': 'Start on System Boot',
    'settings.general.startOnBoot.desc': 'Automatically start Input Locker when the system starts',
    'settings.general.startMinimized.title': 'Start Minimized',
    'settings.general.startMinimized.desc': 'Start the application minimized to the system tray',
    'settings.general.autoLockTitle': 'Auto-Lock Settings',
    'settings.general.autoLockEnabled.title': 'Auto-lock on Idle',
    'settings.general.autoLockEnabled.desc': 'Automatically lock devices after a period of inactivity',
    'settings.general.dataTitle': 'Data Management',
    'settings.general.logRetention': 'Activity Log Retention',

    // Notifications tab
    'settings.notifications.title': 'Notification Preferences',
    'settings.notifications.enable.title': 'Enable Notifications',
    'settings.notifications.enable.desc': 'Show system notifications for lock/unlock events',
    'settings.notifications.sound.title': 'Enable Sound Effects',
    'settings.notifications.sound.desc': 'Play audio feedback when devices are locked/unlocked',
    'settings.notifications.typesTitle': 'Notification Types',
    'settings.notifications.lock.title': 'Lock Notifications',
    'settings.notifications.lock.desc': 'Show notification when devices are locked',
    'settings.notifications.unlock.title': 'Unlock Notifications',
    'settings.notifications.unlock.desc': 'Show notification when devices are unlocked',

    // Security tab extras
    'settings.security.keyboardShortcutsTitle': 'Keyboard Shortcuts',
    'settings.security.hotkeyEnabled.title': 'Enable Global Hotkey',
    'settings.security.hotkeyEnabled.desc': 'Use Ctrl+Alt+L to toggle device lock',
    'settings.security.confirmationTitle': 'Confirmation & Safety',
    'settings.security.requireConfirmation.title': 'Require Confirmation for Lock All',
    'settings.security.requireConfirmation.desc': 'Show confirmation dialog before locking all devices',
    'settings.security.shortcutReferenceTitle': 'Shortcut Reference',
    'settings.security.shortcut.toggleLock': 'Toggle Lock',
    'settings.security.shortcut.emergency': 'Emergency Unlock',

    // Appearance tab
    'settings.appearance.themeTitle': 'Theme Settings',
    'settings.appearance.themeLabel': 'Theme',
    'settings.appearance.theme.dark': 'Dark Mode',
    'settings.appearance.theme.light': 'Light Mode',
    'settings.appearance.theme.system': 'System Default',
    'settings.appearance.accentTitle': 'Accent Color',
    'settings.appearance.layoutTitle': 'Layout Options',
    'settings.appearance.compactMode.title': 'Compact Mode',
    'settings.appearance.compactMode.desc': 'Use smaller cards and reduced spacing',
    'settings.appearance.advancedTitle': 'Advanced',
    'settings.appearance.debugMode.title': 'Debug Mode',
    'settings.appearance.debugMode.desc': 'Show additional information for troubleshooting',
    'settings.appearance.languageTitle': 'Language',

    // Dialog actions
    'settings.actions.reset': 'Reset to Defaults',
    'settings.actions.cancel': 'Cancel',
    'settings.actions.save': 'Save Changes',
    'settings.actions.saveSuccess': 'Settings saved successfully',
    'settings.actions.backendSaveError': 'Failed to save backend settings',

    // Onboarding
    'onboarding.title': 'Welcome to Input Locker',
    'onboarding.intro': "We'll help you set up safe defaults for your devices.",
    'onboarding.devicesTitle': 'Detected devices',
    'onboarding.noDevices': 'No devices detected yet. Make sure the backend is running.',
    'onboarding.quickPrefsTitle': 'Quick preferences',
    'onboarding.notifications.title': 'Enable notifications',
    'onboarding.notifications.desc': 'Show a notification when devices are locked or unlocked.',
    'onboarding.startMinimized.title': 'Start minimized',
    'onboarding.startMinimized.desc': 'Keep the window out of the way and use the tray icon.',
    'onboarding.getStarted': 'Get started',

    // Header / Status / Timer / Devices / Stats components
    'status.systemActive': 'System Active',
    'status.systemOffline': 'System Offline',
    'status.devicesLabel': 'devices',
    'status.blockedLabel': 'blocked',
    'status.uptimeLabel': 'Uptime',

    'timer.title': 'Block Timer',
    'timer.remaining': 'remaining',
    'timer.inactive': 'not active',
    'timer.minutesLabel': 'Minutes',
    'timer.start': 'Start',
    'timer.cancel': 'Cancel Timer',

    'device.status.blocked': 'Blocked',
    'device.status.active': 'Active',
    'device.action.block': 'Block',
    'device.action.unblock': 'Unblock',

    'stats.totalBlockedTime': 'Total Blocked Time',
    'stats.blockedEvents': 'Blocked Events',
    'stats.blockSessions': 'Block Sessions',
    'stats.timeByDevice': 'Time by Device',
    'stats.noData': 'No data yet',
    'stats.activityTimeline': 'Activity Timeline',
    'stats.noActivity': 'No activity data yet',
  },
  es: {
    // Settings dialog
    'settings.title': 'Ajustes',
    'settings.tab.general': 'General',
    'settings.tab.notifications': 'Notificaciones',
    'settings.tab.security': 'Seguridad',
    'settings.tab.appearance': 'Apariencia',
    'settings.tab.diagnostics': 'Diagnóstico',
    // Security
    'security.emergency.title': 'Activar patrón de desbloqueo de emergencia',
    'security.emergency.subtitle': 'Usa ↑↑↓↓ + Enter para desbloquear todos los dispositivos',
    'diagnostics.title': 'Diagnóstico',
    'diagnostics.copy': 'Copiar informe',
    'security.backend.title': 'Ajustes del backend',
    'security.backend.description': 'Atajo global y patrón de emergencia gestionados por el servicio central.',
    'security.backend.hotkey': 'Atajo actual',
    'security.backend.pattern': 'Patrón de emergencia actual',
    'security.backend.hotkey.helper': 'Usa teclas separadas por + (ej. Ctrl + Alt + L). Evita caracteres especiales como Ç, ñ, ¡, etc.; usa letras de la A a la Z.',
    'security.backend.pattern.helper': 'Usa pasos separados por espacios (ej. Up Up Down Down Enter).',
    'security.backend.behavior': 'Comportamiento del backend',
    'security.backend.autoBlock.title': 'Bloquear al iniciar',
    'security.backend.autoBlock.desc': 'Bloquea los dispositivos cuando se inicia el servicio backend',
    'security.backend.notifications.title': 'Notificaciones del backend',
    'security.backend.notifications.desc': 'Permite que el servicio central muestre notificaciones de escritorio',
    'security.backend.touchscreen.title': 'Permitir desbloqueo táctil',
    'security.backend.touchscreen.desc': 'Permite que pantallas táctiles confiables eviten el bloqueo global',
    'diagnostics.summaryTitle': 'Resumen de diagnóstico',
    'diagnostics.copied': 'Diagnóstico copiado al portapapeles',
    'diagnostics.copyError': 'No se pudo copiar el diagnóstico',

    // Header
    'header.title': 'Bloqueador de dispositivos de entrada',
    'header.subtitle': 'Protege tus dispositivos de entrada en Linux',
    'header.refresh': 'Actualizar dispositivos',
    'header.settings': 'Ajustes',

    // Dashboard main
    'dashboard.loading.connecting': 'Conectando con el servidor API...',
    'dashboard.loading.waiting': 'Esperando al servidor API...',
    'dashboard.loading.passwordHint': 'Introduce tu contraseña en el cuadro del sistema si se te pide',
    'dashboard.actions.lockAll': 'Bloquear todo',
    'dashboard.actions.unlockAll': 'Desbloquear todo',
    'dashboard.actions.refresh': 'Actualizar',
    'dashboard.section.devicesTitle': 'Dispositivos de entrada',
    'dashboard.noDevices.title': 'No se encontraron dispositivos de entrada',
    'dashboard.noDevices.subtitle': 'Asegúrate de tener los permisos necesarios',
    'dashboard.section.securityProfilesTitle': 'Perfiles de seguridad',
    'dashboard.profile.activeLabel': 'Activo',
    'dashboard.systemHealth.title': 'Estado del sistema',
    'dashboard.systemHealth.apiStatus': 'Estado de la API',
    'dashboard.systemHealth.devicesDetected': 'Dispositivos detectados',
    'dashboard.systemHealth.activeLocks': 'Bloqueos activos',
    'dashboard.activity.title': 'Registro de actividad',
    'dashboard.activity.emptyTitle': 'Sin actividad todavía',
    'dashboard.activity.emptySubtitle': 'Las acciones aparecerán aquí',
    'dashboard.statistics.title': 'Estadísticas',

    // Security profiles (names & descriptions)
    'profile.focus.name': 'Modo concentración',
    'profile.focus.description': 'Bloquea todo excepto el ratón esencial',
    'profile.child.name': 'Bloqueo infantil',
    'profile.child.description': 'Bloquea todos los dispositivos de entrada',
    'profile.gaming.name': 'Modo juego',
    'profile.gaming.description': 'Bloquea solo el touchpad',
    'profile.presentation.name': 'Presentación',
    'profile.presentation.description': 'Bloquea solo el teclado',

    // General tab texts
    'settings.general.startupTitle': 'Opciones de inicio',
    'settings.general.startOnBoot.title': 'Iniciar con el sistema',
    'settings.general.startOnBoot.desc': 'Inicia Input Locker automáticamente al arrancar el sistema',
    'settings.general.startMinimized.title': 'Iniciar minimizado',
    'settings.general.startMinimized.desc': 'Inicia la aplicación minimizada en la bandeja del sistema',
    'settings.general.autoLockTitle': 'Bloqueo automático',
    'settings.general.autoLockEnabled.title': 'Bloqueo automático en reposo',
    'settings.general.autoLockEnabled.desc': 'Bloquea los dispositivos tras un periodo de inactividad',
    'settings.general.dataTitle': 'Gestión de datos',
    'settings.general.logRetention': 'Retención del registro de actividad',

    // Notifications tab
    'settings.notifications.title': 'Preferencias de notificación',
    'settings.notifications.enable.title': 'Activar notificaciones',
    'settings.notifications.enable.desc': 'Mostrar notificaciones del sistema al bloquear/desbloquear',
    'settings.notifications.sound.title': 'Activar sonidos',
    'settings.notifications.sound.desc': 'Reproducir sonidos al bloquear o desbloquear dispositivos',
    'settings.notifications.typesTitle': 'Tipos de notificación',
    'settings.notifications.lock.title': 'Notificaciones de bloqueo',
    'settings.notifications.lock.desc': 'Mostrar notificación cuando se bloquean dispositivos',
    'settings.notifications.unlock.title': 'Notificaciones de desbloqueo',
    'settings.notifications.unlock.desc': 'Mostrar notificación cuando se desbloquean dispositivos',

    // Security tab extras
    'settings.security.keyboardShortcutsTitle': 'Atajos de teclado',
    'settings.security.hotkeyEnabled.title': 'Activar atajo global',
    'settings.security.hotkeyEnabled.desc': 'Usa Ctrl+Alt+L para alternar el bloqueo de dispositivos',
    'settings.security.confirmationTitle': 'Confirmación y seguridad',
    'settings.security.requireConfirmation.title': 'Pedir confirmación para "Bloquear todo"',
    'settings.security.requireConfirmation.desc': 'Muestra un diálogo de confirmación antes de bloquear todo',
    'settings.security.shortcutReferenceTitle': 'Referencia de atajos',
    'settings.security.shortcut.toggleLock': 'Alternar bloqueo',
    'settings.security.shortcut.emergency': 'Desbloqueo de emergencia',

    // Appearance tab
    'settings.appearance.themeTitle': 'Tema',
    'settings.appearance.themeLabel': 'Tema',
    'settings.appearance.theme.dark': 'Modo oscuro',
    'settings.appearance.theme.light': 'Modo claro',
    'settings.appearance.theme.system': 'Predeterminado del sistema',
    'settings.appearance.accentTitle': 'Color de acento',
    'settings.appearance.layoutTitle': 'Opciones de diseño',
    'settings.appearance.compactMode.title': 'Modo compacto',
    'settings.appearance.compactMode.desc': 'Usa tarjetas más pequeñas y menos espaciado',
    'settings.appearance.advancedTitle': 'Avanzado',
    'settings.appearance.debugMode.title': 'Modo depuración',
    'settings.appearance.debugMode.desc': 'Muestra información adicional para solucionar problemas',
    'settings.appearance.languageTitle': 'Idioma',

    // Dialog actions
    'settings.actions.reset': 'Restablecer valores por defecto',
    'settings.actions.cancel': 'Cancelar',
    'settings.actions.save': 'Guardar cambios',
    'settings.actions.saveSuccess': 'Ajustes guardados correctamente',
    'settings.actions.backendSaveError': 'No se pudieron guardar los ajustes del backend',

    // Onboarding
    'onboarding.title': 'Bienvenido a Input Locker',
    'onboarding.intro': 'Te ayudaremos a configurar valores seguros para tus dispositivos.',
    'onboarding.devicesTitle': 'Dispositivos detectados',
    'onboarding.noDevices': 'Aún no se detectan dispositivos. Asegúrate de que el backend está en ejecución.',
    'onboarding.quickPrefsTitle': 'Preferencias rápidas',
    'onboarding.notifications.title': 'Activar notificaciones',
    'onboarding.notifications.desc': 'Muestra una notificación cuando se bloquean o desbloquean dispositivos.',
    'onboarding.startMinimized.title': 'Iniciar minimizado',
    'onboarding.startMinimized.desc': 'Mantén la ventana fuera de la vista y usa el icono de bandeja.',
    'onboarding.getStarted': 'Comenzar',

    // Header / Status / Timer / Devices / Stats components
    'status.systemActive': 'Sistema activo',
    'status.systemOffline': 'Sistema desconectado',
    'status.devicesLabel': 'dispositivos',
    'status.blockedLabel': 'bloqueados',
    'status.uptimeLabel': 'Tiempo activo',

    'timer.title': 'Temporizador de bloqueo',
    'timer.remaining': 'restante',
    'timer.inactive': 'inactivo',
    'timer.minutesLabel': 'Minutos',
    'timer.start': 'Iniciar',
    'timer.cancel': 'Cancelar temporizador',

    'device.status.blocked': 'Bloqueado',
    'device.status.active': 'Activo',
    'device.action.block': 'Bloquear',
    'device.action.unblock': 'Desbloquear',

    'stats.totalBlockedTime': 'Tiempo total bloqueado',
    'stats.blockedEvents': 'Eventos de bloqueo',
    'stats.blockSessions': 'Sesiones de bloqueo',
    'stats.timeByDevice': 'Tiempo por dispositivo',
    'stats.noData': 'Sin datos todavía',
    'stats.activityTimeline': 'Línea de tiempo de actividad',
    'stats.noActivity': 'Sin datos de actividad todavía',
  },
} as const;

export type SupportedLang = keyof typeof messages;

export function useI18n() {
  const { settings } = useSettings();
  const lang: SupportedLang = (settings.language || 'en') as SupportedLang;

  const t = (key: keyof typeof messages['en']): string => {
    if (messages[lang] && key in messages[lang]) {
      return messages[lang][key];
    }
    return messages.en[key] ?? (key as string);
  };

  return { t, lang };
}
