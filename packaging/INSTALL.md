# Input Locker - Instalación en Linux (Debian/Ubuntu, Fedora/RHEL, Arch/Manjaro)

## 📦 Instalación Rápida (Debian/Ubuntu y derivadas)

### Opción 1 (Debian/Ubuntu): Instalar desde el paquete .deb

```bash
# Copiar el archivo .deb al nuevo equipo y ejecutar:
sudo dpkg -i input-locker_2.0.0_amd64.deb

# Si hay dependencias faltantes:
sudo apt-get install -f
```

### Opción 2 (Debian/Ubuntu): Instalación Manual

```bash
# 1. Instalar dependencias
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm policykit-1 xdotool

# 2. Verificar versión de Node.js (debe ser >= 18)
node --version
# Si es menor a 18, instalar Node.js 18+:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 3. Copiar los archivos a /opt/input-locker
sudo mkdir -p /opt/input-locker
sudo cp -r * /opt/input-locker/

# 4. Crear entorno virtual Python
cd /opt/input-locker
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt

# 5. Instalar dependencias Node.js y construir
cd /opt/input-locker/web-ui
sudo npm install --legacy-peer-deps
sudo npm run build

# 6. Dar permisos de ejecución
sudo chmod +x /opt/input-locker/input-locker.sh
```

## 📦 Instalación en Fedora / RHEL / Rocky / AlmaLinux

### Opción 1: Instalador rápido

Desde el código fuente clonado:

```bash
cd packaging
sudo bash install.sh
```

Este script:

- Instala dependencias con `dnf` (Python, Node.js, npm, polkit, xdotool)
- Copia la aplicación a `/opt/input-locker`
- Crea un entorno virtual Python y instala `requirements.txt`
- Instala dependencias de Node.js y construye la web‑UI
- Crea el lanzador `input-locker` y la entrada de escritorio

### Opción 2: Instalación Manual

```bash
# 1. Instalar dependencias
sudo dnf install -y python3 python3-pip nodejs npm polkit xdotool

# 2. Copiar los archivos a /opt/input-locker
sudo mkdir -p /opt/input-locker
sudo cp -r * /opt/input-locker/

# 3. Crear entorno virtual Python
cd /opt/input-locker
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt

# 4. Instalar dependencias Node.js y construir
cd /opt/input-locker/web-ui
sudo npm install --legacy-peer-deps
sudo npm run build

# 5. Crear lanzador (opcional)
sudo ln -sf /opt/input-locker/input-locker.sh /usr/bin/input-locker
```

## 📦 Instalación en Arch / Manjaro

### Opción 1: Instalador rápido

Desde el código fuente clonado:

```bash
cd packaging
sudo bash install.sh
```

El script detectará `pacman` e instalará:

- `python`, `python-pip`
- `nodejs`, `npm`
- `polkit`
- `xdotool`

Luego repetirá los mismos pasos que en Fedora/Debian: copiar a `/opt/input-locker`, crear venv, construir web‑UI y crear el lanzador.

### Opción 2: Instalación Manual

```bash
# 1. Instalar dependencias
sudo pacman -Sy --needed python python-virtualenv python-pip nodejs npm polkit xdotool

# 2. Copiar los archivos a /opt/input-locker
sudo mkdir -p /opt/input-locker
sudo cp -r * /opt/input-locker/

# 3. Crear entorno virtual Python
cd /opt/input-locker
sudo python -m venv venv
sudo ./venv/bin/pip install -r requirements.txt

# 4. Instalar dependencias Node.js y construir
cd /opt/input-locker/web-ui
sudo npm install --legacy-peer-deps
sudo npm run build

# 5. Crear lanzador (opcional)
sudo ln -sf /opt/input-locker/input-locker.sh /usr/bin/input-locker
```

---

## 🚀 Uso

### Ejecutar la aplicación

```bash
# Desde terminal (requiere privilegios root):
input-locker

# O directamente:
/opt/input-locker/input-locker.sh

# O desde el menú de aplicaciones: buscar "Input Locker"
```

### Atajos de teclado

| Acción | Atajo |
|--------|-------|
| **Bloquear** | `Ctrl + Alt + L` |
| **Desbloquear** | `↑ ↑ ↓ ↓ Enter` |

### Perfiles de Seguridad

| Perfil | Descripción | Dispositivos bloqueados |
|--------|-------------|------------------------|
| **Focus Mode** | Bloquea todo excepto mouse | keyboard, touchpad, touchscreen |
| **Child Lock** | Bloqueo total | keyboard, mouse, touchpad, touchscreen |
| **Gaming Mode** | Solo touchpad | touchpad |
| **Presentation** | Solo teclado | keyboard |

## 🔧 Dependencias del Sistema (resumen)

```bash
# Debian / Ubuntu / Linux Mint
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    nodejs \
    npm \
    policykit-1 \
    xdotool

# Fedora / RHEL / Rocky / AlmaLinux
sudo dnf install -y \
    python3 \
    python3-pip \
    nodejs \
    npm \
    polkit \
    xdotool

# Arch / Manjaro
sudo pacman -Sy --needed \
    python \
    python-virtualenv \
    python-pip \
    nodejs \
    npm \
    polkit \
    xdotool
```

> 💡 **Wayland**
>
> Input Locker trabaja directamente con los dispositivos de `/dev/input/*` usando `evdev`, por lo que el bloqueo de teclado/ratón funciona tanto en X11 como en Wayland siempre que la aplicación tenga permisos suficientes (normalmente ejecutándola como root o mediante `pkexec`). No necesita APIs específicas del compositor.

## 📁 Estructura de Archivos

```
/opt/input-locker/
├── api/                    # Backend FastAPI
│   ├── api_server.py      # Servidor principal
│   └── _internal.py       # Lógica de bloqueo
├── src/                    # Módulos Python
│   ├── core/              # Gestión de dispositivos
│   ├── gui/               # (legacy)
│   └── utils/             # Utilidades
├── web-ui/                 # Frontend React + Electron
│   ├── src/               # Código fuente React
│   ├── electron/          # Configuración Electron
│   └── dist/              # Build compilado
├── config/                 # Configuración por defecto
├── venv/                   # Entorno virtual Python
├── requirements.txt        # Dependencias Python
└── input-locker.sh        # Script de lanzamiento
```

## 🛠️ Construcción del Paquete .deb

Para regenerar el paquete .deb y un archivo .tar.gz portátil:

```bash
cd /opt/input-locker/packaging
sudo ./build-deb.sh
```

Se generarán estos archivos en `/opt/input-locker/packaging`:

- `input-locker_2.0.0_amd64.deb`
- `input-locker_2.0.0_amd64.tar.gz` (carpeta completa lista para copiar)

## 🐛 Solución de Problemas

### La aplicación no inicia
```bash
# Verificar que Node.js está instalado correctamente
node --version  # Debe ser >= 18

# Verificar dependencias Python
/opt/input-locker/venv/bin/pip list

# Reconstruir web-ui
cd /opt/input-locker/web-ui
npm run build
```

### Error de permisos
```bash
# La aplicación necesita permisos root para acceder a /dev/input
# Usar pkexec o sudo:
sudo /opt/input-locker/input-locker.sh
```

### El bloqueo no funciona
```bash
# Verificar que los dispositivos están disponibles
ls -la /dev/input/event*

# Verificar que el usuario tiene acceso a input
sudo usermod -a -G input $USER
# (Cerrar sesión y volver a entrar)
```

### Puerto 8080 en uso
```bash
# Matar procesos anteriores
pkill -9 -f api_server
pkill -9 -f electron
```

## 📝 Desinstalación

```bash
# Si instalaste con dpkg:
sudo dpkg -r input-locker

# Instalación manual:
sudo rm -rf /opt/input-locker
sudo rm -f /usr/bin/input-locker
sudo rm -f /usr/share/applications/input-locker.desktop
```

## 📄 Licencia

MIT License - Ver archivo LICENSE para más detalles.
