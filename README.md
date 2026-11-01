# Plantilla de repositorio base — Especialización en Desarrollo con IA Generativa (Accenture)

Esta es la estructura base utilizada como punto de partida para el proyecto en este programa, la cual se irá ampliando bloque a bloque hasta llegar a la aplicación completa que se entrega en el Gate 3.

---

## 🚀 Instrucciones de Instalación Limpia y Ejecución (Gate 1)

Para clonar, configurar y ejecutar esta miniaplicación desde cero en cualquier entorno local, sigue los pasos a continuación:

### 1. Clonar el repositorio
git clone https://github.com/becareli/mi-primer-repositorio.git
cd mi-primer-repositorio

### 2. Crear y activar el entorno virtual
- **En Windows (PowerShell):**
  python -m venv venv
  .\venv\Scripts\Activate.ps1

- **En macOS / Linux:**
  python3 -m venv venv
  source venv/bin/activate

### 3. Instalar las dependencias
pip install -r requirements.txt

### 4. Configurar las variables de entorno
Copia el archivo de plantilla .env.example para crear tu archivo .env local:

- **En Windows (PowerShell):**
  Copy-Item .env.example .env

- **En macOS / Linux:**
  cp .env.example .env

Abre el archivo .env recién creado e ingresa tu llave real de la API de Gemini:
GEMINI_API_KEY=tu_api_key_real_aqui

### 5. Ejecutar la aplicación
Para ejecutar el script principal con el benchmark de modelos, latencias y banco de prompts:
python src/main.py

Para probar el consumo directo del módulo individual de la API:
python src/consumir_gemini.py

---

## 📂 Estructura de carpetas

- `src/` : Todo el código fuente del proyecto (incluye `main.py`, `consumir_gemini.py` y el banco de prompts).
- `docs/` : Documentación técnica del proyecto (diagramas de arquitectura, decisiones de modelo).
- `tests/` : Pruebas de código.
- `requirements.txt` : Dependencias de Python necesarias para reconstruir el entorno con un solo comando.
- `.env.example` : Plantilla de las variables de entorno que el proyecto necesita, sin valores reales.
- `.gitignore` : Configuración de archivos ignorados por Git (entre ellos, el entorno virtual y el archivo `.env` real).

---

## 🔒 Reglas que se mantienen durante todo el programa

- Ningún secreto (contraseña, llave de API, token) va escrito directamente en el código ni en ningún archivo que se suba al repositorio.
- Cada proyecto nuevo tiene su propio entorno virtual: no se comparten dependencias entre proyectos distintos.
- Todo el trabajo que se entrega en este programa vive en un repositorio de GitHub, sin excepción.

---

## 📋 Registro del Ensayo de Instalación Limpia

- **Fecha de ensayo:** 2026-10-31
- **Hallazgos:** Entorno virtual configurado y dependencias declaradas correctamente en `requirements.txt`.
- **Resultado tras la prueba:** El proyecto se clona, instala y ejecuta de punta a punta sin intervención manual ni excepciones no capturadas.
