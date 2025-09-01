# Extractor de Comentarios de Instagram

Un potente extractor de comentarios de Instagram que obtiene comentarios reales, nombres de usuario, perfiles de usuario y métricas de engagement de posts y reels de Instagram. Incluye soporte completo para caracteres españoles y emojis.

## ✨ Características

- **Extracción Real de Comentarios**: Extrae comentarios reales con nombres de usuario, likes y timestamps
- **Enriquecimiento de Datos de Usuario**: Obtiene el número de seguidores de los autores de comentarios
- **Soporte Unicode**: Manejo perfecto de caracteres españoles (á, é, í, ó, ú, ñ) y emojis (🔥, 😍, 👏)
- **Múltiples Formatos de Exportación**: Opciones de exportación Excel (.xlsx) y CSV
- **Soporte de Autenticación**: Login opcional de Instagram para mejor acceso a datos
- **Gestión de Límites de Velocidad**: Delays y mecanismos de reintento integrados
- **Registro Completo**: Logs detallados para monitoreo y debugging

## 📋 Requisitos

- Python 3.8+
- Cuenta de ScrapFly API (nivel gratuito disponible)
- Compatible con Windows/Mac/Linux

## 🚀 Configuración Rápida

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Obtener Clave API de ScrapFly

1. Visita [ScrapFly.io](https://scrapfly.io/) y crea una cuenta gratuita
2. Copia tu clave API desde el panel de control
3. El extractor te pedirá la clave API en la primera ejecución

### 3. Ejecutar el Extractor

```bash
cd src
python main_controller.py
```

## 📦 Guía de Instalación

### Paso 1: Clonar o Descargar
Descarga este proyecto a tu máquina local.

### Paso 2: Configurar Entorno Python (Recomendado)

```bash
# Crear entorno virtual
python -m venv venv

# Activarlo
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Configurar API de ScrapFly

El extractor usa ScrapFly para acceso confiable a Instagram. En la primera ejecución, se te pedirá introducir tu clave API, que se guardará automáticamente.

**Alternativa**: Crear un archivo `.env` en la raíz del proyecto:
```
SCRAPFLY_API_KEY=tu_clave_api_aqui
```

## 🎯 Cómo Usar

### Uso Básico

1. **Ejecutar la Aplicación**
   ```bash
   cd src
   python main_controller.py
   ```

2. **Solicitud de Autenticación**
   - Elige si hacer login en Instagram (recomendado para mejores resultados)
   - Sin login: Datos limitados, pueden aparecer límites de velocidad
   - Con login: Acceso completo a comentarios y datos de usuario

3. **Introducir URLs de Instagram**
   - Especifica el número de posts a extraer (1-10)
   - Introduce las URLs de posts/reels de Instagram una por una
   - Formatos soportados:
     - `https://www.instagram.com/p/ABC123/`
     - `https://www.instagram.com/reel/XYZ789/`
     - `https://www.instagram.com/username/p/ABC123/`

4. **Elegir Formato de Salida**
   - Excel (recomendado): Formato rico con columnas separadas
   - CSV: Formato simple separado por comas

5. **Esperar Resultados**
   - Las barras de progreso muestran el estado de extracción
   - Resultados guardados en la carpeta `scrape/instagram/`

### Login de Instagram (Opcional pero Recomendado)

Cuando se solicite la autenticación de Instagram:

```
Instagram Login
Username: tu_nombre_usuario_instagram
Password: [entrada oculta]
```

**Beneficios de hacer login:**
- Límites de velocidad más altos
- Acceso a más comentarios
- Mejor extracción de datos de usuario
- Menor probabilidad de bloqueos

## 📊 Formato de Salida

### Estructura de Salida Excel

El archivo Excel contiene estas columnas:

**Columnas de Metadatos (A-N):**
- Now: Timestamp de extracción
- Post URL: URL del post de Instagram
- Publisher Nickname: Nombre de usuario del autor del post
- Publisher @: Nombre de usuario del autor del post
- Publisher URL: URL del perfil del autor del post
- Publish Time: Cuándo se publicó el post
- Post Likes: Número de likes en el post
- Post Shares: Número de compartidos
- Description: Pie de foto del post
- Number of 1st level comments: Conteo de comentarios directos
- Number of 2nd level comments: Conteo de comentarios de respuesta
- Total Comments (actual): Comentarios extraídos
- Total Comments (platform says): Conteo reclamado por Instagram
- Difference: Varianza entre reclamado y real

**Columnas de Comentarios (Q-AB):**
- Comment Number (ID): ID secuencial del comentario
- Nickname: Nombre de usuario del comentarista
- User @: Nombre de usuario del comentarista
- User URL: Enlace al perfil del comentarista
- Comment Text: El comentario real (con Unicode adecuado)
- Time: Timestamp del comentario
- Likes: Conteo de likes del comentario
- Profile Picture URL: Avatar del comentarista
- Followers: Conteo de seguidores del comentarista
- Is 2nd Level Comment: Si es una respuesta
- User Replied To: Comentarista original si es una respuesta
- Number of Replies: Conteo de respuestas a este comentario

### Convención de Nombres de Archivo

Los archivos se guardan como: `instagram_YYYYMMDD_HHMMSS.xlsx`

Ejemplo: `instagram_20250901_143022.xlsx`

## ⚙️ Opciones de Configuración

### Límites de Extracción

Límites predeterminados (pueden modificarse en `scrapfly_config.py`):
- Comentarios por video: 500
- Solicitudes por minuto: 15
- Delay entre solicitudes: 4 segundos

### Configuración de Autenticación

Crear `instagram_config.py` para auto-login:
```python
INSTAGRAM_CREDENTIALS = {
    'username': 'tu_nombre_usuario',
    'password': 'tu_contraseña'
}
```

## 🔧 Solución de Problemas

### Problemas Comunes

**Error "429 Rate Limited":**
- Solución: Habilitar autenticación de Instagram
- Reducir frecuencia de extracción
- Esperar 10-15 minutos antes de reintentar

**Error "ScrapFly API Key":**
- Verificar que tu clave API sea correcta
- Comprobar el estado de la cuenta ScrapFly
- Asegurarse de tener créditos restantes

**"No Comments Found":**
- El post podría tener comentarios deshabilitados
- Intentar con autenticación de Instagram
- El post podría ser muy antiguo o privado

**Los Caracteres Unicode Aparecen como Símbolos:**
- Esto es normal en la consola de Windows
- Revisar el archivo Excel - los caracteres se mostrarán correctamente
- El extractor maneja correctamente todo Unicode

### Modo Debug

Para registro detallado, revisar los archivos de log en la carpeta `logs/`:
- `scraper_YYYYMMDD_HHMMSS.log`

## 📁 Estructura del Proyecto

```
scrape-socialmedia/
├── src/
│   ├── main_controller.py          # Punto de entrada principal de la aplicación
│   ├── instagram_scraper.py        # Lógica principal de extracción de Instagram
│   └── utils/
│       ├── scrapfly_config.py      # Configuración de API ScrapFly
│       ├── file_handler.py         # Manejo de exportación Excel/CSV
│       ├── url_validator.py        # Validación de URLs de Instagram
│       ├── instagram_auth.py       # Autenticación de Instagram
│       └── logger.py               # Configuración de logging
├── scrape/
│   └── instagram/                  # Carpeta de salida para datos extraídos
├── logs/                           # Logs de la aplicación
├── requirements.txt                # Dependencias de Python
└── README.md                       # Este archivo
```

## 🔒 Privacidad y Ética

**Uso Responsable:**
- Solo extraer contenido público de Instagram
- Respetar límites de velocidad y términos de servicio de Instagram
- No extraer información personal o privada
- Usar los datos extraídos de manera responsable y legal

**Protección de Datos:**
- Los datos extraídos se almacenan solo localmente
- No se transmiten datos a terceros
- Las credenciales de Instagram se almacenan localmente (opcional)

## 📋 Dependencias

Dependencias principales en `requirements.txt`:
- `scrapfly-sdk==0.8.23` - Servicio de web scraping
- `openpyxl==3.1.2` - Creación de archivos Excel
- `beautifulsoup4==4.12.2` - Análisis de HTML
- `requests==2.31.0` - Solicitudes HTTP
- `colorama==0.4.6` - Colores de consola
- `tqdm==4.66.1` - Barras de progreso
- `python-dotenv==1.0.0` - Variables de entorno

## 🐛 Problemas Conocidos

1. **Codificación de Consola Windows**: Los emojis pueden mostrarse como `?` en la consola pero se guardan correctamente en los archivos
2. **Límites de Velocidad**: Sin autenticación, Instagram puede limitar el acceso después de varias solicitudes
3. **Posts Privados**: No se pueden extraer comentarios de cuentas privadas de Instagram

## 🔄 Actualizaciones y Mantenimiento

**Mantener Actualizado:**
- Verificar el estado del servicio ScrapFly regularmente
- Actualizar dependencias mensualmente: `pip install -r requirements.txt --upgrade`
- Instagram cambia su estructura ocasionalmente - reportar problemas si la extracción deja de funcionar

## 📞 Soporte

Si encuentras problemas:

1. Revisar la carpeta `logs/` para detalles de errores
2. Verificar tu clave API de ScrapFly y créditos
3. Probar con autenticación de Instagram habilitada
4. Asegurarse de que las URLs sean posts públicos de Instagram

## 📜 Licencia

Esta herramienta es para propósitos educativos e de investigación. Por favor cumple con los Términos de Servicio de Instagram y las leyes aplicables al usar este extractor.

---

**¡Feliz Extracción! 🎉**

*Recuerda usar esta herramienta de manera responsable y ética.*
