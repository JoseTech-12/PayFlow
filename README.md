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

---

## Procesamiento de eventos

![Procesamiento](assets/evidencias/procesamiento.png)

---

## Persistencia de datos

![Persistencia](assets/evidencias/persistencia.png)

---

## Monitoreo

![Monitor](assets/evidencias/monitor.png)

---

# Matriz de control de cambios

| ID | Fecha | Responsable | Observación |
|---|---|---|---|
| RFC-01 | 2026-05-01 | Equipo | Creación inicial del repositorio |
| RFC-02 | 2026-05-03 | Equipo | Inclusión del modelo C4 |
| RFC-03 | 2026-05-06 | Equipo | Documentación de ADRs |
| RFC-04 | 2026-05-09 | Equipo | Evidencias de implementación |
| RFC-05 | 2026-05-12 | Equipo | Ajustes finales y conclusiones |

---

# Conclusiones

- La arquitectura orientada a eventos permitió desacoplar los procesos críticos del sistema.
- La nueva propuesta mejora la capacidad de procesamiento frente a picos de demanda.
- El modelo planteado facilita la observabilidad y trazabilidad de transacciones.
- La separación de responsabilidades reduce el impacto de fallos externos.
- El enfoque serverless permite optimizar costos operativos durante el piloto.

---

# Referencias

- Microsoft Azure Architecture Center
- Arquitectura orientada a eventos
- Documentación oficial de servicios cloud utilizados
- Caso de estudio PayFlow
