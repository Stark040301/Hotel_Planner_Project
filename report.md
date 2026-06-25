# Hotel Event Manager – Informe del Proyecto

## 1. Introducción y objetivo del programa

**Hotel Event Manager** es una aplicación de escritorio desarrollada en Python que facilita la gestión de eventos en establecimientos hoteleros. Su propósito es permitir al personal del hotel administrar el inventario de recursos (salas, empleados y objetos) y planificar eventos (reuniones, conferencias, bodas, etc.) de forma eficiente, evitando solapamientos y respetando las restricciones de compatibilidad entre recursos.

El programa surge de la necesidad de sustituir las hojas de cálculo y los calendarios manuales por una herramienta visual e intuitiva que centralice toda la información. Durante el desarrollo me he centrado en ofrecer una interfaz moderna, accesible y responsiva, junto con un motor de planificación robusto capaz de validar conflictos y sugerir huecos libres.

El proyecto se ha diseñado siguiendo una arquitectura **Modelo‑Vista‑Controlador (MVC)**, lo que ha permitido separar claramente la lógica de negocio, la presentación y el flujo de control. La aplicación se ejecuta en entornos Windows, macOS y Linux, y todos los datos se persisten en un único archivo JSON ubicado en el directorio del usuario.

---

## 2. Funcionalidades principales

El sistema ofrece las siguientes capacidades:

### 2.1. Gestión de inventario

El inventario se compone de tres tipos de recursos:

- **Salas (`Room`)**: con atributos como capacidad, tipo (salón, aula, etc.) e interior/exterior.
- **Empleados (`Employee`)**: con rol (recepcionista, técnico, etc.) y turno (diurno, nocturno, rotativo).
- **Objetos (`Item`)**: con descripción y cantidad disponible.

Cada recurso puede tener **requisitos** (por ejemplo, una sala puede requerir un proyector) y **exclusiones** (por ejemplo, un equipo de sonido puede excluir el uso de comida). Estas restricciones se aplican al planificar eventos.

La vista de inventario presenta los recursos en tarjetas interactivas agrupadas por tipo, con un contador total de recursos. Para facilitar la visualización completa de la información, se ha implementado un diálogo de edición que muestra todos los atributos del recurso, incluyendo requisitos y exclusiones. Esto permite al usuario consultar y modificar cualquier detalle del recurso sin saturar la vista principal.

### 2.2. Planificación de eventos

Los eventos se definen con los siguientes campos:

- Nombre (obligatorio)
- Fecha y hora de inicio y fin (formato ISO)
- Lista de recursos necesarios (nombre y cantidad)
- Recurrencia (ninguna, diaria, semanal, mensual, estacional, personalizada)
- Notas adicionales

Para facilitar la entrada de fechas, se ha incorporado un selector visual con calendario y selectores de hora, que mejora la experiencia de usuario y reduce errores de formato. Al seleccionar una fecha desde el calendario, la duración del evento se actualiza automáticamente.

Al crear un evento, el sistema valida que todos los recursos solicitados estén disponibles en el intervalo indicado y que no se violen las restricciones de requisitos y exclusiones. Si hay conflictos, se informa al usuario con mensajes claros.

### 2.3. Búsqueda de huecos libres

Una de las funcionalidades más útiles es el botón **"Siguiente Hueco"**. Dados unos recursos y una duración, el sistema calcula el primer intervalo disponible dentro de una ventana temporal (por defecto, los próximos 30 días). Esto agiliza enormemente la planificación, ya que el usuario no tiene que probar manualmente distintas fechas.

### 2.4. Persistencia de datos

Todos los datos (inventario y eventos) se almacenan en un único archivo JSON: `~/.hotel_planner/data.json`. Esto facilita la copia de seguridad, la exportación y la importación de configuraciones completas. La escritura se realiza de forma atómica (usando un archivo temporal y `os.replace`) para evitar corrupción en caso de fallo.

### 2.5. Interfaz moderna y accesible

La interfaz está construida con **CustomTkinter**, una extensión de Tkinter que ofrece widgets con aspecto moderno y soporte para temas oscuros y claros. Se han incorporado elementos de accesibilidad como:

- Tooltips en los campos.
- Atajos de teclado (`Ctrl+I` para inventario, `Ctrl+A` para añadir recurso, `Ctrl+E` para eventos, `Ctrl+C` para crear evento).
- Indicadores visuales de foco en botones y campos.
- Contraste de colores verificado según estándares WCAG.

---

## 3. Diseño y decisiones técnicas

### 3.1. Arquitectura MVC

He adoptado el patrón MVC para mantener el código organizado y facilitar futuras extensiones:

- **Modelo**: Las clases `Inventory`, `Resource` (y sus subclases), `Event` y `Scheduler` constituyen el núcleo de la lógica de negocio. El `Scheduler` mantiene los eventos ordenados y un índice por recurso para consultas rápidas.
- **Vista**: Cada pantalla (inventario, añadir recurso, eventos planificados, crear evento) es una clase que hereda de `CTkFrame` y se comunica exclusivamente con el controlador.
- **Controlador**: La clase `Controller` actúa como intermediario. Expone métodos sencillos (`list_events()`, `add_event()`, `find_next_available()`, etc.) y gestiona la concurrencia con `threading.Lock`.

Esta separación ha permitido probar el backend independientemente de la interfaz y ha hecho que el código sea más mantenible.

### 3.2. Elección de CustomTkinter

Decidí usar CustomTkinter en lugar de Tkinter nativo por varias razones:

- **Apariencia moderna**: Los widgets tienen un diseño más atractivo y profesional.
- **Temas oscuros/claros**: La aplicación se adapta automáticamente al tema del sistema o permite al usuario cambiarlo manualmente.
- **API similar**: La curva de aprendizaje fue baja, ya que la API es muy parecida a la de Tkinter.
- **Comunidad activa**: Hay buena documentación y ejemplos disponibles.

### 3.3. Persistencia con JSON

Opté por JSON por su simplicidad y legibilidad. No necesitaba un motor de base de datos relacional, ya que los datos son relativamente pequeños y la estructura es jerárquica. Además, JSON es fácil de exportar e importar, lo que permite al usuario compartir configuraciones.

Para garantizar la integridad de los datos, implementé una escritura atómica: primero escribo en un archivo temporal y luego renombro con `os.replace()`. Si ocurre un error durante la escritura, el archivo original permanece intacto.

### 3.4. Comunicación entre vistas con eventos virtuales

Las vistas no se conocen entre sí, pero necesitan actualizarse cuando los datos cambian (por ejemplo, al añadir un recurso desde la vista de añadir, la vista de inventario debe refrescarse). Para ello, utilicé el sistema de **eventos virtuales de Tkinter**. Cada vista se suscribe a eventos como `<<InventoryChanged>>` o `<<EventsChanged>>` y refresca su contenido al recibirlos. Esto desacopla las vistas y mantiene la lógica de actualización centralizada.

### 3.5. Componentes reutilizables

Para evitar duplicación de código y mantener la consistencia visual, creé una carpeta `components/` con widgets modulares:

- `InventoryCard`: tarjeta para mostrar un recurso.
- `StatsDashboard`: panel de estadísticas (posteriormente simplificado a un contador total).
- `EventAgendaCard`: tarjeta para mostrar un evento.
- `EventAgendaToolbar` y `EventAgendaStats`: análogos para la sección de eventos.

### 3.6. Mejoras en la entrada de fechas

La entrada manual de fechas en formato ISO (`YYYY-MM-DDTHH:MM`) resultaba poco amigable. Para mejorar la experiencia de usuario, desarrollé un componente `DateTimePicker` que integra un calendario visual (con la librería `tkcalendar`) y selectores de hora. Este componente se ha integrado en la pantalla de creación de eventos, permitiendo seleccionar fechas de forma rápida y sin errores de formato.

### 3.7. Simplificación de la vista de inventario

Inicialmente, la vista de inventario incluía una barra de búsqueda, filtros por disponibilidad y un dashboard con estadísticas detalladas. Sin embargo, la disponibilidad de los recursos depende del intervalo temporal de los eventos, por lo que estos filtros resultaban confusos y poco prácticos. Por ello, eliminé la barra de búsqueda y los filtros, dejando únicamente un contador total de recursos. Esta simplificación hace que la vista sea más clara y directa.

### 3.8. Edición de recursos

La funcionalidad de edición de recursos es crucial para mantener el inventario actualizado. Implementé un diálogo de edición que permite modificar todos los atributos del recurso (cantidad, capacidad, tipo, rol, turno, descripción, requisitos y exclusiones) sin cambiar el nombre, que se mantiene como identificador único. Al guardar los cambios, se actualiza el objeto en memoria, se persiste en el archivo JSON y se notifica a la vista para que se refresque automáticamente. De esta forma, el usuario puede consultar y editar toda la información del recurso desde la propia vista de inventario.

---

## 4. Aprendizaje durante el desarrollo

Este proyecto me ha brindado una valiosa experiencia en varios aspectos:

### 4.1. Gestión de interfaces gráficas con Tkinter/CustomTkinter

Aprendí a estructurar layouts complejos usando `grid` y `pack`, a manejar eventos (clics, teclado, foco) y a personalizar la apariencia de los widgets. También descubrí cómo hacer que la interfaz sea responsiva, ajustando tamaños según la resolución de la pantalla.

### 4.2. Patrones de diseño

La implementación de MVC me ayudó a comprender la importancia de separar responsabilidades. Al principio mezclaba lógica de negocio en las vistas, pero rápidamente me di cuenta de que eso dificultaba las pruebas y los cambios. Refactorizar el código para mover toda la lógica al controlador fue una de las decisiones más acertadas.

### 4.3. Manejo de fechas y horas

Trabajar con `datetime` y `timedelta` fue un reto, especialmente al calcular duraciones y buscar huecos libres. Aprendí a normalizar las fechas a formato ISO y a manejar zonas horarias (aunque en este proyecto he asumido que todas las fechas están en la misma zona). La implementación del selector visual de fechas me enseñó a integrar librerías externas y a manejar ventanas modales.

### 4.4. Concurrencia simple

Para las operaciones de guardado y carga, implementé hilos con `threading` para no bloquear la interfaz. Aunque es una solución sencilla, me enseñó los fundamentos de la programación concurrente y la sincronización con `Lock`.

### 4.5. Pruebas y depuración

Desarrollé una serie de pruebas unitarias para el scheduler que me ayudaron a validar las restricciones de requisitos y exclusiones. Aprendí a usar el depurador de VS Code para seguir el flujo de ejecución y encontrar errores lógicos.

### 4.6. Optimización de rendimiento

Durante el desarrollo, observé que la carga del inventario podía ser lenta cuando el número de recursos era elevado, debido a la creación de muchas tarjetas y al acceso al archivo JSON. Aprendí a optimizar la carga mediante la serialización en memoria y a reducir el número de operaciones de E/S.

---

## 5. Guía de uso

### 5.1. Instalación y ejecución

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Stark040301/Hotel_Planner_Project
   cd Hotel_Planner_Project
   ```
2. Crear y activar un entorno virtual:
    ```bash
    python -m venv venv
    source venv/bin/activate      # Linux/macOS
    venv\Scripts\activate         # Windows
    ```

3. Instalar dependencias:
    ```bash
    pip install -r requirements.txt
    ```

4. Ejecutar la aplicación:
    ```bash
    python main.py
    ```

### 5.2. Navegación principal

La ventana se divide en una barra lateral izquierda y un área principal. En la barra lateral hay un menú vertical con cuatro opciones:

- **Inventario**: Muestra todos los recursos en tarjetas agrupadas por tipo, con un contador total. Cada tarjeta tiene botones de editar y eliminar.
- **Añadir Recurso**: Formulario para crear un nuevo recurso.
- **Eventos Planificados**: Lista tabular de todos los eventos.
- **Crear Evento**: Formulario para crear un evento, con selector de fechas integrado.

También hay botones para exportar/importar el archivo JSON y controles para cambiar el tema (claro/oscuro) y la escala de la interfaz.

### 5.3. Ejemplo de uso: Crear un evento

1. Ve a la pestaña "Crear Evento" (o pulsa `Ctrl+C`).
2. Introduce el nombre del evento (ej. "Reunión de ventas").
3. Selecciona la fecha y hora de inicio y fin utilizando el calendario (clic en el botón 📅) o escribiendo manualmente.
4. Añade los recursos necesarios haciendo clic en "+ Recurso". Elige un recurso de la lista desplegable y establece la cantidad.
5. Opcionalmente, selecciona una recurrencia y añade notas.
6. Si deseas que el sistema te proponga un hueco libre, haz clic en "Siguiente Hueco". Aparecerá un diálogo con la propuesta; si aceptas, se rellenarán automáticamente los campos de fecha.
7. Pulsa "Guardar". El evento se añadirá y aparecerá en la lista de eventos planificados.

### 5.4. Ejemplo de uso: Editar un recurso

1. Ve a la vista de Inventario.
2. Localiza el recurso que deseas editar y haz clic en el botón "Editar" de su tarjeta.
3. Se abrirá un diálogo con todos los campos del recurso: cantidad, atributos específicos (capacidad, tipo, rol, turno, descripción), requisitos y exclusiones.
4. Modifica los campos que necesites (el nombre no se puede cambiar).
5. Haz clic en "Guardar". Los cambios se aplicarán inmediatamente y la vista se actualizará.

---

## 6. Dificultades encontradas y soluciones

### 6.1. Conflictos de imports

Al principio usaba imports relativos (`from .controller import Controller`). Esto funcionaba en el entorno de desarrollo, pero al reestructurar el proyecto para que `main.py` estuviera en la raíz, surgieron errores de `ModuleNotFoundError`. La solución fue adoptar **imports absolutos** con el prefijo `hotel_planner.` en todos los archivos. Además, en `main.py` añadí `sys.path.insert(0, ...)` para asegurar que el directorio raíz esté en el `PYTHONPATH`.

### 6.2. Sincronización de datos entre vistas

Cuando se añadía o eliminaba un recurso, la vista de inventario no se actualizaba automáticamente. La solución fue implementar el sistema de **eventos virtuales** de Tkinter. Cada vista se suscribe a eventos como `<<InventoryChanged>>` y `<<EventsChanged>>`, y al recibirlos refresca su contenido. Esto eliminó la necesidad de llamar manualmente a `refresh()` desde otras vistas.

### 6.3. Validación de fechas

Los usuarios podían introducir fechas en formatos incorrectos, lo que provocaba excepciones al parsear con `datetime.fromisoformat()`. Para solucionarlo, añadí una validación previa y mensajes de error claros. También puse placeholders en los campos de fecha y un selector visual que garantiza el formato correcto.

### 6.4. Persistencia atómica

Inicialmente, escribía directamente el archivo JSON. Si la escritura fallaba (por ejemplo, por falta de espacio en disco), el archivo quedaba corrupto. La solución fue escribir primero en un archivo temporal y luego renombrar con `os.replace()`. Esto garantiza que nunca se pierdan los datos originales.

### 6.5. Gestión de recursos con cantidad > 1

El manejo de recursos con cantidad (por ejemplo, 3 proyectores) fue complejo porque cada unidad individual debe ser considerada como un recurso independiente para la planificación. La solución fue tratar la cantidad como un atributo del recurso y, al reservar, verificar que haya suficientes unidades disponibles en el intervalo solicitado. Esto implicó modificar el scheduler para llevar un conteo de uso por recurso y por intervalo.

### 6.6. Rendimiento en la carga del inventario

La creación de muchas tarjetas y la lectura del archivo JSON podían ralentizar la aplicación. Para mejorar el rendimiento, optimicé la serialización de recursos y reduje las operaciones de E/S. Aunque aún hay margen de mejora, la experiencia actual es aceptable para un número razonable de recursos.

### 6.7. Edición de recursos sin cambiar el nombre

Para evitar inconsistencias en los índices del scheduler y en los eventos que referencian recursos, decidí que el nombre no se pueda modificar en el diálogo de edición. Si el usuario necesita renombrar un recurso, debe eliminarlo y volver a crearlo con el nuevo nombre, actualizando también los eventos afectados.

### 6.8. Visualización completa de la información de recursos

La vista de inventario muestra solo una parte de los atributos en las tarjetas para no saturar la interfaz. Para ver toda la información (incluyendo requisitos y exclusiones), el usuario puede hacer clic en "Editar", lo que abre un diálogo que muestra todos los campos. Esta solución mantiene la vista principal limpia y proporciona acceso a los detalles completos cuando se necesitan.

---

## 7. Conclusiones y trabajo futuro

El desarrollo de **Hotel Event Manager** ha sido una experiencia enriquecedora que ha combinado diseño de interfaces, lógica de negocio y gestión de datos. He aprendido a estructurar un proyecto mediano siguiendo buenas prácticas (MVC, componentes reutilizables, persistencia atómica) y a resolver problemas reales de concurrencia, validación y sincronización.

La aplicación cumple con los objetivos planteados: permite gestionar el inventario y planificar eventos de forma intuitiva y visual, con un motor de planificación que respeta restricciones complejas. La interfaz es moderna, accesible y responsiva, y la persistencia en JSON facilita la portabilidad.

### Mejoras identificadas y trabajo futuro

Aunque el sistema es funcional, he identificado varias áreas de mejora que podrían abordarse en futuras versiones:

- **Pantalla de eventos planificados**: Actualmente la lista es simple. Sería deseable añadir filtros (por fecha, recurso, etc.) y una vista de calendario (mes/semana) más visual.
- **Mejora en la visualización de recursos**: La vista de inventario debería mostrar más información directamente en las tarjetas (por ejemplo, requisitos y exclusiones de forma abreviada) sin tener que abrir el editor. También se podría añadir un modo de lista detallada.
- **Rendimiento**: La carga del inventario puede optimizarse aún más, especialmente con muchos recursos, mediante la carga perezosa o el uso de un árbol de widgets más eficiente.
- **Edición de eventos**: Actualmente solo se pueden crear y eliminar. Sería útil poder modificar un evento existente.
- **Recurrencias avanzadas**: Implementar excepciones en patrones recurrentes (por ejemplo, "cada lunes excepto festivos").
- **Autenticación de usuarios**: Para entornos con múltiples operadores.
- **Soporte para lectores de pantalla**: Mejorar la accesibilidad para personas con discapacidad visual.
- **Exportación a formatos estándar**: Generar informes en PDF o calendarios en iCalendar.

En definitiva, el proyecto ha sentado unas bases sólidas para un sistema de planificación hotelera completo y profesional. Estoy satisfecho con el resultado y con todo lo que he aprendido en el camino.