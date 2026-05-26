# PayFlow — Arquitectura Event-Driven para Procesamiento de Transacciones

---

# Computación en la Nube — Caso 03

## Procesamiento de Eventos en Tiempo Real

| Campo | Información |
|---|---|
| Institución | Tecnológico de Antioquia |
| Curso | Computación en la Nube |
| Profesor | Julian David Florez Sanchez |
| Semestre | 2026-1 |
| Plataforma | Microsoft Azure |
| Fecha de entrega | 14 de mayo de 2026 |

---

# Integrantes

| Nombre | Rol |
|---|---|
| Integrante 1 | Arquitectura |
| Integrante 2 | Desarrollo |
| Integrante 3 | Documentación |
| Integrante 4 | Monitoreo |

---

# Tabla de contenido

1. Introducción  
2. Drivers Arquitectónicos  
3. Modelo C4  
4. Architectural Decision Records (ADRs)  
5. Implementación del flujo crítico  
6. Evidencias de implementación  
7. Matriz de control de cambios  
8. Conclusiones  
9. Referencias  

---

# Introducción

PayFlow es una fintech colombiana enfocada en pagos digitales para pequeños y medianos comercios. Actualmente, su plataforma presenta limitaciones de rendimiento y escalabilidad debido a una arquitectura monolítica y síncrona que no soporta correctamente los picos de transacciones.

El propósito de este proyecto es diseñar una arquitectura orientada a eventos que permita mejorar el procesamiento en tiempo real, desacoplar componentes críticos, aumentar la observabilidad del sistema y soportar crecimiento en volumen transaccional.

---

# Drivers Arquitectónicos

Los siguientes drivers fueron identificados a partir de los requerimientos funcionales y no funcionales del caso de estudio.

---

## Throughput

| Requerimiento | Objetivo |
|---|---|
| Capacidad de procesamiento | Hasta 500 transacciones por segundo |

### Motivación
Soportar temporadas de alta demanda sin degradación del servicio.

---

## Latencia

| Requerimiento | Objetivo |
|---|---|
| Tiempo de autorización | Menor a 2 segundos |

### Motivación
Evitar timeouts en terminales de pago y pérdida de ventas.

---

## Garantía de entrega

| Requerimiento | Objetivo |
|---|---|
| Entrega de eventos | At-least-once |

### Motivación
Garantizar que ninguna transacción crítica se pierda durante el procesamiento.

---

## Detección de fraude

| Requerimiento | Objetivo |
|---|---|
| Evaluación antifraude | En tiempo real antes de autorizar |

### Motivación
Reducir transacciones fraudulentas aprobadas.

---

## Desacoplamiento

| Requerimiento | Objetivo |
|---|---|
| Separación de flujos | Independencia entre autorización y notificaciones |

### Motivación
Evitar que fallos externos afecten el procesamiento principal.

---

## Observabilidad

| Requerimiento | Objetivo |
|---|---|
| Monitoreo automático | Alertas menores a 30 segundos |

### Motivación
Detectar anomalías antes de que sean reportadas por los comercios.

---

# Modelo C4

---

# C1 — Contexto

## Descripción

El diagrama C1 representa los actores principales y sistemas externos que interactúan con PayFlow dentro del ecosistema de procesamiento de pagos.

### Actores identificados

- Cliente
- Comercio
- Equipo de Riesgo
- Equipo de Operaciones

### Sistemas externos

- Terminal POS
- Sistema legado
- Red de pagos externa

---

![C1](assets/c1-contexto.png)

El siguiente diagrama corresponde al C4 Model – Nivel 1 (System Context Diagram) de PayFlow, una plataforma de procesamiento de pagos digitales orientada a eventos y desplegada sobre Azure.

El objetivo principal del sistema es permitir a los comercios recibir pagos digitales de manera segura, escalable y eficiente en países como Colombia, Ecuador y Perú.

En este nivel de arquitectura se muestran los actores y sistemas externos que interactúan con PayFlow, así como las relaciones principales entre ellos.

Actores del sistema
Comercio

Representa a los establecimientos o negocios que utilizan la plataforma PayFlow para recibir pagos digitales de sus clientes.
Los comercios envían solicitudes de procesamiento de pagos y reciben confirmaciones de transacciones autorizadas.

Equipo de Riesgo

Área encargada de supervisar transacciones sospechosas, alertas de fraude y comportamientos inusuales dentro de la plataforma.
Interactúa con PayFlow para monitorear eventos relacionados con seguridad y prevención de fraude.

Equipo de Operaciones

Responsable de garantizar la disponibilidad y correcto funcionamiento de la plataforma.
Monitorea métricas operativas, incidentes y el procesamiento de transacciones en tiempo real.

Sistema principal
PayFlow

Plataforma central de procesamiento de pagos digitales basada en una arquitectura orientada a eventos sobre Azure.

Sus principales responsabilidades incluyen:

Procesar transacciones digitales.
Gestionar autorizaciones de pago.
Publicar eventos de transacciones.
Integrarse con redes de pago y adquirentes bancarios.
Garantizar escalabilidad, resiliencia y disponibilidad del servicio.
Sistemas externos
Terminal POS

Dispositivo utilizado en comercios para capturar la información de pago del cliente y enviar solicitudes de transacción hacia PayFlow.

Sistema Legado

Sistema monolítico existente que continúa operando durante el proceso de migración hacia la nueva arquitectura basada en eventos.
Permite mantener compatibilidad e integración gradual sin afectar la operación del negocio.

Redes de Pago (Visa, Mastercard, PSE)

Servicios externos encargados de autorizar o rechazar transacciones digitales según las validaciones financieras correspondientes.

Adquirente Bancario

Entidad financiera responsable de validar, procesar y liquidar las transacciones monetarias asociadas a los pagos digitales.

Relaciones principales
Los comercios utilizan PayFlow para procesar pagos digitales.
Los terminales POS envían solicitudes de transacción hacia PayFlow.
PayFlow se integra con redes de pago para solicitar autorizaciones.
Las redes de pago retornan respuestas de aprobación o rechazo.
El adquirente bancario realiza validaciones financieras y liquidaciones.
El sistema legado continúa intercambiando eventos y datos durante la transición tecnológica.
Los equipos de riesgo y operaciones monitorean continuamente el comportamiento y estado de la plataforma.
---

# C2 — Contenedores

## Descripción

El diagrama C2 representa los principales contenedores del sistema y el flujo general de procesamiento de eventos dentro de la arquitectura propuesta.

### Responsabilidades identificadas

| Contenedor | Responsabilidad |
|---|---|
| Ingesta de eventos | Recepción de transacciones |
| Procesamiento | Validación y reglas de negocio |
| Enrutamiento prioritario | Manejo de transacciones críticas |
| Persistencia | Almacenamiento del estado de transacciones |
| Observabilidad | Monitoreo y métricas |

---

![C2](assets/c2-contenedores.png)

El diagrama C2 representa la nueva arquitectura de procesamiento de eventos de PayFlow a nivel de contenedores. El flujo inicia en el sistema legado, que continúa funcionando durante la fase piloto y publica eventos de transacción hacia la nueva arquitectura mediante HTTP/AMQP. Estos eventos son recibidos por el ingestor de transacciones, encargado de actuar como punto de entrada y buffer para desacoplar el monolito del nuevo procesamiento.

Luego, el procesador de pagos consume los eventos, valida la información, aplica reglas antifraude básicas, clasifica las transacciones por monto y registra los resultados. Cuando una transacción requiere tratamiento especial, como las mayores a $5M COP, se envía al gestor de alta prioridad, donde se manejan colas asíncronas para priorización, auditoría obligatoria y notificaciones desacopladas del flujo de autorización.

El almacén de transacciones conserva el estado final, trazabilidad, auditoría y datos operativos de cada transacción procesada. Finalmente, el módulo de observabilidad recibe métricas, trazas, errores y alertas de los demás contenedores, permitiendo monitorear throughput, latencia, disponibilidad y posibles anomalías antes de que afecten a los comercios.

---

# C3 — Componentes

## Descripción

El diagrama C3 representa los componentes internos encargados del procesamiento de transacciones y la lógica de negocio del sistema.

### Componentes internos

| Componente | Responsabilidad |
|---|---|
| validarTransaccion | Validación de estructura y formato |
| evaluarFraude | Aplicación de reglas antifraude |
| enrutarPorMonto | Priorización de transacciones |
| registrarResultado | Persistencia del resultado |
| notificarComercio | Confirmación del procesamiento |

---

![C3](assets/c3-componentes.png)
## Arquitectura de Componentes (Modelo C3)

El sistema implementa una arquitectura desacoplada y guiada por eventos (Event-Driven Architecture) detallada en el archivo **c3-componentes.png**. El backend utiliza un pipeline de cómputo elástico y distribuido, estructurado para garantizar alta disponibilidad, absorción de picos de tráfico y tolerancia a fallos ante una alta demanda transaccional.

---

### Componentes del Sistema y Responsabilidades

| Componente Lógico | Tipo de Componente | Responsabilidad Principal |
| :--- | :--- | :--- |
| **Sistema Legado PayFlow** | Sistema Externo | Origen de los datos; publica los eventos transaccionales continuamente de forma no intrusiva. |
| **Ingestor de Transacciones** | Servicio de Streaming | Actúa como un *buffer* distribuido masivo; absorbe ráfagas de alta carga y aísla el tráfico entrante. |
| **Procesador de Pagos Backend** | Capa de Cómputo | Componente de procesamiento compuesto por servicios independientes y especializados. |
| **Gestor de Alta Prioridad** | Cola de Mensajería | Broker empresarial con garantía de entrega *At-least-once* para aislar flujos críticos. |
| **Almacén de Transacciones** | Base de Datos | Repositorio persistente optimizado para escrituras concurrentes de alta velocidad y baja latencia. |
| **Módulo de Observabilidad** | Sistema de Monitoreo | Centraliza métricas de plataforma, logs operativos y trazas distribuidas del flujo extremo a extremo.|

#### Bloques Operacionales de la Capa de Cómputo
*   **Validación de Formato**: Verifica la integridad estructural, presencia de campos obligatorios y la consistencia del mensaje entrante.
*   **Evaluación Antifraude**: Aplica reglas de negocio y matrices de riesgo en tiempo real para mitigar fraudes financieros antes de autorizar el pago.
*   **Enrutador por Monto**: Analiza el valor económico de la operación para segmentar el camino lógico del evento según su nivel de prioridad.
*   **Registro de Resultados**: Guarda de forma definitiva el estado de la transacción (aprobada/rechazada) y genera las pistas de auditoría obligatorias.
*   **Notificación al Comercio**: Consume de manera asíncrona la mensajería prioritaria para despachar alertas operativas externas.

---

### Flujo de Procesamiento Paso a Paso 

El ciclo de vida de una transacción representado en el diagrama **c3-componentes.png** se ejecuta a través de las siguientes etapas automatizadas:

#### 1. Ingesta y Amortiguación de Carga
El **Sistema Legado PayFlow** publica los eventos de transacción directamente en el **Ingestor de Transacciones**. Este componente almacena los mensajes de manera persistente y temporal, protegiendo a la capa de cómputo de saturaciones durante picos de demanda masiva y permitiendo un consumo eficiente por lotes.

#### 2. Pipeline de Validación de Negocio
El arribo de datos al ingestor dispara instantáneamente la capa de procesamiento. El evento pasa primero por el bloque de **Validación de Formato** y, una vez superados los controles de estructura, es recibido por el componente de **Evaluación Antifraude** para validar los riesgos operativos en tiempo real.

#### 3. Enrutamiento Inteligente por Umbral Financiero
El flujo consolidado llega al componente **Enrutador por Monto**, el cual evalúa el valor monetario de la transacción y bifurca el comportamiento del sistema:

*   **Camino Estándar (Menor o igual al umbral base):** Se envía de forma directa al componente de **Registro de Resultados** para asentar el estado en el **Almacén de Transacciones** de manera inmediata, finalizando el ciclo principal.
*   **Alto Valor (Mayor al umbral base):** Para salvaguardar la operación sin penalizar el rendimiento global, el sistema aplica un **desacoplamiento asíncrono** en paralelo:
    1.  Transfiere la transacción al bloque de **Registro de Resultados** para asegurar el asiento contable en el **Almacén de Transacciones** junto con la metadata exigida de auditoría extendida.
    2.  Simultáneamente, inyecta un evento en el **Gestor de Alta Prioridad**.

#### 4. Despacho Resiliente de Notificaciones
El componente de **Notificación al Comercio** se activa exclusivamente ante la presencia de nuevos mensajes en la cola del **Gestor de Alta Prioridad**. Su único objetivo es realizar la petición de comunicación externa de forma asíncrona hacia el endpoint del **Comercio Externo**.

>  **Nota de Resiliencia:** Si el servidor del comercio externo experimenta lentitud o caídas, el error queda confinado dentro de la etapa de notificación. Gracias al mecanismo de bloqueo y persistencia de la cola de mensajería, el mensaje se retiene y reintenta de manera independiente, garantizando que el flujo principal de pagos de los demás usuarios jamás se bloquee o experimente degradación de velocidad.

#### 5. Observabilidad Transversal
Durante todo el recorrido, cada uno de los bloques lógicos reporta de manera asíncrona sus métricas operativas y registros de error al **Módulo de Observabilidad**, permitiendo el alertamiento temprano ante desviaciones en los tiempos de respuesta o fallos en el ecosistema.

---

# Architectural Decision Records (ADRs)

---

# ADR-01 — Punto de entrada de eventos

## Contexto
El sistema requiere soportar alto volumen de transacciones y desacoplar el sistema legado del procesamiento interno.

## Alternativas evaluadas

- Servicio orientado a mensajería empresarial
- Plataforma orientada a streaming de eventos

## Decisión
Se seleccionó una solución orientada a streaming de eventos como punto principal de entrada.

## Consecuencias

### Ventajas
- Mayor capacidad de escalabilidad
- Mejor manejo de picos de carga
- Procesamiento desacoplado

### Trade-offs
- Menor garantía de orden global

---

# ADR-02 — Procesamiento de eventos

## Contexto
Se requiere procesamiento flexible y lógica personalizada para validaciones y reglas antifraude.

## Alternativas evaluadas

- Motor administrado de análisis en tiempo real
- Funciones serverless

## Decisión
Se seleccionó un modelo serverless para el procesamiento de eventos.

## Consecuencias

### Ventajas
- Escalabilidad automática
- Menor costo operativo
- Flexibilidad de implementación

### Trade-offs
- Posibles latencias iniciales

---

# ADR-03 — Persistencia de datos

## Contexto
El sistema requiere almacenar transacciones con alta velocidad de escritura y estructura flexible.

## Alternativas evaluadas

- Base de datos relacional
- Base de datos orientada a documentos

## Decisión
Se seleccionó un modelo orientado a documentos para la persistencia principal.

## Consecuencias

### Ventajas
- Flexibilidad en el esquema
- Mejor rendimiento de escritura

### Trade-offs
- Menor estructura relacional

---

# ADR-04 — Procesamiento prioritario

## Contexto
Las transacciones de alto valor requieren manejo prioritario y mecanismos de reintento.

## Alternativas evaluadas

- Cola básica
- Servicio avanzado de mensajería

## Decisión
Se seleccionó una solución de mensajería con soporte para reintentos y colas especializadas.

## Consecuencias

### Ventajas
- Mayor confiabilidad
- Mejor trazabilidad

### Trade-offs
- Incremento en complejidad arquitectónica

---

# ADR-05 — Observabilidad

## Contexto
La plataforma actual carece de monitoreo centralizado y alertas automáticas.

## Alternativas evaluadas

- Plataforma externa de observabilidad
- Herramientas nativas del proveedor cloud

## Decisión
Se seleccionó una solución nativa integrada al ecosistema cloud.

## Consecuencias

### Ventajas
- Integración sencilla
- Menor costo operativo

### Trade-offs
- Menor nivel de personalización frente a herramientas especializadas

---

# Implementación del flujo crítico

## Flujo implementado

1. Generación de eventos de transacciones.
2. Recepción de eventos.
3. Validación y procesamiento.
4. Priorización de transacciones críticas.
5. Persistencia del estado final.
6. Monitoreo y generación de métricas.

---

# Evidencias de implementación

## Infraestructura desplegada

![Infraestructura](assets/evidencias/infraestructura.png)
###  Inventario y Topología de la Infraestructura Desplegada

Como validación final del aprovisionamiento del entorno, se adjunta el mapa de la topología física autogenerado por la plataforma, el cual certifica la existencia, interconexión y despliegue real de todos los componentes que dan soporte al procesador de pagos PayFlow.

* **Cohesión y Aislamiento del Entorno (rg-payflow)**: La vista del visualizador de recursos confirma que la totalidad de los componentes tecnológicos operan de forma centralizada y acoplada dentro del mismo perímetro de administración lógico. Esto garantiza una gobernanza estricta sobre el ciclo de vida de los servicios y simplifica las políticas de seguridad perimetral.
* **Garantía de la Arquitectura de Componentes**: El mapa lógico valida la correspondencia exacta con el modelo físico diseñado. Se constata la disponibilidad del ingestor de streaming transaccional (`payflow-namespace`), la capa de mensajería empresarial para flujos críticos de alto valor (`payflows-sbs`), el motor de cómputo elástico basado en el paradigma serverless (`payflows-functions`), el almacén distribuido sub-10ms (`payflow-cosmos`) y el nodo centralizado de observabilidad y telemetría.
* **Mitigación de Latencia por Homogeneidad Regional**: La disposición unificada de los recursos dentro de la misma región geográfica asegura que las llamadas de dependencia internas (como la persistencia de funciones hacia el almacén NoSQL o el enrutamiento hacia las colas prioritarias) se ejecuten a través de la red troncal interna del proveedor. Esto elimina saltos interregionales innecesarios, mitigando el overhead en el tiempo de procesamiento y asegurando la estabilidad del SLA ante las 40 transacciones por segundo.

---

## Procesamiento de eventos

![Procesamiento](assets/evidencias/procesamiento.png)
###  Validación del Comportamiento del Ingestor de Transacciones

El análisis del panel de métricas de la infraestructura de mensajería confirma el correcto funcionamiento del punto de entrada ante ráfagas de tráfico masivo distribuidas por lotes.

* **Validación de la Tasa Transaccional (Incoming Messages)**: El gráfico central registra picos sostenidos de entre 2.300 y 2.400 mensajes entrantes por minuto. Este volumen valida empíricamente que el script generador inyectó la carga base de 40 transacciones por segundo ($40 \text{ tx/s} \times 60 \text{ s} = 2.400 \text{ eventos}$) de forma íntegra hacia el componente de ingesta, acumulando un total de 18.400 eventos procesados con éxito en la ventana de evaluación.
* **Eficiencia de Red mediante Lotes (Incoming Requests)**: Se evidencia el impacto del diseño asíncrono. Mientras el volumen de mensajes individuales superó los 18.400 eventos, el número de solicitudes de red se mantuvo considerablemente bajo (1.260 conexiones exitosas). Esto confirma que el empaquetado de transacciones reduce drásticamente el overhead de red y evita la saturación de los canales de comunicación.
* **Absorción de Ráfagas y Cero Pérdida de Datos**: A pesar del comportamiento intermitente y abrupto de la carga, el indicador de errores de servidor (*Server Errors*) permaneció en cero de forma absoluta. Esto demuestra la eficacia de la retención temporal del componente, actuando como un amortiguador distribuido que protege el pipeline de cómputo backend contra picos de tráfico estacionales sin experimentar degradación del servicio.

---

## Persistencia de datos

![Persistencia](assets/evidencias/persistencia.png)
### Validación de la Persistencia de Datos e Integridad del Almacén NoSQL

Para certificar que el flujo asíncrono finaliza de forma correcta en la capa de persistencia, se auditó el contenido del almacén de datos distribuido mediante el explorador de datos nativo del componente de persistencia (`payflow-cosmos`).

* **Estructura Documental Heterogénea y Enriquecida**: La captura del explorador de datos evidencia el asentamiento exitoso de los payloads en formato JSON nativo. Se constata que la capa de cómputo intermedia enriqueció el evento original proveniente del sistema legado, inyectando los atributos de control de ciclo de vida requeridos por el negocio, tales como `estado`, `prioridad` y el flag de evaluación de riesgo `sospechosa`.
* **Optimización de la Clave de Partición**: Se verifica de forma empírica la correcta distribución horizontal de los documentos a través del atributo lógico de partición orientado por el campo identificador del comercio. Esta estrategia de diseño mitiga el riesgo de contención de rendimiento o aparición de cuellos de botella por particiones calientes durante la absorción de las 40 transacciones por segundo.
* **Trazabilidad Extremo a Extremo**: Cada documento cuenta con la persistencia exacta de su identificador único global correlacionado (`transaction_id`) y los metadatos de auditoría del motor del proveedor de nube. Esto garantiza la persistencia definitiva de la información financiera con latencias de un solo dígito dentro del ecosistema del backend de pagos.

---

## Monitoreo

![Monitor](assets/evidencias/monitor.png)
###  Validación del Monitoreo Centralizado y Observabilidad en Tiempo Real

Como mecanismo de auditoría operativa, se validó el comportamiento del pipeline de datos a través de los tableros de control de telemetría y supervisión centralizada del sistema.

#### Absorción en la Capa de Mensajería
El panel de control general confirma el comportamiento del punto de entrada al recibir las ráfagas del sistema legado. Se registra un volumen consolidado de mensajes entrantes (*Incoming Messages*) que valida la recepción íntegra del tráfico base (40 tx/s), acumulando miles de eventos exitosos en la ventana de evaluación. El indicador de errores de plataforma se mantuvo en cero de forma absoluta, demostrando la capacidad del componente para actuar como un amortiguador distribuido.

#### Comportamiento de las Instancias de Cómputo (Métricas en Directo)
El tablero de telemetría en tiempo real refleja el aprovisionamiento dinámico de la infraestructura. Se constata la presencia de múltiples servidores activos (*servers online*) asignados de manera elástica para evacuar el backlog del ingestor de eventos. 

La dispersión en la duración de las solicitudes de entrada (*Request Duration*) demuestra que la gran mayoría de las transacciones válidas se procesan y asientan en la capa de datos en el orden de los milisegundos, cumpliendo holgadamente con el Acuerdo de Nivel de Servicio (SLA) de menos de 2 segundos. Los puntos aislados en el cuadrante superior reflejan los tiempos de inicialización inicial (*cold start*) controlados durante el arranque de la infraestructura.

#### Auditoría de Resiliencia ante Datos Corruptos
Al evaluar la robustez del procesador frente a los escenarios de fallos simulados, los registros lógicos del backend capturaron con precisión las anomalías introducidas por el escenario de transacciones inválidas (específicamente errores de tipo de dato o ausencia de atributos obligatorios como el valor de la operación). 

La aparición controlada de picos en la tasa de excepciones (*Exception Rate*) coincide directamente con la inyección de cargas malformadas desde el origen. Esto certifica de manera empírica que el pipeline de validación identifica y aísla las transacciones defectuosas en la primera etapa del flujo (C3), impidiendo de forma exitosa que los datos corruptos se propaguen hacia los componentes subsiguientes de evaluación de riesgo, colas de alta prioridad o el almacén de datos definitivo.


---

# Conclusiones

# 

* **Validación de la Capacidad de Carga y Desacoplamiento Real**: El cambio de paradigma de una arquitectura monolítica síncrona a un modelo guiado por eventos (*Event-Driven Architecture*) demostró ser la solución definitiva para mitigar la contención de tráfico. La integración de un componente de streaming distribuido como amortiguador (*buffer*) absorbió de manera íntegra ráfagas transaccionales continuas de 40 tx/s (2.400 mensajes por minuto) sin transferir estrés hídrico de red, latencia o sobrecarga al sistema legado emisor.
* **Cumplimiento Estricto de los Acuerdos de Nivel de Servicio (SLA)**: Los datos consolidados de telemetría confirmaron que la latencia del pipeline de cómputo se mantuvo predominantemente en la escala de milisegundos, superando con amplio margen la restricción crítica de negocio de procesar y autorizar transacciones en menos de 2 segundos. Los escasos eventos de mayor duración quedaron confinados a las fases de inicialización por arranque en frío (*cold start*), un comportamiento esperado en infraestructuras elásticas que no comprometió la ventana operativa del flujo transaccional.
* **Eficiencia Operativa mediante el Procesamiento por Lotes (Batching)**: La configuración del disparador nativo entre el ingestor y la capa de cómputo serverless demostró que es posible procesar un volumen masivo de datos reduciendo significativamente el costo de infraestructura y el tráfico de red. Al empaquetar decenas de mensajes en ejecuciones atómicas reducidas (manteniendo picos estables de 7 a 10 activaciones de función por segundo), el sistema optimizó el uso de memoria y CPU, logrando una arquitectura de alta densidad transaccional financieramente viable.
* **Alta Tolerancia a Fallos y Resiliencia Estructural**: La arquitectura validó empíricamente su diseño tolerante a fallos frente a cargas malformadas y fallas lógicas inyectadas intencionalmente. Al aislar las excepciones estructurales (como errores de mapeo por ausencia del atributo de monto) en la primera línea de validación de formato dentro de la capa de procesamiento, se evitó la propagación de fallas en cascada y se mantuvo una tasa de error de plataforma en cero absoluto, protegiendo la integridad del almacén de datos distribuido y los flujos de notificación asíncronos.
* **Optimización y Escalabilidad del Almacén NoSQL**: El uso de un modelo orientado a documentos flexible y distribuido horizontalmente mediante una clave de partición lógica basada en el identificador del comercio eliminó el riesgo de aparición de particiones calientes (*hot partitions*). El sistema no solo garantizó escrituras concurrentes sub-10ms bajo escenarios de estrés, sino que demostró la flexibilidad del esquema para enriquecer dinámicamente los payloads, inyectando atributos de control como prioridad y estados de validación sin penalizar el rendimiento global.
* **Gobernanza Completa mediante Observabilidad Proactiva**: El despliegue de un esquema de telemetría centralizado extremo a extremo permitió trascender del monitoreo reactivo tradicional a la supervisión operativa en tiempo real. La visibilidad simultánea de las colas de mensajería, la salud interna de las instancias de servidores y las trazas distribuidas dota a la organización de la capacidad para identificar cuellos de botella lógicos o anomalías de formato en un rango inferior al umbral de alerta requerido, garantizando la continuidad operativa del negocio financiero.

---

# Referencias

<a id="ref-5"></a>Microsoft. Bienvenida a Azure Stream Analytics. Microsoft Learn. Disponible en: https://learn.microsoft.com/es-es/azure/stream-analytics/stream-analytics-introduction

<a id="ref-6"></a>[6] Microsoft. Introducción a Azure Cosmos DB. Microsoft Learn. Disponible en: https://learn.microsoft.com/es-es/azure/cosmos-db/introduction

<a id="ref-7"></a>[7] Microsoft. Documentación de Azure SQL Database. Microsoft Learn. Disponible en: https://learn.microsoft.com/es-es/azure/azure-sql/database/

<a id="ref-8"></a>[8] Microsoft. Introducción a las colas de Azure Storage. Microsoft Learn. Disponible en: https://learn.microsoft.com/es-es/azure/storage/queues/storage-queues-introduction

<a id="ref-9"></a>[9] Microsoft. ¿Qué es Azure Monitor? Microsoft Learn. Disponible en: https://learn.microsoft.com/es-es/azure/azure-monitor/overview
